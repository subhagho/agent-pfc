"""How far each query's own operation is ahead of the best other modality."""

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from agent_pfc.domain import Modality
from agent_pfc.evaluation.ranking import ScoredQuery

WORST_CASE_COUNT = 10


@dataclass(frozen=True)
class MarginCase:
    query_id: str
    concept: str
    expected: Modality
    best_other: Modality
    margin: float


@dataclass(frozen=True)
class MarginSummary:
    mean: float
    minimum: float
    percentile_5: float
    worst: tuple[MarginCase, ...]


def margin_case(query: ScoredQuery) -> MarginCase:
    others = {m: s for m, s in query.scores.items() if m != query.expected}
    best = max(others, key=others.__getitem__)
    return MarginCase(
        query_id=query.query_id,
        concept=query.concept,
        expected=query.expected,
        best_other=best,
        margin=query.scores[query.expected] - others[best],
    )


def summarize_margins(
    scored: Sequence[ScoredQuery], worst_count: int = WORST_CASE_COUNT
) -> MarginSummary:
    if not scored:
        raise ValueError("no queries to score")
    cases = sorted(map(margin_case, scored), key=lambda c: (c.margin, c.query_id))
    margins = np.array([case.margin for case in cases])
    return MarginSummary(
        mean=float(margins.mean()),
        minimum=float(margins.min()),
        percentile_5=float(np.percentile(margins, 5)),
        worst=tuple(cases[:worst_count]),
    )
