<!-- insrc:artifact PLAN-2152718849ceb87c-s1 -->

# Plan: STORY-2152718849ceb87c-s1

## Summary

**Epic:** `test-modality-collapse-operation-embeddings`
**LLD run:** `wf-1795685420064-vbz7yv`
**LLD effective hash:** `67fcbde13b3d...`

Building this story means creating the project's first real code: a small set of one-responsibility packages for records, embedding, composition, scoring, probe loading, orchestration, reporting and the command line, all testable offline with a fake embedder. It ends with a draft probe set of 100 operations and 300 queries for the user to review. No pass or fail verdict exists until that review happens and the run is made against the local model.

## Contents

1. [Tasks](#1-tasks)
2. [Test-strategy coverage](#2-test-strategy-coverage)
3. [References](#3-references)

## 1. Tasks

| # | Task | Size | Status | Depends on | Tests | Derived from |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | **`t1`** Domain records and package foundation | M | — | — | unit: import direction between packages follows the allowed table and rejects a forbidden example; unit: modality phase table and operation identity by concept and modality | [[c1]] [[c2]] |
| 2 | **`t2`** Embeddings protocol, errors and disk cache | M | — | `t1` | unit: cache key changes with digest, dimension, convention and text; corrupt entry recovery; unit: empty input rejection and duplicate inputs in order | [[c1]] [[c2]] |
| 3 | **`t3`** Ollama backend | M | — | `t2` | unit: Ollama backend against a stubbed transport: batching, order, bad responses, digest mismatch, non-loopback URL; unit: absence of Ollama knowledge outside embeddings/ollama.py; live: dimensions 256, 512 and 1024 return unit vectors in input order | [[c1]] [[c2]] |
| 4 | **`t4`** Composition | M | — | `t1` | unit: composition formulas, C2 at 1.0 equals C0, zero-norm rejection; unit: symmetric query composition never uses the expected modality or phase | [[c1]] [[c2]] |
| 5 | **`t5`** Evaluation | M | — | `t1` | unit: ranking, ties, confusion matrix, pairwise accuracy, margins, neutral share; unit: variant selection tie-break and confirm-split verdict | [[c1]] [[c2]] |
| 6 | **`t6`** Probe loading and validation | M | — | `t1` | unit: probe loading and each validation failure | [[c1]] [[c2]] |
| 7 | **`t7`** Experiment orchestration | M | — | `t2`, `t4`, `t5` | integration: C5 control yields all ties; integration: draft run states no verdict | [[c1]] [[c2]] |
| 8 | **`t8`** Reporting and command line | M | — | `t3`, `t6`, `t7` | integration: collapse run writes run record and report; integration: existing run directory is not overwritten; integration: criterion is recorded before embedding and errors end with no verdict | [[c1]] [[c2]] |
| 9 | **`t9`** Probe concepts and stored operations | M | — | `t6` | unit: committed probe operations have 100 records, five modalities per concept and a 10 and 10 split | [[c1]] [[c2]] |
| 10 | **`t10`** Draft queries and manifest for user review | M | — | `t9` | unit: committed probe set passes validation with 300 queries | [[c1]] [[c2]] |

### 1.1 TASK-2152718849ceb87c-s1-t1 — Domain records and package foundation

Add numpy through uv, remove the hello stub, ignore the runs directory, add the domain package with the modality and phase table, split, ProbeOperation, ProbeQuery, ProbeSet (records, reviewed flag, file hashes), MethodVariant, QueryTrack and PassCriterion, and add the import-direction test that encodes the allowed dependency table.

**Acceptance checks:**
- numpy is the only new runtime dependency and uv.lock is updated
- The hello stub is gone and the import test passes
- runs/ is in the ignore list
- domain imports nothing from the project
- The import-direction test fails on any import outside the LLD table, including a deliberately forbidden example it is checked against
- The phase table gives +1, +2, +1, -1, -1 for required, strict_required, permitted, not_required, prohibited
- An operation is identified by concept and modality, never by phase or concept alone

### 1.2 TASK-2152718849ceb87c-s1-t2 — Embeddings protocol, errors and disk cache

Add the Embedder protocol and the EncoderFingerprint record in embeddings/protocol.py, EmbeddingBackendError, a disk cache wrapper keyed by fingerprint and text with atomic writes and read validation, and a deterministic fake embedder for tests. The fingerprint lives here because embeddings may import no other project package.

**Acceptance checks:**
- The fingerprint holds model name, digest, quantization, backend name and version, dimension, text convention and dtype
- Cache key changes when digest, dimension, text convention or text changes
- A corrupt or truncated entry is discarded and encoded again
- Entries are written through a temporary file and atomic rename
- Empty or whitespace input raises ValueError
- Duplicate inputs return identical rows in input order
- embeddings imports no other project package

### 1.3 TASK-2152718849ceb87c-s1-t3 — Ollama backend

Add the Ollama embedder in embeddings/ollama.py using the standard library HTTP client: loopback-only base URL, local model list and digest check before encoding, batches of at most 32, and response checks for count, shape, finiteness and norm. Add the live contract test for dimensions 256, 512 and 1024.

**Acceptance checks:**
- Stubbed-transport tests cover batching, order, bad responses, digest mismatch and a non-loopback URL
- An unreachable server, an error status and a model missing from the local list each raise EmbeddingBackendError naming the endpoint and model
- No partial result is returned and nothing from a bad batch is cached
- Live test passes against qwen3-embedding:0.6b at all three dimensions and is skipped with a stated reason when Ollama is unavailable
- No module outside embeddings/ollama.py holds Ollama knowledge apart from the command line constructing it

### 1.4 TASK-2152718849ceb87c-s1-t4 — Composition

Add rendering that builds the stored and symmetric-query texts for each method from domain records, and pure vector arithmetic for C0, C1, C2, C4 and C5 with normalization and zero-norm rejection.

**Acceptance checks:**
- Formulas match the LLD for every method and weight
- C2 at weight 1.0 equals C0
- A norm at or below 1e-12 raises ValueError naming the method and weight
- Symmetric query composition never uses the expected modality or phase, and the C4 query text has no Phase field
- No negated vector is used
- composition imports only domain and reads no files and calls no model

### 1.5 TASK-2152718849ceb87c-s1-t5 — Evaluation

Add the CollapseResult types and pure functions for modality ranking with ties, the 5x5 confusion matrix with a tie column, pairwise accuracy, margins and worst cases, the neutral top-five share, variant selection on the select split and the verdict on the confirm split.

**Acceptance checks:**
- Scores within 1e-6 count as a tie and a wrong answer
- Accuracy, confusion, the ten pairwise accuracies, margins and neutral share match hand-computed examples
- A split with no queries for a modality pair is an error, never a perfect score
- Selection order is accuracy, worst pair, smallest dimension, then method id and weight, using only select results
- The verdict uses only the chosen variant on confirm results against 0.95 and 0.90 on the natural track
- evaluation imports only domain

### 1.6 TASK-2152718849ceb87c-s1-t6 — Probe loading and validation

Add the probes package that loads operations.jsonl, queries.jsonl and manifest.json into a domain ProbeSet and validates fields, unique ids, five modalities per concept, phase table, split per concept, queries for every modality pair in each split, query text distinct from stored text and manifest hashes, reporting every failure together.

**Acceptance checks:**
- Each validation failure has a test using a small synthetic probe set
- A split lacking queries for any modality pair is rejected
- All failures are listed in one error
- The reviewed_by_user flag is returned to the caller
- probes imports only domain and reads nothing from the benchmark archive

### 1.7 TASK-2152718849ceb87c-s1-t7 — Experiment orchestration

Add the run config holding the pass criterion, variants, weights and dimensions, and the collapse run that takes a ProbeSet and injected embedders, composes both tracks, evaluates both splits, checks the C5 control, applies draft or verdict rules and returns a run result carrying the config and encoder fingerprints.

**Acceptance checks:**
- The criterion is fixed in the config before the first encode call and is unchanged in the run result
- C5 results that are not all ties fail the run as a harness error
- An unreviewed probe set runs only with the draft option and yields no verdict
- C2 at 1.0 is computed once and C3 is reported as identical to C1
- Natural and symmetric results are never mixed
- experiments uses only the embedder protocol from embeddings and does not import probes or reporting

### 1.8 TASK-2152718849ceb87c-s1-t8 — Reporting and command line

Add the run record and Markdown report writers under runs/ and the command line that loads the probes, builds the cache and Ollama embedders, opens the run through reporting so the directory, criterion and config are written first, runs the experiment, then writes the results. Add a project script entry point.

**Acceptance checks:**
- An offline end-to-end test with the fake embedder writes the run record and report
- An existing run directory stops the command before any embedding and is not overwritten
- The criterion appears in the run record before any embedding happens
- A draft report is labelled draft and states no verdict
- Backend and validation errors end the command with a clear message and no verdict
- The command line holds wiring only and reporting does not import embeddings

### 1.9 TASK-2152718849ceb87c-s1-t9 — Probe concepts and stored operations

Author data/probes/modality_collapse_v1/operations.jsonl with 20 operation concepts, all five modalities each, and 10 select and 10 confirm concepts.

**Acceptance checks:**
- 100 operations, one per concept and modality, with phases matching the table
- 10 select and 10 confirm concepts, assigned before any run
- No concept used in the earlier preliminary modality probe is in the confirm split
- The benchmark archive is not opened while authoring

### 1.10 TASK-2152718849ceb87c-s1-t10 — Draft queries and manifest for user review

Author queries.jsonl with three natural paraphrases per concept and modality (300 queries) and a synonym term each, the manifest with reviewed_by_user false, and a separate list of ambiguous wording for the user to decide.

**Acceptance checks:**
- The set passes validation with 100 operations and 300 queries split 10 and 10 by concept
- The manifest has reviewed_by_user false and only the user's explicit review changes it
- Words that fit more than one modality are excluded or listed for the user to assign
- No query copies a stored text, and the benchmark archive is not opened while authoring
- No embedding result is used to write or edit a query

## 2. Test-strategy coverage

| LLD strategy item | Covered by |
| :--- | :--- |
| composition formulas, C2 at 1.0 equals C0, zero-norm rejection | `t4` |
| symmetric query composition never uses the expected modality or phase | `t4` |
| ranking, ties, confusion matrix, pairwise accuracy, margins, neutral share | `t5` |
| variant selection tie-break and confirm-split verdict | `t5` |
| probe loading and each validation failure | `t6` |
| cache key changes with digest, dimension, convention and text; corrupt entry recovery | `t2` |
| Ollama backend against a stubbed transport: batching, order, bad responses, digest mismatch, non-loopback URL | `t3` |
| import direction between packages and the absence of Ollama knowledge outside embeddings/ollama.py | `t1`, `t3` |
| collapse run writes run record and report | `t8` |
| C5 control yields all ties | `t7` |
| draft run states no verdict | `t7` |
| existing run directory is not overwritten | `t8` |
| dimensions 256, 512 and 1024 return unit vectors in input order | `t3` |

## 3. References

- **[[c1]]** `prior-artifact` `LLD s1 contractDetails, dataModelChanges, errorPaths, testStrategy and migration`
- **[[c2]]** `doc` `CLAUDE.md` — "Separation of concerns and modularity are the prime directive."
