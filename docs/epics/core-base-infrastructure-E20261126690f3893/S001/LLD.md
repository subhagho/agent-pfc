<!-- insrc:artifact LLD-690f38931e7d3b57-s1 -->

# LLD: STORY-690f38931e7d3b57-s1 — Define memory entries and shared failures

## Summary

**Epic:** `core-base-infrastructure`
**HLD base run:** `wf-1795756288787-nvbycn`
**HLD effective hash:** `689c403bed6f...`

This story creates the definitions every module shares: memory entries and their tagged names, source references, projects, session checkpoints and one failure type, with their checks written once. A definition checks itself when created, and retiring an entry, which records the time, is the only change it allows. The import test learns nested packages and rejects cycles between modules.

## Contents

1. [HLD context](#1-hld-context)
2. [Contract details](#2-contract-details)
3. [Data model changes](#3-data-model-changes)
4. [Interaction with shared contracts](#4-interaction-with-shared-contracts)
5. [Error paths](#5-error-paths)
6. [Test strategy](#6-test-strategy)
7. [Alternatives considered](#7-alternatives-considered)
8. [References](#8-references)

## 1. HLD context

> See **HLD-690f38931e7d3b57** § 2. Framework summary

**Rollout phase:** Phase A: definitions and layout
**Owns:** `sc1` (Memory definitions, checkpoints and failures), `sc2` (Core layout and import table), `sc10` (Definition checks)

**Adjacent scope (owned by other stories — do NOT implement here):**
- `s2`: Per-platform location rules, the configuration file format and its validation, including the compaction defaults, and how activity is written and rotated. Session archiving itself belongs to a later module. — owns `sc3`, `sc4`, `sc5`
- `s3`: The rule that identifies a project from a location and how it behaves across worktrees and machines. — owns `sc6`
- `s4`: Wire encoding, endpoint layout, version compatibility rule, time limits, the HTTP library and how failures are mapped to shared kinds. — owns `sc7`
- `s5`: The move of the embedding protocol into core/common, of its checks into core/utils and of its cache into core/cache/embedding, and the exact method signatures of the interfaces. The local model's instructions belong to the parser design and the calling agent's steering to the MCP adapter design. The loose matching technique, the ranking, the meaning of a score, how history is laid out and how compaction works are left to the store design, and starting compaction on schedule to the memory server design. — owns `sc8`, `sc9`

## 2. Contract details

**Surface level:** internal-shared

### 2.1 `FailureKind`

```typescript
class FailureKind(StrEnum): INVALID_INPUT, INVALID_CONFIGURATION, UNKNOWN_PROJECT, SERVER_UNREACHABLE, INCOMPATIBLE_VERSION, REQUEST_FAILED, BACKEND_FAILED  # values are the lower-case names
```

**Returns:** `FailureKind` — One of the seven failure kinds.

**Postconditions:**
- Each value equals the string in the approved contract.

### 2.2 `Failure`

```typescript
class Failure(Exception): __init__(self, kind: FailureKind, message: str); kind: FailureKind; message: str
```

**Parameters:**
- `kind: FailureKind` — Lets a caller tell failures apart.
- `message: str` — What went wrong, in words a user can act on.

**Returns:** `Failure` — The one exception modules raise for shared failures.

**Errors:**
- `TypeError` when kind is not a FailureKind; a programming error.
- `ValueError` when message is blank; a programming error.

**Postconditions:**
- str(failure) equals the message.

### 2.3 `Validation`

```typescript
require_text(field: str, value: object) -> str; require_position(field: str, value: object) -> int; require_offset_time(field: str, value: object) -> str
```

**Parameters:**
- `field: str` — Name used in the failure message.
- `value: object` — The value to check.

**Returns:** `str | int` — The accepted value, unchanged.

**Errors:**
- `Failure(invalid_input)` when require_text: not a string, or blank. require_position: not an integer, a boolean, or negative. require_offset_time: not an ISO 8601 string with a UTC offset.

**Postconditions:**
- No value is trimmed or converted.

### 2.4 `EntryKind`

```typescript
class EntryKind(StrEnum): INSTRUCTION = 'instruction', DATA_POINT = 'data_point'
```

**Returns:** `EntryKind` — Whether an entry is an instruction or a data point.

### 2.5 `EntryStatus`

```typescript
class EntryStatus(StrEnum): ACTIVE = 'active', RETIRED = 'retired'
```

**Returns:** `EntryStatus` — Whether an entry is in force.

### 2.6 `ProjectId`

```typescript
@dataclass(frozen=True) class ProjectId: value: str
```

**Parameters:**
- `value: str` — Identifier of the project; how it is derived belongs to s3.

**Returns:** `ProjectId` — A project identity usable as a dictionary key.

**Errors:**
- `Failure(invalid_input)` when value fails require_text.

**Postconditions:**
- Equal values compare equal.

### 2.7 `Source`

```typescript
@dataclass(frozen=True, kw_only=True) class Source: agent: str; session_id: str; file: str; position: int; spoken_at: str
```

**Parameters:**
- `file: str` — The session history file.
- `position: int` — Where the message is in the file; its unit is set by the history reader.
- `spoken_at: str` — When the message was written, as ISO 8601 with a UTC offset.

**Returns:** `Source` — A reference to the message an entry came from, without its wording.

**Errors:**
- `Failure(invalid_input)` when A string fails require_text, position fails require_position or spoken_at fails require_offset_time.

### 2.8 `Provenance`

```typescript
@dataclass(frozen=True, kw_only=True) class Provenance: extraction_model: str; embedding_model: str
```

**Returns:** `Provenance` — The models that produced an entry.

**Errors:**
- `Failure(invalid_input)` when Either name fails require_text.

### 2.9 `NamedEntity`

```typescript
@dataclass(frozen=True, kw_only=True) class NamedEntity: text: str; start: int; end: int
```

**Parameters:**
- `start: int` — Index of the first character, counted in Python string positions.
- `end: int` — Index after the last character.

**Returns:** `NamedEntity` — A tagged official name within an entry's text.

**Errors:**
- `Failure(invalid_input)` when text is blank, a position is invalid, or end minus start differs from the length of text.

### 2.10 `Entry`

```typescript
@dataclass(frozen=True, kw_only=True) class Entry: id: str; project: ProjectId; kind: EntryKind; text: str; entities: tuple[NamedEntity, ...]; sources: tuple[Source, ...]; provenance: Provenance; status: EntryStatus; retired_at: str | None = None; replaced_by: str | None = None; retire(self, retired_at: str, replaced_by: str | None = None) -> None  # compares by value, not hashable
```

**Parameters:**
- `text: str` — Normalized rule or fact, at most 500 characters counted as Python string positions.
- `entities: tuple[NamedEntity, ...]` — Tagged names; may be empty.
- `sources: tuple[Source, ...]` — Where the entry came from; at least one.
- `retired_at: str | None` _(optional)_ — When the entry was retired, as ISO 8601 with a UTC offset. Required when retired and absent when active; the argument of retire is required.
- `replaced_by: str | None` _(optional)_ — Identifier of the entry that replaced a retired one.

**Returns:** `Entry` — A checked entry that only retire can change.

**Errors:**
- `Failure(invalid_input)` when On creation: kind or project is empty; a value has the wrong type; id or text is blank; text is longer than 500 characters; entities or sources is not a tuple of the right type; sources is empty; an entity differs from the text at its positions; a retired entry has no retired_at or one that fails require_offset_time; an active entry has retired_at or replaced_by; replaced_by is blank or equals id. The message names the field.
- `Failure(invalid_input)` when On retire: the entry is already retired, retired_at fails require_offset_time, or replaced_by is blank or equals id. Nothing changes.
- `TypeError` when A required argument is left out; a programming error.

**Postconditions:**
- After retire, the same object has status retired, the given retirement time and the given replacement, and every other field is unchanged.
- A retired entry may be created directly, with its retirement time and with or without a replacement, so that stored entries can be read back.
- The definitions do not prevent an active copy of a retired entry; the store refuses it.

### 2.11 `Checkpoint`

```typescript
@dataclass(frozen=True, kw_only=True) class Checkpoint: agent: str; session_id: str; file: str; position: int; last_message_id: str; last_message_at: str
```

**Parameters:**
- `position: int` — Where to proceed from in the file.

**Returns:** `Checkpoint` — How far one session has been processed.

**Errors:**
- `Failure(invalid_input)` when A string fails require_text, position fails require_position or last_message_at fails require_offset_time.

**Postconditions:**
- No comparison or update rule is defined here; that belongs to the store and server.

### 2.12 `ImportTable`

```typescript
ALLOWED: dict[str, frozenset[str]]  # dotted package path below agent_pfc -> packages or modules it may import; NAMESPACES: frozenset[str] = {'core', 'core.cache'}
```

**Returns:** `list[str]` — Violations; empty when every import follows the table and no modules form a cycle.

**Preconditions:**
- Imports are read statically; dynamic importing stays forbidden.

**Postconditions:**
- A module belongs to the longest table key that prefixes its path.
- A module with no owning key is a violation unless it is the __init__ of a namespace.
- A namespace __init__ holds only a docstring.
- Every key starting 'core.' may import only keys starting 'core.'.
- A cycle among project module imports is a violation naming the modules.

## 3. Data model changes

### 3.1 `agent_pfc.core.common.failures` — new

Module holding FailureKind and Failure. Imports nothing from the project, so the checks can import it without a cycle.


### 3.2 `agent_pfc.core.utils.validation` — new

Module holding the three checks. Imports only the failures module.


### 3.3 `agent_pfc.core.common.entries` — new

Module holding EntryKind, EntryStatus, ProjectId, Source, Provenance, NamedEntity and Entry, with the 500-character limit. Imports the failures and validation modules. An entry owns its entities and sources.


### 3.4 `agent_pfc.core.common.checkpoints` — new

Module holding Checkpoint. Imports the validation module.


### 3.5 `agent_pfc.core, core.common and core.utils packages` — new

Each __init__ holds only a docstring, so importing one module loads no other.


### 3.6 `Import table` — field-modify

Keyed by dotted package paths, lists the approved core packages plus the existing embeddings package, which keeps its empty entry until s5 moves it, and gains the cycle check.

**Call sites:**
- `tests/test_architecture.py:17-90`

### 3.7 `agent_pfc package docstring` — field-modify

Replaced with the current project description, since it describes the removed design.

**Call sites:**
- `src/agent_pfc/__init__.py`

## 4. Interaction with shared contracts

| Contract | Role | How |
| :--- | :--- | :--- |
| `sc1` | implements | The three common modules define every type in the contract with snake_case field names and tuples for lists. The existing EmbeddingBackendError is not touched; s5 moves it onto the backend_failed kind. |
| `sc10` | implements | The validation module defines the three checks, and the definitions of this story use them. |
| `sc2` | implements | The import test holds the approved table and namespaces, checks nested packages and rejects module cycles. Packages of later stories are listed now and created by those stories. |

## 5. Error paths

**Error cases**

- **An entry is created with an empty kind or project.** (recoverable)
  - Detection: The entry's creation check tests both fields for no value before any other check.
  - Response: Failure with invalid_input naming the field.
  - User impact: The caller learns which value is missing; nothing is created.
- **A value has the wrong type, such as a string for kind, a list for sources or a boolean for a position.** (recoverable)
  - Detection: The shared checks and the creation checks test each field's type, treating a boolean as not an integer.
  - Response: Failure with invalid_input naming the field.
  - User impact: The caller learns which value is wrong.
- **Entry text is longer than 500 characters.** (recoverable)
  - Detection: The entry measures the length of text on creation.
  - Response: Failure with invalid_input naming text.
  - User impact: The parser must shorten or split the entry, or it is not stored.
- **A tagged name does not match the entry text.** (recoverable)
  - Detection: The entry compares each entity's text with its own text between start and end, including an end beyond the text's length.
  - Response: Failure with invalid_input naming entities.
  - User impact: A wrongly positioned tag cannot reach the index.
- **A time is not ISO 8601 or has no UTC offset.** (recoverable)
  - Detection: The time check parses the value with the standard library and tests that the result has an offset.
  - Response: Failure with invalid_input naming the field.
  - User impact: Times from different machines stay comparable.
- **An entry's status and retirement fields disagree: retired without a retirement time, or active with a retirement time or a replacement.** (recoverable)
  - Detection: The creation check compares status with retired_at and replaced_by.
  - Response: Failure with invalid_input naming retired_at or replaced_by.
  - User impact: A retired entry always carries the time that purging needs.
- **A retired entry is retired again, or retire is given an invalid time, the entry's own identifier or a blank replacement.** (recoverable)
  - Detection: retire reads the status and checks both arguments before changing anything.
  - Response: Failure with invalid_input naming status, retired_at or replaced_by; the entry is unchanged.
  - User impact: A recorded retirement cannot be silently overwritten.
- **Code assigns a field of an entry directly.** (terminal)
  - Detection: The frozen dataclass rejects the assignment.
  - Response: The language's frozen-instance error.
  - User impact: The mistake shows up in tests of the assigning module.
- **A failure is created with a blank message or an unknown kind.** (terminal)
  - Detection: The failure checks its arguments itself, without the shared checks.
  - Response: ValueError or TypeError, since the mistake is in the code raising it.
  - User impact: The mistake shows up in tests of the raising module.
- **A package imports something its table entry does not allow, is not in the table, or modules import each other in a loop.** (recoverable)
  - Detection: The import test reads every source file's imports statically and searches the module import graph for a cycle.
  - Response: The test fails naming the modules.
  - User impact: The developer fixes the dependency before it is merged.

**Edge cases**

| Input | Expected |
| :--- | :--- |
| Entry text of exactly 500 characters. | Accepted. |
| An entry with no named entities. | Accepted with an empty tuple. |
| Entry text containing non-Latin characters or emoji before a tagged name. | Positions and length count Python string positions, so the tag matches. |
| The same name tagged twice at two places in one entry. | Both tags are accepted. |
| An entry read back already retired, with a retirement time and no replacement. | Accepted. |
| A retirement time earlier than the source's time. | Accepted; the definitions do not compare times from different clocks. |
| An active copy of a retired entry made by code. | Created; refusing it is the store's duty. |
| A rule with leading or trailing spaces, a negation and a condition. | Text is kept exactly as given. |
| A source or checkpoint at position zero. | Accepted. |
| A time ending in Z. | Accepted as an offset of zero. |
| Two entries with equal fields, then one is retired. | They compare equal before and unequal after. |

## 6. Test strategy

**Test framework:** `pytest`

**Test levels**

- **unit** — Each definition and check accepts valid values and rejects invalid ones with the right failure.
  - Subjects: `Failure and FailureKind`, `The validation checks`, `Entry creation and retire, including the retirement time`, `NamedEntity, Source, Provenance and ProjectId`, `Checkpoint`
- **contract** — The definitions match the approved contract and the packages follow the import table.
  - Subjects: `Failure kind, entry kind and entry status values`, `Field names of Source and Entry`, `ImportTable over the real source tree`, `ImportTable against forbidden and accepted examples for nested packages and cycles`

**Acceptance mapping**

| Criterion | Proving tests |
| :--- | :--- |
| `ac1` | `tests/test_entries.py: an entry with an empty kind raises an invalid_input failure naming kind`, `tests/test_entries.py: an entry with an empty project raises an invalid_input failure naming project` |
| `ac2` | `tests/test_entries.py: retire changes the same entry and records the time, with and without a replacement`, `tests/test_entries.py: retiring a retired entry fails and leaves it unchanged`, `tests/test_entries.py: retire with an invalid time fails and leaves the entry active`, `tests/test_entries.py: a retired entry needs a retirement time and an active entry has none`, `tests/test_entries.py: assigning a field of an entry directly is rejected` |
| `ac3` | `tests/test_entries.py: entry text with a negation, a scope and surrounding spaces is kept exactly`, `tests/test_entries.py: a source has only agent, session, file, position and time` |
| `ac4` | `tests/test_architecture.py: the real source tree follows the table and has no module cycle`, `tests/test_architecture.py: examples reject core.common importing outside common and utils, an unlisted nested package, a namespace with code, a core package importing outside core and a module cycle` |
| `ac5` | `tests/test_entries.py: text of 501 characters raises an invalid_input failure naming text and text of 500 is accepted` |
| `ac6` | `tests/test_entries.py: an entity that differs from the text at its positions raises an invalid_input failure naming entities` |

## 7. Alternatives considered

### 7.1 a1: Frozen dataclasses with a retire method — **CHOSEN**

Standard-library frozen dataclasses that check themselves with the shared checks; only retire changes an entry.

Each definition is a frozen dataclass that runs the shared checks when created. Entry has one method, retire, which takes the retirement time and an optional replacement, checks them, and then sets status, retired_at and replaced_by on the same object, bypassing the freeze for those three fields only. Entries compare by value and are not hashable, since they can change.

### 7.2 a2: Private fields with read-only properties

Entry as an ordinary class with private fields, read-only properties and a retire method; other definitions as frozen dataclasses.

Entry stores private attributes and exposes each through a property, with retire changing the private status, retirement time and replacement. Equality and representation are written by hand.

**Rejected because:** More code for no stronger guarantee.

### 7.3 a3: Mutable dataclass

Entry as an ordinary mutable dataclass with a retire method.

Entry is a plain dataclass checked on creation, with retire setting status, retirement time and replacement. Nothing prevents other assignments.

**Rejected because:** Cannot hold the retirement rule.

## 8. References

- **[[c1]]** `analyze-bundle` `s1` — "One source package with a single subpackage, embeddings; the only project imports are inside it or from tests."
- **[[c2]]** `code` `tests/test_architecture.py:17-90`
- **[[c3]]** `code` `src/agent_pfc/embeddings/protocol.py:14-32`
- **[[c4]]** `code` `src/agent_pfc/__init__.py`
- **[[c5]]** `doc` `docs/REQUIREMENTS.md`
- **[[c6]]** `convention` `CLAUDE.md:18-28`
