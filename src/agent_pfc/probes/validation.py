"""Pure checks that turn decoded probe files into a ProbeSet.

Every failure is collected, so one error lists all of them.
"""

from collections import defaultdict
from collections.abc import Mapping, Sequence
from enum import StrEnum
from typing import Any

from agent_pfc.domain import (
    PHASE_BY_MODALITY,
    Modality,
    ProbeOperation,
    ProbeQuery,
    ProbeSet,
    Split,
)

OPERATIONS_FILE = "operations.jsonl"
QUERIES_FILE = "queries.jsonl"
DATA_FILES = (OPERATIONS_FILE, QUERIES_FILE)

# A decoded record and where it came from, for example "queries.jsonl:3".
Located = tuple[str, Any]

_OPERATION_STRINGS = ("concept", "phase_modality_text", "contextual_text")
_QUERY_STRINGS = ("id", "concept", "text", "synonym_term")


class ProbeValidationError(ValueError):
    def __init__(self, failures: Sequence[str]) -> None:
        self.failures = tuple(failures)
        super().__init__(
            f"invalid probe set ({len(self.failures)} failures):\n"
            + "\n".join(f"- {failure}" for failure in self.failures)
        )


def build_probe_set(
    operation_records: Sequence[Located],
    query_records: Sequence[Located],
    manifest: Any,
    file_hashes: Mapping[str, str],
    read_failures: Sequence[str] = (),
) -> ProbeSet:
    """The probe set, or ProbeValidationError naming everything wrong with it."""
    failures = list(read_failures)
    operations = _operations(operation_records, failures)
    queries = _queries(query_records, failures)
    reviewed = _manifest(
        manifest,
        {OPERATIONS_FILE: len(operation_records), QUERIES_FILE: len(query_records)},
        file_hashes,
        failures,
    )
    splits = _concepts(operations, failures)
    _query_references(queries, splits, failures)
    _split_coverage(queries, splits, failures)
    _copied_texts(operations, queries, failures)
    if failures:
        raise ProbeValidationError(failures)
    return ProbeSet(
        operations=tuple(operation for _, operation in operations),
        queries=tuple(query for _, query in queries),
        reviewed_by_user=reviewed,
        file_hashes=dict(file_hashes),
    )


def _field_failures(
    where: str,
    record: Any,
    strings: Sequence[str],
    enums: Mapping[str, type[StrEnum]],
) -> list[str]:
    if not isinstance(record, dict):
        return [f"{where}: not a JSON object"]
    failures = [
        f"{where}: field {name!r} is missing or not a non-empty string"
        for name in strings
        if not (isinstance(record.get(name), str) and record[name].strip())
    ]
    failures += [
        f"{where}: field {name!r} must be one of {[m.value for m in kind]}"
        for name, kind in enums.items()
        if record.get(name) not in [m.value for m in kind]
    ]
    return failures


def _operations(
    records: Sequence[Located], failures: list[str]
) -> list[tuple[str, ProbeOperation]]:
    operations = []
    for where, record in records:
        found = _field_failures(
            where,
            record,
            _OPERATION_STRINGS,
            {"modality": Modality, "split": Split},
        )
        if isinstance(record, dict) and type(record.get("phase")) is not int:
            found.append(f"{where}: field 'phase' is missing or not an integer")
        if found:
            failures += found
            continue
        operation = ProbeOperation(
            concept=record["concept"],
            modality=Modality(record["modality"]),
            phase=record["phase"],
            phase_modality_text=record["phase_modality_text"],
            contextual_text=record["contextual_text"],
            split=Split(record["split"]),
        )
        expected = PHASE_BY_MODALITY[operation.modality]
        if operation.phase != expected:
            failures.append(
                f"{where}: phase {operation.phase:+d} does not match modality "
                f"{operation.modality}, which has {expected:+d}"
            )
        operations.append((where, operation))
    return operations


def _queries(
    records: Sequence[Located], failures: list[str]
) -> list[tuple[str, ProbeQuery]]:
    queries = []
    seen: dict[str, str] = {}
    for where, record in records:
        found = _field_failures(where, record, _QUERY_STRINGS, {"modality": Modality})
        if found:
            failures += found
            continue
        query = ProbeQuery(
            id=record["id"],
            concept=record["concept"],
            modality=Modality(record["modality"]),
            text=record["text"],
            synonym_term=record["synonym_term"],
        )
        if query.id in seen:
            failures.append(
                f"{where}: query id {query.id!r} already used at {seen[query.id]}"
            )
        seen.setdefault(query.id, where)
        queries.append((where, query))
    return queries


def _manifest(
    manifest: Any,
    counts: Mapping[str, int],
    file_hashes: Mapping[str, str],
    failures: list[str],
) -> bool:
    if not isinstance(manifest, dict):
        failures.append("manifest.json: not a JSON object")
        return False
    reviewed = manifest.get("reviewed_by_user")
    if not isinstance(reviewed, bool):
        failures.append("manifest.json: 'reviewed_by_user' must be true or false")
    stated_counts = manifest.get("counts")
    stated_hashes = manifest.get("sha256")
    for name in DATA_FILES:
        key = name.removesuffix(".jsonl")
        stated = stated_counts.get(key) if isinstance(stated_counts, dict) else None
        if stated != counts[name]:
            failures.append(
                f"manifest.json: counts.{key} is {stated}, the file has {counts[name]}"
            )
        digest = stated_hashes.get(name) if isinstance(stated_hashes, dict) else None
        if name in file_hashes and digest != file_hashes[name]:
            failures.append(f"manifest.json: sha256 of {name} does not match the file")
    return reviewed is True


def _concepts(
    operations: Sequence[tuple[str, ProbeOperation]], failures: list[str]
) -> dict[str, Split]:
    """Check each concept's operations and return the split of each concept."""
    by_concept: dict[str, list[ProbeOperation]] = defaultdict(list)
    for _, operation in operations:
        by_concept[operation.concept].append(operation)
    splits = {}
    for concept, members in by_concept.items():
        modalities = [operation.modality for operation in members]
        for modality in Modality:
            if modalities.count(modality) != 1:
                failures.append(
                    f"concept {concept!r}: {modalities.count(modality)} operations "
                    f"with modality {modality}, expected 1"
                )
        if len({operation.split for operation in members}) > 1:
            failures.append(f"concept {concept!r}: operations are in both splits")
        splits[concept] = members[0].split
    return splits


def _query_references(
    queries: Sequence[tuple[str, ProbeQuery]],
    splits: Mapping[str, Split],
    failures: list[str],
) -> None:
    for where, query in queries:
        if query.concept not in splits:
            failures.append(f"{where}: no operations for concept {query.concept!r}")


def _split_coverage(
    queries: Sequence[tuple[str, ProbeQuery]],
    splits: Mapping[str, Split],
    failures: list[str],
) -> None:
    """Each split queries every modality, so every pair is tested from both sides."""
    covered = {
        (splits[query.concept], query.modality)
        for _, query in queries
        if query.concept in splits
    }
    for split in Split:
        for modality in Modality:
            if (split, modality) not in covered:
                failures.append(
                    f"split {split}: no queries for modality {modality}, "
                    "so its pairs are not tested"
                )


def _folded(text: str) -> str:
    return " ".join(text.casefold().split())


def _copied_texts(
    operations: Sequence[tuple[str, ProbeOperation]],
    queries: Sequence[tuple[str, ProbeQuery]],
    failures: list[str],
) -> None:
    stored = {
        _folded(text): where
        for where, operation in operations
        for text in (operation.contextual_text, operation.phase_modality_text)
    }
    for where, query in queries:
        source = stored.get(_folded(query.text))
        if source:
            failures.append(f"{where}: query text copies a stored text at {source}")
