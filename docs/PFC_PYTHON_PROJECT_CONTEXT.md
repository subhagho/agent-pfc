# PFC — Intermediate Action Memory Framework

**Project context and implementation brief**  
Version 0.1 · 26 November 2026  
Implementation language: **Python**  
Companion artifact: `PFC_Embedding_Benchmark_v0.1.zip`

## 0. Instructions for the new repository-anchored agent

This document is the consolidated context for a new, standalone Python project. Read it and the accompanying benchmark README and manifest before proposing or implementing the architecture. It supersedes the intermediate speculative designs in the earlier conversation. In particular, do not implement an AFM language learner, a custom neural model, a concept hierarchy, or a conventional semantic knowledge graph.

The first objective is **an empirical comparison of entity and operation embedding composition methods**. Establish whether the representation works before building the full memory service. Use the supplied synthetic fixture unchanged for the first reproducible baseline. Do not claim that a model or method has been validated until it has actually been run and measured. Do not use held-out test answers to construct query prompts or select parameters.

The sections marked *agreed* record design decisions from the discussion. Sections marked *proposed* describe a starting implementation or experiment, not a finalized design. Do not treat those proposals as fixed requirements; preserve the architectural invariants while testing alternatives.

---

## 1. Motivation and scope

### 1.1 The problem in insrc

insrc is an SDLC orchestration and governance framework that coordinates existing coding agents. Large collaborative projects accumulate user directives, design choices, exceptions, corrections, architectural invariants and operational decisions over many sessions and across agents. Even a strong coding model can make locally reasonable decisions that violate a previously agreed constraint because the relevant instruction is absent from its active context.

Session transcripts, summaries and document-level vector retrieval are useful but insufficient. The issue is not simply a lack of context-window capacity. A directive can be expressed in language very different from the design decision where it is relevant. Many directives share the same topic but differ in scope, modality or exceptions. A document embedding may retrieve a nearby but incorrect directive. Static rule systems require continual manual segmentation of task intent and become brittle as projects evolve.

A memory must be recoverable when a coding agent is making a decision, without requiring the agent to know in advance which historical directive to search for. However, the memory system is **not** responsible for discovering what decisions need to be made, anticipating all consequences of actions, or reasoning independently about the project. The coding agent supplies the decision context at the relevant point in its existing workflow.

### 1.2 Information memory versus action memory (agreed)

| Dimension | Information memory | Action memory |
|---|---|---|
| Content | Facts, observations, recent context, evidence | Directives, decisions, constraints, corrections, commitments |
| Function | Inform reasoning | Influence or constrain a pending decision |
| Typical retrieval | Associative document retrieval, vector search | Contextual activation of applicable directional relationships |
| Lifecycle | Relevance, staleness, redundancy | Validity, scope, exceptions, authority, supersession |
| Principal risk | Missing useful facts | Forgetting or misapplying a directive |

Near-term information memory can remain a conventional vector store. Code graphs, repository search and semantic indexes can remain separate tools. This project addresses **action memory only**. Do not build the near-term information store as part of the initial experimental engine.

### 1.3 System 1 / System 2 analogy

The coding agent functions as the deeper reasoning system (loosely analogous to System 2). The PFC action-memory module functions as a fast associative system (loosely analogous to System 1). These are design metaphors, not claims of biological equivalence. The module is a memory substrate, not an autonomous policy maker, reasoning engine, or decision veto system.

The small-model idea was considered: a tiny continuously trainable model could learn transitions or traversal paths. We are not pursuing that as the initial solution. A frozen embedding model plus a dynamically maintained topology may supply the needed adaptation without a weight-training harness. A learnable metric or transition function remains an optional later experiment if frozen embeddings prove inadequate.

---

## 2. Relationship to AFM (agreed)

The long-term goal is an AFM-based PFC module. AFM (Attractor Field Model) explored an amodal concept fabric in which meaning resides in directional relational traversals, not in individual nodes. AOTD is its relationship grammar: Attention, Operation, Target and Decorators. Original AFM mechanisms include frequency-based concept identity, signed phase modulation, composite excitation, selective forward O resonance and a base resonance threshold. The implementation used sparse numerical operations, not a graph database.

A complete AFM implementation would require a learned conceptual substrate and bidirectional language segment. It would have to learn concepts in prerequisite order, before it can understand complex software abstractions. Reproducing that architecture is a long-term research effort, not a prerequisite for practical agent memory.

The intermediate module deliberately borrows existing language knowledge from pretrained embeddings. It retains the relational and activation principles but does not attempt to simulate or learn the amodal substrate.

| Long-term AFM | Intermediate PFC |
|---|---|
| Learned amodal concept identity | Stable IDs with pretrained language embeddings |
| Concept learning and compositional phase structures | Explicit pseudo-AOTD decomposition of directives |
| Learned language-to-AOTD and AOTD-to-language segment | LLM-assisted structured extraction; stored natural-language directives for output |
| Waveform resonance | Numerical embedding similarity |
| Sparse directional topology | Sparse directional topology |
| Thresholded forward O propagation | Thresholded forward O propagation |
| Learned language and concepts | No custom model training initially |

Do not presume the precise AFM language segment implementation has been verified. It has not been reviewed against the local AFM repository in this chat. The earlier `AFM_PFC_CONTEXT.md` is historical context for that longer-term project, not the implementation specification for this new project.

---

## 3. Core representation (agreed)

### 3.1 Pseudo-AOTD

A directive is expressed as a directional relationship:

```text
A[D_A...]  -- O[phase] -->  T[D_T...]
```

- A and T are **roles in a relationship**, not distinct kinds of nodes.
- D is a set or ordered composition of contextual qualifiers attached to the corresponding entity. It is not an independently connected node in the initial representation.
- O is the operation that relates the two entities.
- Phase expresses the signed scale or polarity of the operation. Keep exact modality as well: `not_required` and `prohibited` are not the same, and `permitted` and `required` are not the same.
- Original directives, including conditions and exact numeric values, remain authoritative. Embeddings are an activation mechanism, not an exact logical encoding.

Example (canonical conceptual forms, not a universal engineering policy):

```text
A: report[D: month-end]  O: consistency[+]  T: transaction
A: report[D: dashboard]  O: consistency[-]  T: transaction
```

These encode the project directives that month-end reports require transactional consistency and dashboards need not require it. The latter is not a prohibition of consistency.

### 3.2 One flat entity population

There is exactly one entity registry. The same entity ID and embedding can participate as A in one relationship and T in another. It must not be duplicated or re-embedded because of its role. `source_id` and `target_id` refer to the same registry.

Entity identity is the composition of concept and decorators, not a hierarchy. For example:

```text
report + []
report + [financial]
report + [month-end]
report + [dashboard]
report + [month-end, consolidated, financial]
```

These are separate flat contextual entity states. Their embeddings may naturally resonate because of pretrained semantic knowledge. Do not require traversing `report -> financial -> month-end -> consolidated`. Do not construct a taxonomy, prerequisite concept graph, inherited attributes, or a tensor containing an entire AOTD relationship. A+D determines the selected or generated entity embedding directly.

Likewise, run, walk and sprint do not need to be mapped onto a fundamental learned `move` phase space in this project. That is the AFM research problem we are explicitly avoiding. We do not need full language decomposition; only enough structured interpretation to represent a particular constraint or query.

### 3.3 Independent operation population

Operations occupy a second, independently indexed population. O+phase is the composition to embed. The stored operation text should be able to express exact phase/modality in language.

```text
consistency + required       (+)
consistency + strict_required (++)
consistency + not_required   (-)
logging + prohibited         (-)
logging + permitted          (positive permission, not obligation)
```

Phase numbers in the fixture are conventions: +1, +2, -1, etc. A null phase in a query means the phase is not specified, not zero or a guessed positive requirement. Do not infer modality purely from a sign. Keep explicit metadata and the authoritative rule text; do not silently convert "not required" into "must not".

### 3.4 Directed relationships and provenance

An operation is referenced by a directed edge between two entity IDs. Edges can share operation embeddings; multiple operation edges can connect the same pair of entities. An entity can have thousands of incoming and outgoing edges.

For a directive about report consistency, an alternate transaction-oriented perspective can be explicitly authored by the background LLM:

```text
report[month-end] -- requires consistency of --> transaction
transaction -- must guarantee consistency for --> report[month-end]
```

These are separate directed edges with common rule provenance. A reverse relationship must be independently meaningful. Never mechanically invert every edge: `authentication requires database access` does not imply `database access requires authentication`.

The original directive should be returned once even if multiple activated edges point to it. Keep edge identity for diagnostics. Neither a multi-hop path nor a strong similarity score establishes a new logically entailed constraint.

### 3.5 Minimal Python domain schema (proposed)

Use typed dataclasses or Pydantic models. The actual fixture field names below are compatible with the supplied JSONL; production extensions can be optional.

```python
@dataclass(frozen=True)
class Entity:
    id: str
    concept: str
    decorators: tuple[str, ...]
    contextual_text: str

@dataclass(frozen=True)
class Operation:
    id: str
    concept: str
    phase: int | None
    phase_symbol: str | None
    modality: str | None
    contextual_text: str

@dataclass(frozen=True)
class Relationship:
    id: str
    source_id: str
    operation_id: str
    target_id: str
    rule_id: str

@dataclass(frozen=True)
class Constraint:
    id: str
    family: str
    directive: str
    modality: str
    phase: int
    canonical_edge_id: str
    alternate_edge_ids: tuple[str, ...]
```

The code example is illustrative, not a required verbatim implementation. Preserve the exact fixture identifiers. Production rule records should additionally include project scope, source evidence, author/authority, active or superseded status, revision, effective time and exceptions where necessary. Store vectors in separate arrays keyed by stable row maps; do not serialize NumPy arrays into every logical record. Concept normalization and decorator ordering must not erase meaningful distinctions; do not sort every decorator combination indiscriminately.

---

## 4. Embedding design and experimental question

### 4.1 Frozen language encoder (agreed)

Use an existing pretrained language embedding model, with Qwen3-Embedding-0.6B as the initial candidate. No model fine-tuning, adapter training, or open-weights training harness in the initial project. The encoder is unaware of the relationship graph and any hierarchy. Its role is to supply semantic representation of the composed entity or operation phrase.

Pin the exact model revision, tokenizer, pooling, normalization, dimension, inference dtype and text formatting. Confirm the selected backend supports the desired output dimension. Proposed dimensions are 256, 512 and 1024; apply the documented truncation strategy if supported, then normalize again. Do not silently treat arbitrary truncation as a supported model feature. Measure CPU/local accelerator behaviour rather than assuming a latency figure.

### 4.2 Composition methods (proposed experiments)

Define `u(text)` as the L2-normalized embedding returned by the frozen encoder and `norm` as L2 normalization. For entity concept `a`, decorators `d_i`, and contextual phrase `c`, test:

| ID | Method | Entity vector |
|---|---|---|
| C0 | Direct contextual | `u(c)` |
| C1 | Mean decorator superposition | `norm(u(a) + lambda * mean(u(d_i)))` |
| C2 | Contextual interpolation | `norm((1-lambda)*u(a) + lambda*u(c))` |
| C3 | Individually weighted sum | `norm(u(a) + sum(lambda_i*u(d_i)))` |
| C4 | Structured input | `u('Entity: ...; Qualifiers: ...')` |
| C5 | Base-only control | `u(a)` |
| R0 | Whole-rule baseline | `u(original_directive)`; compare only on constraint retrieval |

C1/C3 with no decorators reduce to the base vector. C2 at lambda=1 equals C0 and at lambda=0 equals C5. Test lambda values 0.25, 0.5, 0.75, 1.0 on dev. For C3 compare a fixed total decorator budget against equal per-decorator weights, especially for two- and three-decorator states.

For O+phase apply analogous direct contextual, additive, interpolated and structured variants with phase/modality rendered in text. The operation concept is the base. For a neutral operation query use the concept only, or the supplied neutral paraphrase; do not insert a polarity that the query did not supply. Keep neutral, phase-specific, and exact-modality queries separate. Do not use negating the entire vector as the default encoding of negation: a negative directive must still be found by a neutral query. If tested at all, it is a distinct ablation.

Do not assume vector addition preserves linguistic binding. Direct contextual embedding is the baseline because the encoder may already understand the composition. Superposition could be beneficial by preserving base concept resonance and controllable decorator contribution, but this is an empirical hypothesis. Similarly, interpolation is not assumed to define semantically meaningful intermediate points.

### 4.3 Symmetric encoding and exact metadata

Start with identical encoding conventions for stored and query components to measure symmetric cosine resonance. Instruction-conditioned query embedding may be useful but must be a separate experiment with documented prompts. Do not mix asymmetric variants without labeling them.

Entity and operation vectors occupy separate logical registries even if produced by the same model. A and T do not have separate encoders or separate spaces. Compare a supplied entity component to the shared entity matrix; compare O to the operation matrix.

Similarity does not define identity, equivalence, scope or truth. Two near vectors may be different entities or contradictory operations. Exact phase/modality, authoritative directive and provenance survive outside the embedding. An exact metadata gate can be useful but must be evaluated separately from the raw embedding ranking to show what the encoder actually learned.

### 4.4 Embedding cache (proposed)

Cache raw embeddings by hash of model revision, tokenizer/backend settings, pooling, dimension, instruction/role convention, canonical input and dtype. Cache composed normalized vectors separately by composition method and parameters. No graph topology is encoded in the cache key for entity identity. Changes in connectivity should not require re-embedding unchanged concepts. Encoder revision or composition policy changes require a new compatible snapshot; never silently combine incompatible vector spaces.

---

## 5. Resonance and graph runtime

### 5.1 Established invariants (agreed)

- The coding agent supplies decision context when a design choice is being considered. The PFC does not preemptively reason about unrelated tasks.
- A pseudo-AOTD construct is passed as the query. Initial excitation includes **all supplied terms**, not only Attention. Missing query terms are omitted, not invented.
- After initial excitation, further propagation takes place through forward Operation resonance. The original AFM base threshold rejects insufficiently resonant paths early.
- Connectivity is directional. No automatic reverse traversal, shortest-path semantics, ontology inference, or rule derivation. Alternate directions are explicitly stored.
- No graph database is necessary. A sparse numerical representation is sufficient. Queue/frontier machinery may implement the numerical propagation but must not substitute unconditional BFS/DFS for resonance.
- The module returns stored action memories and evidence of activation, not generated design decisions or logical conclusions.

### 5.2 Numerical representation (proposed)

For embedding dimension d, store two normalized float matrices and a sparse edge table:

```text
E: float32[N_entities, d]
O: float32[N_operations, d]
G: (edge_id, source_row, operation_row, target_row, rule_id)
```

Use a source-indexed CSR-style adjacency: `indptr[N+1]`, `edge_indices`, and compact arrays for source, operation, target and provenance row IDs. A simple Python dictionary of outgoing edge IDs is sufficient in the reference implementation. NumPy is sufficient initially; SciPy sparse structures may help when scale warrants it. No need for a graph DB, ANN service, GPU, or PyTorch outside embedding inference in the first milestone.

For normalized query vectors q_A, q_T, q_O compute independent cosine scores:

```python
r_a = E @ q_a  # if present
r_t = E @ q_t  # if present
r_o = O @ q_o  # if present
```

Compute each operation score once per query and gather it by edge operation index. High-degree nodes do not require a fresh dense dot product for every edge when operation IDs are shared. Exact exhaustive scoring establishes the baseline; an ANN index can later accelerate initial activation while remaining independent of topology.

### 5.3 Initial excitation and single-edge scoring (experimental)

The agreed mechanism is composite initial excitation, followed by O-based propagation. The precise initial fusion is **not yet finalized**.

Compare these explicitly labeled experimental choices:

1. Same-role initial matching: q_A against a stored source, q_T against a stored target, q_O against its operation. Use only supplied terms.
2. Role-agnostic initial entity excitation: both supplied entity terms excite the shared population, allowing a relevant entity to seed its own outgoing authored relationships. This is not reverse traversal. Keep provenance of which query term caused the seed.
3. Single-edge ranking control: combine the applicable source, operation and target scores using min, product (with explicit nonnegative mapping), or weighted sum. Record the component scores. This is a retrieval baseline, not multi-hop propagation or proof of the final resonance model.

A hard conjunctive T gate may wrongly suppress broad queries where the agent wants to see other entities connected to its decision. A pure OR seed may create unnecessary noise. Compare on dev and report separately. Thresholds and weighting choices are not architectural facts. Broad queries should recover all appropriate policy variants, even if their phases differ.

### 5.4 Forward O resonance (reference algorithm, proposed)

Begin with initial seeds; for the supplied path benchmark the seed is provided by the oracle to isolate propagation. Hold the query operation fixed for the initial experiment. For each active source, examine only its outgoing relationships, look up cached O scores and activate qualifying edges. The reached target becomes an eligible source for the next step. Stop on no remaining qualifying edges, with explicit cycle protection.

```python
# Illustrative single-query reference, not the final optimized implementation.
operation_scores = O @ q_o
frontier = list(initial_seed_rows)
expanded = set()
active_edges = set()
while frontier:
    source = frontier.pop()
    if source in expanded:
        continue
    expanded.add(source)
    for edge in outgoing[source]:
        if operation_scores[edge.operation_row] <= threshold:
            continue
        active_edges.add(edge.id)
        frontier.append(edge.target_row)
```

Do not confuse the worklist with conventional graph semantics: an edge enters the active set only through resonance. Log visited source count, evaluated and surviving edges, and whether any safety cap was reached. The sample algorithm collects active edges, not all paths; preserve parent transitions and reconstruct cycle-safe paths separately when evaluating `gold_paths`. A global expanded set is safe for reachable edge collection with a fixed operation score but not sufficient to enumerate all distinct paths or preserve path-dependent activation. If later evaluating cumulative resonance, the state must include the required path context.

Open questions: whether excitation amplitude should decay, accumulate or saturate; whether the threshold is shared or separately calibrated for initial entity/operation matches and forward edges; how to handle a query with no O; whether operation resonance should remain anchored to the original query or be updated by the preceding operation. Start with a fixed O anchor and a threshold. Test alternatives only after the simple reference works. Never silently follow every outgoing edge when O is missing; define and measure a separate fallback. Cycles and safety caps are implementation controls, not memory semantics.

### 5.5 Output contract

Return the exact active rule text, IDs, provenance, relevant source/target/operation descriptions, phase, modality and scores. Deduplicate by `rule_id` for the coding agent, but retain activated edge IDs and traces for auditing. Multiple opposing rules may correctly activate for a broad decision context. Do not merge them into a compromise or assume that one supersedes another based on score. An explicit warning about conflict or uncertainty is preferable to invented resolution. Relevance scores are not calibrated probabilities of correctness.

---

## 6. Benchmark package v0.1 (existing artifact)

The supplied synthetic benchmark was generated for this experiment. Its manifest and files are the source of truth. Counts verified against the existing manifest in the current session:

| Corpus | Count |
|---|---:|
| Entities | 167 |
| Operations | 114 |
| Directed relationships | 236 |
| Authoritative constraints | 152 |
| Policy families | 14 |
| Retrieval queries | 568 (204 dev, 364 test) |
| Additional path scenarios | 8 (3 dev, 5 test) |

| Task | Dev | Test | Total |
|---|---:|---:|---:|
| Entity | 49 | 90 | 139 |
| Operation topic | 15 | 26 | 41 |
| Operation modality | 25 | 41 | 66 |
| Relationship/constraint | 115 | 207 | 322 |
| Path (additional) | 3 | 5 | 8 |

Development policy families: cache, events, export, reporting, schema. Held-out test policy families: access, API, concurrency, deployment, logging, notification, payment, storage, testing. The corpus is shared and indexed in full; the query families are held out for parameter selection. This is a retrieval benchmark, not an encoder training dataset.

The fixture is deliberately dense: closely related scopes, overlapping decorators, one-decorator changes, shared targets, opposing phase/modality, independently authored directional views, and same-source different-operation distractors. The export and notification families include two- and three-decorator variation. Eight path fixtures contain two same-operation branches and hard negatives involving a different operation and an incoming edge.

### 6.1 Files and interfaces

```text
pfc_embedding_benchmark/
  README.md
  manifest.json
  entities.jsonl
  operations.jsonl
  relationships.jsonl
  constraints.jsonl
  queries_dev.jsonl
  queries_test.jsonl
  paths_dev.jsonl
  paths_test.jsonl
  aliases_audit_only.jsonl
  build_dataset.py
  score.py
```

Query records have `id`, `task`, `split`, `family`, `query`, `view`, `positive_ids`, `hard_negative_ids`, and task-specific oracle fields. Some relationship queries have `oracle_aotd` and `positive_edge_ids`. Path records have `seed_entity_id`, `oracle_aotd`, `positive_edge_ids`, `hard_negative_edge_ids` and `gold_paths`. Read actual JSONL schemas rather than assuming all optional fields are present.

The scorer expects JSONL rows:

```json
{"id": "q_...", "ranked_ids": ["e_...", "e_..."]}
```

Use entity IDs for entity tasks, operation IDs for operation tasks, **rule IDs** for relationship retrieval, and edge IDs for path tasks. No duplicate ranking IDs. Missing predictions count as empty; partial runs should be labeled and not confused with complete evaluation. For path scoring and edge-level directional diagnostics retain actual paths as separate output files. The provided scorer calculates ranked and returned-set metrics; it does not implement full path reconstruction or model inference.

```bash
python data/benchmark_v0_1/score.py --split dev --predictions runs/experiment/predictions_dev.jsonl --k 10
```

Adjust the path to the actual extracted location in the new repository.

### 6.2 Leakage controls

- Do not index `aliases_audit_only.jsonl`, gold fields, query records, the generator source or held-out test answers as memories or prompt examples.
- Oracle query fields are privileged inputs for isolating numerical composition; never expose them to the LLM in the natural-query track. Report oracle results separately because canonical concepts may make that task substantially easier.
- The natural-query model receives only user-style decision text and allowed interface context. It must not see source rule IDs, qrels, family labels where they reveal the answer, or the benchmark generator. Freeze its prompt/model settings before test.
- Select weights, dimensions, threshold, scoring fusion and candidate caps on dev only. Freeze a small candidate set and run test once for the experiment report. Test-side tuning requires a new held-out split.
- Keep the original fixture immutable; save versioned additions separately. Synthetic policies are not real engineering or compliance recommendations.

The fixture passed structural validation and the scorer passed a synthetic gold-ranking smoke test in the earlier turn. No embeddings have been measured yet. The synthetic corpus is small, intentionally curated, and not sufficient evidence of real-world production performance. It does not establish reliable conflict resolution, continual learning, or generalization across all real codebases.

---

## 7. Experimental sequence and success criteria

The initial work should answer empirical questions, not demonstrate an elaborate service. Keep all results reproducible and report failures as well as successes.

### Experiment 1 — Entity composition

For C0–C5, rank the complete shared entity registry for each entity query. Start with exhaustive cosine scoring, not approximate search. Report narrow decorated queries, broad/base queries, target-origin aliases and partial/multiple decorator queries separately. Compare oracle structured component inputs against natural query text where appropriate. C5 is a deliberately weak control for specificity. For broad queries measure coverage of all expected variants rather than rewarding a single high-ranked match. Record examples in which a wrong decorator outranks the correct entity. Examine the distribution of positive and hard-negative scores and the effect of decorator count. A good composition must preserve base concept recall without collapsing contradictory contexts.

### Experiment 2 — Operation composition

Rank the full operation registry using operation-topic and operation-modality tasks separately. A neutral query about consistency must be able to surface both positive and negative requirements. An explicitly phase/modality-specific query should discriminate appropriate variants. Measure whether phase-aware composition improves discrimination without harming neutral topic recall. Record failures where permitted, required, prohibited and not-required modalities are confused. Report embedding-only retrieval before adding metadata gates. If exact metadata gates improve correctness, describe that as a hybrid method, not as evidence that the embedding learned negation.

### Experiment 3 — Constraint retrieval

Freeze the most promising entity and operation composition settings from development results. Compare whole-directive R0, single-edge matching, and composite initial excitation. Use oracle AOTD to isolate the graph/embedding algorithm before introducing the query extractor. Then use natural-query extraction with a fixed prompt and model. Measure the change between tracks. Deduplicate returned rule IDs across separately authored edges. Also evaluate edge-level direction where provided. Investigate whether the structured method actually beats whole-rule retrieval on densely overlapping policies and whether it recovers broader scopes without undue noise. R0 is a serious baseline, not a strawman.

### Experiment 4 — Propagation

With oracle seed and a fixed operation query, run the forward threshold algorithm on all path fixtures. Return both same-operation branches, reject incoming-edge and different-operation distractors, preserve the original rule provenance, and verify cycle handling on additional unit fixtures. Record actual paths and activated edges. Separate path activation precision/recall from any claimed reasoning capability. These eight scenarios are smoke tests rather than a large statistical sample; extend them with harder paths in a future version.

### Experiment 5 — Scale and latency (proposed)

After establishing quality, create a separately versioned stress corpus varying graph size, degree, operation reuse and density. Measure initial embedding latency, matrix score time, seed selection, edge filtering, propagation and result materialization separately. Distinguish cold model load from warm inference; record platform and hardware. Compare exact vector scores with ANN candidate generation only after measuring exact quality. Report ANN candidate recall and graph-edge evaluation cost, not only average wall time. Include p50/p95 latency and memory footprint; avoid imposing an arbitrary millisecond target before establishing the hardware and realistic integration budget.

### Metrics

- Recall@5/10/20, precision@5/10/20, MRR, full gold coverage, hard-negative exposure and hard-negative outranking.
- Thresholded returned-set recall/precision and count of false activations. Report the actual returned set, not merely the top-k ranking. A threshold and a top-k cap are different mechanisms.
- Query-view and family breakdowns; narrow versus broad and neutral versus phase-sensitive results. Broad queries may have more gold items than k, so a top-k coverage ceiling is not necessarily a defect.
- Path edge recall/precision, valid full path coverage, incoming-edge false activation, different-operation false activation, cap/termination events.
- End-to-end latency and per-stage timings, embedding calls/cache hit rates, candidate count, visited nodes and evaluated/surviving edges.

For production action memory, missing a mandatory rule is often more costly than returning an extra relevant-looking candidate. Nevertheless, too many false activations recreate the context overload problem. Do not pick a method solely from average similarity or MRR. Use a dev-only recall/precision operating curve and compare errors that matter. No absolute quality target or production readiness criterion has been agreed yet. A development report should recommend thresholds and explicit failure handling based on measurements, not invent success percentages. If structured methods do not beat R0 or fail to retain applicable rules, revise the representation or retrieval approach before adding complexity.

---

## 8. Background learning and the runtime language boundary

### 8.1 Memory formation (agreed concept)

Project learning occurs in entity and operation registries and the directional graph, not in pretrained model weights. The local/background LLM processes user directives, corrections, accepted design decisions and associated evidence. It creates or revises pseudo-AOTD relations. It is not required to reconstruct a full conceptual language or model a taxonomy.

The background job should be able to perform these mutations:

| Event | Action |
|---|---|
| New directive | Preserve original text and provenance; create independently meaningful directional relationship(s) |
| New contextual entity | Create or reuse flat concept+decorators identity and embedding |
| New operation | Create or reuse operation+phase+modality representation |
| Additional valid perspective | Add separately authored edge to the same rule |
| Repeated evidence | Optionally update confidence/reinforcement metadata; not automatically change phase |
| Exception | Preserve exception and explicit applicability; do not globally weaken the original rule |
| User correction or revised decision | Explicitly revise or supersede the affected rule, with history retained |
| Obsolete memory | Deactivate or prune affected relationships without deleting shared entity/operation data |

Reinforcement of memory strength is distinct from the signed phase that expresses the directive. The exact weighting mechanism, if any, is open. An asserted strong constraint does not become optional just because it was mentioned once. Repeated references do not independently confer authority. Do not merge merely because vectors are close.

### 8.2 Proposed update transaction

```text
interaction/decision event
  -> retrospective extraction by background LLM
  -> proposed rule + entity/operation/edge mutations
  -> structural and semantic checks
  -> embed only newly introduced or revised compositions
  -> stage immutable snapshot or delta
  -> regression checks against known memories
  -> atomic publication
```

Use an explicit structured mutation contract, not free-form generated code. Validate references, phase/modality combinations, direction, provenance, and contradictory or superseded rules. Do not automatically convert an agent's unapproved proposal into a user-approved directive. For source conflicts or uncertain scope, retain uncertainty and original evidence; policy authority resolution is outside the embedding engine.

One-shot memory formation is a core desired property: no need for repeated examples or training epochs to record a newly agreed instruction. However, inserting a rule does not guarantee that all relevant future queries will retrieve it. Production should retain a direct lookup or scope-based explicit safety mechanism for mandatory rules where exact completeness is required; do not present approximate resonance as a formal constraint enforcement system. The exact fallback and integration policy remain open.

### 8.3 Query and response language interface

For the initial benchmark, oracle structured queries let us test the numerical engine without a runtime LLM. For realistic use, the coding agent can provide structured decision context itself, or a lightweight local LLM can map supplied natural language into pseudo-AOTD. Compare these as interface options; a runtime LLM is not an architectural requirement for the numerical engine.

A proposed query object has optional attention, operation and target components; each entity component has concept, decorators and contextual text; the operation has concept, optional phase/modality and contextual text. Preserve ambiguity, return multiple constructs when appropriate, and never invent missing scope or phase. Use the same entity registry for A/T. The coding agent does not need to understand the numerical representation; it receives natural-language directives with traceable IDs. A second generative decoding call is unnecessary when the exact original rule text is retained. A generated synopsis may be added later as non-authoritative output, but must not replace the original directive.

The local LLM is responsible for extraction, relationship creation, and offline maintenance, not runtime traversal or independent design reasoning. This is deliberately different from the long-term AFM language segment. Query extraction quality and graph retrieval quality should remain separately measurable.

---

## 9. Persistence, concurrency and integration (later milestones)

insrc previously considered an immutable memory-swap model: each active session holds a stable view of memory while an asynchronous job produces a consolidated version. Once the new snapshot is ready it is atomically published; older snapshots remain until their consumers release them. Adopt the principle later, after the benchmark engine is established.

Proposed persisted snapshot contents: canonical entity/operation/rule registries, directed edge table, vector matrices, row-ID mappings, encoder/composition fingerprint, optional adjacency/index artifacts, version and provenance manifest. NumPy `.npy` arrays with optional memory mapping and JSONL/SQLite metadata are sufficient initially. Prefer explicit schemas and atomic snapshot publication over mutable shared arrays. If using SQLite, it is a persistence layer, not a semantic graph database. Separate encoder caches from graph versions; retain immutable history and regression results where needed.

For concurrent background updates, use one writer or optimistic version checks. Readers pin a consistent snapshot. Avoid combining a graph from one version with vectors from another. Crash recovery must not expose partial snapshots. Explicitly design how newly approved mandatory directives reach long-lived sessions; a pinned old snapshot cannot silently be treated as the latest policy. A small pending-directive overlay or re-pin at decision boundaries is a possible approach, not yet agreed. No cross-session or cross-project leakage; preserve project and organization scope and authorization. Repository content and historical user instructions may contain sensitive data, so local inference and access boundaries matter in production. No external hosted embedding service is needed for the initial project.

Potential eventual integration: an insrc decision hook supplies a decision context at relevant design stages; a separate background retrospective job emits structured learning events; the PFC returns exact relevant memories for the coding agent's consideration. Do not integrate into insrc until the standalone quality baseline is understood. No Node.js dependency or TypeScript implementation for this project.

---

## 10. Python project layout and dependencies (proposed)

Use Python 3.11+ or 3.12, with the exact supported interpreter pinned after checking embedding backend compatibility. Keep the numerical engine independent of the model backend and LLM provider. The following layout is a recommendation, not a requirement to create every module immediately.

```text
pfc/
  pyproject.toml
  README.md
  docs/
    PROJECT_CONTEXT.md
    experiments/
  configs/
    baseline.toml
  data/
    benchmark_v0_1/         # extracted, immutable supplied fixture
  src/pfc/
    models.py              # typed domain records and queries
    io.py                  # JSONL, integrity checks, fixture loading
    embeddings/
      protocol.py          # pluggable encode interface
      qwen.py              # frozen local embedding backend
      cache.py
      composition.py       # C0-C5, normalized output
    retrieval/
      exact.py             # cosine ranking, entity/operation isolation
      edge_score.py        # single-edge reference scoring
      resonance.py         # initial excitation + O-based forward propagation
    graph/
      index.py             # compact directional adjacency and row mappings
      traces.py            # actual edges/path diagnostics
    benchmark/
      runner.py            # experiments, predictions, timings
      metrics.py           # extended metrics, scorer integration
      report.py
    learning/              # later: structured extraction and mutation
    persistence/           # later: snapshots, version publication
    cli.py
  tests/
    unit/
    integration/
    regression/
  runs/                    # generated artifacts; not gold data or source code
```

Suggested dependencies: `numpy` for numerical operations, `pytest` for tests, `sentence-transformers` or `transformers` + `torch` for local Qwen inference after verifying the selected model's official requirements. Use an optional backend dependency group, so fixture validation and numerical tests can run without downloading a model. SciPy, ANN libraries, Pydantic, a local LLM client, and a service framework are optional later additions only when justified. Do not require a GPU, training harness, graph DB, vector DB service, orchestration framework, Node runtime, or cloud account for initial tests. Pin dependencies using the project's selected Python packaging workflow; do not rely on unversioned model `main` for published results.

Suggested backend protocol:

```python
class Embedder(Protocol):
    def encode(self, texts: Sequence[str]) -> np.ndarray:
        """Return one vector per input, with explicit dtype/dimension."""
        ...
```

Keep composition functions pure and separately testable. Use a deterministic fake embedder in unit tests to test vector arithmetic and graph mechanics without network access or model inference. Add optional real-model tests, clearly labeled. A fake encoder validates mechanics, never semantic retrieval quality.

Proposed CLI (not implemented):

```bash
python -m pfc validate --data data/benchmark_v0_1
python -m pfc benchmark --task entity --split dev --config configs/baseline.toml
python -m pfc benchmark --task operation_topic --split dev --config configs/baseline.toml
python -m pfc benchmark --task operation_modality --split dev --config configs/baseline.toml
python -m pfc benchmark --task relationship --split dev --track oracle --config configs/baseline.toml
python -m pfc benchmark --task path --split dev --config configs/baseline.toml
```

Every run should store an immutable configuration, model fingerprint, corpus hash, parameter values, split, timing/environment information, ranked predictions and component scores. Provide a comparison report that identifies the best development variants and failure cases. Do not report the missing tasks in partial prediction files as genuine model failures; use task-filtered metrics or explicitly label the scorer's empty predictions for unrun tasks.

---

## 11. Implementation milestones and acceptance tests

### M0 — Bootstrap and fixture validation

Set up the Python package and tests. Extract the supplied ZIP. Verify manifest counts, record IDs, shared registry, edge references, rule provenance, qrels IDs, split separation, path continuity and absence of duplicate IDs. Do not mutate the fixture. Use the supplied scorer and a synthetic perfect ranking as a smoke test. The test suite should run offline without embedding weights. Record file hashes and dependency lock.

### M1 — Frozen encoder and composition primitives

Implement a pluggable encoder, local Qwen candidate, raw-vector cache, normalization, C0–C5 and R0 controls. Test vector shape, dtype, no NaNs, stable row mapping, deterministic formatting, batch/order consistency within numeric tolerance, and zero-vector handling. Verify C2 endpoints, C1/C3 without decorators, and fixed total versus per-decorator weights. Cache invalidation tests must cover model revision, dimension, prompt and text changes. No training or graph traversal required.

### M2 — Entity and operation benchmark

Run development experiments, evaluate complete candidate populations, produce ranked predictions, compare composition/dimension/weight settings, and write an analysis of errors including hard negatives. Separate neutral topic and phase-specific operation retrieval. Compare raw embedding retrieval with optional metadata gating. Freeze selected variants before test. This is the first substantive project deliverable. Do not proceed directly to production integration.

### M3 — Directed graph and propagation

Implement shared entity/operation row maps and sparse outgoing connectivity. Test that a node used in both A and T roles is exactly the same entity; multiple edges can reference one operation; alternative perspectives are explicit; reversing a relationship is not automatic. Test threshold boundary (`>` vs `>=`, document chosen convention), multiple qualifying branches, disconnected regions, cycles, missing O fallback, and same-source different-operation filtering. Test rule deduplication and preservation of negative/prohibited/permission distinctions. Use controlled vectors to prove mechanics independently of semantic quality, then run the provided path datasets with real embeddings.

### M4 — End-to-end retrieval

Compare R0 with structured oracle and natural-query tracks. Store component scores and paths, evaluate direction and rule-level precision/recall, and characterize the gap caused by extraction. Report threshold operating curves and actual costs. Test broad queries activating opposite requirements, narrow queries separating scopes, omitted components, partial decorators, exact negative modality, and supersession/exception preservation in additional fixtures. Do not treat an activated path as a new logical directive.

### M5 — Incremental memory mutation and snapshots (after validation)

Implement explicit background mutation input, deterministic validation, embeddings for new entities/operations, version publication and regression tests. Prove one-shot insertion is queryable, unaffected vectors are not regenerated, shared concepts survive pruning, an old snapshot stays consistent, and failed publication does not alter the active version. Test concurrent readers, superseded directives, authority/evidence separation, duplicate rules and incompatible encoder revisions. Evaluate new memory recall and retained old memory recall after additions/corrections. These tests measure structural learning rather than neural continual learning.

### M6 — insrc integration and real-project evaluation (later)

Integrate with actual decision points and asynchronous retrospectives. Evaluate on human-reviewed project experiences, including long sessions and cross-agent constraints. Compare with existing information-memory retrieval. Measure missed constraints, false activations, context size, latency, and downstream decisions, with explicit attribution limits. Verify project isolation and policy validity. Real-world evaluation is necessary before claiming the PFC improves agent governance.

---

## 12. Open design questions

1. Which A+D composition yields the best trade-off between broad entity resonance and narrow scope discrimination? Is superposition useful, or does direct contextual embedding already dominate?
2. Which O+phase composition preserves both neutral topic recall and exact modality discrimination? What portion needs explicit metadata rather than vector geometry?
3. How should all supplied query terms contribute to initial excitation? Same-role matching, role-agnostic seeding, and score fusion must be compared, not assumed equivalent.
4. Should O propagation keep a fixed operation anchor, or allow resonance to shift along the path? Should activation accumulate or decay? Start with a fixed anchor and simple threshold to isolate the mechanism.
5. How should the engine handle omitted operation or entity components, multiple query constructs and uncertainty? No implicit exhaustive graph traversal.
6. How should flat entity identity be canonicalized without confusing aliases, scopes or materially different decorators? Embedding similarity is evidence, not an identity rule.
7. How many alternate directional perspectives should the background LLM author for a directive? Avoid combinatorial expansion and invalid inverses.
8. How should conditions, exceptions, mandatory rule coverage, conflicts and immediate changes be surfaced to agents? Approximate retrieval is not proof of correctness.
9. If the frozen encoder fails, is a small trainable metric, online transition model, different encoder or better textual composition warranted? Only investigate after measured baseline results. No training harness should be introduced preemptively.

---

## 13. Architectural guardrails — do not drift

- Python, not Node.js.
- Intermediate PFC action memory, not an AFM implementation or an autonomous reasoning engine.
- One flat entity population; A/T are edge roles. A+D and T+D are independently composed contextual entities in that same space.
- One separate operation population; O+phase composition, with exact modality and provenance preserved.
- No mandatory hierarchy, concept prerequisites, complete language decomposition, base-concept phase ontology, or entire-AOTD tensor.
- Frozen pretrained embedding model initially; learn structurally via directed relationships, not weight updates.
- Composite query excitation, followed by selective forward O resonance with a base threshold. No automatic reverse traversal, semantic graph inference or shortest-path retrieval.
- Sparse numerical representation; no required graph DB. Conventional whole-rule vector retrieval is a comparison baseline, not the memory architecture.
- The coding agent supplies decision context and owns decisions. The memory layer returns existing directives, never invents new requirements.
- Maintain exact original language, conditions, authority and rule provenance outside embeddings.
- Benchmark first, then evolve; compare variants rather than assume superposition works. Never leak qrels into natural query inputs or tune on the test set.

## 14. Suggested first instruction for the repository agent

> Read this project context and the companion PFC Embedding Benchmark v0.1 README/manifest. Set up a standalone Python project for milestones M0–M2 only. First verify the benchmark schema and propose a minimal package layout, local frozen embedding backend, and reproducible experiment configuration. Implement model-independent validation and composition tests, then run entity and operation retrieval experiments against the dev split. Keep test labels isolated until the configuration is frozen. Do not introduce AFM language learning, model training, a graph database, a concept hierarchy, a service layer, or insrc integration. Report actual measured results and failure cases before proceeding to graph propagation.

