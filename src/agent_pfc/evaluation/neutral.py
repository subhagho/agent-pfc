"""Whether a bare concept still finds all of its modalities."""

from collections.abc import Mapping

import numpy as np

from agent_pfc.domain import Modality, OperationKey

TOP = len(Modality)


def neutral_share(
    concept_vectors: Mapping[str, np.ndarray],
    stored: Mapping[OperationKey, np.ndarray],
) -> float:
    """Mean share of a concept's operations in the top five of all stored ones.

    On equal scores another concept's operation ranks first.
    """
    if not concept_vectors:
        raise ValueError("no concepts to score")
    keys = list(stored)
    matrix = np.stack([stored[key] for key in keys])
    shares = []
    for concept, vector in concept_vectors.items():
        scores = matrix @ vector
        ranked = sorted(
            zip(keys, scores),
            key=lambda item: (-item[1], item[0].concept == concept),
        )
        shares.append(sum(key.concept == concept for key, _ in ranked[:TOP]) / TOP)
    return sum(shares) / len(shares)
