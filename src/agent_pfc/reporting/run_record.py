"""The directory of one run: `run.json` and, once completed, `report.md`.

The configuration and criterion are written when the run is opened, before
anything is embedded. A directory that exists is never reused.
"""

import json
import os
from collections.abc import Mapping
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agent_pfc.domain import MethodVariant
from agent_pfc.evaluation.ranking import MODALITIES
from agent_pfc.evaluation.results import CollapseResult
from agent_pfc.experiments.collapse import RunResult
from agent_pfc.experiments.config import RunConfig
from agent_pfc.reporting.markdown import render_report

RECORD_FILE = "run.json"
REPORT_FILE = "report.md"


class RunExistsError(RuntimeError):
    """The run directory is already there."""


class RunRecord:
    def __init__(self, directory: Path, record: dict[str, Any]) -> None:
        self.directory = directory
        self._record = record

    @classmethod
    def open(
        cls, runs_directory: Path, run_id: str, config: RunConfig, draft: bool
    ) -> "RunRecord":
        if run_id != Path(run_id).name or run_id in ("", ".", ".."):
            raise ValueError(f"run id {run_id!r} is not a directory name")
        directory = runs_directory / run_id
        try:
            directory.mkdir(parents=True, exist_ok=False)
        except FileExistsError as error:
            raise RunExistsError(
                f"{directory} already exists; earlier results are never replaced"
            ) from error
        record = cls(
            directory,
            {
                "run_id": run_id,
                "status": "started",
                "started_at": _now(),
                "draft": draft,
                "criterion": asdict(config.criterion),
                "weights": list(config.weights),
                "dimensions": list(config.dimensions),
                "variants": [_variant(v) for v in config.variants],
                "aliases": [
                    {"name": _variant(name), "same_as": _variant(computed)}
                    for name, computed in config.aliases
                ],
            },
        )
        record._save()
        return record

    @property
    def report_path(self) -> Path:
        return self.directory / REPORT_FILE

    def complete(self, result: RunResult) -> None:
        verdict = result.verdict
        self._record |= {
            "status": "completed",
            "finished_at": _now(),
            "encoders": [asdict(f) for f in result.fingerprints],
            "probes": {
                "reviewed_by_user": result.probes_reviewed,
                "sha256": dict(result.probe_hashes),
            },
            "modalities": [m.value for m in MODALITIES],
            "results": [_result(r) for r in result.results],
            "verdict": None
            if verdict is None
            else {
                "passed": verdict.passed,
                "variant": _variant(verdict.confirm.variant),
                "dimension": verdict.confirm.dimension,
                "select": _result(verdict.select),
                "confirm": _result(verdict.confirm),
            },
        }
        _write(self.report_path, render_report(self._record["run_id"], result))
        self._save()

    def fail(self, reason: str) -> None:
        self._record |= {"status": "failed", "finished_at": _now(), "error": reason}
        self._save()

    def _save(self) -> None:
        text = json.dumps(self._record, indent=2) + "\n"
        _write(self.directory / RECORD_FILE, text)


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _write(path: Path, text: str) -> None:
    temporary = path.with_name(f"{path.name}.tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def _variant(variant: MethodVariant) -> Mapping[str, Any]:
    return {"method": variant.method.value, "weight": variant.weight}


def _result(result: CollapseResult) -> dict[str, Any]:
    margins = result.margins
    return {
        "variant": _variant(result.variant),
        "dimension": result.dimension,
        "track": result.track.value,
        "split": result.split.value,
        "query_count": result.query_count,
        "accuracy": result.accuracy,
        "worst_pair": result.worst_pair,
        # Rows are expected modalities; the extra last column counts ties.
        "confusion": [list(row) for row in result.confusion],
        "pairwise": [
            {"pair": [first.value, second.value], "accuracy": value}
            for (first, second), value in result.pairwise.items()
        ],
        "margins": {
            "mean": margins.mean,
            "minimum": margins.minimum,
            "percentile_5": margins.percentile_5,
            "worst": [asdict(case) for case in margins.worst],
        },
        "neutral_share": result.neutral_share,
    }
