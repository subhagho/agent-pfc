<!-- insrc:artifact HLD-3b5f9aa550b6fe9d -->

# HLD: core-base-infrastructure

## Summary

Everything the later modules share lives under one core: a single package of definitions that depends on nothing, and one package for each job that needs doing. Updates to memory are idempotent because every one states the session checkpoint it started from and the one it reached. The local model writes official names into each entry and tags them, and the calling agent sends official names with its query, so entries can be found by name.

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

> See **DEF-3b5f9aa550b6fe9d** § 1. Problem

## 2. Framework summary

agent_pfc/core holds only subpackages. core/common holds every shared definition, one subject per module, and imports nothing from the project; this is how constraint k1 is met, as the only common package allowed. locations, config, activity, identity, client and cache/embedding each do one job. An import table enforced by test keeps dependencies pointing one way.

## 3. Architecture shape

Packages under agent_pfc/core and what each may import from the project. common: nothing. Its modules are entries, checkpoints and failures (s1), locations, settings and activity shapes (s2), project resolution shape (s3), server contract (s4), and embedding, extraction and storage interfaces (s5); it does no I/O and holds no helper functions, only definitions and the validity checks of those definitions. locations: common. identity: common. cache.embedding: common. config: common, locations. activity: common, locations, config. client: common, config, activity. core and core.cache are namespaces with no code of their own; core.cache is open to other kinds of cache. Nothing under core may import anything in the project outside core. Later modules sit beside core.

The existing embeddings package is dissolved: its protocol and fingerprint move to common's embedding module with their validity checks, its error becomes the backend failure kind, and its disk cache moves to cache/embedding with unchanged behaviour. The import-direction test is extended to packages nested two and three levels deep.

Named entities are part of an entry's definition. Names are normalized by models, not by code: the extractor's implementation instructs the local model to write each named entity's official name, keeping versions, reusing the project's known names, and to tag it; the calling agent is steered to the same rule and sends official names with its query. There is no normalizer package or alias list. The store keyword indexes only tagged entities and matches them loosely against the names of a query. The index is private to the store and is not part of the core.

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
interface Source { agent: string; sessionId: string; messageId: string; spokenAt: string; author: string; text: string }
// Source.text keeps the original wording; Entry.text is normalized and uses official names.
interface Provenance { extractionModel: string; embeddingModel: string }
// An official name in an entry's text, such as a library, database or file. Valid only if text equals the entry text from start up to, not including, end.
interface NamedEntity { text: string; start: number; end: number }
interface Entry { id: string; project: ProjectId; kind: EntryKind; text: string; entities: NamedEntity[]; sources: Source[]; provenance: Provenance; status: EntryStatus; replacedBy?: string }
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
// 'core.common': []
// 'core.locations': ['core.common']; 'core.identity': ['core.common']; 'core.cache.embedding': ['core.common']
// 'core.config': ['core.common','core.locations']
// 'core.activity': ['core.common','core.locations','core.config']
// 'core.client': ['core.common','core.config','core.activity']
```

### 5.3 sc3: File locations

**Owner Story:** `s2`
**Consumed by:** `s4`

**Purpose:** Where configuration, data, models and logs live on the current platform.

**Interface sketch (type-level):**

```
interface Locations { configFile: string; dataDir: string; modelDir: string; logDir: string }
```

### 5.4 sc4: Settings

**Owner Story:** `s2`
**Consumed by:** `s4`

**Purpose:** Validated settings, including model choices and the server address.

**Interface sketch (type-level):**

```
interface ModelChoice { source: string; file: string }
interface Settings { embeddingModel: ModelChoice; extractionModel: ModelChoice; server: { host: string; port: number } }
```

### 5.5 sc5: Activity record

**Owner Story:** `s2`
**Consumed by:** `s4`

**Purpose:** One shape for what every process records.

**Interface sketch (type-level):**

```
interface ActivityRecord { at: string; process: string; level: 'debug' | 'info' | 'warning' | 'error'; event: string; message: string }
```

### 5.6 sc6: Project resolution

**Owner Story:** `s3`
**Consumed by:** `s4`

**Purpose:** One rule that turns a working location into a project, or says it cannot.

**Interface sketch (type-level):**

```
interface ProjectResolver { resolve(location: string): ProjectId }
```

### 5.7 sc7: Memory server contract and client

**Owner Story:** `s4`

**Purpose:** The versioned requests and answers of the memory server and the one way to send them, with idempotent updates.

**Interface sketch (type-level):**

```
interface ContractVersion { major: number; minor: number }
interface QueryRequest { version: ContractVersion; project: ProjectId; text: string; entities: string[]; kind?: EntryKind; limit: number }
// entities: official names the calling agent gives for what the query is about; may be empty.
interface QueryResult { entry: Entry; score: number }
interface QueryResponse { version: ContractVersion; results: QueryResult[] }
interface NamesRequest { version: ContractVersion; project: ProjectId }
interface NamesResponse { version: ContractVersion; names: string[] }
interface CheckpointRequest { version: ContractVersion; agent: string; sessionId: string }
interface CheckpointResponse { version: ContractVersion; checkpoint: Checkpoint | null }
interface UpdateRequest { version: ContractVersion; project: ProjectId; from: Checkpoint | null; to: Checkpoint; add: Entry[]; retire: { entryId: string; replacedBy?: string }[] }
type UpdateOutcome = 'applied' | 'unchanged' | 'out_of_sequence';
interface UpdateResponse { version: ContractVersion; outcome: UpdateOutcome; checkpoint: Checkpoint | null; added: string[]; retired: string[] }
// Decided in this order against the stored checkpoint of the session:
// 'unchanged'       to.position is at or before the stored position
// 'applied'         from equals the stored checkpoint (both null for a new session); the stored checkpoint becomes to
// 'out_of_sequence' anything else; nothing changes and the stored checkpoint is returned
interface MemoryClient { query(request: QueryRequest): QueryResponse; names(request: NamesRequest): NamesResponse; checkpoint(request: CheckpointRequest): CheckpointResponse; update(request: UpdateRequest): UpdateResponse }
```

### 5.8 sc8: Embedding interface and cache

**Owner Story:** `s5`

**Purpose:** Turning text into vectors that say which model produced them, with an optional disk cache offering the same interface.

**Interface sketch (type-level):**

```
interface EncoderFingerprint { modelName: string; modelDigest: string; quantization: string; backendName: string; backendVersion: string; dimension: number; textConvention: string; dtype: string }
interface Embedder { fingerprint: EncoderFingerprint; encode(texts: string[]): number[][] }
interface CachedEmbedder extends Embedder { }
```

**Assumptions cited:** [[c5]]

### 5.9 sc9: Extraction and storage interfaces

**Owner Story:** `s5`

**Purpose:** Turning conversation messages into candidate entries that use and tag official names, and keeping and finding entries and checkpoints, without naming a runtime or store.

**Interface sketch (type-level):**

```
interface Message { source: Source; role: 'user' | 'agent' }
interface Candidate { kind: EntryKind; text: string; entities: NamedEntity[]; sources: Source[]; replaces: string[] }
interface Extractor { modelName: string; extract(window: Message[], existing: Entry[], knownNames: string[]): Candidate[] }
// Candidate text uses official names, keeping versions, and reuses a known name where it means the same thing.
// Every implementation returns only entities that appear in the candidate text, with their positions.
interface StoredVector { fingerprint: EncoderFingerprint; values: number[] }
interface Change { from: Checkpoint | null; to: Checkpoint; add: { entry: Entry; vector: StoredVector }[]; retire: { entryId: string; replacedBy?: string }[] }
interface ChangeResult { outcome: 'applied' | 'unchanged' | 'out_of_sequence'; checkpoint: Checkpoint | null }
interface EntryStore { checkpoint(agent: string, sessionId: string): Checkpoint | null; apply(change: Change): ChangeResult; names(project: ProjectId): string[]; search(project: ProjectId, vector: StoredVector, entities: string[], kind: EntryKind | null, limit: number): { entry: Entry; score: number }[] }
// Guarantees required of every implementation:
// after a failure at any point, submitting the same change again leaves no entry stored twice;
// only tagged entities are keyword indexed;
// an entry whose tagged entity loosely matches a name in the query is a search candidate even if vector search would not have returned it;
// missing a relevant entry is worse than returning an extra one;
// exact name matches rank ahead of looser ones, and looser matches do not crowd out strong vector results.
```

## 6. Story boundaries

### 6.1 Story STORY-3b5f9aa550b6fe9d-s1

**Owns:** `sc1`, `sc2`

How entries and named entities are checked and represented in Python, the entries, checkpoints and failures modules of core/common, and the changes to the import-direction test for nested packages.

### 6.2 Story STORY-3b5f9aa550b6fe9d-s2

**Owns:** `sc3`, `sc4`, `sc5`
**Depends on:** `sc1`, `sc2`

Per-platform location rules, the configuration file format and its validation, and how activity is written and rotated.

### 6.3 Story STORY-3b5f9aa550b6fe9d-s3

**Owns:** `sc6`
**Depends on:** `sc1`, `sc2`

The rule that identifies a project from a location and how it behaves across worktrees and machines.

### 6.4 Story STORY-3b5f9aa550b6fe9d-s4

**Owns:** `sc7`
**Depends on:** `sc1`, `sc2`, `sc3`, `sc4`, `sc5`, `sc6`

Wire encoding, endpoint layout, version compatibility rule, time limits, the HTTP library and how failures are mapped to shared kinds.

### 6.5 Story STORY-3b5f9aa550b6fe9d-s5

**Owns:** `sc8`, `sc9`
**Depends on:** `sc1`, `sc2`

The move of the embedding protocol into core/common and of its cache into core/cache/embedding, and the exact method signatures of the interfaces. The local model's instructions belong to the parser design and the calling agent's steering to the MCP adapter design. The loose matching technique, the ranking and the meaning of a score are left to the store design.

## 7. Non-functional targets

- **Performance:** No targets are agreed.
- **Observability:** Every process records activity in the shape of sc5; the client records its calls through the activity package.
- **Durability:** Updates are idempotent: the session checkpoint decides whether a change is applied, unchanged or out of sequence, and a checkpoint advances only with stored entries. The store design must keep this true across a failure between writing entries and advancing the checkpoint.

## 8. Rollout

**Phase A: definitions and layout**

**Stories:** `s1`

Every other story uses the definitions, named entities, checkpoints, failure kinds and import table.

**Backward compat:** The existing embedding tests keep passing; the import test still rejects unlisted packages.

**Phase B: base infrastructure and interfaces**

**Stories:** `s2`, `s3`, `s5`

Each depends only on the shared definitions and layout.

**Backward compat:** The embedding protocol and cache move with unchanged behaviour and the cache tests keep passing.

**Phase C: server contract and client**

**Stories:** `s4`

The client needs settings, activity records and project identity.

**Ordering rationale:** s1 first because all stories depend on it; s2, s3 and s5 are independent of each other; s4 depends on s2 and s3 and lands last.

**Risky bits**

| Area | Why | Mitigation |
| :--- | :--- | :--- |
| Idempotent updates across a crash | A failure between writing entries and advancing the checkpoint could store entries twice, and a rerun model may word them differently. | sc9 requires that resubmitting adds nothing twice; the store design must show how, checking what LanceDB can commit together. |
| Checkpoint position | The rule assumes a position that only increases within a session history; a rewritten or split history file would break it. | The history reader design confirms this for each agent before relying on it. |
| Name normalization by two models | The small local model may miss or wrongly resolve a name, and the calling agent may choose a different official form. | Both follow one rule, the local model reuses known names and matching is loose; the parser test measures name resolution before the parser design is accepted. |

## 9. Alternatives considered

### 9.1 a1: Nested core with one definitions package — **CHOSEN**

Core packages under agent_pfc/core, with all shared definitions in core/common and behaviour in separate packages.

A core namespace holds only subpackages. One package, core/common, holds every shared definition: entry types with their tagged entities, failure kinds, server contract types, interfaces, and the shapes of settings, locations and activity records, one subject per module. It imports nothing from the project and does no I/O.

Packages that do work (locations, config, activity, identity, client, cache/embedding) sit beside it under core and depend on it. The import-direction test enforces the table and forbids anything under core from importing outside it. This is the shape the project owner has chosen.

**Pros:**
- Every shared definition has one place to look for it.
- Definitions cannot form import cycles with each other across packages.
- The core boundary shows in every import path and one rule enforces it.

**Cons:**
- core/common can collect unrelated items; only the one-subject-per-module rule and review prevent that.
- A package needing one definition depends on the package holding all of them.
- The import checker must be rewritten to handle nested packages.

**Cost estimate:** M

### 9.2 a2: Nested core with a definitions package per subject

Core packages under agent_pfc/core, with separate packages for entries, failures, contract and each interface.

The same core namespace, but definitions are split into one package per subject, such as domain, failures, contract and the interface packages.

Behaviour packages depend only on the definition packages they use, and the import table lists each edge.

**Pros:**
- Each dependency names exactly what a package uses.
- A definition package cannot grow beyond its subject without being renamed.

**Cons:**
- Many small packages and a longer import table.
- Shared definitions are spread across the tree, which the owner has decided against.

**Cost estimate:** M

**Rejected because:** Satisfies every constraint as worded, but goes against the owner's decision to keep shared definitions in one package.

### 9.3 a3: Flat packages without a core namespace

Single-responsibility packages directly under agent_pfc with a layered import table.

No core namespace; core packages and later modules sit side by side directly under the project package.

Which packages form the core is recorded as a list in the import-direction test.

**Pros:**
- The existing one-level import checker needs the least change.
- Import paths are shorter.

**Cons:**
- The core boundary is visible only in the test, not in the tree.
- The owner has decided the packages belong under core.

**Cost estimate:** S

**Rejected because:** Goes against the owner's decision to nest the packages under core.

## 10. References

- **[[c1]]** `analyze-bundle` `s1` — "One source package with a single subpackage, embeddings; the only project imports are inside it or from tests."
- **[[c2]]** `code` `src/agent_pfc/embeddings/protocol.py:26`
- **[[c3]]** `code` `src/agent_pfc/embeddings/cache.py`
- **[[c4]]** `code` `tests/test_architecture.py`
- **[[c5]]** `doc` `docs/REQUIREMENTS.md:116-123`
- **[[c6]]** `convention` `CLAUDE.md:20-24`
