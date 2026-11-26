# Authoring record: modality_collapse_v1

Written by the author of the data (Claude, in the build of task t9). It shows the
evidence that exists and says which statement rests on the author's word alone.

## Split assignment

- The splits were fixed in commit `5ee5ab9`, which added `operations.jsonl`
  (SHA-256 `4085397dbe33bd387757f1be168c55ece0ecee867d3872189751e5537768782d`).
- At the time of this record no run had been made on this probe set: the set had
  no `queries.jsonl` or `manifest.json`, so the command could not load it, and the
  repository had no `runs/` directory. The only earlier runs used the synthetic
  sets of the tests and one smoke run of that synthetic set.
- A later change to a concept's split changes the file hash recorded in every run.

## Concepts of the preliminary modality probe

The preliminary probe, run during the scope review, was this script. Its list `C`
is the source of the excluded names. None of the ten appears in either split.

```python
import json,math,urllib.request as U,statistics as S
def e(t):
    return json.load(U.urlopen(U.Request('http://localhost:11434/api/embed',data=json.dumps({'model':'qwen3-embedding:0.6b','input':t}).encode(),headers={'Content-Type':'application/json'}),timeout=100))['embeddings']
cos=lambda a,b:sum(x*y for x,y in zip(a,b))
norm=lambda v:[x/math.sqrt(cos(v,v)) for x in v]
C=['logging','caching','encryption','retry','consistency','staleness','authentication','audit retention','compression','notification']
F={'req':'{} is required','perm':'{} is permitted','proh':'{} is prohibited','notreq':'{} is not required','req_para':'{} is mandatory','perm_para':'{} is allowed'}
V={k:e([f.format(c) for c in C]) for k,f in F.items()}
def rep(name,a,b):
    x=[cos(p,q) for p,q in zip(V[a],V[b])];print('direct   %-28s mean %.3f min %.3f max %.3f'%(name,S.mean(x),min(x),max(x)))
for n,a,b in (('required vs permitted','req','perm'),('required vs mandatory','req','req_para'),('permitted vs allowed','perm','perm_para'),('required vs prohibited','req','proh'),('required vs not required','req','notreq')):rep(n,a,b)
for a,b,other in (('req_para','req','perm'),('perm_para','perm','req')):
    print(a,'closer to its own modality:',sum(cos(p,q)>cos(p,o) for p,q,o in zip(V[a],V[b],V[other])),'/',len(C))
u=e(C);m=e(['required','permitted'])
print('modality words alone cos %.3f'%cos(*m))
for lam in (0.25,0.5,0.75,1):
    x=[cos(*[norm([i+lam*j for i,j in zip(v,w)]) for w in m]) for v in u];print('additive lambda %.2f  req vs perm mean %.3f max %.3f'%(lam,S.mean(x),max(x)))
```

## How the stored operations were produced

This script produced `operations.jsonl` byte for byte. It reads no file.

```python
import json, sys
from pathlib import Path

# concept -> verb that agrees with it
SPLITS = {
    "select": {
        "input validation": "is", "pagination": "is", "rate limiting": "is",
        "schema migration": "is", "feature flagging": "is", "deduplication": "is",
        "batching": "is", "anonymization": "is", "API versioning": "is",
        "health checks": "are",
    },
    "confirm": {
        "backups": "are", "code review": "is", "load testing": "is",
        "data masking": "is", "request signing": "is", "dependency pinning": "is",
        "rollback": "is", "sharding": "is", "deprecation warnings": "are",
        "connection pooling": "is",
    },
}
MODALITIES = [
    ("required", 1, "required"),
    ("strict_required", 2, "strictly required, with no exceptions"),
    ("permitted", 1, "permitted"),
    ("not_required", -1, "not required"),
    ("prohibited", -1, "prohibited"),
]
with Path(sys.argv[1]).open("w") as out:
    for split, concepts in SPLITS.items():
        for concept, verb in concepts.items():
            for modality, phase, phrase in MODALITIES:
                out.write(json.dumps({
                    "concept": concept, "modality": modality, "phase": phase,
                    "phase_modality_text": phrase,
                    "contextual_text": f"{concept} {verb} {phrase}",
                    "split": split,
                }) + "\n")
```

## The benchmark archive

Author's statement, which the files cannot prove: the benchmark archive was not
opened while authoring this probe set. The author had inspected the benchmark's
dev split earlier, during the scope review, so the concepts are not independent
of that knowledge in the way a second author's would be.

## Queries

`queries.jsonl` was written by hand by the same author, one list per concept and
modality, with synonym terms assigned by position. The first draft (commit
`510fafe`) reused sentence patterns. At the user's request it was rewritten, in
several passes guided by phrase counts, the word-only baseline below and a final
read-through. `REVIEW.md` reports the resulting figures.

Author's statement, which the files cannot prove: no embedding of any query was
computed or looked at while writing or editing them. Neither version has been
embedded by any run at the time of this record. The benchmark archive was not
opened.

The word-only baseline was computed by this script:

```python
"""How well single words alone predict the modality: naive Bayes, one concept held out."""
import json, math, re, sys
from collections import Counter

records = [json.loads(l) for l in open(sys.argv[1])]
concepts = sorted({r["concept"] for r in records})
modalities = sorted({r["modality"] for r in records})
tokens = lambda text: set(re.findall(r"[a-z']+", text.lower()))
right = Counter()
for held in concepts:
    train = [r for r in records if r["concept"] != held]
    counts = {m: Counter(w for r in train if r["modality"] == m for w in tokens(r["text"])) for m in modalities}
    size = {m: sum(r["modality"] == m for r in train) for m in modalities}
    vocabulary = set().union(*counts.values())
    for r in (r for r in records if r["concept"] == held):
        words = tokens(r["text"]) & vocabulary
        guess = max(modalities, key=lambda m: sum(math.log((counts[m][w] + 1) / (size[m] + 2)) for w in words))
        right[r["modality"]] += guess == r["modality"]
total = Counter(r["modality"] for r in records)
print(json.dumps({"overall": sum(right.values()) / len(records), **{m: right[m] / total[m] for m in modalities}}))
```
