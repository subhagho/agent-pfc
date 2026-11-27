<!-- insrc:artifact PLAN-690f38931e7d3b57-s1 -->

# Plan: STORY-690f38931e7d3b57-s1

## Summary

**Epic:** `core-base-infrastructure`
**LLD run:** `wf-1795756585971-7m6t9b`
**LLD effective hash:** `689c403bed6f...`

The build first teaches the import test about nested packages and cycles, so that new core code is checked from its first file. It then adds the failure type and checks, followed by the entry definitions and the checkpoint. Everything is new code except the import test and one docstring.

## Contents

1. [Tasks](#1-tasks)
2. [Test-strategy coverage](#2-test-strategy-coverage)
3. [References](#3-references)

## 1. Tasks

| # | Task | Size | Status | Depends on | Tests | Derived from |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | **`t1`** Extend the import test to nested packages and cycles | M | — | — | unit: tests/test_architecture.py: the real source tree follows the table and has no module cycle; unit: tests/test_architecture.py: examples reject core.common importing outside common and utils, an unlisted nested package, a namespace with code, a core package importing outside core and a module cycle; unit: tests/test_architecture.py: allowed examples for nested packages are accepted | [[c1]] [[c2]] [[c3]] [[c4]] |
| 2 | **`t2`** Add the shared failure type and the definition checks | S | — | `t1` | unit: tests/test_failures.py: failure kind values equal the contract and a failure reads as its message; unit: tests/test_failures.py: a blank message or unknown kind is a programming error; unit: tests/test_validation.py: each check returns an accepted value unchanged; unit: tests/test_validation.py: each check rejects an invalid value with an invalid_input failure naming the field | [[c1]] [[c2]] [[c3]] [[c5]] |
| 3 | **`t3`** Add the entry definitions | M | — | `t2` | unit: tests/test_entries.py: an entry with an empty kind raises an invalid_input failure naming kind; unit: tests/test_entries.py: an entry with an empty project raises an invalid_input failure naming project; unit: tests/test_entries.py: retire changes the same entry and records the time, with and without a replacement; unit: tests/test_entries.py: retiring a retired entry fails and leaves it unchanged; unit: tests/test_entries.py: retire with an invalid time fails and leaves the entry active; unit: tests/test_entries.py: a retired entry needs a retirement time and an active entry has none; unit: tests/test_entries.py: assigning a field of an entry directly is rejected; unit: tests/test_entries.py: entry text with a negation, a scope and surrounding spaces is kept exactly; unit: tests/test_entries.py: a source has only agent, session, file, position and time; unit: tests/test_entries.py: text of 501 characters raises an invalid_input failure naming text and text of 500 is accepted; unit: tests/test_entries.py: an entity that differs from the text at its positions raises an invalid_input failure naming entities; unit: tests/test_entries.py: tags after non-Latin text or emoji and repeated names are accepted; unit: tests/test_entries.py: wrong types and invalid source, provenance and project values are rejected naming the field; unit: tests/test_entries.py: entry kind and status values equal the contract; unit: tests/test_entries.py: entries compare by value and are not hashable | [[c1]] [[c2]] [[c3]] [[c4]] |
| 4 | **`t4`** Add checkpoints and replace the stale package description | S | — | `t2` | unit: tests/test_checkpoints.py: a checkpoint accepts position zero; unit: tests/test_checkpoints.py: an invalid checkpoint value is rejected naming the field; unit: tests/test_architecture.py: the real source tree follows the table and has no module cycle | [[c1]] [[c2]] [[c4]] |

### 1.1 TASK-690f38931e7d3b57-s1-t1 — Extend the import test to nested packages and cycles

In tests/test_architecture.py, key the allowed table by dotted package paths with the approved core entries and the existing embeddings entry, add the namespace rule, the core boundary rule and the module cycle check, and rewrite the example tables to match.

**Acceptance checks:**
- A module belongs to the longest table key that prefixes its path
- A module with no owning key is rejected unless it is a namespace __init__, and a namespace __init__ with code is rejected
- A package under core importing outside core is rejected
- A module import cycle is rejected and the modules are named
- Dynamic importing is still rejected and the whole suite passes

### 1.2 TASK-690f38931e7d3b57-s1-t2 — Add the shared failure type and the definition checks

Create the core, core.common and core.utils packages with docstring-only __init__ files, the failures module and the validation module, with their tests.

**Acceptance checks:**
- The seven failure kind values equal the contract strings and str of a failure is its message
- A blank message or unknown kind raises ValueError or TypeError
- Each check returns the value unchanged or raises an invalid_input Failure naming the field
- A wrong type, a boolean or negative position, and a time without an offset are rejected; a time ending in Z is accepted
- failures imports nothing from the project and validation imports only failures

### 1.3 TASK-690f38931e7d3b57-s1-t3 — Add the entry definitions

Add the entries module with EntryKind, EntryStatus, ProjectId, Source, Provenance, NamedEntity and Entry, its 500-character limit and retire, with the tests for the acceptance criteria.

**Acceptance checks:**
- Entry kind and status values equal the contract strings
- Empty kind or project, wrong types, empty sources and mismatched tags are rejected naming the field
- Text of 501 characters is rejected and 500 is accepted; text is kept exactly
- Tags after non-Latin text or emoji and a name tagged twice are accepted
- retire changes the same entry once and records the time, with or without a replacement; a failed retire changes nothing
- A retired entry needs a retirement time and may be created directly; an active entry has no time or replacement
- Direct field assignment is rejected; entries compare by value before and after retirement and are not hashable
- A source has only agent, session, file, position and time

### 1.4 TASK-690f38931e7d3b57-s1-t4 — Add checkpoints and replace the stale package description

Add the checkpoints module with its tests and replace the root package docstring with the current project description.

**Acceptance checks:**
- A blank string, an invalid position or a time without an offset in a checkpoint is rejected naming the field
- Position zero is accepted
- The root docstring describes the current project
- The whole suite passes with the real source tree following the table and having no cycle

## 2. Test-strategy coverage

| LLD strategy item | Covered by |
| :--- | :--- |
| Failure and FailureKind | `t2` |
| The validation checks | `t2` |
| Entry creation and retire, including the retirement time | `t3` |
| NamedEntity, Source, Provenance and ProjectId | `t3` |
| Checkpoint | `t4` |
| Failure kind, entry kind and entry status values | `t2`, `t3` |
| Field names of Source and Entry | `t3` |
| ImportTable over the real source tree | `t1`, `t4` |
| ImportTable against forbidden and accepted examples for nested packages and cycles | `t1` |

## 3. References

- **[[c1]]** `prior-artifact` `LLD s1 contractDetails`
- **[[c2]]** `prior-artifact` `LLD s1 dataModelChanges`
- **[[c3]]** `prior-artifact` `LLD s1 errorPaths`
- **[[c4]]** `prior-artifact` `LLD s1 testStrategy`
- **[[c5]]** `prior-artifact` `LLD s1 interactionWithShared`
