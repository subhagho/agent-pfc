"""The probe set committed under data/probes."""

import json
from collections import Counter
from pathlib import Path

from agent_pfc.domain import PHASE_BY_MODALITY, Modality

DIRECTORY = Path(__file__).parents[1] / "data/probes/modality_collapse_v1"
# Concepts whose embeddings were seen in the preliminary modality probe.
SEEN_BEFORE = {
    "logging",
    "caching",
    "encryption",
    "retry",
    "consistency",
    "staleness",
    "authentication",
    "audit retention",
    "compression",
    "notification",
}


def _records(name: str) -> list[dict]:
    return [json.loads(line) for line in (DIRECTORY / name).read_text().splitlines()]


def test_committed_operations() -> None:
    operations = _records("operations.jsonl")
    assert len(operations) == 100

    pairs = Counter((o["concept"], o["modality"]) for o in operations)
    concepts = {o["concept"] for o in operations}
    assert len(concepts) == 20 and set(pairs.values()) == {1}
    assert {m for _, m in pairs} == {m.value for m in Modality}
    for operation in operations:
        assert operation["phase"] == PHASE_BY_MODALITY[Modality(operation["modality"])]

    splits = {(o["concept"], o["split"]) for o in operations}
    assert len(splits) == 20
    assert Counter(split for _, split in splits) == {"select": 10, "confirm": 10}
    assert not SEEN_BEFORE & concepts
