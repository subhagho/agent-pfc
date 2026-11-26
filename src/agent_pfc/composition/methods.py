"""Pure vector arithmetic of the composition methods."""

from collections.abc import Sequence

import numpy as np

from agent_pfc.domain import Method, MethodVariant

MIN_NORM = 1e-12


def compose(variant: MethodVariant, vectors: Sequence[np.ndarray]) -> np.ndarray:
    """The unit float32 vector of `variant` from its embedded texts."""
    weights = _weights(variant)
    if len(vectors) != len(weights):
        raise ValueError(
            f"method {variant.method} takes {len(weights)} vectors, got {len(vectors)}"
        )
    total = sum(
        weight * np.asarray(vector, np.float64)
        for weight, vector in zip(weights, vectors)
    )
    norm = float(np.linalg.norm(total))
    if not norm > MIN_NORM:
        raise ValueError(
            f"method {variant.method} with weight {variant.weight} "
            f"cannot be normalized: norm {norm}"
        )
    return np.asarray(total / norm, np.float32)


def _weights(variant: MethodVariant) -> tuple[float, ...]:
    """The coefficient of each vector. None is negative: nothing is negated."""
    method, weight = variant.method, variant.weight
    match method:
        case Method.C1 if weight is not None and weight >= 0:
            return (1.0, weight)
        case Method.C2 if weight is not None and 0 <= weight <= 1:
            return (1.0 - weight, weight)
        case Method.C0 | Method.C4 | Method.C5 if weight is None:
            return (1.0,)
    raise ValueError(f"method {method} cannot be composed with weight {weight}")
