from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from probe_fixture import operation_records, query_records, write_probe_set

from agent_pfc.domain import Modality, OperationKey, Split
from agent_pfc.probes.loading import load_probe_set
from agent_pfc.probes.validation import ProbeValidationError


@pytest.mark.parametrize("reviewed", [False, True])
def test_valid_set_is_loaded_with_review_flag(tmp_path: Path, reviewed: bool) -> None:
    probes = load_probe_set(write_probe_set(tmp_path, reviewed=reviewed))
    assert probes.reviewed_by_user is reviewed
    assert len(probes.operations) == 10 and len(probes.queries) == 10
    assert sorted(probes.file_hashes) == ["operations.jsonl", "queries.jsonl"]
    first = probes.operations[0]
    assert first.key == OperationKey("log", Modality.REQUIRED)
    assert (first.phase, first.split) == (1, Split.SELECT)


# Edits the records in place; whatever it returns is ignored.
Change = Callable[[list[dict[str, Any]], list[dict[str, Any]]], object]


def _set(records: int, index: int, field: str, value: Any) -> Change:
    def change(operations, queries) -> None:
        (operations, queries)[records][index][field] = value

    return change


def _drop_field(records: int, field: str) -> Change:
    def change(operations, queries) -> None:
        del (operations, queries)[records][0][field]

    return change


def _drop_modality_queries(operations, queries) -> None:
    # The confirm concept loses its permitted query.
    queries[:] = [q for q in queries if q["id"] != "retry-permitted"]


OPERATIONS, QUERIES = 0, 1
CASES: dict[str, tuple[Change, str]] = {
    "operation-field-missing": (
        _drop_field(OPERATIONS, "contextual_text"),
        "operations.jsonl:1: field 'contextual_text'",
    ),
    "query-field-missing": (
        _drop_field(QUERIES, "synonym_term"),
        "queries.jsonl:1: field 'synonym_term'",
    ),
    "blank-text": (_set(QUERIES, 0, "text", "  "), "field 'text'"),
    "unknown-modality": (
        _set(OPERATIONS, 0, "modality", "optional"),
        "field 'modality' must be one of",
    ),
    "unknown-split": (_set(OPERATIONS, 0, "split", "dev"), "field 'split'"),
    "phase-not-integer": (_set(OPERATIONS, 0, "phase", "1"), "field 'phase'"),
    "phase-wrong": (
        _set(OPERATIONS, 1, "phase", 1),
        "phase +1 does not match modality strict_required",
    ),
    "duplicate-query-id": (
        _set(QUERIES, 1, "id", "log-required"),
        "query id 'log-required' already used at queries.jsonl:1",
    ),
    "modality-missing": (
        lambda operations, queries: operations.pop(0),
        "concept 'log': 0 operations with modality required",
    ),
    "modality-twice": (
        lambda operations, queries: operations.append(dict(operations[0])),
        "concept 'log': 2 operations with modality required",
    ),
    "concept-in-both-splits": (
        _set(OPERATIONS, 0, "split", "confirm"),
        "concept 'log': operations are in both splits",
    ),
    "unknown-concept": (
        _set(QUERIES, 0, "concept", "cache"),
        "no operations for concept 'cache'",
    ),
    "split-without-modality-queries": (
        _drop_modality_queries,
        "split confirm: no queries for modality permitted",
    ),
    "copies-contextual-text": (
        _set(QUERIES, 0, "text", "  Retry as a   REQUIRED step "),
        "queries.jsonl:1: query text copies a stored text",
    ),
    "copies-modality-text": (
        _set(QUERIES, 0, "text", "Permitted Phrase"),
        "query text copies a stored text",
    ),
}


@pytest.mark.parametrize(("change", "message"), CASES.values(), ids=CASES.keys())
def test_each_validation_failure(
    tmp_path: Path, change: Change, message: str
) -> None:
    operations, queries = operation_records(), query_records()
    change(operations, queries)
    write_probe_set(tmp_path, operations, queries)
    with pytest.raises(ProbeValidationError) as caught:
        load_probe_set(tmp_path)
    assert message in str(caught.value)


def test_a_split_lacking_a_pair_is_rejected(tmp_path: Path) -> None:
    queries = [
        q
        for q in query_records()
        if not (q["concept"] == "log" and q["modality"] != "required")
    ]
    write_probe_set(tmp_path, queries=queries)
    with pytest.raises(ProbeValidationError) as caught:
        load_probe_set(tmp_path)
    assert len(caught.value.failures) == 4
    assert all("split select" in f for f in caught.value.failures)


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"reviewed_by_user": "false"}, "'reviewed_by_user' must be true or false"),
        ({"counts": {"operations": 9, "queries": 10}}, "counts.operations is 9"),
        ({"counts": None}, "counts.queries is None"),
        ({"sha256": {}}, "sha256 of queries.jsonl does not match"),
    ],
)
def test_manifest_failures(
    tmp_path: Path, changes: dict[str, Any], message: str
) -> None:
    write_probe_set(tmp_path, manifest_changes=changes)
    with pytest.raises(ProbeValidationError, match=message):
        load_probe_set(tmp_path)


def test_edited_file_no_longer_matches_its_hash(tmp_path: Path) -> None:
    path = write_probe_set(tmp_path) / "queries.jsonl"
    path.write_text(path.read_text().replace("case 0", "case zero"))
    with pytest.raises(ProbeValidationError) as caught:
        load_probe_set(tmp_path)
    assert caught.value.failures == (
        "manifest.json: sha256 of queries.jsonl does not match the file",
    )


def test_all_failures_are_listed_together(tmp_path: Path) -> None:
    operations, queries = operation_records(), query_records()
    operations[0]["phase"] = 2
    queries[3]["id"] = queries[2]["id"]
    queries.append(["not", "an", "object"])  # type: ignore[arg-type]
    write_probe_set(tmp_path, operations, queries, reviewed=None)
    with (tmp_path / "operations.jsonl").open("a") as stream:
        stream.write("{broken\n")

    with pytest.raises(ProbeValidationError) as caught:
        load_probe_set(tmp_path)
    message = str(caught.value)
    for expected in (
        "phase +2 does not match",
        "already used",
        "queries.jsonl:11: not a JSON object",
        "operations.jsonl:11: not valid JSON",
        "'reviewed_by_user'",
        "sha256 of operations.jsonl",
        "counts.operations",
    ):
        assert expected in message


def test_missing_files_are_all_reported(tmp_path: Path) -> None:
    with pytest.raises(ProbeValidationError) as caught:
        load_probe_set(tmp_path / "absent")
    message = str(caught.value)
    for name in ("operations.jsonl", "queries.jsonl", "manifest.json"):
        assert f"{name}: cannot be read" in message
