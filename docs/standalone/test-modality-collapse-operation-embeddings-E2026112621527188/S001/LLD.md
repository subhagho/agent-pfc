<!-- insrc:artifact LLD-2152718849ceb87c-s1 -->

# LLD: STORY-2152718849ceb87c-s1 — Test modality collapse in operation embeddings

## Summary

**Epic:** `test-modality-collapse-operation-embeddings`
**HLD base run:** `wf-1795685420064-vbz7yv`
**HLD effective hash:** `67fcbde13b3d...`

This story builds an offline-testable experiment that measures whether operations differing only in modality stay distinguishable under each composition method and dimension. It adds a versioned probe set, a pluggable embedder with a local Ollama backend and cache, pure composition and evaluation functions, and a run that writes confusion matrices, margins and a pass or fail verdict against a criterion fixed beforehand.

## Contents

1. [HLD context](#1-hld-context)
2. [Contract details](#2-contract-details)
3. [Data model changes](#3-data-model-changes)
4. [Diagrams](#4-diagrams)
5. [Error paths](#5-error-paths)
6. [Test strategy](#6-test-strategy)
7. [Migration](#7-migration)
8. [Alternatives considered](#8-alternatives-considered)
9. [References](#9-references)

## 1. HLD context

**Framework:** Standalone feature — no parent HLD. Design directly against the repo, grounded on the s1 analyze passes. There are no HLD shared contracts to honour.
**Rollout phase:** standalone

## 2. Contract details

**Surface level:** internal

### 2.1 `Embedder`

```typescript
class Embedder(Protocol): fingerprint: EncoderFingerprint; def encode(self, texts: Sequence[str]) -> np.ndarray
```

**Parameters:**
- `texts: Sequence[str]` — Non-empty strings to embed, in order. Dimension is fixed when the embedder is constructed.

**Returns:** `np.ndarray` — float32 array of shape (len(texts), dimension), each row unit length, in input order.

**Errors:**
- `ValueError` when Any input is empty or whitespace only.
- `EmbeddingBackendError` when The backend is unreachable, returns an error, returns the wrong count or dimension, returns a non-finite or zero vector, or its model digest differs from the configured one.

**Preconditions:**
- The embedder was constructed with a supported dimension: 256, 512 or 1024.

**Postconditions:**
- No partial result is returned.
- Equal inputs under an equal fingerprint come from the same cache entry when the cache wrapper is used.

## 3. Data model changes

### 3.1 `ProbeOperation` — new

Domain record: concept, modality (required, strict_required, permitted, not_required, prohibited), phase (+1, +2, +1, -1, -1 in that order, matching the usual v0.1 convention), phase_modality_text, contextual_text, split (select or confirm). Identity is concept plus modality; phase never identifies an operation. One record per concept and modality, and every concept has all five (confirmed by the user).


### 3.2 `ProbeQuery` — new

Domain record: id, concept, expected modality, text (a natural paraphrase) and synonym_term (a synonym of the modality wording, used only by the symmetric track). A query text never equals any stored contextual_text or phase_modality_text. Size, confirmed by the user: 20 concepts, 3 queries per concept and modality, 300 queries, split by concept into 10 select and 10 confirm. The user reviews the paraphrases before a verdict run. A word that fits more than one modality, such as 'optional' for permitted and not_required, is either excluded or assigned to one modality by the user during that review.


### 3.3 `ProbeSet` — new

Versioned files under data/probes/modality_collapse_v1: operations.jsonl, queries.jsonl and manifest.json with counts, file hashes and a reviewed_by_user flag. Benchmark v0.1 is not read or modified by this story. The package probes loads and validates; it holds no scoring logic.


### 3.4 `MethodVariant` — new

Method id plus weight. Stored vectors, with u the unit embedding, o concept, m phase_modality_text, c contextual_text: C0 u(c); C1 norm(u(o)+w*u(m)); C2 norm((1-w)*u(o)+w*u(c)); C4 u of the text 'Operation: o; Phase: p; Modality: m'; C5 u(o). C3 for operations is defined by the benchmark README as the same formula as C1, so it is reported as identical to C1 and not run twice. Weights 0.25, 0.5, 0.75, 1.0 for C1 and C2; C2 at 1.0 equals C0 and is computed once. No vector negation and no instruction-conditioned queries. R0 does not apply.

**Call sites:**
- `docs/PFC_PYTHON_PROJECT_CONTEXT.md:113-226`

### 3.5 `QueryTrack` — new

natural (primary, decides the verdict): query vector is u(text) for every method. symmetric (diagnostic): the query is composed by the same method from concept, synonym_term and text: C0 u(text); C1 norm(u(o)+w*u(synonym_term)); C2 norm((1-w)*u(o)+w*u(text)); C4 u of the text 'Operation: o; Modality: synonym_term'; C5 u(o). A query is never built from the expected modality or its phase, so the C4 query has no Phase field although the stored C4 text has one. Results of the two tracks are never mixed.

**Call sites:**
- `docs/PFC_SCOPE_REVIEW.md`

### 3.6 `CollapseResult` — new

Per variant, dimension, track and split. Modality ranking: each query ranks the five stored operations of its own concept; it is correct only if the expected one scores strictly highest, with scores within 1e-6 counted as a tie and therefore wrong. Reports accuracy, a 5x5 confusion matrix with a separate tie column, pairwise accuracy for each of the 10 modality pairs (queries of either modality whose own operation strictly outscores the other), margin (own cosine minus best other cosine: mean, minimum, 5th percentile) and the worst cases. Neutral measure: u(o) ranks all stored operations of all concepts in the split; reports the share of its five modalities found in the top five. It is reported, not part of the verdict.


### 3.7 `PassCriterion` — new

Confirmed by the user. Held in the run config and copied into the run record before any embedding: minimum accuracy 0.95 and minimum pairwise accuracy 0.90, natural track. The variant, weight and dimension are chosen on the select split (highest accuracy, then highest worst pair, then smallest dimension, then method id and weight order). The verdict is that single choice evaluated on the confirm split. Confirm results for other variants are reported but cannot change the choice.


### 3.8 `EncoderFingerprint` — new

Model name, model digest, quantization, backend name and version, dimension, text convention and dtype. It is part of every cache key together with the input text, and is stored in each run record.

**Call sites:**
- `docs/PFC_PYTHON_PROJECT_CONTEXT.md:113-226`

### 3.9 `PackageLayout` — new

Under src/agent_pfc, with dependencies pointing only downward. domain: records and enums, imports nothing from the project. probes: loading.py and validation.py, depends on domain. embeddings: protocol.py, ollama.py, cache.py, errors.py; no project imports beyond its own package. composition: rendering.py builds texts from domain records, methods.py is pure vector arithmetic. evaluation: ranking.py, margins.py, neutral.py, verdict.py, pure functions over arrays and domain records. experiments: config.py and collapse.py orchestrate, receiving an Embedder instance. reporting: run_record.py and markdown.py write under runs/. cli.py constructs the concrete objects, may import domain records to pass them between packages, and calls experiments then reporting. Only embeddings/ollama.py knows about Ollama; it uses the standard library HTTP client, sends batches of at most 32, and accepts only a loopback base URL. numpy is the only new runtime dependency. The scaffold hello stub is removed.

**Call sites:**
- `src/agent_pfc/__init__.py`
- `pyproject.toml`
- `tests/test_import.py`

## 4. Diagrams

- [Component dependencies](./component-dependency.html)

## 5. Error paths

**Error cases**

- **Ollama is not running or the model is not installed** (recoverable)
  - Detection: The HTTP request fails to connect, returns a non-2xx status, or the model is absent from the local model list.
  - Response: Raise EmbeddingBackendError naming the endpoint and model; the run stops without a verdict.
  - User impact: Run fails with a clear message.
- **Installed model differs from the configured digest** (recoverable)
  - Detection: The digest reported by the local model list is compared with the configured digest before any encoding.
  - Response: Raise EmbeddingBackendError showing both digests.
  - User impact: Results from another model cannot be mixed in.
- **Backend returns a missing, extra, wrong-sized, non-finite or zero vector** (recoverable)
  - Detection: The backend checks response count against input count, then shape, finiteness and norm of each row.
  - Response: Raise EmbeddingBackendError; nothing from that batch is cached.
  - User impact: Run fails instead of scoring bad vectors.
- **A composed vector cannot be normalized** (terminal)
  - Detection: The composition function finds a norm at or below 1e-12.
  - Response: Raise ValueError naming the method and weight.
  - User impact: Run fails; no silent zero vector.
- **Probe set is malformed or incomplete** (recoverable)
  - Detection: Validation checks required fields, unique ids, five modalities per concept, phase matching the modality table, split per concept, no query text equal to a stored text after case and whitespace folding, and manifest hashes.
  - Response: Raise a validation error listing every failure before any embedding.
  - User impact: The user fixes the data.
- **Probe set has not been reviewed by the user** (recoverable)
  - Detection: The manifest reviewed_by_user flag is false.
  - Response: Run proceeds only with an explicit draft option; the report is labelled draft and states no verdict.
  - User impact: Unreviewed data cannot produce a pass or fail claim.
- **The control behaves like a real method** (terminal)
  - Detection: C5 results are checked: every modality ranking must be a tie.
  - Response: Fail the run as a harness error.
  - User impact: A scoring bug is caught before results are read.
- **A cache entry is corrupt or truncated** (recoverable)
  - Detection: On read, shape, dtype, finiteness and norm are checked against the fingerprint.
  - Response: Discard the entry and encode again; write entries through a temporary file and atomic rename.
  - User impact: None beyond recomputation.
- **Run directory already exists** (recoverable)
  - Detection: Directory creation fails because the path is present.
  - Response: Stop without overwriting.
  - User impact: Earlier results are never replaced.
- **Configured base URL is not loopback** (recoverable)
  - Detection: The host of the configured URL is checked at construction.
  - Response: Raise EmbeddingBackendError.
  - User impact: Text is never sent off the machine.

**Edge cases**

| Input | Expected |
| :--- | :--- |
| Two modality vectors are identical | Scores within 1e-6 count as a tie, the query is wrong and the tie column increments. |
| C2 weight 1.0 | Identical to C0; computed once and reported under both names. |
| C3 requested | Reported as identical to C1 for operations, with no separate computation. |
| More texts than one batch | Split into batches of at most 32 with order preserved. |
| Duplicate texts in one call | One row per input, identical rows for identical texts. |
| A modality pair with no queries in a split | Validation rejects the probe set; no pair is reported as perfect by default. |
| Several variants tie on the select split | The documented tie-break order picks exactly one. |

**Invariants to preserve**

- Benchmark v0.1 stays unchanged and is not read by this run. [[c1]]
- Operation identity includes concept and modality; phase or concept text alone never identifies an operation. [[c2]]
- No negated vector is used to encode negation. [[c3]]
- Unit tests run offline with a deterministic fake embedder and make no semantic quality claim. [[c4]]
- Selection uses only the select split; the verdict uses only the confirm split and the criterion recorded before embedding. [[c5]]

## 6. Test strategy

**Test framework:** `pytest`

**Test levels**

- **unit** — Prove arithmetic, scoring, validation, caching and backend response checks offline.
  - Subjects: `composition formulas, C2 at 1.0 equals C0, zero-norm rejection`, `symmetric query composition never uses the expected modality or phase`, `ranking, ties, confusion matrix, pairwise accuracy, margins, neutral share`, `variant selection tie-break and confirm-split verdict`, `probe loading and each validation failure`, `cache key changes with digest, dimension, convention and text; corrupt entry recovery`, `Ollama backend against a stubbed transport: batching, order, bad responses, digest mismatch, non-loopback URL`, `import direction between packages and the absence of Ollama knowledge outside embeddings/ollama.py`
  - Fixtures: `deterministic fake embedder`, `small synthetic probe set`
- **integration** — Run the whole experiment offline with the fake embedder and check the written artifacts.
  - Subjects: `collapse run writes run record and report`, `C5 control yields all ties`, `draft run states no verdict`, `existing run directory is not overwritten`
  - Fixtures: `temporary run and cache directories`
- **live** — Check the real local model contract before a measured run.
  - Subjects: `dimensions 256, 512 and 1024 return unit vectors in input order`
  - Fixtures: `running Ollama with qwen3-embedding:0.6b`

**Acceptance mapping**

| Criterion | Proving tests |
| :--- | :--- |
| `ac1` | `composition formulas, C2 at 1.0 equals C0, zero-norm rejection`, `symmetric query composition never uses the expected modality or phase`, `collapse run writes run record and report` |
| `ac2` | `ranking, ties, confusion matrix, pairwise accuracy, margins, neutral share`, `variant selection tie-break and confirm-split verdict` |
| `ac3` | `probe loading and each validation failure`, `draft run states no verdict` |
| `ac4` | `Ollama backend against a stubbed transport: batching, order, bad responses, digest mismatch, non-loopback URL`, `dimensions 256, 512 and 1024 return unit vectors in input order` |
| `ac5` | `import direction between packages and the absence of Ollama knowledge outside embeddings/ollama.py` |

## 7. Migration

**State before:** A scaffold package exporting a hello stub, one import test, no runtime dependencies and no persisted data.

**State after:** Layered packages for the collapse test, numpy as a runtime dependency, a versioned probe set under data/probes, and run outputs under runs/.

**Zero downtime:** yes — **Data rewrite:** no

**Steps**

1. Add numpy to project dependencies and update the lock file. — ↩ rollbackable
2. Add the new packages and tests, and remove the hello stub. — ↩ rollbackable
3. Add runs/ to the ignore list and add the draft probe set. — ↩ rollbackable

**Backward compat:** The hello stub is removed; nothing in the repository other than the package itself uses it, and the import test keeps passing.

## 8. Alternatives considered

### 8.1 a1: Single experiment script

One script reads a probe file, calls Ollama, composes, scores and prints a report.

A single module under the source package holds the probe records, the HTTP call, an in-memory cache, the composition formulas, the metrics and the report writing, with one test file for the formulas.

**Rejected because:** Violates the non-negotiable separation of concerns and package modularity rule.

### 8.2 a2: Layered packages for this test only — **CHOSEN**

Small one-responsibility packages with one-way dependencies, containing only what the collapse test needs.

Packages: domain (operation and probe records, no project imports); probes (load and validate the versioned probe set); embeddings (Embedder protocol, Ollama backend, disk cache wrapper, each its own module); composition (pure functions turning component vectors into method vectors, plus the text rendering each method needs); evaluation (pure ranking, confusion, margin and criterion functions); experiments (orchestrates one collapse run from a config); reporting (writes run artifacts and the report); cli (wiring only).

### 8.3 a3: General benchmark framework

A task-agnostic experiment framework with registries, covering entity, operation and retrieval tasks, with the collapse test as its first plugin.

The a2 packages plus a method and task registry, a generic benchmark runner over the v0.1 fixture, scorer integration and BM25 and R0 baselines, with the collapse test registered as one task.

**Rejected because:** Adds the M2 runner, scorer and baselines, which are outside this story.

## 9. References

- **[[c1]]** `doc` `docs/PFC_PYTHON_PROJECT_CONTEXT.md:366-374`
- **[[c2]]** `doc` `docs/PFC_PYTHON_PROJECT_CONTEXT.md:113-125`
- **[[c3]]** `doc` `docs/PFC_PYTHON_PROJECT_CONTEXT.md:194-212`
- **[[c4]]** `doc` `docs/PFC_PYTHON_PROJECT_CONTEXT.md:518-529`
- **[[c5]]** `step-output` `s4`
- **[[c6]]** `analyze-bundle` `s1`
