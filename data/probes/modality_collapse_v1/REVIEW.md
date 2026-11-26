# Wording to review: modality_collapse_v1

The set is **unreviewed**. Only your review changes `reviewed_by_user` in `manifest.json`.

## Words excluded from queries

These fit more than one modality, or copy a stored modality word, and appear in no query:
`optional`, `optionally`, `should`, `recommended`, `essential`, `critical`, `discouraged`, `may not`, `required`, `permitted`, `prohibited`.

## Words that could fit more than one modality

For each query below, confirm the assigned modality, reword it, or drop the word.

### `must` (5 queries): required or strict_required

| Query | Assigned | Text |
| --- | --- | --- |
| schema-migration-prohibited-3 | prohibited | This team has no authority to alter the shared database layout and must leave it alone. |
| code-review-prohibited-2 | prohibited | Authors must never approve their own changes. |
| data-masking-required-1 | required | Support screens must hide card numbers. |
| dependency-pinning-prohibited-3 | prohibited | Our published library must not lock exact versions, since that breaks its users. |
| connection-pooling-prohibited-1 | prohibited | Connections holding user-specific credentials must never go into a shared pool. |

### `may` (2 queries): permitted, or not_required when read as 'need not'

| Query | Assigned | Text |
| --- | --- | --- |
| rate-limiting-permitted-1 | permitted | The reporting endpoint's owner decides whether load warrants a throttle, and may add one. |
| load-testing-strict_required-1 | strict_required | Marketing may have announced the date, but without a stress run there is no launch, full stop. |

### `can` (47 queries): permitted or not_required

| Query | Assigned | Text |
| --- | --- | --- |
| input-validation-permitted-2 | permitted | Module owners can tighten their argument checks as they see fit. |
| input-validation-not_required-1 | not_required | Values produced by our own compiler can be trusted as they are. |
| pagination-strict_required-3 | strict_required | Nobody can sign away the paging of result sets, not even the product owner. |
| pagination-permitted-2 | permitted | The export screen can deliver rows page by page where that reads better. |
| pagination-not_required-2 | not_required | This settings screen can ship with everything on a single page. |
| pagination-not_required-3 | not_required | Page support on the three-row lookup is work you can leave undone. |
| rate-limiting-not_required-3 | not_required | The test environment can leave request volume unlimited without anyone minding. |
| schema-migration-not_required-2 | not_required | The feature can go out while the old tables stay untouched. |
| schema-migration-not_required-3 | not_required | Our scratch database can be rebuilt from nothing, so migrating it serves no purpose. |
| feature-flagging-required-2 | required | A risky change is ready for release once it can be toggled off. |
| feature-flagging-not_required-1 | not_required | A copy fix can go straight to everyone; a toggle adds nothing. |
| deduplication-not_required-2 | not_required | This job can run happily with duplicates left in. |
| deduplication-not_required-3 | not_required | Repeated entries in the debug stream can be left where they are. |
| batching-strict_required-1 | strict_required | Row-at-a-time writes are out for every producer, large or small, and no one can grant a waiver. |
| batching-not_required-3 | not_required | Buffering these calls is effort we can all spare. |
| anonymization-strict_required-1 | strict_required | Data that still points to a person does not leave the vault, and no executive can authorise otherwise. |
| anonymization-permitted-1 | permitted | The demo dataset's keeper can scrub names from it at will. |
| anonymization-permitted-3 | permitted | A team that wants to anonymise its samples can do so. |
| anonymization-not_required-2 | not_required | This report can use the figures just as they are, names and all. |
| anonymization-not_required-3 | not_required | Aggregate totals can be published without any scrubbing step. |
| api-versioning-required-3 | required | An externally visible contract is complete only when callers can address a specific version. |
| api-versioning-strict_required-2 | strict_required | Every external interface carries a version, and nobody can talk their way out of it. |
| api-versioning-permitted-1 | permitted | The internal API's team can introduce a second version at their discretion. |
| api-versioning-not_required-2 | not_required | This purely additive change can be released under the existing number. |
| health-checks-permitted-3 | permitted | Services can also report the state of their dependencies. |
| health-checks-not_required-1 | not_required | A one-off script can do without a status endpoint. |
| backups-not_required-2 | not_required | Scratch tables can live and die unarchived. |
| code-review-permitted-1 | permitted | A prototype's author can ask a colleague for a look whenever it suits. |
| code-review-not_required-1 | not_required | Automated version bumps can merge with no human reading them. |
| load-testing-strict_required-2 | strict_required | Each checkout release is exercised at peak volume; nobody can excuse one from it. |
| load-testing-not_required-1 | not_required | A documentation site can go live untested for peak traffic. |
| data-masking-permitted-2 | permitted | This list can hide part of each email address. |
| data-masking-not_required-1 | not_required | Public product codes can appear in full. |
| data-masking-not_required-3 | not_required | Published figures can stay visible; concealing them gains nothing we ask for. |
| request-signing-permitted-1 | permitted | The metrics client can sign its calls if its maintainer likes. |
| dependency-pinning-permitted-1 | permitted | An example project's author can fix its versions if that appeals. |
| dependency-pinning-not_required-1 | not_required | A throwaway notebook can float on whatever is newest. |
| rollback-strict_required-2 | strict_required | Even a one-line release keeps a proven path back; no approval chain can remove that condition. |
| rollback-permitted-1 | permitted | The person on call can revert the release when the graphs look odd. |
| rollback-not_required-3 | not_required | Rehearsing the undo of a config tweak can be dropped from the checklist. |
| sharding-strict_required-1 | strict_required | The ledger lives on multiple nodes, and no quarterly pressure can postpone that. |
| sharding-permitted-1 | permitted | A growing metrics store can be partitioned at the owner's discretion. |
| sharding-not_required-2 | not_required | The service can stay on a single database server. |
| deprecation-warnings-strict_required-1 | strict_required | Nothing public disappears unannounced, and no maintainer can make that call alone or together. |
| deprecation-warnings-not_required-1 | not_required | An unreleased method can vanish without any sunset notice. |
| connection-pooling-permitted-1 | permitted | This module can keep a pool of HTTP connections where useful. |
| connection-pooling-not_required-1 | not_required | A nightly script can open its connection directly and be done. |

### `need`, `needs` (5 queries): required, or not_required when negated

| Query | Assigned | Text |
| --- | --- | --- |
| rate-limiting-not_required-1 | not_required | Internal health probes need no ceiling on how often they call. |
| schema-migration-required-1 | required | A table change needs its matching migration script in the same pull request. |
| api-versioning-required-2 | required | This public endpoint needs its version number in place for partners. |
| code-review-not_required-3 | not_required | A typo fix in the notes need not wait for anyone's approval. |
| request-signing-required-2 | required | Our outbound webhooks are signed cryptographically, and yours need to be too. |

### `never` (7 queries): strict_required or prohibited

| Query | Assigned | Text |
| --- | --- | --- |
| batching-prohibited-2 | prohibited | Never combine two payment authorisations into a single call. |
| anonymization-strict_required-3 | strict_required | A looming deadline is never grounds to hand over records with people still recognisable in them. |
| api-versioning-strict_required-1 | strict_required | A published contract is never altered in place, however small the tweak or loud the partner. |
| code-review-prohibited-2 | prohibited | Authors must never approve their own changes. |
| rollback-prohibited-1 | prohibited | Once data has been written, never revert the database upgrade. |
| rollback-prohibited-3 | prohibited | Payment releases are never undone automatically. |
| connection-pooling-prohibited-1 | prohibited | Connections holding user-specific credentials must never go into a shared pool. |

### `without exception`, `exempt`, `exemption`, `excused` (2 queries): strict_required; check it is not read as prohibited

| Query | Assigned | Text |
| --- | --- | --- |
| batching-not_required-2 | not_required | This worker is excused from grouping its writes. |
| sharding-strict_required-3 | strict_required | Every large table is partitioned; architects cannot grant themselves an exemption. |

### `fine` (6 queries): permitted or not_required

| Query | Assigned | Text |
| --- | --- | --- |
| schema-migration-permitted-2 | permitted | Including a migration in a patch version is fine by us. |
| feature-flagging-not_required-2 | not_required | This small bug repair ships fine without a switch. |
| api-versioning-not_required-3 | not_required | Private endpoints get along fine unnumbered. |
| dependency-pinning-not_required-3 | not_required | Fixed versions for linters are more trouble than they are worth, and leaving them floating is fine. |
| rollback-not_required-2 | not_required | This disposable experiment ships fine without a prepared way back. |
| sharding-not_required-3 | not_required | The lookup tables are fine undistributed. |

### `free to`, `at liberty` (1 queries): permitted or not_required

| Query | Assigned | Text |
| --- | --- | --- |
| deprecation-warnings-not_required-2 | not_required | Private helpers are free to disappear quietly. |

### `go ahead`, `welcome`, `open to you` (5 queries): permitted

| Query | Assigned | Text |
| --- | --- | --- |
| batching-permitted-3 | permitted | Go ahead and buffer events to send them together. |
| backups-permitted-3 | permitted | Go ahead and keep copies of your sandbox. |
| code-review-permitted-2 | permitted | Pulling in an extra reviewer is welcome. |
| request-signing-permitted-2 | permitted | A signature header here is a welcome extra. |
| connection-pooling-permitted-3 | permitted | Go ahead and reuse connections to the cache. |

### `against policy`, `against the rules`, `off limits`, `off the table`, `out of bounds` (1 queries): prohibited, or strict_required when it forbids skipping

| Query | Assigned | Text |
| --- | --- | --- |
| schema-migration-strict_required-2 | strict_required | Hand-editing a table is off limits to everyone, so each structural change travels as a migration, always. |

### `skip`, `skips` (1 queries): not_required or permitted

| Query | Assigned | Text |
| --- | --- | --- |
| feature-flagging-not_required-3 | not_required | Edits to the developer docs skip the flag process entirely. |

### `acceptable` (3 queries): permitted; negated it reads as strict_required or prohibited

| Query | Assigned | Text |
| --- | --- | --- |
| pagination-permitted-3 | permitted | Cursor-based paging on this route is an acceptable choice. |
| anonymization-permitted-2 | permitted | Removing identities from internal reports is an acceptable preference. |
| rollback-permitted-3 | permitted | Returning to the earlier build is acceptable. |

## How much the wording alone gives away

The first draft reused sentence patterns, so it was rewritten. Counts are queries
per modality (of 60) containing a cue phrase of the first draft:

| Modality | Cues in this draft | Queries with one: first draft | Now |
| --- | --- | --- | --- |
| required | obliged 0; has/have to 1; need(s) 3 | 58 | 4 |
| strict_required | non-negotiable 0; never 2; exception/exempt 1 | 51 | 3 |
| permitted | may 1; allowed 0; feel free 0 | 54 | 1 |
| not_required | no need / does not need 0; without 11; obligation/nobody 1 | 54 | 12 |
| prohibited | do not 4; forbidden 0; banned 0 | 57 | 4 |

Word-only baseline: a naive Bayes classifier over single words, trained on 19
concepts and tested on the one held out. It uses no embedding. Chance is 0.20.

| Modality | First draft | Now |
| --- | --- | --- |
| overall | 0.92 | 0.63 |
| not_required | 0.90 | 0.60 |
| permitted | 0.93 | 0.53 |
| prohibited | 0.90 | 0.42 |
| required | 0.90 | 0.67 |
| strict_required | 0.97 | 0.92 |

What remains is partly unavoidable: forbidding or permitting something uses
characteristic words. Read a model's score against this baseline.

## Questions for you

1. Is the line between `required` and `strict_required` right? Strict queries stress that nothing or nobody is excused.
2. Many strict queries say that nobody can waive or bypass the rule. Does any of them read as a prohibition of something else instead?
3. Several `prohibited` queries ban a thing in one place only ('in the billing core'). Is that a prohibition of the concept for you?
4. Several `not_required` queries state that something works without the practice ('can go out with no stress run'). Do they read as 'not required', or as permission to omit it?
