# agent-pfc

## About this project

agent-pfc is a standalone Python project: the PFC, a **memory of instructions and data points** for coding agents. It is not embedded in insrc.

Decided so far:

- Memory holds short, normalized entries in LanceDB, as instructions or data points, scoped to one project.
- The coding agent does not save entries. A separate worker process, started by a daemon on timed triggers, parses chat histories in moving windows, resuming each session from its checkpoint up to 5 minutes before the run.
- A local HTTP memory server owns the store. Its indexer thread is the only writer.
- Agents query the server through MCP, when they choose to. Memory must not be intrusive.
- Gemma 4 E2B classifies and normalizes; Qwen3 0.6B embeds. Both come from config and are downloaded if absent.
- Models run through llama.cpp as a Python library, installed by the memory service installer, with no Ollama dependency. It must support Linux, macOS and Windows.

Read first: `docs/REQUIREMENTS.md`. Design is done one module at a time, in the order it lists. Do not design against a requirement marked Proposed as if it were settled. Code and documents from the earlier design are not a reference for new work.

## Coding guidelines (non-negotiable)

**Separation of concerns and modularity are the prime directive.** They apply to the package structure as much as to the code.

- Each package and module has one responsibility. No catch-all `utils` modules.
- `core/common` holds only shared definitions (types, failure types and interfaces): no logic that does I/O, no helper functions, and no imports from the rest of the project. Each module in it has one subject.
- Layers depend on explicit interfaces (protocols) and domain types. Backend-specific details, such as llama.cpp or LanceDB, stay inside their backend.
- Dependencies point one way. Domain models depend on nothing else in the project; the CLI only wires parts together.
- Keep pure logic apart from I/O. Core logic does not read files, call models or access the store directly.
- Designs state these boundaries, and a violation fails review.

<!-- insrc:steering:start -->
## insrc — front door (insrc MCP server)

### Hard gates — never skipped, whatever the host agent

These apply to every agent (Claude Code, Codex, Vibe, …) working in this repo.
If a gate cannot be satisfied, stop and ask the user — do not improvise around it.

1. **Approval is a human gate.** Never call `insrc_workflow_approve` unless the
   user gave an explicit in-chat yes in the same turn, for the specific artifact:
   the yes names the artifact id/path, or answers "yes" to the summary you just
   presented after `insrc_present`. A blanket "approve all" covers ONLY the
   artifacts you declared with `insrc_present` in that same turn — list them.
   Never batch-approve via `{ epicHash }` without naming each artifact and
   getting a yes for that batch. Never approve via raw daemon IPC/socket —
   only through the registered `insrc_workflow_approve` MCP tool.
2. **Present before you ask.** `insrc_present` must report every declared name
   as `presented` before you ask for approval. If it errors, or any name comes
   back `notPending`, correct the name and call again; if it cannot succeed,
   STOP and tell the user — do not approve anything that was not presented.
3. **Automated reviews are unavailable.** Design and code review endpoints raise an exception stating they are being rewritten. Validate changes and report self-check evidence; keep human artifact approval.
4. **Never patch off-ledger.** Every feature and every defect goes through
   triage → tracked artifact → approval → build → validate → approve. No direct
   commits that implement tracked work without the chain's records.
5. **Workflows run only via `insrc_workflow_step`**, turn-by-turn, preserving
   the opaque `state` token. Never `insrc_workflow_run`, never raw IPC.
6. **If `insrc_schema` / `insrc_guide` / `insrc_present` are unavailable or
   error, do not improvise their content from memory — say so and ask the user.**

This is the SKELETON. It names every insrc surface and routes an intent to the
right one; it does NOT inline each workflow's full procedure. Two on-demand
lookups carry the detail so this block can stay small:

- **`insrc_schema`** — the exact INPUT SHAPE of any insrc_* tool (and, for a
  multi-turn tool, its accepted `phase` set). Call it before you emit a call
  whose argument shape you are unsure of, instead of guessing.
- **`insrc_guide`** — a workflow's full STEP-BY-STEP PROCEDURE. Call
  `insrc_guide({ workflow })` before running a workflow you don't have fresh in
  context, with one of: `define`, `design.epic`, `design.story`, `plan`,
  `build`, `review`, `code-review`, `brainstorm`, `bugfix`, `tracker`, `triage`.
  Omit `workflow` to get the list of keys back.

**Schema-first rule:** call `insrc_schema` before emitting any insrc_* call whose
shape (fields, or the `phase` you're in) you are not certain of. Don't hand-shape
a call from memory when the contract is one lookup away.

### Front-door decision tree (intent → surface)

- **Finding things in the codebase — your own tools or the analyzer?** Ask:
  *could a text match alone give a wrong or incomplete answer?*
  - **No → use your own tools** (`Grep` / `Glob` / `Read`). The answer is
    whether or where some text occurs: "does this code use file IO?", "where is
    this config key read?", "which files mention X?", "show me this function".
  - **Yes → use the analyzer**: `insrc_analyze_step` (multi-turn, in-session,
    preferred) or `insrc_analyze` (one-shot, Ollama). The answer depends on
    relationships or meaning that text matching can't see: "where is this
    module used, and what depends on it?", "what breaks if I change this?",
    "does the code follow this documented rule?", "does the codebase already do
    X?", "how does X work?", "what are the conventions here?".
  - A task often needs both: analyze to understand the area, then search and
    read to work in it. Don't run the analyzer for a lookup, and don't answer a
    relationship question from a text match alone.
  - For "where is X used", also grep for the name and report any call site the
    analyzer missed — its call graph can be incomplete.
  - **Send a structured `request`, not just the prompt.** Read the user's prompt
    yourself and decide what it is about, then call `insrc_analyze_step` (or
    `insrc_analyze`) with `request: { question, scopeRef: { kind, value },
    target?, sizeHint?, context? }`. `scopeRef` names what to analyse: a
    module or file as an ABSOLUTE path, a symbol as
    `<absolute file path>#<entity name>` (a bare name is not accepted), or the repo; use
    `workspace` only when the prompt names no area. Put background the user
    gave that bears on the answer in `context` (it never decides the scope).
    The daemon checks the scope against the repository and answers
    `scope-not-found` or `scope-repo-mismatch` rather than guessing. A
    `focus`-only call still works and analyses the whole workspace.
- **Draw / diagram / document / map the code** (a self-contained HTML doc from
  the graph) → `insrc_docgen`. For PROPOSED designs, use the workflow
  artifact definitions below; docgen describes existing code, not a future model.
- **Build / add / implement a feature** → do NOT hand-pick a stage and do NOT
  just start editing. Route it: `brainstorm` (if the idea is rough) →
  `insrc_triage` (sizes + routes) → the routed workflow → present → approve →
  build → validate → human approval → complete. Every feature, big or small, is tracked. See
  `insrc_guide({ workflow: 'triage' })` for the routing table. For a later Story
  of an Epic, the first activity of its design.story, plan and build is a
  complete impact analysis of what the Epic has already built (see those guides).
- **Fix a bug / defect** → same front door: `insrc_triage` classifies it
  `bugfix` (magnitude `small` or `sized`) and routes to the `issue` stage — a
  defect gets tracked exactly like a feature, never patched off-ledger. Small →
  issue → build; sized → issue → design.story → plan → build. On the approval of
  the tracked `issue`, the bugfix chain auto-advances to its next stage. See
  `insrc_guide({ workflow: 'bugfix' })`.
- **Produce a design artifact / decision / tracker push** (Epic, HLD, LLD,
  GitHub) → drive the workflow chain turn-by-turn with `insrc_workflow_step`.
  See the matching `insrc_guide` key.
- **The exact shape of a call** → `insrc_schema`.
- **A workflow's full procedure** → `insrc_guide({ workflow })`.

### Tool catalog (all registered insrc_* MCP tools)

Call `insrc_schema({ tool })` for any tool's exact input shape (add `phase` for
a multi-turn tool). Call `insrc_guide({ workflow })` for a workflow's procedure.

| Tool | Purpose |
|------|---------|
| `insrc_analyze` | One-shot 7-layer context bundle for a codebase question (Ollama pipeline). |
| `insrc_analyze_step` | Multi-turn context bundle — same queries, reasoning stays in-session (preferred). |
| `insrc_docgen` | Generate a self-contained offline HTML doc/diagram from the code graph. |
| `insrc_triage` | Size a feature request and return a pre-filled `nextCall` routing it to a start stage. |
| `insrc_workflow_step` | Drive one tracked workflow turn (define / design.epic / design.story / plan / brainstorm / tracker). **This is the ONLY supported way to run a workflow — always drive it turn-by-turn in-session.** |
| `insrc_workflow_run` | Daemon-side async run (START → POLL). **NOT recommended — do not use.** The async poll/handoff can stall in a resolution loop and error out on completion; drive workflows with `insrc_workflow_step` instead. |
| `insrc_build_step` | Drive the build stage (`implement` → `validate`) that turns an approved LLD/plan into code. |
| `insrc_review_step` | Retained endpoint; fails immediately: design review is being rewritten. |
| `insrc_code_review_step` | Retained endpoint; fails immediately: code review is being rewritten. |
| `insrc_security_review_step` | Run a dedicated two-round, dependency-advisory-aware security review over given targets; pauses with `confirm_wait` on a stale index. |
| `insrc_workflow_approve` | Approve a pending artifact by `artifactPath` (or `epicHash` to batch) — only on the user's explicit yes. |
| `insrc_present` | Declare the documents (artifact ids or repo-relative paths) you are asking the user to review, so the chat opens them — call it before asking for approval. |
| `insrc_schema` | Return any insrc_* tool's registered input shape + accepted phases. |
| `insrc_guide` | Return one workflow's full step-by-step procedure from the canonical steering source. |

`insrc_analyze` / `insrc_analyze_step` / `insrc_docgen`: **repo** falls back to
`$INSRC_REPO`; the repo must be registered with the daemon and finished
indexing. The multi-turn tools (`*_step`, `insrc_triage`) hand you a `next` /
`guidance` / `prompt` / `schema` each turn — follow `next` verbatim and preserve
the opaque `state` token between calls. Do NOT use analyze to edit files, run
tests/builds, answer non-context questions, or do a plain text lookup (see the
decision tree above); when a returned bundle is empty or off-topic, fall back
to `Read` / `Grep` / `Glob`.

`insrc_docgen` `docType` values (each single-sources from the code graph — no
hallucinated paths): `type-structure` (classes/interfaces + inheritance in a
scope, `path?`), `component-dependency` (module dependency topology, `path?`),
`call-sequence` (call flow from an entry point — needs `symbol`, `maxDepth?`),
`narrative` (a base diagram + a graph-grounded walkthrough — needs `base` +
`question`).

### Relevant design artifacts

Authors, builders and reviewers must judge relevance from the change, not its
size or whether a definition already exists. An isolated class implementation
change with no entity/relationship impact needs no ERD. Relationship changes,
even simple ones, MUST document endpoints, direction, cardinality/ownership and
compatibility where applicable. Clear prose or a small table may suffice; add
an ERD when it materially clarifies the model. Use sequence/component diagrams
for interaction/dependency boundaries and UX mocks for changed layout, states
or flows when those visuals materially aid assessment. No blanket diagram rule.

For proposed designs author `erDefinition` (LinkML), `sequenceDefinition`,
`componentDependencyDefinition`, or `uxDefinition` (Adaptive Cards subset).
These structured definitions are the source of truth; the framework generates
and attaches `companions`. Do not hand-author companion references. Describe
what each relevant visual explains and retain source/element descriptions.

Reviewers independently assess necessary artifacts even when no definitions
are supplied. Inspect linked files, generated content and rendering against
the design; a definition alone is not proof of a working visual. Request author
correction/regeneration for missing, broken or inconsistent artifacts. If
rendering is unavailable, inspect source where possible and report the limit;
never claim a visual was verified. Material inadequacy is `does-not-hold` with
MED/HIGH and blocks; genuinely unavailable evidence is `could-not-verify`.
Optional improvements to an otherwise adequate design are narrative advice,
not a `warn` verdict or a false failure/unverified finding. Builders maintain
relevant artifacts when implementation changes documented relationships or UX.
Record which checks were actually performed and any unavailable evidence.

### Approval discipline (applies to every workflow artifact)

Never auto-approve and never send the user to the TUI. When a `done` response
carries a `pendingApproval` block — or any step you drove leaves a record
pending (check `insrc_workflow_step`'s done response and the pending list) —
the gate is the same every time: first DECLARE what you are about to show by
calling `insrc_present({ documents: [...] })` with each document's artifact id
(for example `LLD-<hash>-s1`) or repo-relative path, and require every name
to come back `presented`; then PRESENT a concise summary (give the document's
path in your message too) and ASK the user. Only then, on the user's explicit
in-chat yes **for that artifact** (the message names its id/path, or answers
"yes" to the summary you just presented), call
`insrc_workflow_approve({ artifactPath })`. A blanket "approve all" authorizes
only the artifacts you presented in that same turn. Never batch via
`{ epicHash }` without listing each artifact and getting a yes for the batch.
Never call `insrc_workflow_approve` through raw daemon IPC or a socket — only
through the MCP tool. Automated reviews are unavailable; present the artifact and obtain explicit human approval.

### Review availability

Automated design and code review functionality has been removed while it is being rewritten. Retained endpoints fail immediately; do not start or poll them. Historical review records remain readable. Human approval, build validation, integrity, task accounting, upstream and team/signoff gates still apply.

The chat opens exactly the documents you declare with `insrc_present`; it does
not work out what to open from tool output, so a document you do not declare is
not opened for the user. The answer lists each name as `presented` or
`notPending` (misspelt, already approved, or with no document file yet): correct
a `notPending` name and call again, and require every declared name to be
`presented` before you ask for approval. If `insrc_present` itself is
unavailable or errors, do not approve anything that turn — report the tool
failure and ask the user instead.

### Keep the user informed during long work

Group long work into small batches rather than one long-running batch, and post
a short update to the chat after each batch: what finished and what comes next.

Do not chain activities such as reviews and test runs silently. Before starting
the next one, say in the chat what the last one found and what you are starting.

These updates need no answer. Carry on, and stop for the user only where the
rules above require it.
<!-- insrc:steering:end -->
