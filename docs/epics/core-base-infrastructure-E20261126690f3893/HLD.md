<!-- insrc:artifact HLD-690f38931e7d3b57 -->

# HLD: core-base-infrastructure

## Summary

Everything the later modules share lives under one core: shared definitions in common, shared functions in utils, and one package for each job that needs doing. Memory keeps normalized entries with a reference to where they came from, not the original wording; the local model compares each new entry with similar ones, and retired entries move to history on a schedule. Updates are idempotent, and entries can be found by the official names tagged in them.

## Contents

1. [Problem context](#1-problem-context)
2. [Framework summary](#2-framework-summary)
3. [Architecture shape](#3-architecture-shape)
4. [Diagrams](#4-diagrams)
5. [Shared contracts](#5-shared-contracts)
6. [Story boundaries](#6-story-boundaries)
7. [Non-functional targets](#7-non-functional-targets)
8. [Rollout](#8-rollout)
9. [Alternatives considered](#9-alternatives-considered)
10. [References](#10-references)

## 1. Problem context

> See **DEF-690f38931e7d3b57** § 1. Problem

## 2. Framework summary

agent_pfc/core holds only subpackages. core/common holds the shared definitions and core/utils the shared functions, each divided into modules by subject. locations, config, activity, identity, client and cache/embedding each do one job. An import table enforced by test keeps dependencies pointing one way.

## 3. Architecture shape

Packages under agent_pfc/core and what each may import from the project. common: utils. utils: common. locations, identity and cache.embedding: common, utils. config: common, utils, locations. activity: common, utils, locations, config. client: common, utils, config, activity. common and utils may import each other as packages, never in a cycle between modules, and the import-direction test checks both rules. Modules of common are entries, checkpoints and failures (s1), locations, settings and activity shapes (s2), project resolution shape (s3), server contract (s4), and embedding, extraction and storage interfaces (s5). utils begins with the validation module that the definitions use (s1). core and core.cache are namespaces with no code of their own. Nothing under core may import anything in the project outside core. Later modules sit beside core.

The existing embeddings package is dissolved: its protocol and fingerprint move to common's embedding module, its checks to utils, its error becomes the backend failure kind, and its disk cache moves to cache/embedding with unchanged behaviour. The import-direction test is extended to packages nested two and three levels deep.

Entries hold normalized text of at most 500 characters and a source reference to the session file and position; the original wording is not stored. Names are normalized by models, not by code: the extractor's implementation instructs the local model to split each turn into simple directives and facts, write each named entity's official name, keeping versions, reusing the project's known names, and tag it; the calling agent is steered to the same rule and sends official names with its query. The store keyword indexes only tagged entities and matches them loosely against the names of a query. The index is private to the store.

Adding a rule takes two model steps. The extractor turns a window into candidates; the caller fetches similar entries for each; the extractor then decides whether a candidate is new, a duplicate or a replacement. A retired entry records when it was retired. The store takes new entries only as active with an unused identifier and never returns retired ones from a search. A scheduled compaction, written by the single indexer thread, moves retired entries to history without their embedding or keyword index, purges those older than the configured period, which is off by default, and removes old table versions.

## 4. Diagrams

- [ER model](./er-model.html)
- [Component dependencies](./component-dependency.html)

## 5. Shared contracts

### 5.1 sc1: Memory definitions, checkpoints and failures

**Owner Story:** `s1`
**Consumed by:** `s2`, `s3`, `s4`, `s5`

**Purpose:** One definition of entries and their named entities, sources, projects, session checkpoints and the failures modules raise.

**Interface sketch (type-level):**

```
type EntryKind = 'instruction' | 'data_point'; type EntryStatus = 'active' | 'retired';
interface ProjectId { value: string }
// A reference to where an entry came from. The original wording is not stored.
interface Source { agent: string; sessionId: string; file: string; position: number; spokenAt: string }
interface Provenance { extractionModel: string; embeddingModel: string }
// An official name in an entry's text, such as a library, database or file. Valid only if text equals the entry text from start up to, not including, end.
interface NamedEntity { text: string; start: number; end: number }
// text is normalized, uses official names and is at most 500 characters.
// retiredAt is an offset time, present on a retired entry and absent on an active one; replacedBy only on a retired one.
interface Entry { id: string; project: ProjectId; kind: EntryKind; text: string; entities: NamedEntity[]; sources: Source[]; provenance: Provenance; status: EntryStatus; retiredAt?: string; replacedBy?: string; retire(retiredAt: string, replacedBy?: string): void }
// retire changes this entry, once, recording the time its caller gives; nothing else about an entry changes. A retired entry is never reactivated, and retiring it again is invalid input.
// Entries compare by value. Refusing a copy of a retired entry is the store's duty (sc9).
// An empty kind or project is invalid input naming the field.
interface Checkpoint { agent: string; sessionId: string; file: string; position: number; lastMessageId: string; lastMessageAt: string }
type FailureKind = 'invalid_input' | 'invalid_configuration' | 'unknown_project' | 'server_unreachable' | 'incompatible_version' | 'request_failed' | 'backend_failed';
interface Failure { kind: FailureKind; message: string }
```

**Assumptions cited:** [[c5]]

### 5.2 sc2: Core layout and import table

**Owner Story:** `s1`
**Consumed by:** `s2`, `s3`, `s4`, `s5`

**Purpose:** Which core packages exist and what each may import.

**Interface sketch (type-level):**

```
interface ImportTable { [packagePath: string]: string[] }
// 'core.common': ['core.utils']; 'core.utils': ['core.common']
// 'core.locations', 'core.identity', 'core.cache.embedding': ['core.common','core.utils']
// 'core.config': ['core.common','core.utils','core.locations']
// 'core.activity': ['core.common','core.utils','core.locations','core.config']
// 'core.client': ['core.common','core.utils','core.config','core.activity']
// No cycle between modules.
```

### 5.3 sc10: Definition checks

**Owner Story:** `s1`
**Consumed by:** `s2`, `s3`, `s4`, `s5`

**Purpose:** One implementation of each check that definitions, settings and requests apply to their values.

**Interface sketch (type-level):**

```
// Module core.utils.validation. Each check returns the accepted value or raises an invalid_input Failure naming the field.
interface Validation { requireText(field: string, value: unknown): string; requirePosition(field: string, value: unknown): number; requireOffsetTime(field: string, value: unknown): string }
```

### 5.4 sc3: File locations

**Owner Story:** `s2`
**Consumed by:** `s4`

**Purpose:** Where configuration, data, models and logs live on the current platform.

**Interface sketch (type-level):**

```
interface Locations { configFile: string; dataDir: string; modelDir: string; logDir: string }
```

### 5.5 sc4: Settings

**Owner Story:** `s2`
**Consumed by:** `s4`

**Purpose:** Validated settings, including model choices, the server address, session archiving and the compaction schedule.

**Interface sketch (type-level):**

```
interface ModelChoice { source: string; file: string }
// intervalMinutes: how often compaction runs; its default is set by the s2 design.
// purgeAfterDays: how long history keeps a retired entry; null, meaning never purged, when the configuration does not set it.
interface CompactionSettings { intervalMinutes: number; purgeAfterDays: number | null }
// archiveSessions is false when the configuration does not set it.
interface Settings { embeddingModel: ModelChoice; extractionModel: ModelChoice; server: { host: string; port: number }; archiveSessions: boolean; compaction: CompactionSettings }
```

### 5.6 sc5: Activity record

**Owner Story:** `s2`
**Consumed by:** `s4`

**Purpose:** One shape for what every process records.

**Interface sketch (type-level):**

```
interface ActivityRecord { at: string; process: string; level: 'debug' | 'info' | 'warning' | 'error'; event: string; message: string }
```

### 5.7 sc6: Project resolution

**Owner Story:** `s3`
**Consumed by:** `s4`

**Purpose:** One rule that turns a working location into a project, or says it cannot.

**Interface sketch (type-level):**

```
interface ProjectResolver { resolve(location: string): ProjectId }
```

### 5.8 sc7: Memory server contract and client

**Owner Story:** `s4`

**Purpose:** The versioned requests and answers of the memory server and the one way to send them, with idempotent updates.

**Interface sketch (type-level):**

```
interface ContractVersion { major: number; minor: number }
interface QueryRequest { version: ContractVersion; project: ProjectId; text: string; entities: string[]; kind?: EntryKind; limit: number }
// entities: official names the calling agent gives for what the query is about; may be empty.
// Results never include retired entries.
interface QueryResult { entry: Entry; score: number }
interface QueryResponse { version: ContractVersion; results: QueryResult[] }
interface NamesRequest { version: ContractVersion; project: ProjectId }
interface NamesResponse { version: ContractVersion; names: string[] }
interface CheckpointRequest { version: ContractVersion; agent: string; sessionId: string }
interface CheckpointResponse { version: ContractVersion; checkpoint: Checkpoint | null }
interface Retirement { entryId: string; retiredAt: string; replacedBy?: string }
interface UpdateRequest { version: ContractVersion; project: ProjectId; from: Checkpoint | null; to: Checkpoint; add: Entry[]; retire: Retirement[] }
type UpdateOutcome = 'applied' | 'unchanged' | 'out_of_sequence';
interface UpdateResponse { version: ContractVersion; outcome: UpdateOutcome; checkpoint: Checkpoint | null; added: string[]; retired: string[] }
// Decided in this order against the stored checkpoint of the session:
// 'unchanged'       to.position is at or before the stored position
// 'applied'         from equals the stored checkpoint (both null for a new session); the stored checkpoint becomes to
// 'out_of_sequence' anything else; nothing changes and the stored checkpoint is returned
// An update that would apply but adds an entry that is not active, or whose id is already used, is invalid_input and nothing changes.
// Additions are applied before retirements, so one update may add an entry and retire it.
interface MemoryClient { query(request: QueryRequest): QueryResponse; names(request: NamesRequest): NamesResponse; checkpoint(request: CheckpointRequest): CheckpointResponse; update(request: UpdateRequest): UpdateResponse }
```

### 5.9 sc8: Embedding interface and cache

**Owner Story:** `s5`

**Purpose:** Turning text into vectors that say which model produced them, with an optional disk cache offering the same interface.

**Interface sketch (type-level):**

```
interface EncoderFingerprint { modelName: string; modelDigest: string; quantization: string; backendName: string; backendVersion: string; dimension: number; textConvention: string; dtype: string }
interface Embedder { fingerprint: EncoderFingerprint; encode(texts: string[]): number[][] }
interface CachedEmbedder extends Embedder { }
```

**Assumptions cited:** [[c5]]

### 5.10 sc9: Extraction and storage interfaces

**Owner Story:** `s5`

**Purpose:** Turning conversation messages into candidate entries that use and tag official names, comparing them with similar ones, and keeping, finding and compacting entries and checkpoints, without naming a runtime or store.

**Interface sketch (type-level):**

```
// text is the original wording, read while parsing and not stored.
interface Message { source: Source; role: 'user' | 'agent'; text: string }
interface Candidate { kind: EntryKind; text: string; entities: NamedEntity[]; sources: Source[] }
// replaces: ids of entries in stored. replacesEarlier: positions in earlier.
interface Comparison { outcome: 'new' | 'duplicate' | 'replacement'; replaces: string[]; replacesEarlier: number[] }
interface Extractor { modelName: string; extract(window: Message[], knownNames: string[]): Candidate[]; compare(candidate: Candidate, stored: Entry[], earlier: Candidate[]): Comparison }
// Each candidate holds one directive or fact, with the condition or scope that applies to it; one message may give several.
// Candidate text uses official names, keeping versions, and reuses a known name where it means the same thing.
// Every implementation returns only entities that appear in the candidate text, with their positions, and no text over 500 characters.
// The caller gives compare the similar active entries, found by vector and name search, and the candidates kept earlier in the same run.
// 'duplicate': the candidate means the same as one of them and is not added. 'new': nothing is replaced. 'replacement': at least one is replaced.
// A replaced earlier candidate not yet stored is added and retired in the same change, so history keeps it.
interface StoredVector { fingerprint: EncoderFingerprint; values: number[] }
interface Retirement { entryId: string; retiredAt: string; replacedBy?: string }
interface Change { from: Checkpoint | null; to: Checkpoint; add: { entry: Entry; vector: StoredVector }[]; retire: Retirement[] }
interface ChangeResult { outcome: 'applied' | 'unchanged' | 'out_of_sequence'; checkpoint: Checkpoint | null }
interface CompactionResult { moved: number; purged: number }
interface EntryStore { checkpoint(agent: string, sessionId: string): Checkpoint | null; apply(change: Change): ChangeResult; names(project: ProjectId): string[]; search(project: ProjectId, vector: StoredVector, entities: string[], kind: EntryKind | null, limit: number): { entry: Entry; score: number }[]; compact(now: string, purgeAfterDays: number | null): CompactionResult }
// Guarantees required of every implementation:
// after a failure at any point, submitting the same change again leaves no entry stored twice;
// an added entry is accepted only if it is active and its id is used by no active or history entry;
// only a retirement changes an existing entry; additions are applied before retirements;
// search never returns a retired entry, whether or not compaction has run;
// compact moves retired entries to history without their vector or keyword index, removes from history those retired more than purgeAfterDays before now (none when null), and removes old table versions;
// apply and compact are called only by the single indexer thread;
// only tagged entities are keyword indexed;
// an entry whose tagged entity loosely matches a name in the query is a search candidate even if vector search would not have returned it;
// missing a relevant entry is worse than returning an extra one;
// exact name matches rank ahead of looser ones, and looser matches do not crowd out strong vector results.
```

## 6. Story boundaries

### 6.1 Story STORY-690f38931e7d3b57-s1

**Owns:** `sc1`, `sc2`, `sc10`

How entries and named entities are checked and represented in Python, the entries, checkpoints and failures modules of core/common, the validation module of core/utils, and the changes to the import-direction test for nested packages and module cycles.

### 6.2 Story STORY-690f38931e7d3b57-s2

**Owns:** `sc3`, `sc4`, `sc5`
**Depends on:** `sc1`, `sc10`, `sc2`

Per-platform location rules, the configuration file format and its validation, including the compaction defaults, and how activity is written and rotated. Session archiving itself belongs to a later module.

### 6.3 Story STORY-690f38931e7d3b57-s3

**Owns:** `sc6`
**Depends on:** `sc1`, `sc10`, `sc2`

The rule that identifies a project from a location and how it behaves across worktrees and machines.

### 6.4 Story STORY-690f38931e7d3b57-s4

**Owns:** `sc7`
**Depends on:** `sc1`, `sc10`, `sc2`, `sc3`, `sc4`, `sc5`, `sc6`

Wire encoding, endpoint layout, version compatibility rule, time limits, the HTTP library and how failures are mapped to shared kinds.

### 6.5 Story STORY-690f38931e7d3b57-s5

**Owns:** `sc8`, `sc9`
**Depends on:** `sc1`, `sc10`, `sc2`

The move of the embedding protocol into core/common, of its checks into core/utils and of its cache into core/cache/embedding, and the exact method signatures of the interfaces. The local model's instructions belong to the parser design and the calling agent's steering to the MCP adapter design. The loose matching technique, the ranking, the meaning of a score, how history is laid out and how compaction works are left to the store design, and starting compaction on schedule to the memory server design.

## 7. Non-functional targets

- **Performance:** No targets are agreed.
- **Observability:** Every process records activity in the shape of sc5; the client records its calls through the activity package.
- **Durability:** Updates are idempotent: the session checkpoint decides whether a change is applied, unchanged or out of sequence, and a checkpoint advances only with stored entries. The store design must keep this true across a failure between writing entries and advancing the checkpoint.

## 8. Rollout

**Phase A: definitions and layout**

**Stories:** `s1`

Every other story uses the definitions, checks, failure kinds and import table.

**Backward compat:** The existing embedding tests keep passing; the import test still rejects unlisted packages.

**Phase B: base infrastructure and interfaces**

**Stories:** `s2`, `s3`, `s5`

Each depends only on the shared definitions, checks and layout.

**Backward compat:** The embedding protocol and cache move with unchanged behaviour and the cache tests keep passing.

**Phase C: server contract and client**

**Stories:** `s4`

The client needs settings, activity records and project identity.

**Ordering rationale:** s1 first because all stories depend on it; s2, s3 and s5 are independent of each other; s4 depends on s2 and s3 and lands last.

**Risky bits**

| Area | Why | Mitigation |
| :--- | :--- | :--- |
| Interrupted writes | A failure between writing entries and advancing the checkpoint could store entries twice, and one during compaction could lose entries that should be kept. | sc9 requires that resubmitting adds nothing twice; the store design must show how updates and compaction survive interruption, checking what LanceDB can commit together. |
| Positions in history files | Checkpoints and source references assume a position that only increases in an appended file; a rewritten or split file would break both. | The history reader design confirms this for each agent before relying on it. |
| Judgments by the local model | With no original wording stored, a lost condition, a badly split turn or a wrong name cannot be detected from stored data; a wrong comparison drops a new rule as a duplicate or retires a valid one, and purging can then erase it. | The parser test measures splitting, kept conditions, names, duplicates and replacements before the parser design is accepted; purging stays off by default. |

## 9. Alternatives considered

### 9.1 a1: Nested core with common and utils packages — **CHOSEN**

Core packages under agent_pfc/core, with shared definitions in core/common, shared functions in core/utils and behaviour in separate packages.

A core namespace holds only subpackages. core/common holds the shared definitions and core/utils the shared functions, such as the checks the definitions run; both are divided into modules by subject.

Packages that do work sit beside them under core. The import-direction test enforces a table, rejects cycles between modules and forbids anything under core from importing outside it. This is the shape the project owner has chosen.

**Pros:**
- Each shared rule is written once.
- Every shared definition and function has one place to look for it.
- The core boundary shows in every import path and one rule enforces it.

**Cons:**
- common and utils depend on each other as packages, so the test must also check for module cycles.
- A package needing one definition depends on the package holding all of them.
- The import checker must be rewritten to handle nested packages.

**Cost estimate:** M

### 9.2 a2: Nested core with a definitions package per subject

Core packages under agent_pfc/core, with separate packages for entries, failures, contract and each interface.

The same core namespace, but definitions are split into one package per subject, each holding its own checks.

Behaviour packages depend only on the definition packages they use, and the import table lists each edge.

**Pros:**
- Each dependency names exactly what a package uses.
- No two packages depend on each other.

**Cons:**
- Checks are repeated across packages.
- Does not put shared code in common and utils packages, which the owner requires.

**Cost estimate:** M

**Rejected because:** Fails the shared-code constraint.

### 9.3 a3: Flat packages without a core namespace

Common, utils and behaviour packages directly under agent_pfc with an import table.

No core namespace; core packages and later modules sit side by side directly under the project package.

Which packages form the core is recorded as a list in the import-direction test.

**Pros:**
- The existing one-level import checker needs the least change.
- Import paths are shorter.

**Cons:**
- The core boundary is visible only in the test, not in the tree.
- The owner has decided the packages belong under core.

**Cost estimate:** S

**Rejected because:** Weakens the core boundary and goes against the owner's decision to nest under core.

## 10. References

- **[[c1]]** `analyze-bundle` `s1` — "One source package with a single subpackage, embeddings; the only project imports are inside it or from tests."
- **[[c2]]** `code` `src/agent_pfc/embeddings/protocol.py:26`
- **[[c3]]** `code` `src/agent_pfc/embeddings/cache.py`
- **[[c4]]** `code` `tests/test_architecture.py`
- **[[c5]]** `doc` `docs/REQUIREMENTS.md`
- **[[c6]]** `convention` `CLAUDE.md:18-28`
