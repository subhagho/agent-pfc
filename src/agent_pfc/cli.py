"""The command line: builds the parts and hands them to each other."""

import argparse
import sys
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path

from agent_pfc.embeddings.cache import CachedEmbedder
from agent_pfc.embeddings.errors import EmbeddingBackendError
from agent_pfc.embeddings.ollama import DEFAULT_BASE_URL, OllamaEmbedder
from agent_pfc.embeddings.protocol import Embedder
from agent_pfc.experiments.collapse import (
    HarnessError,
    require_runnable,
    run_collapse,
)
from agent_pfc.experiments.config import RunConfig
from agent_pfc.probes.loading import load_probe_set
from agent_pfc.reporting.run_record import RunExistsError, RunRecord

DEFAULT_MODEL = "qwen3-embedding:0.6b"
DEFAULT_DIGEST = "ac6da0dfba84a81fdbfbaf330198c33cd77c4cdfc53e8bc50eb581914a15621d"
DEFAULT_PROBES = Path("data/probes/modality_collapse_v1")
RUN_ERRORS = (EmbeddingBackendError, HarnessError, OSError, ValueError)

# (parsed arguments, dimension) -> the embedder for that dimension
EmbedderFactory = Callable[[argparse.Namespace, int], Embedder]


def _cached_ollama(arguments: argparse.Namespace, dimension: int) -> Embedder:
    backend = OllamaEmbedder(
        arguments.model, arguments.model_digest, dimension, arguments.base_url
    )
    return CachedEmbedder(backend, arguments.cache)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent-pfc")
    commands = parser.add_subparsers(dest="command", required=True)
    collapse = commands.add_parser(
        "collapse", help="test whether operation modalities collapse"
    )
    collapse.add_argument("--probes", type=Path, default=DEFAULT_PROBES)
    collapse.add_argument("--runs", type=Path, default=Path("runs"))
    collapse.add_argument("--cache", type=Path, default=Path("runs/cache"))
    collapse.add_argument("--run-id", help="directory name under --runs")
    collapse.add_argument(
        "--draft", action="store_true", help="state no verdict; allow unreviewed probes"
    )
    collapse.add_argument("--model", default=DEFAULT_MODEL)
    collapse.add_argument("--model-digest", default=DEFAULT_DIGEST)
    collapse.add_argument("--base-url", default=DEFAULT_BASE_URL)
    return parser


def main(
    argv: Sequence[str] | None = None,
    build_embedder: EmbedderFactory = _cached_ollama,
) -> int:
    arguments = _parser().parse_args(argv)
    run_id = arguments.run_id or f"collapse-{datetime.now(UTC):%Y%m%dT%H%M%SZ}"
    config = RunConfig()
    try:
        probes = load_probe_set(arguments.probes)
        require_runnable(probes, arguments.draft)
        embedders = [build_embedder(arguments, d) for d in config.dimensions]
        record = RunRecord.open(arguments.runs, run_id, config, arguments.draft)
    except (RunExistsError, *RUN_ERRORS) as error:
        return _stop(error)

    try:
        result = run_collapse(probes, embedders, config, arguments.draft)
        record.complete(result)
    except RUN_ERRORS as error:
        record.fail(f"{type(error).__name__}: {error}")
        return _stop(error)

    if result.verdict is None:
        outcome = "draft run, no verdict"
    else:
        outcome = f"verdict: {'PASS' if result.verdict.passed else 'FAIL'}"
    print(f"{outcome}\nreport: {record.report_path}")
    return 0


def _stop(error: Exception) -> int:
    print(f"error, no verdict: {error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
