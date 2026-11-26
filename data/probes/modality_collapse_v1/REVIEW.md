# Wording to review: modality_collapse_v1

The set is **unreviewed**. Only your review changes `reviewed_by_user` in `manifest.json`.

## Words excluded from queries

These fit more than one modality, or copy a stored modality word, and appear in no query:
`optional`, `optionally`, `should`, `recommended`, `essential`, `critical`, `discouraged`, `may not`, `required`, `permitted`, `prohibited`.

## Words that could fit more than one modality

For each query below, confirm the assigned modality, reword it, or drop the word.

### `may` (22 queries): permitted, or not_required when read as 'need not'

| Query | Assigned | Text |
| --- | --- | --- |
| input-validation-strict_required-2 | strict_required | Under no circumstances may unchecked data enter the system, even for internal callers. |
| input-validation-permitted-1 | permitted | You may add extra checks on incoming fields if you find them useful. |
| pagination-permitted-3 | permitted | You may offer cursor paging on this endpoint. |
| rate-limiting-permitted-1 | permitted | You may throttle the reporting endpoint if load becomes a problem. |
| schema-migration-permitted-2 | permitted | A migration may be included in the patch version. |
| feature-flagging-permitted-2 | permitted | You may use flags to stage this change. |
| deduplication-permitted-1 | permitted | You may collapse identical log lines. |
| batching-permitted-1 | permitted | You may group the notifications into one request. |
| anonymization-permitted-1 | permitted | You may anonymise the demo dataset if you like. |
| api-versioning-strict_required-3 | strict_required | No team may be exempted from putting versions on external interfaces. |
| api-versioning-permitted-1 | permitted | You may introduce a second version of the internal API. |
| health-checks-permitted-1 | permitted | You may add a deeper readiness probe. |
| backups-permitted-1 | permitted | You may take an extra snapshot before the upgrade. |
| code-review-permitted-1 | permitted | You may ask a colleague to look over your prototype. |
| load-testing-permitted-1 | permitted | You may stress the staging cluster this week. |
| data-masking-permitted-1 | permitted | You may blur names in the demo screenshots. |
| request-signing-permitted-1 | permitted | You may sign requests to the internal metrics service. |
| dependency-pinning-permitted-1 | permitted | You may fix the versions in your example project. |
| rollback-permitted-1 | permitted | You may revert the release if the graphs look odd. |
| sharding-permitted-1 | permitted | You may partition the metrics store if it grows. |
| deprecation-warnings-permitted-1 | permitted | You may log a notice when the old flag is used. |
| connection-pooling-permitted-1 | permitted | You may keep a pool of HTTP connections here. |

### `can` (25 queries): permitted or not_required

| Query | Assigned | Text |
| --- | --- | --- |
| input-validation-not_required-2 | not_required | This internal script can ship without checking its arguments. |
| pagination-not_required-2 | not_required | This endpoint can return everything at once without page support. |
| rate-limiting-strict_required-1 | strict_required | The login route is throttled without exception; nobody can switch it off. |
| rate-limiting-not_required-2 | not_required | The admin tool can go live without throttling. |
| schema-migration-not_required-2 | not_required | The feature can ship while the old table layout stays untouched. |
| feature-flagging-strict_required-3 | strict_required | No release manager can waive the feature flag on payment changes. |
| feature-flagging-not_required-2 | not_required | This bug fix can go out without a feature switch. |
| deduplication-not_required-2 | not_required | This job can run without removing duplicates. |
| batching-not_required-2 | not_required | This worker can send records individually; bulk mode is not something we ask for. |
| anonymization-strict_required-1 | strict_required | Identifiable data never leaves the vault, and no executive can override that. |
| anonymization-not_required-2 | not_required | This report can use the data as it is, without anonymising it. |
| api-versioning-not_required-2 | not_required | This additive change can be released without a new API version. |
| health-checks-not_required-2 | not_required | This job can run without any liveness probe. |
| backups-not_required-1 | not_required | The cache can be rebuilt, so there is no need to back it up. |
| backups-not_required-2 | not_required | Scratch tables can live without any backup. |
| code-review-not_required-2 | not_required | Your personal experiment branch can be merged without anyone reading it. |
| load-testing-not_required-2 | not_required | This small internal tool can launch without being tested under traffic. |
| data-masking-not_required-2 | not_required | This table can show the values in full, masking is unnecessary. |
| request-signing-strict_required-1 | strict_required | An unsigned payment call is never accepted, and nobody can disable the check. |
| dependency-pinning-not_required-2 | not_required | This sample can depend on the latest releases without a lock file. |
| rollback-not_required-2 | not_required | This experiment can be deployed without preparing a way back. |
| sharding-not_required-2 | not_required | The service can run on a single node without splitting its data. |
| deprecation-warnings-strict_required-1 | strict_required | Nothing is removed without prior notice to callers, and no maintainer can waive that. |
| deprecation-warnings-not_required-1 | not_required | An unreleased method can be removed without any sunset notice. |
| connection-pooling-not_required-2 | not_required | This tool can open a single connection and skip pooling. |

### `need`, `needs` (51 queries): required, or not_required when negated

| Query | Assigned | Text |
| --- | --- | --- |
| input-validation-not_required-1 | not_required | There is no need to validate values that our own compiler generated. |
| pagination-required-2 | required | Any query that returns many rows needs to be paginated. |
| pagination-not_required-1 | not_required | The country list is tiny, so there is no need to page it. |
| rate-limiting-required-3 | required | A new external endpoint needs a request quota before launch. |
| rate-limiting-not_required-1 | not_required | Internal health probes do not need a request cap. |
| schema-migration-required-2 | required | Releases that alter columns need an accompanying migration. |
| schema-migration-not_required-1 | not_required | Adding this index needs no migration step. |
| feature-flagging-required-2 | required | Risky changes need a feature toggle before release. |
| feature-flagging-not_required-1 | not_required | A copy fix does not need a toggle. |
| feature-flagging-not_required-3 | not_required | There is no need to flag changes to the developer docs. |
| deduplication-required-2 | required | Imported contacts need duplicate removal before saving. |
| deduplication-not_required-1 | not_required | The source already guarantees unique records, so there is no need to filter repeats. |
| batching-required-2 | required | The sync job needs to send records in bulk. |
| batching-not_required-1 | not_required | Low-volume jobs do not need to group their writes. |
| batching-not_required-3 | not_required | There is no need to buffer these calls. |
| anonymization-required-3 | required | A research export needs identities removed first. |
| anonymization-not_required-1 | not_required | Synthetic records do not need identities removed. |
| api-versioning-required-2 | required | Public endpoints need a version number. |
| api-versioning-not_required-1 | not_required | An internal function call does not need a version scheme. |
| api-versioning-not_required-3 | not_required | There is no need to number the private endpoints. |
| health-checks-required-2 | required | The load balancer needs a readiness probe from every instance. |
| health-checks-not_required-1 | not_required | A one-off script does not need a status endpoint. |
| health-checks-not_required-3 | not_required | There is no need for readiness reporting on the local mock. |
| backups-required-2 | required | Each production store needs a backup plan. |
| backups-not_required-1 | not_required | The cache can be rebuilt, so there is no need to back it up. |
| code-review-required-2 | required | Each pull request needs a second pair of eyes. |
| code-review-not_required-1 | not_required | Automated dependency bumps do not need a human reviewer. |
| code-review-not_required-3 | not_required | There is no need for peer approval on typo fixes in notes. |
| load-testing-required-2 | required | A capacity change needs a stress run. |
| load-testing-not_required-1 | not_required | A documentation site does not need a stress run. |
| load-testing-not_required-3 | not_required | There is no need to simulate peak volume for a config change. |
| data-masking-required-2 | required | Logs that show account details need the sensitive parts obscured. |
| data-masking-not_required-1 | not_required | Public product codes do not need to be hidden. |
| request-signing-required-2 | required | Webhooks we send need to be cryptographically signed. |
| request-signing-not_required-1 | not_required | Public read-only calls do not need a signature. |
| request-signing-not_required-3 | not_required | There is no need to sign calls that stay inside one process. |
| dependency-pinning-required-2 | required | The build needs a lock file with fixed releases. |
| dependency-pinning-not_required-1 | not_required | A throwaway notebook does not need locked library versions. |
| dependency-pinning-not_required-3 | not_required | There is no need to freeze versions of the linters. |
| rollback-required-2 | required | A deployment plan needs a tested revert step. |
| rollback-not_required-1 | not_required | A static page update does not need a revert plan. |
| rollback-not_required-3 | not_required | There is no need to rehearse undoing the config tweak. |
| sharding-required-2 | required | At this volume the store needs to be partitioned by customer. |
| sharding-not_required-1 | not_required | A table of a few thousand rows does not need partitioning. |
| sharding-not_required-3 | not_required | There is no need to distribute the lookup tables. |
| deprecation-warnings-required-2 | required | Before removing an endpoint we need to announce it with a warning. |
| deprecation-warnings-not_required-2 | not_required | Private helpers do not need to warn before they disappear. |
| deprecation-warnings-not_required-3 | not_required | There is no need to announce removal of dead test code. |
| connection-pooling-required-2 | required | The service needs a connection pool before it takes traffic. |
| connection-pooling-not_required-1 | not_required | A nightly script does not need a connection pool. |
| connection-pooling-not_required-3 | not_required | There is no need to pool calls to the local file store. |

### `never` (18 queries): strict_required or prohibited

| Query | Assigned | Text |
| --- | --- | --- |
| input-validation-strict_required-3 | strict_required | Skipping input checks is never acceptable, not even for a hotfix. |
| pagination-strict_required-1 | strict_required | Returning an unbounded list is never tolerated, whatever the deadline. |
| rate-limiting-strict_required-3 | strict_required | Never expose an unthrottled public route, no matter who asks. |
| schema-migration-strict_required-1 | strict_required | Altering tables outside a migration is never excused, even during an incident. |
| feature-flagging-strict_required-1 | strict_required | Unflagged launches are never tolerated, however small the change. |
| deduplication-strict_required-1 | strict_required | A duplicate charge is never acceptable, so repeats are filtered without exception. |
| batching-strict_required-1 | strict_required | Sending rows one at a time is never accepted here, even for a single customer. |
| anonymization-strict_required-1 | strict_required | Identifiable data never leaves the vault, and no executive can override that. |
| api-versioning-strict_required-1 | strict_required | Changing a published contract without a new version is never excused. |
| health-checks-strict_required-1 | strict_required | A service without a health probe is never deployed, without a single exception. |
| backups-strict_required-1 | strict_required | Running production without recoverable copies is never acceptable, whatever the cost. |
| load-testing-strict_required-1 | strict_required | Launching without a stress run is never allowed, even if marketing has announced the date. |
| data-masking-strict_required-1 | strict_required | A full card number is never displayed to anyone, with no override for managers. |
| request-signing-strict_required-1 | strict_required | An unsigned payment call is never accepted, and nobody can disable the check. |
| dependency-pinning-strict_required-1 | strict_required | Floating versions are never tolerated in production builds, for any library. |
| rollback-strict_required-1 | strict_required | Shipping something that cannot be reverted is never permissible, even under pressure. |
| sharding-strict_required-1 | strict_required | Keeping all tenants on one node is never acceptable for this system, no matter the quarter. |
| connection-pooling-strict_required-1 | strict_required | Opening a fresh connection per query is never accepted, in any service. |

### `without exception`, `exempt`, `exemption`, `excused` (15 queries): strict_required; check it is not read as prohibited

| Query | Assigned | Text |
| --- | --- | --- |
| pagination-strict_required-3 | strict_required | No exemption will be granted: results are paged, full stop. |
| rate-limiting-strict_required-1 | strict_required | The login route is throttled without exception; nobody can switch it off. |
| schema-migration-strict_required-1 | strict_required | Altering tables outside a migration is never excused, even during an incident. |
| deduplication-strict_required-1 | strict_required | A duplicate charge is never acceptable, so repeats are filtered without exception. |
| deduplication-strict_required-3 | strict_required | No source is exempt from duplicate filtering, whatever its reputation. |
| api-versioning-strict_required-1 | strict_required | Changing a published contract without a new version is never excused. |
| backups-strict_required-3 | strict_required | No environment holding customer data is exempt from being backed up. |
| code-review-strict_required-3 | strict_required | No change is exempt from a reviewer, however trivial. |
| load-testing-strict_required-3 | strict_required | No release on the checkout path skips performance testing, without exception. |
| data-masking-strict_required-3 | strict_required | No screen is exempt from hiding sensitive fields, whatever the support case. |
| request-signing-strict_required-3 | strict_required | No integration partner is exempt from signed calls, without exception. |
| rollback-strict_required-3 | strict_required | No release is excused from being reversible, without exception. |
| sharding-strict_required-3 | strict_required | No large table is exempt from being split between servers. |
| deprecation-warnings-strict_required-3 | strict_required | No public symbol is exempt from a sunset notice, whatever the schedule. |
| connection-pooling-strict_required-3 | strict_required | No client of the primary database is exempt from pooling. |

### `feel free` (14 queries): permitted or not_required

| Query | Assigned | Text |
| --- | --- | --- |
| pagination-permitted-1 | permitted | Feel free to page the audit view if it helps. |
| feature-flagging-permitted-1 | permitted | Feel free to hide the new banner behind a toggle. |
| batching-permitted-3 | permitted | Feel free to buffer events and send them together. |
| health-checks-permitted-3 | permitted | Feel free to report dependency health too. |
| backups-permitted-3 | permitted | Feel free to back up your sandbox. |
| code-review-permitted-3 | permitted | Feel free to have another team read the change. |
| load-testing-permitted-3 | permitted | Feel free to benchmark it under load. |
| data-masking-permitted-3 | permitted | Feel free to obscure internal identifiers too. |
| request-signing-permitted-3 | permitted | Feel free to sign the sandbox traffic. |
| dependency-pinning-permitted-3 | permitted | Feel free to freeze the packages for the demo. |
| rollback-permitted-3 | permitted | Feel free to go back to the earlier build. |
| sharding-permitted-3 | permitted | Feel free to distribute the search index. |
| deprecation-warnings-permitted-3 | permitted | Feel free to warn callers ahead of time. |
| connection-pooling-permitted-3 | permitted | Feel free to reuse connections to the cache. |

### `fine` (3 queries): permitted or not_required

| Query | Assigned | Text |
| --- | --- | --- |
| rate-limiting-permitted-3 | permitted | It is fine to cap traffic on the sandbox. |
| deduplication-permitted-2 | permitted | It is fine to drop repeated alerts if they get noisy. |
| api-versioning-permitted-2 | permitted | It is fine to number the experimental endpoints. |

### `allowed` (21 queries): permitted; negated ('never allowed') it reads as prohibited or strict_required

| Query | Assigned | Text |
| --- | --- | --- |
| input-validation-permitted-2 | permitted | Go ahead and validate inputs in the client as well, that is allowed. |
| pagination-permitted-2 | permitted | The export screen is allowed to split its results into pages. |
| rate-limiting-permitted-2 | permitted | Teams are allowed to set their own request quotas. |
| schema-migration-permitted-3 | permitted | Changing the database layout during this sprint is allowed. |
| feature-flagging-permitted-3 | permitted | Wrapping the experiment in a switch is allowed. |
| deduplication-permitted-3 | permitted | The importer is allowed to merge duplicate rows. |
| batching-permitted-2 | permitted | Bulk inserts are allowed if they simplify the code. |
| anonymization-permitted-2 | permitted | Removing identities from internal reports is allowed. |
| api-versioning-permitted-3 | permitted | Adding a version prefix to this route is allowed. |
| health-checks-permitted-2 | permitted | Exposing a status endpoint on the batch tool is allowed. |
| backups-permitted-2 | permitted | Copying the development database for safekeeping is allowed. |
| code-review-permitted-2 | permitted | Requesting an extra reviewer is allowed. |
| load-testing-strict_required-1 | strict_required | Launching without a stress run is never allowed, even if marketing has announced the date. |
| load-testing-permitted-2 | permitted | Running a traffic simulation on the new endpoint is allowed. |
| data-masking-permitted-2 | permitted | Hiding part of the email address in this list is allowed. |
| request-signing-permitted-2 | permitted | Adding a signature header to these calls is allowed. |
| dependency-pinning-permitted-2 | permitted | Locking this development tool to one release is allowed. |
| rollback-permitted-2 | permitted | Undoing yesterday's deployment is allowed. |
| sharding-permitted-2 | permitted | Splitting this collection across nodes is allowed. |
| deprecation-warnings-permitted-2 | permitted | Adding a sunset message to the internal helper is allowed. |
| connection-pooling-permitted-2 | permitted | Sharing sessions through a pool is allowed in this worker. |

### `skip`, `skips` (2 queries): not_required or permitted

| Query | Assigned | Text |
| --- | --- | --- |
| load-testing-strict_required-3 | strict_required | No release on the checkout path skips performance testing, without exception. |
| connection-pooling-not_required-2 | not_required | This tool can open a single connection and skip pooling. |

### `acceptable` (4 queries): permitted; negated it reads as strict_required or prohibited

| Query | Assigned | Text |
| --- | --- | --- |
| input-validation-strict_required-3 | strict_required | Skipping input checks is never acceptable, not even for a hotfix. |
| deduplication-strict_required-1 | strict_required | A duplicate charge is never acceptable, so repeats are filtered without exception. |
| backups-strict_required-1 | strict_required | Running production without recoverable copies is never acceptable, whatever the cost. |
| sharding-strict_required-1 | strict_required | Keeping all tenants on one node is never acceptable for this system, no matter the quarter. |

## Repeated phrasing

The author reused sentence patterns. A high score may partly reflect these cue words,
so decide whether to vary them. Queries per modality containing each cue (of 60):

| Modality | Cue counts | Queries with at least one |
| --- | --- | --- |
| required | obliged 19; has/have to 20; need(s) 19 | 58 |
| strict_required | non-negotiable 20; never 18; exception/exempt 15 | 51 |
| permitted | may 20; allowed 20; feel free 14 | 54 |
| not_required | no need / does not need 31; without 16; obligation/nobody 7 | 54 |
| prohibited | do not 20; forbidden 20; banned 17 | 57 |

## Questions for you

1. Is the line between `required` and `strict_required` right? Strict queries stress that nothing or nobody is excused.
2. Many strict queries are worded negatively ('never', 'no ... is exempt'). Is that how you would state them, or should some be positive ('in every case')?
3. Several `prohibited` queries ban a thing in one place only ('in the billing core'). Is that a prohibition of the concept for you?
