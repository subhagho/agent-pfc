# Expected parser entries: design session of 26 November 2026

**Status: draft, awaiting user correction. Do not score a model against it yet.**

- Source: Claude Code session `4d725813-dfb9-4a24-adc4-d020a02fcb08`, project agent-pfc.
- Range: typed user messages #1 to #55 (last: `59a748ae`, "yes, go ahead"), with the agent's replies as context.
- Written by the agent that took part in the session, before any parser model saw the log.

## Conventions to confirm

1. **Instruction:** how something must be done, including design decisions. **Data point:** a fact about the project or its environment.
2. An entry needs the user to state it, or to accept an agent proposal.
3. One-off requests, questions and examples are not entries.
4. "Active" is the expected state after message #55.

## Active entries

| ID | Kind | Entry | From |
|---|---|---|---|
| A01 | instruction | Treat separation of concerns and modularity as the prime directive, in code and in package structure. | #6 |
| A03 | instruction | Build PFC to persist and recover the instructions given to a coding agent, not as a general inference engine. | #21 |
| A04 | instruction | Tune retrieval for generic agent queries about a decision, such as "decide transaction mode". | #21, #22 |
| A05 | instruction | Memory must not be intrusive: steering guides when to consult it, and the agent decides. | #26 |
| A06 | instruction | Enforce destructive actions, such as deleting data or pushing code, with harness controls, not memory rules. | #27 |
| A07 | instruction | Store instructions and data points as separate kinds. | #28 |
| A08 | instruction | Store concise, normalized rules, not verbose statements. | #31, #34 |
| A09 | instruction | Store entries in a vector store. | #34 |
| A10 | instruction | The coding agent does not save memory; a local model parses chat logs offline. | #35 |
| A11 | instruction | Ignore conversational turns; store only new additions that need storing. | #35 |
| A12 | instruction | Parse chat history in moving windows, not turn by turn. | #36 |
| A13 | instruction | Run parsing as a batch over all available histories, resuming each session from its checkpoint, up to 5 minutes before the run. | #37 |
| A14 | instruction | Keep memory project centric. | #38 |
| A15 | instruction | Start batch runs with timed triggers in the daemon. | #39 |
| A16 | instruction | Keep PFC standalone, not embedded in insrc; agents access it through MCP. | #40 |
| A17 | instruction | Use one store. | #41 |
| A18 | instruction | Run parsing in a separate worker process, started by the daemon. | #41, confirmed after #55 ("yes, separate process"); extend the range and snapshot before scoring |
| A19 | instruction | Serve memory through an HTTP service on a small local web server, which MCP consumes and the daemon calls. | #43 |
| A20 | data point | Memory may later become organization memory for a project. | #43 |
| A21 | instruction | Make CLI agents' chat history available to the daemon for indexing. | #43 |
| A22 | instruction | Use LanceDB as the vector store. | #44, #45 |
| A23 | data point | insrc uses LanceDB. | #45 |
| A24 | instruction | Only the indexer thread, managed by the memory server, writes to the store; allow no external writes. | #46, #47 |
| A25 | instruction | Use two local models: one for embedding, one for classification and normalization. | #49 |
| A26 | instruction | Do not use a 17 GB model for classification and normalization; use a small one. | #51 |
| A27 | instruction | Use Gemma 4 E2B for classification and normalization. | #52, reworded after #55; extend the range and snapshot before scoring |
| A28 | data point | Embedding libraries tried in insrc performed badly on CPU. | #42 |
| A29 | instruction | Do not depend on Ollama. | #42, confirmed after #55; extend the range and snapshot before scoring |
| A30 | instruction | The memory service installer must install llama.cpp, used as a Python library. | confirmed after #55; extend the range and snapshot before scoring |
| A32 | instruction | Use the Qwen embedding model for embeddings. | stated after #55; extend the range and snapshot before scoring |
| A31 | instruction | Support Linux, macOS and Windows. | confirmed after #55; extend the range and snapshot before scoring |

## Entries that should be created and later retired

| ID | Entry | Created | Retired by |
|---|---|---|---|
| R01 | A qwen embedding model is available locally through Ollama. (Use of Ollama) | #5 | #42 (A29); may stay as a plain fact |
| R06 | Parse logs with a local **Ollama** model. | #35 | #42; A10 stays without Ollama |

## Must not be stored

| ID | Content | Why | From |
|---|---|---|---|
| N01 | Commit or push the files | one-off request | #3, #11 |
| N02 | Write review findings; copy the schema file; run triage; start; fix both; rewrite queries; download the model | one-off tasks | #4, #12 to #15, #19, #53 |
| N03 | "approved", "cmd done", "yes, go ahead" as entries of their own | progress replies | #16 to #18, #55 |
| N04 | "No PII data to be saved locally", "never violate transactional consistency", "customer data is saved in file ...", "PII data is never to be persisted locally", "don't paginate customer record", "always paginate order records" | examples used to explain the design | #22, #28, #31 |
| N05 | "Birds can fly" and "penguins can't fly" | analogy | #23 |
| N06 | llama.cpp is installed as part of the Ollama server | unverified guess in a request to check | #54 |
| N07 | Use Gunicorn; use llama.cpp | asked as questions, not decided | #48, #50 |
| N08 | SQLite store; per-session stdio MCP server; FastAPI on Uvicorn; loopback token; Claude Code reader first | agent proposals replaced or not accepted | agent replies |
| N09 | Any statement about the earlier representation design or its experiments | no longer relevant (user, after #55) | #7 to #11, #19, #29, #31 |

## Judgement calls for the user

1. **A18:** answered. Parsing runs in a separate process.
2. **A29:** answered. No Ollama dependency.
3. **Default and exception (#23):** should "generic rules answer by default; exceptions are stated explicitly" be an entry?
4. **llama.cpp:** answered. Decided after #55 (A30); it stays in N07 only for the range ending at #55.
5. **A27:** answered by restating the choice: "gemma e2b for classification/nomralization, qwen for embedding". Read as a stored instruction. A general rule for trial decisions was not stated.
6. **Design decisions as instructions:** answered. The user confirmed "use LanceDB - yes", read as: A22 and similar decisions are instructions, so convention 1 stands.

## Scoring

- **Missed:** an active entry with no matching parser entry.
- **Wrongly added:** a parser entry matching a "must not be stored" row, or nothing in this file.
- **Not retired:** a retired entry still active at the end.
- **Distorted:** a match that loses scope, negation or a condition.
- **Duplicate:** two active parser entries matching one expected entry.
