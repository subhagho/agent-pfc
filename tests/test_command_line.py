"""End to end, offline: the command line with a fake embedder."""

import json
from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pytest
from fake_embedder import FakeEmbedder
from probe_fixture import write_probe_set

from agent_pfc.cli import main
from agent_pfc.embeddings.errors import EmbeddingBackendError


class Factory:
    def __init__(self, embedder: type[FakeEmbedder] = FakeEmbedder) -> None:
        self.built: list[FakeEmbedder] = []
        self._embedder = embedder

    def __call__(self, arguments, dimension: int) -> FakeEmbedder:
        self.built.append(self._embedder(dimension))
        return self.built[-1]

    @property
    def calls(self) -> int:
        return sum(len(e.calls) for e in self.built)


def _arguments(tmp_path: Path, reviewed: bool = True, *extra: str) -> list[str]:
    probes = write_probe_set(tmp_path / "probes", reviewed=reviewed)
    return [
        "collapse",
        "--probes",
        str(probes),
        "--runs",
        str(tmp_path / "runs"),
        "--cache",
        str(tmp_path / "cache"),
        "--run-id",
        "one",
        *extra,
    ]


def _record(tmp_path: Path) -> dict:
    return json.loads((tmp_path / "runs/one/run.json").read_text())


def test_run_writes_record_and_report(tmp_path: Path, capsys) -> None:
    assert main(_arguments(tmp_path), Factory()) == 0

    record = _record(tmp_path)
    assert record["status"] == "completed" and record["draft"] is False
    assert record["criterion"] == {
        "min_accuracy": 0.95,
        "min_pairwise_accuracy": 0.9,
    }
    assert [e["dimension"] for e in record["encoders"]] == [256, 512, 1024]
    assert record["probes"]["reviewed_by_user"] is True
    # 10 variants, 3 dimensions, 2 tracks, 2 splits.
    assert len(record["results"]) == 120
    result = record["results"][0]
    assert len(result["confusion"]) == 5 and len(result["confusion"][0]) == 6
    assert len(result["pairwise"]) == 10
    assert record["verdict"]["passed"] is False

    report = (tmp_path / "runs/one/report.md").read_text()
    assert "## Verdict: FAIL" in report and "DRAFT" not in report
    for heading in ("natural track, confirm split", "Expected \\ predicted"):
        assert heading in report
    assert "| C3 w=0.5 | C1 w=0.5 |" in report
    assert "| C2 w=1 | C0 |" in report
    assert "verdict: FAIL" in capsys.readouterr().out


@pytest.mark.parametrize("reviewed", [False, True])
def test_draft_report_has_no_verdict(tmp_path: Path, reviewed: bool, capsys) -> None:
    assert main(_arguments(tmp_path, reviewed, "--draft"), Factory()) == 0
    record = _record(tmp_path)
    assert record["draft"] is True and record["verdict"] is None
    report = (tmp_path / "runs/one/report.md").read_text()
    assert report.startswith("# Modality collapse run one (DRAFT)")
    assert "## No verdict" in report
    assert "Verdict:" not in report and "PASS" not in report and "FAIL" not in report
    assert ("unreviewed" in report) is not reviewed
    assert "no verdict" in capsys.readouterr().out


def test_existing_run_directory_is_not_overwritten(tmp_path: Path, capsys) -> None:
    kept = tmp_path / "runs/one/run.json"
    kept.parent.mkdir(parents=True)
    kept.write_text("earlier")
    factory = Factory()

    assert main(_arguments(tmp_path), factory) == 1
    assert kept.read_text() == "earlier"
    assert list(kept.parent.iterdir()) == [kept]
    assert factory.calls == 0
    assert "already exists" in capsys.readouterr().err


def test_criterion_is_recorded_before_any_embedding(tmp_path: Path) -> None:
    seen: list[dict] = []

    class Watching(FakeEmbedder):
        def encode(self, texts: Sequence[str]) -> np.ndarray:
            seen.append(_record(tmp_path))
            return super().encode(texts)

    assert main(_arguments(tmp_path), Factory(Watching)) == 0
    first = seen[0]
    assert first["status"] == "started"
    assert first["criterion"]["min_accuracy"] == 0.95
    assert "results" not in first
    assert _record(tmp_path)["criterion"] == first["criterion"]


def test_backend_failure_during_the_run_leaves_no_verdict(
    tmp_path: Path, capsys
) -> None:
    class Failing(FakeEmbedder):
        def encode(self, texts: Sequence[str]) -> np.ndarray:
            raise EmbeddingBackendError("server went away")

    assert main(_arguments(tmp_path), Factory(Failing)) == 1
    record = _record(tmp_path)
    assert record["status"] == "failed" and "server went away" in record["error"]
    assert "verdict" not in record
    assert not (tmp_path / "runs/one/report.md").exists()
    assert "error, no verdict: server went away" in capsys.readouterr().err


def test_unreachable_backend_stops_before_a_run_is_opened(
    tmp_path: Path, capsys
) -> None:
    # The real backend; port 1 on loopback has no listener.
    arguments = _arguments(tmp_path, True, "--base-url", "http://127.0.0.1:1")
    assert main(arguments) == 1
    assert not (tmp_path / "runs").exists()
    message = capsys.readouterr().err
    assert "error, no verdict" in message and "127.0.0.1:1" in message


def test_invalid_probes_stop_with_every_failure(tmp_path: Path, capsys) -> None:
    arguments = _arguments(tmp_path)
    (tmp_path / "probes/manifest.json").write_text("{}")
    factory = Factory()
    assert main(arguments, factory) == 1
    assert not (tmp_path / "runs").exists() and factory.built == []
    message = capsys.readouterr().err
    assert "reviewed_by_user" in message and "counts.queries" in message


def test_unreviewed_probes_need_the_draft_option(tmp_path: Path, capsys) -> None:
    factory = Factory()
    assert main(_arguments(tmp_path, False), factory) == 1
    assert not (tmp_path / "runs").exists() and factory.built == []
    assert "only a draft run" in capsys.readouterr().err


def test_run_id_must_be_a_directory_name(tmp_path: Path, capsys) -> None:
    arguments = _arguments(tmp_path) + ["--run-id", "../outside"]
    assert main(arguments, Factory()) == 1
    assert not (tmp_path / "outside").exists()
    assert "not a directory name" in capsys.readouterr().err
