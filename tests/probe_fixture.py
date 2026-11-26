"""A small synthetic probe set, one concept per split."""

import hashlib
import json
from pathlib import Path
from typing import Any

from agent_pfc.domain import PHASE_BY_MODALITY, Modality

CONCEPTS = {"log": "select", "retry": "confirm"}


def operation_records() -> list[dict[str, Any]]:
    return [
        {
            "concept": concept,
            "modality": modality.value,
            "phase": PHASE_BY_MODALITY[modality],
            "phase_modality_text": f"{modality.value} phrase",
            "contextual_text": f"{concept} as a {modality.value} step",
            "split": split,
        }
        for concept, split in CONCEPTS.items()
        for modality in Modality
    ]


def query_records() -> list[dict[str, Any]]:
    return [
        {
            "id": f"{concept}-{modality.value}",
            "concept": concept,
            "modality": modality.value,
            "text": f"question about {concept}, case {number}",
            "synonym_term": f"synonym {number}",
        }
        for concept in CONCEPTS
        for number, modality in enumerate(Modality)
    ]


def write_probe_set(
    directory: Path,
    operations: list[Any] | None = None,
    queries: list[Any] | None = None,
    reviewed: Any = False,
    manifest_changes: dict[str, Any] | None = None,
) -> Path:
    """Write the files with a manifest that matches them, then apply changes."""
    data = {
        "operations": operation_records() if operations is None else operations,
        "queries": query_records() if queries is None else queries,
    }
    manifest: dict[str, Any] = {
        "counts": {},
        "sha256": {},
        "reviewed_by_user": reviewed,
    }
    directory.mkdir(parents=True, exist_ok=True)
    for key, records in data.items():
        content = "".join(json.dumps(record) + "\n" for record in records).encode()
        (directory / f"{key}.jsonl").write_bytes(content)
        manifest["counts"][key] = len(records)
        manifest["sha256"][f"{key}.jsonl"] = hashlib.sha256(content).hexdigest()
    manifest.update(manifest_changes or {})
    (directory / "manifest.json").write_text(json.dumps(manifest))
    return directory
