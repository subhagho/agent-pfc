"""The result of one variant, dimension, track and split."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from agent_pfc.domain import MethodVariant, Modality, QueryTrack, Split
from agent_pfc.evaluation.margins import MarginSummary, summarize_margins
from agent_pfc.evaluation.ranking import (
    ScoredQuery,
    accuracy,
    confusion,
    pairwise_accuracy,
)


@dataclass(frozen=True)
class CollapseResult:
    variant: MethodVariant
    dimension: int
    track: QueryTrack
    split: Split
    query_count: int
    accuracy: float
    confusion: tuple[tuple[int, ...], ...]
    pairwise: Mapping[tuple[Modality, Modality], float]
    margins: MarginSummary
    neutral_share: float

    @property
    def worst_pair(self) -> float:
        return min(self.pairwise.values())


def collapse_result(
    variant: MethodVariant,
    dimension: int,
    track: QueryTrack,
    split: Split,
    scored: Sequence[ScoredQuery],
    neutral_share: float,
) -> CollapseResult:
    return CollapseResult(
        variant=variant,
        dimension=dimension,
        track=track,
        split=split,
        query_count=len(scored),
        accuracy=accuracy(scored),
        confusion=confusion(scored),
        pairwise=pairwise_accuracy(scored),
        margins=summarize_margins(scored),
        neutral_share=neutral_share,
    )
