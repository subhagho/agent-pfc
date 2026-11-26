"""Choosing a variant on the select split and judging it on the confirm split.

Only the natural track counts.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from agent_pfc.domain import Method, PassCriterion, QueryTrack, Split
from agent_pfc.evaluation.results import CollapseResult

METHOD_ORDER = tuple(Method)


@dataclass(frozen=True)
class Verdict:
    criterion: PassCriterion
    select: CollapseResult
    confirm: CollapseResult
    passed: bool


def _preference(result: CollapseResult) -> tuple[float, float, int, int, float]:
    """Smaller is better."""
    return (
        -result.accuracy,
        -result.worst_pair,
        result.dimension,
        METHOD_ORDER.index(result.variant.method),
        result.variant.weight or 0.0,
    )


def choose(results: Sequence[CollapseResult]) -> CollapseResult:
    """The best natural-track result on the select split."""
    candidates = [
        r
        for r in results
        if r.split == Split.SELECT and r.track == QueryTrack.NATURAL
    ]
    if not candidates:
        raise ValueError("no natural-track results on the select split")
    return min(candidates, key=_preference)


def judge(results: Sequence[CollapseResult], criterion: PassCriterion) -> Verdict:
    chosen = choose(results)
    matching = [
        r
        for r in results
        if r.split == Split.CONFIRM
        and r.track == QueryTrack.NATURAL
        and (r.variant, r.dimension) == (chosen.variant, chosen.dimension)
    ]
    if len(matching) != 1:
        raise ValueError(
            f"expected one confirm result for the chosen variant, found {len(matching)}"
        )
    (confirm,) = matching
    return Verdict(
        criterion=criterion,
        select=chosen,
        confirm=confirm,
        passed=confirm.accuracy >= criterion.min_accuracy
        and confirm.worst_pair >= criterion.min_pairwise_accuracy,
    )
