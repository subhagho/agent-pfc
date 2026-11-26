<!-- insrc:artifact DEF-3b5f9aa550b6fe9d -->

# Epic: core-base-infrastructure

## Summary

**Flavor:** new-capability

This Epic gives every later part of agent-pfc one shared vocabulary and one set of basics: what is remembered, how the memory server is asked for it, and how settings, logs, errors, files and projects are handled. Later modules can then be designed and tested one at a time against agreed boundaries.

## Contents

1. [Problem](#1-problem)
2. [Functional requirements](#2-functional-requirements)
3. [Non-goals](#3-non-goals)
4. [Assumptions](#4-assumptions)
5. [Constraints](#5-constraints)
6. [Stories](#6-stories)
7. [References](#7-references)

## 1. Problem

agent-pfc is made of several separately designed modules that run in more than one process and must agree on what a memory entry, a project, a session source and a checkpoint are, how a request to the memory server is expressed and versioned, how settings and files are found on Linux, macOS and Windows, and how failures are reported. Almost none of this exists: the code holds only an embedding interface, its cache, one error type and a test of import direction. Without an agreed shared foundation, each later module would define these for itself, the definitions would diverge, and the rule that every package has one responsibility with dependencies pointing one way could not be held.

## 2. Functional requirements

- **E202611263b5f9aa5:FR001** — The system has one definition of a memory entry that distinguishes instructions from data points, belongs to one project, and can carry its source, author, producing models and active or retired state.
- **E202611263b5f9aa5:FR002** — The system has one versioned definition of what can be asked of the memory server and what it answers.
- **E202611263b5f9aa5:FR003** — Every module that calls the memory server does so through one shared client.
- **E202611263b5f9aa5:FR004** — Settings, including which models are used, are loaded from configuration and rejected with a clear message when invalid.
- **E202611263b5f9aa5:FR005** — Every process records its activity and reports failures in one consistent way.
- **E202611263b5f9aa5:FR006** — The system finds its configuration, data, models and logs in the appropriate place on Linux, macOS and Windows.
- **E202611263b5f9aa5:FR007** — The system decides in one consistent way which project a session or query belongs to.
- **E202611263b5f9aa5:FR008** — Modules depend on the model runtime and the store only through interfaces, so each can be replaced.

**s1:**

- **E202611263b5f9aa5:S001:FR001** — A memory entry is either an instruction or a data point and belongs to exactly one project.
- **E202611263b5f9aa5:S001:FR002** — An entry carries its source text, session, time, author, producing models and whether it is active or retired.
- **E202611263b5f9aa5:S001:FR003** — Sources, projects and session checkpoints have one shared definition.
- **E202611263b5f9aa5:S001:FR004** — Failures raised across modules belong to shared, distinguishable kinds with a message a user can act on.

**s2:**

- **E202611263b5f9aa5:S002:FR001** — Configuration, data, models and logs have defined locations on Linux, macOS and Windows.
- **E202611263b5f9aa5:S002:FR002** — Settings, including the embedding and extraction models, are loaded from configuration.
- **E202611263b5f9aa5:S002:FR003** — Invalid settings are reported clearly and are never silently replaced.
- **E202611263b5f9aa5:S002:FR004** — Every process records its activity in one consistent way.

**s3:**

- **E202611263b5f9aa5:S003:FR001** — A session history and a query are assigned to a project by one shared rule.
- **E202611263b5f9aa5:S003:FR002** — A location whose project cannot be determined is reported rather than assigned to another project.

**s4:**

- **E202611263b5f9aa5:S004:FR001** — Requests to the memory server and its answers have one versioned definition covering querying and updating entries.
- **E202611263b5f9aa5:S004:FR002** — One shared client is the way modules call the memory server.
- **E202611263b5f9aa5:S004:FR003** — A server that is unreachable, answers with a failure or speaks an incompatible version is reported as such.

**s5:**

- **E202611263b5f9aa5:S005:FR001** — Embedding text, extracting entries and storing entries are each reached through a shared interface that names no specific product.
- **E202611263b5f9aa5:S005:FR002** — Vectors produced by different embedding models are distinguishable.

## 3. Non-goals

- **Process startup, shutdown, health checks and single-instance locking.** — Process lifecycle is a separate module with its own design.
- **Access token and request origin checks.** — They are designed with the memory server and were left out of the core.
- **Shared test support such as fake models or an in-memory store.** — Left out of the core by the project owner.
- **Implementing model download, model runtime, store, memory server, MCP adapter, history readers, parser, daemon or installer.** — Each is a separate module designed after the core.
- **A general-purpose reasoning engine or controls on destructive agent actions.** — Out of scope for the project; destructive actions belong in the agent harness.

## 4. Assumptions

- `med` The embedding interface and cache that remain may be reused, moved or replaced as part of defining the model runtime interfaces. [[c5]]
- `med` A first set of platforms of macOS on Apple silicon, Linux x64 and ARM64, and Windows x64 guides file location behaviour; only macOS can be verified on the current machine. [[c6]]

## 5. Constraints

| ID | Type | Text | Source |
| :--- | :--- | :--- | :--- |
| `k1` | convention | Separation of concerns and modularity apply to code and package structure; no catch-all utils or common modules, and a violation fails review. | [[c1]] |
| `k2` | invariant | The core is a set of single-responsibility packages that depends on no other module. | [[c2]] |
| `k3` | invariant | Dependencies point one way and domain types depend on nothing else in the project; the existing import-direction test enforces the declared table. | [[c3]] |
| `k4` | contract | The memory server HTTP API is versioned. | [[c4]] |
| `k5` | contract | Entries are instructions or data points, short and normalized, one rule or fact each, scoped to one project, keeping scope, negation and conditions; replaced entries are retired, not erased, and a stored rule is not stored again. | [[c7]] |
| `k6` | stakeholder | agent-pfc is a standalone Python system supporting Linux, macOS and Windows, with no dependency on Ollama. | [[c8]] |
| `k7` | convention | Requirements marked Proposed are not treated as settled in design. | [[c9]] |

## 6. Stories

### 6.1 STORY-3b5f9aa550b6fe9d-s1 — Define memory entries and shared failures

**User value:** `size: M`

Every module author works with one definition of what is remembered and one way of reporting failures.

**Acceptance criteria:**

- **ac1:** Given an entry without a kind or without a project, when a module tries to create it, then it is rejected with a failure naming what is missing. _(operationalizes `k5`)_
- **ac2:** Given an active entry that is replaced by a newer one, when it is retired, then it remains available as a retired entry and is distinguishable from active ones. _(operationalizes `k5`)_
- **ac3:** Given a rule with a negation and a scope, when it is held as an entry, then its text keeps both and its original source text is retained alongside it. _(operationalizes `k5`)_
- **ac4:** Given the shared domain definitions, when the import direction check runs, then they depend on nothing else in the project. _(operationalizes `k2`, `k3`)_

### 6.2 STORY-3b5f9aa550b6fe9d-s2 — Load settings, locate files and record activity

**User value:** `size: M`

An operator can configure agent-pfc and find its files and logs the same way in every process on every supported platform.

**Depends on:** `s1`

**Acceptance criteria:**

- **ac1:** Given any supported platform, when a process asks where its configuration, data, models or logs belong, then it receives the location appropriate to that platform. _(operationalizes `k6`)_
- **ac2:** Given a configuration naming the embedding and extraction models, when settings are loaded, then those choices are available to the modules that need them. _(operationalizes `k2`)_
- **ac3:** Given a configuration with an unknown or malformed setting, when settings are loaded, then loading fails with a message naming the setting and the file. _(operationalizes `k1`)_
- **ac4:** Given two different processes, when each records an event, then both records have the same shape and identify the process that wrote them. _(operationalizes `k1`)_

### 6.3 STORY-3b5f9aa550b6fe9d-s3 — Identify the project of a session or query

**User value:** `size: S`

A coding agent receives only knowledge that belongs to the project it is working on, however that project is reached.

**Depends on:** `s1`

**Acceptance criteria:**

- **ac1:** Given a session and a query made from the same project, when each is identified, then both resolve to the same project. _(operationalizes `k5`)_
- **ac2:** Given two unrelated projects, when each is identified, then they resolve to different projects. _(operationalizes `k5`)_
- **ac3:** Given a location whose project cannot be determined, when it is identified, then the caller is told so and no entry is attributed to a guessed project. _(operationalizes `k5`)_

### 6.4 STORY-3b5f9aa550b6fe9d-s4 — Ask the memory server through one versioned contract

**User value:** `size: L`

Authors of the MCP adapter, daemon and worker call the memory server in one agreed way, and the server author knows exactly what to answer.

**Depends on:** `s1`, `s2`, `s3`

**Acceptance criteria:**

- **ac1:** Given a request that matches the contract, when it is sent through the shared client, then the caller receives an answer of the defined form. _(operationalizes `k4`)_
- **ac2:** Given a client and a server on incompatible contract versions, when the client calls the server, then the caller is told the versions are incompatible and no change is made. _(operationalizes `k4`)_
- **ac3:** Given a memory server that is not running, when a module calls it, then the caller receives a distinct unreachable failure. _(operationalizes `k4`)_
- **ac4:** Given a query that names no project, when it is checked against the contract, then it is rejected. _(operationalizes `k5`)_

### 6.5 STORY-3b5f9aa550b6fe9d-s5 — Depend on models and storage through interfaces

**User value:** `size: M`

Authors of the model runtime and store can build and replace them without changing the modules that use them.

**Depends on:** `s1`

**Extends:** [[c10]]

**Acceptance criteria:**

- **ac1:** Given a module that needs embeddings, extraction or storage, when it is built, then it depends only on the shared interface and not on a specific runtime or store. _(operationalizes `k1`, `k3`)_
- **ac2:** Given vectors from two different embedding models, when they are presented together through the interfaces, then the difference is detectable so they are not mixed. _(operationalizes `k5`)_
- **ac3:** Given the core packages, when the import direction check runs, then none of them depends on a module outside the core. _(operationalizes `k2`, `k3`)_

## 7. References

- **[[c1]]** `doc` `docs/REQUIREMENTS.md` — "Separation of concerns and modularity are the prime directive, in code and in package structure."
- **[[c2]]** `doc` `docs/REQUIREMENTS.md` — "The core is a set of packages with one responsibility each, not a catch-all. It depends on no other module."
- **[[c3]]** `doc` `CLAUDE.md` — "Dependencies point one way. Domain models depend on nothing else in the project; the CLI only wires parts together."
- **[[c4]]** `doc` `docs/REQUIREMENTS.md` — "The HTTP API is versioned."
- **[[c5]]** `code` `src/agent_pfc/embeddings/protocol.py:26`
- **[[c6]]** `doc` `docs/REQUIREMENTS.md` — "First targets: macOS on Apple silicon, Linux x64 and ARM64, Windows x64."
- **[[c7]]** `doc` `docs/REQUIREMENTS.md` — "Memory is project centric: an entry belongs to the project whose history produced it."
- **[[c8]]** `doc` `docs/REQUIREMENTS.md` — "Support Linux, macOS and Windows."
- **[[c9]]** `doc` `CLAUDE.md` — "Do not design against a requirement marked Proposed as if it were settled."
- **[[c10]]** `code` `src/agent_pfc/embeddings/protocol.py:26`
