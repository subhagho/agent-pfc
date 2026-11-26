"""The embedder contract and the checks that enforce it."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

import numpy as np

UNIT_NORM_TOLERANCE = 1e-4


@dataclass(frozen=True)
class EncoderFingerprint:
    """Everything that can change the vector produced for a text."""

    model_name: str
    model_digest: str
    quantization: str
    backend_name: str
    backend_version: str
    dimension: int
    text_convention: str
    dtype: str


class Embedder(Protocol):
    @property
    def fingerprint(self) -> EncoderFingerprint: ...

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        """One float32 unit row per text, in input order, or nothing.

        Raises ValueError for an empty or whitespace-only text and
        EmbeddingBackendError when the backend cannot deliver every row.
        """
        ...


def require_texts(texts: Sequence[str]) -> None:
    for index, text in enumerate(texts):
        if not text.strip():
            raise ValueError(f"text {index} is empty or whitespace only")


def vector_fault(row: np.ndarray, fingerprint: EncoderFingerprint) -> str | None:
    """Why `row` is not a valid vector of this encoder, or None if it is."""
    if row.shape != (fingerprint.dimension,):
        return f"shape {row.shape}, expected ({fingerprint.dimension},)"
    if row.dtype != np.dtype(fingerprint.dtype):
        return f"dtype {row.dtype}, expected {fingerprint.dtype}"
    if not np.isfinite(row).all():
        return "non-finite values"
    norm = float(np.linalg.norm(row))
    if abs(norm - 1.0) > UNIT_NORM_TOLERANCE:
        return f"norm {norm:.6f}, expected 1"
    return None
