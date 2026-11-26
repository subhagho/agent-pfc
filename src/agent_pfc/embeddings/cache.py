"""A disk cache in front of any embedder."""

import hashlib
import json
import os
import tempfile
import zipfile
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path

import numpy as np

from agent_pfc.embeddings.errors import EmbeddingBackendError
from agent_pfc.embeddings.protocol import (
    Embedder,
    EncoderFingerprint,
    require_texts,
    vector_fault,
)


def cache_key(fingerprint: EncoderFingerprint, text: str) -> str:
    payload = json.dumps([asdict(fingerprint), text], sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class CachedEmbedder:
    """Serves stored vectors and asks the inner embedder only for the rest."""

    def __init__(self, inner: Embedder, directory: Path) -> None:
        self._inner = inner
        self._directory = directory

    @property
    def fingerprint(self) -> EncoderFingerprint:
        return self._inner.fingerprint

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        require_texts(texts)
        keys = [cache_key(self.fingerprint, text) for text in texts]
        rows: dict[str, np.ndarray] = {}
        missing: dict[str, str] = {}
        for key, text in zip(keys, texts):
            stored = self._read(key)
            if stored is None:
                missing[key] = text
            else:
                rows[key] = stored
        if missing:
            rows.update(self._encode_and_store(missing))
        if not keys:
            return np.empty((0, self.fingerprint.dimension), self.fingerprint.dtype)
        return np.stack([rows[key] for key in keys])

    def _encode_and_store(self, missing: dict[str, str]) -> dict[str, np.ndarray]:
        produced = self._inner.encode(list(missing.values()))
        if len(produced) != len(missing):
            raise EmbeddingBackendError(
                f"embedder returned {len(produced)} rows for {len(missing)} texts"
            )
        # Check every row before writing any, so a bad batch leaves no entry.
        for row in produced:
            fault = vector_fault(row, self.fingerprint)
            if fault:
                raise EmbeddingBackendError(f"embedder returned a bad vector: {fault}")
        rows = dict(zip(missing, produced))
        for key, row in rows.items():
            self._write(key, row)
        return rows

    def _path(self, key: str) -> Path:
        return self._directory / f"{key}.npy"

    def _read(self, key: str) -> np.ndarray | None:
        """The stored vector, or None if it is absent or unusable."""
        try:
            row = np.load(self._path(key), allow_pickle=False)
        except (OSError, ValueError, EOFError, zipfile.BadZipFile):
            return None
        if not isinstance(row, np.ndarray) or vector_fault(row, self.fingerprint):
            return None
        return row

    def _write(self, key: str, row: np.ndarray) -> None:
        self._directory.mkdir(parents=True, exist_ok=True)
        handle, name = tempfile.mkstemp(dir=self._directory, suffix=".tmp")
        temporary = Path(name)
        try:
            with os.fdopen(handle, "wb") as stream:
                np.save(stream, row, allow_pickle=False)
            os.replace(temporary, self._path(key))
        finally:
            temporary.unlink(missing_ok=True)
