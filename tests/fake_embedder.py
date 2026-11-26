"""A deterministic embedder for offline tests. Its vectors carry no meaning."""

import hashlib
from collections.abc import Sequence

import numpy as np

from agent_pfc.embeddings.protocol import EncoderFingerprint, require_texts


def fake_fingerprint(dimension: int = 8) -> EncoderFingerprint:
    return EncoderFingerprint(
        model_name="fake",
        model_digest="digest",
        quantization="none",
        backend_name="fake",
        backend_version="1",
        dimension=dimension,
        text_convention="raw",
        dtype="float32",
    )


class FakeEmbedder:
    def __init__(self, dimension: int = 8) -> None:
        self.fingerprint = fake_fingerprint(dimension)
        self.calls: list[list[str]] = []

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        require_texts(texts)
        self.calls.append(list(texts))
        rows = np.empty((len(texts), self.fingerprint.dimension), np.float32)
        for index, text in enumerate(texts):
            seed = int.from_bytes(hashlib.sha256(text.encode()).digest()[:8])
            row = np.random.default_rng(seed).standard_normal(rows.shape[1])
            rows[index] = row / np.linalg.norm(row)
        return rows
