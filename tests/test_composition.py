from dataclasses import replace

import numpy as np
import pytest

from agent_pfc.composition.methods import compose
from agent_pfc.composition.rendering import stored_texts, symmetric_query_texts
from agent_pfc.domain import (
    PHASE_BY_MODALITY,
    Method,
    MethodVariant,
    Modality,
    ProbeOperation,
    ProbeQuery,
    Split,
)

WEIGHTS = (0.25, 0.5, 0.75, 1.0)
RENDERED = (Method.C0, Method.C1, Method.C2, Method.C4, Method.C5)

OPERATION = ProbeOperation(
    concept="log",
    modality=Modality.PROHIBITED,
    phase=-1,
    phase_modality_text="must not",
    contextual_text="must not log it",
    split=Split.SELECT,
)
QUERY = ProbeQuery(
    id="q1",
    concept="log",
    modality=Modality.PROHIBITED,
    text="logging this is off limits",
    synonym_term="forbidden",
)

O = np.array([1.0, 0.0, 0.0], np.float32)
X = np.array([0.0, 0.6, 0.8], np.float32)


def _variant(method: Method, weight: float = 0.5) -> MethodVariant:
    weighted = method in (Method.C1, Method.C2)
    return MethodVariant(method, weight if weighted else None)


def _unit(vector: np.ndarray) -> np.ndarray:
    return vector / np.linalg.norm(vector)


def test_stored_texts_per_method() -> None:
    texts = {m: stored_texts(OPERATION, _variant(m)) for m in RENDERED}
    assert texts == {
        Method.C0: ("must not log it",),
        Method.C1: ("log", "must not"),
        Method.C2: ("log", "must not log it"),
        Method.C4: ("Operation: log; Phase: -1; Modality: must not",),
        Method.C5: ("log",),
    }
    positive = replace(OPERATION, phase=2)
    assert "Phase: +2;" in stored_texts(positive, _variant(Method.C4))[0]


@pytest.mark.parametrize("method", [Method.C0, Method.C4, Method.C5])
def test_unweighted_formula(method: Method) -> None:
    result = compose(MethodVariant(method), [X])
    np.testing.assert_allclose(result, X, atol=1e-7)
    assert result.dtype == np.float32


@pytest.mark.parametrize("weight", WEIGHTS)
def test_weighted_formulas(weight: float) -> None:
    additive = compose(MethodVariant(Method.C1, weight), [O, X])
    np.testing.assert_allclose(additive, _unit(O + weight * X), atol=1e-7)

    interpolated = compose(MethodVariant(Method.C2, weight), [O, X])
    np.testing.assert_allclose(
        interpolated, _unit((1 - weight) * O + weight * X), atol=1e-7
    )
    assert additive.dtype == interpolated.dtype == np.float32
    assert (additive >= 0).all() and (interpolated >= 0).all()


def test_interpolation_at_one_equals_direct_contextual() -> None:
    interpolated = compose(MethodVariant(Method.C2, 1.0), [O, X])
    np.testing.assert_allclose(
        interpolated, compose(MethodVariant(Method.C0), [X]), atol=1e-7
    )


@pytest.mark.parametrize(
    ("variant", "vectors"),
    [
        (MethodVariant(Method.C1, 1.0), [O, -O]),
        (MethodVariant(Method.C2, 0.5), [O, -O]),
        (MethodVariant(Method.C0), [O * 1e-13]),
        (MethodVariant(Method.C5), [O * np.nan]),
    ],
)
def test_zero_norm_is_rejected(variant, vectors) -> None:
    with pytest.raises(ValueError) as caught:
        compose(variant, vectors)
    message = str(caught.value)
    assert variant.method in message and str(variant.weight) in message


@pytest.mark.parametrize(
    "variant",
    [
        MethodVariant(Method.C1),
        MethodVariant(Method.C1, -0.5),
        MethodVariant(Method.C2, 1.5),
        MethodVariant(Method.C0, 0.5),
        MethodVariant(Method.C3, 0.5),
    ],
)
def test_weights_that_negate_or_do_not_apply_are_rejected(variant) -> None:
    with pytest.raises(ValueError, match="cannot be composed"):
        compose(variant, [O, X])


def test_wrong_vector_count_and_unrendered_method_are_rejected() -> None:
    with pytest.raises(ValueError, match="takes 2"):
        compose(MethodVariant(Method.C1, 0.5), [O])
    with pytest.raises(ValueError, match="not rendered"):
        stored_texts(OPERATION, MethodVariant(Method.C3, 0.5))
    with pytest.raises(ValueError, match="not rendered"):
        symmetric_query_texts(QUERY, MethodVariant(Method.C3, 0.5))


def test_symmetric_query_texts_per_method() -> None:
    texts = {m: symmetric_query_texts(QUERY, _variant(m)) for m in RENDERED}
    assert texts == {
        Method.C0: ("logging this is off limits",),
        Method.C1: ("log", "forbidden"),
        Method.C2: ("log", "logging this is off limits"),
        Method.C4: ("Operation: log; Modality: forbidden",),
        Method.C5: ("log",),
    }
    assert "Phase" not in texts[Method.C4][0]


@pytest.mark.parametrize("method", RENDERED)
def test_symmetric_query_never_depends_on_expected_modality(method: Method) -> None:
    variant = _variant(method)
    texts = {
        symmetric_query_texts(replace(QUERY, modality=modality), variant)
        for modality in Modality
    }
    assert len(texts) == 1
    ((rendered),) = texts
    for text in rendered:
        assert not any(modality.value in text for modality in Modality)
        assert not any(f"{phase:+d}" in text for phase in PHASE_BY_MODALITY.values())


@pytest.mark.parametrize("method", RENDERED)
def test_symmetric_query_and_stored_operation_take_as_many_vectors(method) -> None:
    variant = _variant(method)
    assert len(symmetric_query_texts(QUERY, variant)) == len(
        stored_texts(OPERATION, variant)
    )
