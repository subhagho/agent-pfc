from dataclasses import replace

import numpy as np
import pytest

from agent_pfc.domain import (
    Method,
    MethodVariant,
    Modality,
    OperationKey,
    PassCriterion,
    ProbeQuery,
    QueryTrack,
    Split,
)
from agent_pfc.evaluation.margins import summarize_margins
from agent_pfc.evaluation.neutral import neutral_share
from agent_pfc.evaluation.ranking import (
    MODALITIES,
    PAIRS,
    ScoredQuery,
    accuracy,
    confusion,
    pairwise_accuracy,
    score_queries,
)
from agent_pfc.evaluation.results import CollapseResult, collapse_result
from agent_pfc.evaluation.verdict import choose, judge

REQ, STRICT, PERM, NOT_REQ, PROHIB = MODALITIES


def _scored(query_id: str, expected: Modality, *scores: float) -> ScoredQuery:
    return ScoredQuery(query_id, "log", expected, dict(zip(MODALITIES, scores)))


# One query per modality, with the outcome worked out by hand.
EXAMPLE = (
    _scored("right", REQ, 0.9, 0.5, 0.4, 0.3, 0.2),
    _scored("wrong", STRICT, 0.8, 0.6, 0.1, 0.1, 0.1),  # predicts required
    _scored("own-tie", PERM, 0.1, 0.1, 0.7, 0.7 + 5e-7, 0.1),
    _scored("other-tie", NOT_REQ, 0.9, 0.9, 0.1, 0.5, 0.1),
    _scored("just-ahead", PROHIB, 0.5, 0.1, 0.1, 0.1, 0.5 + 2e-6),
)


def test_ranking_and_ties() -> None:
    assert [q.predicted for q in EXAMPLE] == [REQ, REQ, None, None, PROHIB]
    assert [q.correct for q in EXAMPLE] == [True, False, False, False, True]
    assert accuracy(EXAMPLE) == pytest.approx(2 / 5)


def test_confusion_matrix_has_a_tie_column() -> None:
    assert confusion(EXAMPLE) == (
        (1, 0, 0, 0, 0, 0),
        (1, 0, 0, 0, 0, 0),
        (0, 0, 0, 0, 0, 1),
        (0, 0, 0, 0, 0, 1),
        (0, 0, 0, 0, 1, 0),
    )


def test_pairwise_accuracy_over_ten_pairs() -> None:
    pairs = pairwise_accuracy(EXAMPLE)
    assert len(pairs) == len(PAIRS) == 10
    assert pairs == {
        (REQ, STRICT): 0.5,  # the strict query loses to required
        (REQ, PERM): 1.0,
        (REQ, NOT_REQ): 0.5,  # the not_required query loses to required
        (REQ, PROHIB): 1.0,
        (STRICT, PERM): 1.0,
        (STRICT, NOT_REQ): 0.5,
        (STRICT, PROHIB): 1.0,
        (PERM, NOT_REQ): 0.5,  # the permitted query ties with not_required
        (PERM, PROHIB): 1.0,
        (NOT_REQ, PROHIB): 1.0,
    }


def test_pair_without_queries_is_an_error() -> None:
    only_two = EXAMPLE[:2]
    with pytest.raises(ValueError, match="no queries for the pair"):
        pairwise_accuracy(only_two)
    for empty in (accuracy, summarize_margins, pairwise_accuracy):
        with pytest.raises(ValueError):
            empty(())


def test_margins_and_worst_cases() -> None:
    margins = summarize_margins(EXAMPLE, worst_count=2)
    expected = [0.4, -0.2, -5e-7, -0.4, 2e-6]
    assert margins.mean == pytest.approx(np.mean(expected))
    assert margins.minimum == pytest.approx(-0.4)
    # Sorted: -0.4, -0.2, ...; the 5th percentile is a fifth of the way up.
    assert margins.percentile_5 == pytest.approx(-0.36)
    assert [c.query_id for c in margins.worst] == ["other-tie", "wrong"]
    assert margins.worst[1].best_other == REQ


def test_score_queries_uses_the_query_concept() -> None:
    basis = np.eye(10, dtype=np.float32)
    stored = {
        OperationKey(concept, modality): basis[5 * c + m]
        for c, concept in enumerate(("log", "retry"))
        for m, modality in enumerate(MODALITIES)
    }
    query = ProbeQuery("q", "retry", PERM, "text", "term")
    (scored,) = score_queries([query], basis[[7]], stored)
    assert scored.scores == {m: float(m == PERM) for m in MODALITIES}
    with pytest.raises(ValueError, match="vectors for"):
        score_queries([query], basis[:2], stored)


def test_neutral_share() -> None:
    basis = np.eye(2, dtype=np.float32)
    stored = {OperationKey("a", m): basis[0] for m in MODALITIES}
    stored |= {OperationKey("b", m): basis[1] for m in MODALITIES}
    assert neutral_share({"a": basis[0], "b": basis[1]}, stored) == 1.0

    # Two of a's operations move to b's direction: a finds 3 of 5.
    stored[OperationKey("a", REQ)] = stored[OperationKey("a", PERM)] = basis[1]
    assert neutral_share({"a": basis[0]}, stored) == pytest.approx(3 / 5)
    # All equal: the other concept's five rank first.
    flat = {key: basis[0] for key in stored}
    assert neutral_share({"a": basis[0]}, flat) == 0.0


def test_collapse_result_gathers_the_measures() -> None:
    result = collapse_result(
        MethodVariant(Method.C0), 256, QueryTrack.NATURAL, Split.SELECT, EXAMPLE, 0.5
    )
    assert (result.query_count, result.accuracy) == (5, pytest.approx(0.4))
    assert result.worst_pair == 0.5 and result.neutral_share == 0.5


BASE = collapse_result(
    MethodVariant(Method.C0), 256, QueryTrack.NATURAL, Split.SELECT, EXAMPLE, 0.5
)


def _result(
    method: Method = Method.C0,
    weight: float | None = None,
    dimension: int = 256,
    accuracy: float = 0.96,
    worst: float = 0.92,
    split: Split = Split.SELECT,
    track: QueryTrack = QueryTrack.NATURAL,
) -> CollapseResult:
    return replace(
        BASE,
        variant=MethodVariant(method, weight),
        dimension=dimension,
        accuracy=accuracy,
        pairwise={pair: worst if pair == PAIRS[0] else 1.0 for pair in PAIRS},
        split=split,
        track=track,
    )


@pytest.mark.parametrize(
    ("better", "worse"),
    [
        (_result(accuracy=0.97, worst=0.5, dimension=1024), _result()),
        (_result(worst=0.93, dimension=1024), _result()),
        (_result(Method.C4, dimension=256), _result(dimension=512)),
        (_result(Method.C1, 1.0), _result(Method.C2, 0.25)),
        (_result(Method.C1, 0.25), _result(Method.C1, 0.5)),
    ],
    ids=["accuracy", "worst-pair", "dimension", "method", "weight"],
)
def test_selection_order(better: CollapseResult, worse: CollapseResult) -> None:
    assert choose([worse, better]) == choose([better, worse]) == better


def test_selection_ignores_confirm_and_symmetric_results() -> None:
    chosen = _result()
    tempting = [
        _result(Method.C1, 0.5, accuracy=1.0, split=Split.CONFIRM),
        _result(Method.C4, accuracy=1.0, track=QueryTrack.SYMMETRIC),
    ]
    assert choose([*tempting, chosen]) == chosen
    with pytest.raises(ValueError, match="select split"):
        choose(tempting)


@pytest.mark.parametrize(
    ("accuracy", "worst", "passed"),
    [
        (0.95, 0.90, True),
        (285 / 300, 54 / 60, True),
        (0.949, 1.0, False),
        (1.0, 0.899, False),
    ],
)
def test_verdict_uses_the_chosen_variant_on_confirm(accuracy, worst, passed) -> None:
    criterion = PassCriterion(0.95, 0.90)
    chosen = _result(accuracy=0.99)
    confirm = _result(accuracy=accuracy, worst=worst, split=Split.CONFIRM)
    others = [
        _result(Method.C1, 0.5, accuracy=0.5),
        # A perfect confirm result of a variant that was not chosen.
        _result(Method.C1, 0.5, accuracy=1.0, worst=1.0, split=Split.CONFIRM),
        _result(accuracy=1.0, worst=1.0, split=Split.CONFIRM, dimension=512),
        _result(
            accuracy=1.0, split=Split.CONFIRM, track=QueryTrack.SYMMETRIC
        ),
    ]
    verdict = judge([chosen, confirm, *others], criterion)
    assert (verdict.select, verdict.confirm, verdict.passed) == (chosen, confirm, passed)
    assert verdict.criterion == criterion


def test_verdict_needs_one_confirm_result() -> None:
    with pytest.raises(ValueError, match="found 0"):
        judge([_result()], PassCriterion(0.95, 0.90))
