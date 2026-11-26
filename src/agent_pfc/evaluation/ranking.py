"""Ranking the five modalities of a query's own concept."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from itertools import combinations

import numpy as np

from agent_pfc.domain import Modality, OperationKey, ProbeQuery

# Scores this close are a tie, and a tie is a wrong answer.
TIE_TOLERANCE = 1e-6
MODALITIES = tuple(Modality)
PAIRS = tuple(combinations(MODALITIES, 2))


@dataclass(frozen=True)
class ScoredQuery:
    query_id: str
    concept: str
    expected: Modality
    scores: Mapping[Modality, float]

    @property
    def predicted(self) -> Modality | None:
        """The single highest-scoring modality, or None if the top is tied."""
        top = max(self.scores.values())
        leaders = [m for m, s in self.scores.items() if top - s <= TIE_TOLERANCE]
        return leaders[0] if len(leaders) == 1 else None

    @property
    def correct(self) -> bool:
        return self.predicted == self.expected

    def beats(self, other: Modality) -> bool:
        return self.scores[self.expected] - self.scores[other] > TIE_TOLERANCE


def score_queries(
    queries: Sequence[ProbeQuery],
    query_vectors: np.ndarray,
    stored: Mapping[OperationKey, np.ndarray],
) -> tuple[ScoredQuery, ...]:
    """Cosine of each unit query vector with its concept's unit stored vectors."""
    if len(queries) != len(query_vectors):
        raise ValueError(f"{len(query_vectors)} vectors for {len(queries)} queries")
    return tuple(
        ScoredQuery(
            query_id=query.id,
            concept=query.concept,
            expected=query.modality,
            scores={
                modality: float(
                    np.dot(vector, stored[OperationKey(query.concept, modality)])
                )
                for modality in MODALITIES
            },
        )
        for query, vector in zip(queries, query_vectors)
    )


def accuracy(scored: Sequence[ScoredQuery]) -> float:
    if not scored:
        raise ValueError("no queries to score")
    return sum(query.correct for query in scored) / len(scored)


def confusion(scored: Sequence[ScoredQuery]) -> tuple[tuple[int, ...], ...]:
    """Counts by expected modality (row) and prediction (column).

    Rows and the first five columns follow MODALITIES; the sixth counts ties.
    """
    counts = np.zeros((len(MODALITIES), len(MODALITIES) + 1), int)
    for query in scored:
        predicted = query.predicted
        column = (
            len(MODALITIES) if predicted is None else MODALITIES.index(predicted)
        )
        counts[MODALITIES.index(query.expected), column] += 1
    return tuple(tuple(int(n) for n in row) for row in counts)


def pairwise_accuracy(
    scored: Sequence[ScoredQuery],
) -> dict[tuple[Modality, Modality], float]:
    """For each pair, how often a query of either one beats the other."""
    result = {}
    for first, second in PAIRS:
        outcomes = [
            query.beats(second if query.expected == first else first)
            for query in scored
            if query.expected in (first, second)
        ]
        if not outcomes:
            raise ValueError(f"no queries for the pair {first} and {second}")
        result[first, second] = sum(outcomes) / len(outcomes)
    return result
