# PFC scope and benchmark review

Date: 26 November 2026  
Reviewed: `PFC_PYTHON_PROJECT_CONTEXT.md` (v0.1) and `PFC_Embedding_Benchmark_v0.1.zip`  
Archive SHA-256: `b630cadf5054791e8142aca00b0380ca074613709fe2642f4529066c4c1e3dac`

## Summary

The scope is well bounded and the benchmark package is structurally sound. Parts of the benchmark are too easy to tell the methods apart, so the evaluation protocol should be fixed before M2. Several propagation design gaps should be settled before M3.

No embedding model was run. All measurements below use the dev split.

## Strengths

- **Narrow first deliverable:** M0–M2 asks whether the representation works before any service is built.
- **Clear status:** *agreed* and *proposed* decisions are kept apart, and the guardrails say what not to build.
- **Honest controls:** whole-rule retrieval (R0) is treated as a serious baseline, embedding-only results are separated from metadata-gated ones, and the leakage rules are explicit.

## Fixture validation

| Check | Result |
|---|---|
| Entities / operations / relationships / constraints | 167 / 114 / 236 / 152, matching the manifest |
| Queries (dev / test), paths (dev / test) | 204 / 364 and 3 / 5, matching |
| Duplicate IDs, broken references, invalid gold IDs | none |
| Positive and hard-negative overlap, path discontinuities | none |
| Supplied scorer with perfect dev rankings | 1.0 recall and MRR on every task |

Cross-split query text overlap was not rechecked. Test files got structural checks only, with no queries or answers printed.

## Design gaps in the context document

Ordered by importance.

1. **Propagation may undo scope discrimination (§5.4).** With a fixed query operation, each hop checks only the operation score, so entities and decorators stop mattering after the seed. Once a path reaches a shared node, any matching outgoing edge activates, including ones belonging to other scopes. Compare a hop limit, decay or entity re-gating. See benchmark finding 4.
2. **No experiment shows that propagation helps retrieval.** Experiment 3 compares R0, single-edge scoring and initial excitation. Experiment 4 tests propagation only from oracle seeds. M4 does not clearly require a propagation on/off comparison.
3. **Initial excitation is underdefined for Target (§5.3).** Propagation starts from source entities and follows outgoing edges. If only `q_T` matches a stored target, activating that edge's source is effectively reverse traversal, and seeding the target misses the matched edge unless an alternate direction was authored. Define whether initial excitation activates edges, entities or both.
4. **No decision rule (§7, §12).** "Revise if structured methods don't beat R0" names no metric or margin. Before the test run, fix a primary metric, a minimum margin over R0 and a limit on missed rules.
5. **The data is thin for the search space (§4, §6).** Methods × λ × dimensions × fusion × thresholds is a large grid for 204 dev queries, with only 15 for operation topic and 3 dev paths. Select in stages, report per-family results with paired bootstrap intervals, and treat path thresholds as uncalibrated.
6. **The R0 comparison needs matched inputs.** Oracle AOTD gives structured methods information that R0 may not get. State what query text R0 receives in each track. Add a lexical baseline and an R0 plus structured hybrid.

### Smaller inconsistencies

- **C3 duplicates C1:** splitting a fixed total λ equally across n decorators gives `λ * mean(u(d_i))`, which is C1. Only the constant per-decorator weight is new, and the choice of unequal `λ_i` is not specified.
- **Redundant run:** C2 at λ=1 is C0.
- **Decorator order:** §3.1 and §3.5 allow order to carry meaning, but C1 and C3 are order-invariant. Record this as a known limit.
- **Contextual text:** C0 and C2 depend on authored phrases. State who writes them for stored items and queries in real use.
- **Phase 2:** the fixture also uses phase 2 with `permitted` (a greater degree of permission), not only `strict_required`. §3.3 does not describe this.
- **Test isolation:** M0 validation has to open test files. Limit it to structural checks that print no answers.

## Benchmark findings

### 1. Oracle entity inputs mostly give away the answer

In 42 of 49 entity queries, the oracle concept and decorators exactly match the correct stored entity. Composing both sides the same way yields identical vectors, so C1, C3 and C4 would rank it first (barring ties) whatever the encoder understands. Relationship oracles also match stored entities (110 of 115 attention, 115 of 115 target).

**Change:** compare entity methods using the natural query text. Treat oracle runs as a mechanics check.

### 2. Most modality queries copy stored text

20 of 25 operation-modality queries are verbatim copies of an operation's contextual text, which favors C0. The task says little about whether the encoder understands modality.

**Change:** add paraphrased queries in a separately versioned addition.

### 3. A keyword baseline already scores high

BM25 with lowercase alphanumeric tokens, no stemming, k1 = 1.2, b = 0.75. Entities and operations are indexed by contextual text, constraints by directive.

| Task | Queries | Recall@10 | MRR@10 | Top result correct |
|---|---:|---:|---:|---:|
| Entity | 49 | 0.959 | 0.840 | 77.6% |
| Operation topic | 15 | 0.929 | 1.000 | 100% |
| Operation modality | 25 | 0.827 | 0.980 | 96.0% |
| Constraint retrieval | 115 | 0.894 | 0.646 | 53.9% |
| – natural decision | 40 | 0.950 | 0.820 | 77.5% |
| – structured paraphrase | 40 | 0.850 | 0.528 | 42.5% |
| – alternate attention | 30 | 0.900 | 0.569 | 40.0% |
| – broad scope | 5 | 0.767 | 0.650 | 40.0% |

Entity ranking and constraint retrieval leave room to improve at the top rank. Operation topic leaves almost none.

**Change:** add BM25 as a required baseline next to R0. Use MRR or recall@1 as the primary ranking metric, with a separate recall requirement for mandatory rules.

### 4. Propagation added noise in a simulation

Seeds came from the oracle entity, and only edges whose operation concept matched the oracle operation exactly were followed. This stands in for ideal operation matching, without embeddings. Results cover relationship dev queries with oracle AOTD; the mean gold count is 1.22 rules.

| Seeds | Hops | Queries | Recall | Precision | Mean rules returned |
|---|---|---:|---:|---:|---:|
| Attention | 1 | 110 | 1.00 | 0.77 | 2.36 |
| Attention | 2 or unlimited | 110 | 1.00 | 0.32 | 5.09 |
| Attention + target | 1, 2 or unlimited | 115 | 1.00 | 0.35 | 5.13 |

Five queries had no usable attention seed. With attention seeds, the second hop found nothing new and more than doubled the rules returned. These queries may not need multiple hops, so this does not show that propagation is never useful.

**Change:** add path cases that pass through shared nodes into other scopes, and a one-hop versus multi-hop comparison in Experiment 3.

### 5. Some compositions cannot distinguish operation wordings

39 of 64 concept, phase and modality combinations have more than one contextual text. Methods built only from those fields give them identical vectors, so their ranking falls to tie-breaking.

### 6. Some views are very small

Dev has only 5 broad-entity, 3 partial-decorator and 5 broad-scope queries. Report them as examples, not as evidence for tuning.

## Scaffold versus §10

| Item | Document | Repository |
|---|---|---|
| Package name | `pfc` | `agent_pfc` |
| Python | 3.11+ or 3.12 | `>=3.12` (compatible) |
| Dependencies | `numpy`, optional model group | only `pytest`, for development |
| `runs/` | generated artifacts | not in `.gitignore` |
| Context doc | `docs/PROJECT_CONTEXT.md` | `docs/PFC_PYTHON_PROJECT_CONTEXT.md` |

The `hello()` stub and placeholder project description also remain.

## Recommended actions

### Before M2

- [ ] Make natural query text the primary comparison.
- [ ] Add BM25 next to R0, and state the query text R0 receives.
- [ ] Fix the primary metric, margin over R0 and mandatory-rule recall requirement.
- [ ] Add paraphrased modality queries as benchmark v0.2, leaving v0.1 unchanged.
- [ ] Choose the package name (suggested: keep `agent_pfc` and amend §10).

### Before M3

- [ ] Define what initial excitation activates, including target-only queries.
- [ ] Choose scope controls to compare: hop limit, decay or entity re-gating.
- [ ] Add cross-scope propagation cases to benchmark v0.2.
- [ ] Add a one-hop versus multi-hop comparison to Experiment 3.
