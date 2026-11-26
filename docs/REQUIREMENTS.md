# agent-pfc requirements

Version 0.5. 27 November 2026.

This document says what the system must do. Design is done separately, one module at a time.

**Status** of each requirement:

- **Agreed:** stated or confirmed by the project owner.
- **Proposed:** suggested during discussion and not yet confirmed. Do not design against it as settled.

## 1. Purpose

agent-pfc keeps the instructions given to a coding agent and returns the relevant ones when the agent asks, as efficiently as possible.

General memory is served adequately by reading files or by ordinary vector lookup. This project is about recalling the instructions that bear on what an agent is about to decide. "Do not paginate customer records" is an instruction the agent needs when it decides how to display tabular output.

## 2. Scope

| ID | Requirement | Status |
|---|---|---|
| S1 | Persist and recover instructions and data points for coding agents. | Agreed |
| S2 | Run as a standalone system, not embedded in insrc. | Agreed |
| S3 | Be written in Python. | Agreed |
| S4 | Install and run on a local machine. | Agreed |
| S5 | Do not rule out later use as shared organization memory for a project. | Agreed |

Not in scope:

- A general-purpose inference or reasoning engine.
- Controls on destructive actions, such as deleting data or pushing code. These belong in the agent harness.
- Organization features (accounts, sharing between people) in the first version.

## 3. Memory entries

| ID | Requirement | Status |
|---|---|---|
| E1 | Each entry is an **instruction** (how something must be done, including design decisions) or a **data point** (a fact about the project or its environment). The two are kept distinct. | Agreed |
| E2 | Entries are short, normalized rules or facts, not verbose statements. An entry's text is at most 500 characters. | Agreed |
| E3 | Memory is project centric: an entry belongs to the project whose history produced it. | Agreed |
| E4 | An entry keeps its scope, negation and conditions through normalization. | Agreed |
| E5 | One entry holds one rule or fact. | Agreed |
| E6 | An entry records its source (agent, session, session file, position and time) and the models that produced it. The original wording is not stored. | Agreed |
| E7 | An entry is created only from what the user states or accepts. An agent's unaccepted proposal is not an entry. | Agreed |
| E8 | A newer decision replaces the outdated entry. The old one is retired, not erased. An entry can also be retired with no replacement. A retired entry is not reactivated. | Agreed |
| E9 | A rule already stored is not stored again. | Agreed |

E1: that design decisions count as instructions is agreed.

## 4. Capturing entries

| ID | Requirement | Status |
|---|---|---|
| C1 | The coding agent does not write memory. Entries come from parsing chat history with a local model. | Agreed |
| C2 | Parsing is a batch run, started by timed triggers in the agent-pfc daemon. | Agreed |
| C3 | A run covers all available conversation histories. | Agreed |
| C4 | Each session is processed from its last checkpoint up to 5 minutes before the run. | Agreed |
| C5 | Parsing analyses a moving window of messages, not one turn at a time. | Agreed |
| C6 | Conversational turns are ignored. New instructions and data points are classified and stored if required. | Agreed |
| C7 | Parsing runs in its own worker process, started by the daemon. | Agreed |
| C8 | The history of command-line coding agents is made available to the daemon. | Agreed |
| C9 | Tool output, compaction summaries, subagent traffic and injected messages are excluded. Pasted text is marked as pasted. | Proposed |
| C10 | Updates are idempotent. A session's checkpoint decides which file is read and from where, and advances only after the entries are confirmed stored. Submitting again without new turns changes nothing. | Agreed |
| C11 | Only one run is active at a time. Missed triggers lead to one run, not one per missed trigger. | Proposed |
| C12 | When sessions overlap, the later message wins. | Proposed |
| C13 | Support Claude Code history first, then Codex. | Proposed |
| C14 | A history reader reports records it does not recognise instead of skipping them silently. | Proposed |
| C15 | Raw chat history stays on the user's machine. Only entries and source references reach the memory server. | Proposed |
| C16 | The local model breaks each turn into simple directives and facts, one per entry, each keeping the condition or scope that applies to it. A turn is not stored whole as one entry. | Agreed |
| C17 | A setting, off by default, turns on local archiving of Claude sessions, so that an entry's source can be looked up after the agent deletes its history. Remote archiving may follow. | Agreed |

## 5. Querying

| ID | Requirement | Status |
|---|---|---|
| Q1 | The agent decides when to consult memory. Memory is never pushed into a session. | Agreed |
| Q2 | Steering text may guide when and how to consult memory. | Agreed |
| Q3 | Retrieval works for generic queries about a decision, such as "display tabular output" or "decide transaction mode". | Agreed |
| Q4 | Instructions and data points can both be queried. | Agreed |
| Q5 | Agents access memory through MCP. | Agreed |
| Q6 | A query returns only entries of the named project. | Proposed |
| Q7 | Results are returned as stored, labelled as instruction or data point, with source and date. | Proposed |
| Q8 | The agent may send related concerns with a query, for example "transaction consistency" for a sharding decision. | Proposed |
| Q9 | The agent judges which results apply. Search is not expected to reject every irrelevant result. | Agreed |
| Q10 | While normalizing an entry, the local model replaces each named entity with its official name, keeping versions, and tags it. Only tagged entities are keyword indexed. The calling agent is steered to use official names and to send them with its query. Names are matched loosely: missing a relevant entry is worse than returning an extra one. Exact matches rank first, and loose matches do not crowd out strong vector results. Generic queries rely on vector search. | Agreed |

## 6. Service and storage

| ID | Requirement | Status |
|---|---|---|
| V1 | A local HTTP memory server serves queries and updates. The MCP side and the daemon use it over HTTP. | Agreed |
| V2 | There is one store, in LanceDB, owned by agent-pfc and not shared with insrc. | Agreed |
| V3 | One indexer thread, managed by the memory server, is the only writer. There are no external writes. | Agreed |
| V4 | The work is split across processes so that parsing does not overload the daemon. | Agreed |
| V5 | The server listens only on loopback, requires a token and checks request origins. | Proposed |
| V6 | The HTTP API is versioned. | Agreed |
| V7 | A user can list and retire entries, through the server. | Proposed |

## 7. Models and installation

| ID | Requirement | Status |
|---|---|---|
| M1 | Two local models: one for embeddings, one for classification and normalization. | Agreed |
| M2 | Classification and normalization use Gemma 4 E2B. A 17 GB model is not needed. | Agreed |
| M3 | Embeddings use Qwen3 Embedding 0.6B. | Agreed |
| M4 | Both models are chosen by configuration and downloaded if not present. | Agreed |
| M5 | No dependency on Ollama. | Agreed |
| M6 | The memory service installer installs llama.cpp, used as a Python library. | Agreed |
| M7 | Support Linux, macOS and Windows. | Agreed |
| M8 | First targets: macOS on Apple silicon, Linux x64 and ARM64, Windows x64. | Proposed |
| M9 | Downloads are pinned to a revision and verified by checksum. A failure never substitutes another model. | Proposed |
| M10 | Entries embedded by different embedding models are never mixed. Changing the model means re-embedding. | Proposed |

## 8. Engineering constraints

| ID | Requirement | Status |
|---|---|---|
| N1 | Separation of concerns and modularity are the prime directive, in code and in package structure. | Agreed |
| N2 | Model runtime, storage and history formats sit behind interfaces so each can be replaced. | Proposed |
| N3 | A core, built first, provides the domain types, service contract and base infrastructure that the other modules share. | Agreed |
| N4 | The core is a set of packages with one responsibility each. It depends on no other module. | Agreed |
| N5 | Base infrastructure covers configuration, logging, error types, file locations, project identity and shared interfaces. | Agreed |
| N6 | The core includes the HTTP client for the memory server, used by every module that calls it. | Agreed |
| N7 | Process lifecycle is a separate module with its own design, outside the core. | Agreed |
| N8 | Process lifecycle covers startup, shutdown, health checks and single-instance locking for the server, daemon and worker. | Proposed |
| N9 | Shared code goes in `common` and `utils` packages, organized into modules by subject. | Agreed |

## 9. Quality targets

None are agreed yet. Each needs a number before the module it governs is accepted.

| Measure | Applies to |
|---|---|
| Instructions missed, wrongly added, distorted or not retired | Parsing |
| Relevant entry found within the first few results | Retrieval |
| Query response time, including while parsing runs | Server |
| Run time and memory use | Parsing worker |

Draft expected entries for measuring the parser are in `data/parser_eval/session_v1/expected.md`.

## 10. What early tests showed

Small, throwaway tests on one Apple M3 Pro. They are indications, not acceptance results.

- On 40 short rules and 40 queries, vector search with the Qwen model put the intended rule in the top 3 for 35 queries. Keyword search managed 9.
- A similarity score threshold did not reliably separate relevant from irrelevant queries.
- Gemma 4 E2B and the Qwen embedding model both load through the llama.cpp Python library (0.3.38).
- On a four-message example, Gemma 4 E2B labelled a fact as an instruction when run without its reasoning step. The labels had not been defined in the prompt.
- Setting the thread count explicitly matters on a loaded machine.
- Linux and Windows are untested.
- The llama.cpp Python release checked had no ready-built package for Intel Macs or Windows ARM64.
- Claude Code deletes old transcripts after 30 days by default, so they must be parsed before then.

## 11. Open questions

1. Should exceptions be linked to the general rules they limit, or only state their own scope?
2. How are replacements and duplicates detected?
3. What window size and overlap should parsing use?
4. How does each agent's history reach the daemon, and which agents come first?
5. How is a project identified, so that the same project matches across machines?
6. Are there preferences that apply to every project?
7. Should trial decisions ("start with X") be stored differently from settled ones?
8. What are the quality targets in section 9?
9. How is the daemon, server and MCP side started and kept running on each platform?

## 12. Modules to design

Proposed breakdown and order. Each gets its own design.

Module 1 is tracked as insrc Epic `690f38931e7d3b57` (`docs/epics/core-base-infrastructure-E20261126690f3893/`). It supersedes Epic `3b5f9aa550b6fe9d`, whose documents are history and must not be designed against.

Module 1 comes first because the others build on it. Its contents are:

| Part | Responsibility |
|---|---|
| Domain types | Entries, kinds, sources, projects and checkpoints |
| Service contract | Request and response types of the memory server API, and its version |
| HTTP client | The one client for the memory server, built on the service contract |
| Configuration | Loading and validating settings, including model selection |
| Logging | One logging setup for every process |
| Errors | Shared error types |
| File locations | Where configuration, data, models and logs live on each platform |
| Project identity | Deciding which project a session or query belongs to |
| Interfaces | The protocols through which modules depend on the model runtime and store |

| Order | Module | Covers |
|---|---|---|
| 1 | Core and base infrastructure | E1 to E9, V6, N1 to N6, N9 |
| 2 | Model management | M1 to M4, M9 |
| 3 | Model runtime | M5, M6 |
| 4 | Store | V2, V3, M10, Q10 |
| 5 | Process lifecycle | N7, N8, C11 |
| 6 | Memory server | V1, V3 to V7 |
| 7 | MCP adapter | Q1 to Q9 |
| 8 | History readers | C3, C8, C9, C13 to C15, C17 |
| 9 | Parser | C5, C6, C16, E4, E5, E7 to E9 |
| 10 | Daemon | C2, C4, C7, C10, C12 |
| 11 | Installer | M6 to M8, S4 |
