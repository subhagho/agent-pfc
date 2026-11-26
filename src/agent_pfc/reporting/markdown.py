"""The Markdown report of a completed run. Pure: it returns text."""

from collections.abc import Iterable, Sequence

from agent_pfc.domain import Method, MethodVariant, QueryTrack, Split
from agent_pfc.evaluation.ranking import MODALITIES
from agent_pfc.evaluation.results import CollapseResult
from agent_pfc.experiments.collapse import RunResult


def render_report(run_id: str, result: RunResult) -> str:
    title = f"# Modality collapse run {run_id}"
    sections = [
        f"{title} (DRAFT)" if result.draft else title,
        _verdict(result),
        _encoder(result),
        *(
            _summary(result.results, track, split)
            for track in QueryTrack
            for split in (Split.SELECT, Split.CONFIRM)
        ),
        _aliases(result),
        _details(result),
    ]
    return "\n\n".join(sections) + "\n"


def _name(variant: MethodVariant) -> str:
    if variant.weight is None:
        return variant.method.value
    return f"{variant.method.value} w={variant.weight:g}"


def _table(header: Sequence[str], rows: Iterable[Sequence[object]]) -> str:
    lines = [header, ["---"] * len(header), *rows]
    return "\n".join("| " + " | ".join(map(str, row)) + " |" for row in lines)


def _verdict(result: RunResult) -> str:
    criterion = result.config.criterion
    required = (
        f"Criterion, fixed before embedding: accuracy at least "
        f"{criterion.min_accuracy:.2f} and every modality pair at least "
        f"{criterion.min_pairwise_accuracy:.2f}, natural track."
    )
    verdict = result.verdict
    if verdict is None:
        reviewed = "" if result.probes_reviewed else " The probe set is unreviewed."
        return (
            f"## No verdict\n\nThis is a draft run and states no verdict."
            f"{reviewed}\n\n{required}"
        )
    chosen = verdict.confirm
    rows = [
        (r.split.value, f"{r.accuracy:.4f}", f"{r.worst_pair:.4f}", r.query_count)
        for r in (verdict.select, verdict.confirm)
    ]
    return "\n\n".join(
        [
            f"## Verdict: {'PASS' if verdict.passed else 'FAIL'}",
            required,
            f"Chosen on the select split: **{_name(chosen.variant)}** at dimension "
            f"{chosen.dimension}. The confirm row decides.",
            _table(("Split", "Accuracy", "Worst pair", "Queries"), rows),
        ]
    )


def _encoder(result: RunResult) -> str:
    first = result.fingerprints[0]
    dimensions = ", ".join(str(f.dimension) for f in result.fingerprints)
    rows = [
        ("Model", first.model_name),
        ("Digest", first.model_digest),
        ("Quantization", first.quantization),
        ("Backend", f"{first.backend_name} {first.backend_version}"),
        ("Dimensions", dimensions),
        ("Text convention", first.text_convention),
        ("Dtype", first.dtype),
        *((f"SHA-256 of {n}", d) for n, d in sorted(result.probe_hashes.items())),
    ]
    return "## Encoder and probes\n\n" + _table(("Setting", "Value"), rows)


def _summary(
    results: Sequence[CollapseResult], track: QueryTrack, split: Split
) -> str:
    note = " (diagnostic)" if track == QueryTrack.SYMMETRIC else ""
    rows = [
        (
            _name(r.variant),
            r.dimension,
            f"{r.accuracy:.4f}",
            f"{r.worst_pair:.4f}",
            f"{r.margins.mean:+.4f}",
            f"{r.margins.percentile_5:+.4f}",
            f"{r.margins.minimum:+.4f}",
            f"{r.neutral_share:.4f}",
        )
        for r in results
        if r.track == track and r.split == split
    ]
    header = (
        "Variant",
        "Dim",
        "Accuracy",
        "Worst pair",
        "Margin mean",
        "Margin p5",
        "Margin min",
        "Neutral top-5",
    )
    return f"## {track.value} track{note}, {split.value} split\n\n" + _table(
        header, rows
    )


def _aliases(result: RunResult) -> str:
    rows = [(_name(a), _name(b)) for a, b in result.config.aliases]
    return (
        "## Variants not computed separately\n\n"
        + _table(("Variant", "Identical to"), rows)
        + "\n\nC5 is the control: it must tie every query, and the run fails if not."
    )


def _details(result: RunResult) -> str:
    """Matrices for the chosen variant, or for the baseline in a draft run.

    `run.json` holds them for every result.
    """
    if result.verdict is None:
        variant = MethodVariant(Method.C0)
        dimension = max(result.config.dimensions)
        reason = "the direct contextual baseline, not a chosen variant"
    else:
        variant = result.verdict.confirm.variant
        dimension = result.verdict.confirm.dimension
        reason = "the chosen variant"
    parts = [
        f"## Detail: {_name(variant)} at dimension {dimension}\n\nShown for {reason}. "
        "`run.json` has the same detail for every result."
    ]
    parts += [
        _detail(r)
        for r in result.results
        if (r.variant, r.dimension) == (variant, dimension)
    ]
    return "\n\n".join(parts)


def _detail(result: CollapseResult) -> str:
    names = [m.value for m in MODALITIES]
    confusion = _table(
        ("Expected \\ predicted", *names, "tie"),
        [(name, *row) for name, row in zip(names, result.confusion)],
    )
    pairs = _table(
        ("Pair", "Accuracy"),
        [(f"{a} / {b}", f"{v:.4f}") for (a, b), v in result.pairwise.items()],
    )
    worst = _table(
        ("Query", "Concept", "Expected", "Best other", "Margin"),
        [
            (
                c.query_id,
                c.concept,
                c.expected.value,
                c.best_other.value,
                f"{c.margin:+.4f}",
            )
            for c in result.margins.worst
        ],
    )
    heading = f"### {result.track.value} track, {result.split.value} split"
    return "\n\n".join([heading, confusion, pairs, "Smallest margins:", worst])
