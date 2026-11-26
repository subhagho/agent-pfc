import os
from collections.abc import Sequence
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from fake_embedder import FakeEmbedder, fake_fingerprint

from agent_pfc.embeddings.cache import CachedEmbedder, cache_key
from agent_pfc.embeddings.errors import EmbeddingBackendError


def test_cache_key_changes_with_fingerprint_and_text() -> None:
    base = fake_fingerprint()
    key = cache_key(base, "text")
    assert key == cache_key(fake_fingerprint(), "text")
    assert cache_key(base, "other") != key
    for name, value in asdict(base).items():
        change: dict[str, Any] = {
            name: value + 1 if isinstance(value, int) else f"{value}x"
        }
        assert cache_key(replace(base, **change), "text") != key, name


def test_stored_entry_is_reused(tmp_path: Path) -> None:
    inner = FakeEmbedder()
    first = CachedEmbedder(inner, tmp_path).encode(["a", "b"])
    second = CachedEmbedder(inner, tmp_path).encode(["b", "a"])
    assert inner.calls == [["a", "b"]]
    np.testing.assert_array_equal(second, first[::-1])


def _truncate(path: Path) -> None:
    path.write_bytes(path.read_bytes()[:-8])


def _save(array: np.ndarray):
    return lambda path: np.save(path, array)


@pytest.mark.parametrize(
    "corrupt",
    [
        _truncate,
        lambda path: path.write_bytes(b""),
        lambda path: path.write_bytes(b"not an array"),
        lambda path: path.write_bytes(b"PK\x03\x04broken"),
        _save(np.ones(3, np.float32)),
        _save(np.eye(8)[0]),  # float64
        _save(np.full(8, np.nan, np.float32)),
        _save(np.zeros(8, np.float32)),
    ],
    ids=["truncated", "empty", "garbage", "zip", "shape", "dtype", "nan", "zero"],
)
def test_corrupt_entry_is_encoded_again(tmp_path: Path, corrupt) -> None:
    inner = FakeEmbedder()
    cached = CachedEmbedder(inner, tmp_path)
    expected = cached.encode(["a"])
    entry = tmp_path / f"{cache_key(inner.fingerprint, 'a')}.npy"
    corrupt(entry)

    np.testing.assert_array_equal(cached.encode(["a"]), expected)
    assert inner.calls == [["a"], ["a"]]
    np.testing.assert_array_equal(np.load(entry), expected[0])


def test_entry_is_renamed_into_place(tmp_path: Path, monkeypatch) -> None:
    renames: list[tuple[Path, Path]] = []

    def fail(source: Path, target: Path) -> None:
        renames.append((Path(source), Path(target)))
        raise OSError("disk full")

    monkeypatch.setattr(os, "replace", fail)
    with pytest.raises(OSError, match="disk full"):
        CachedEmbedder(FakeEmbedder(), tmp_path).encode(["a"])

    ((source, target),) = renames
    assert source.suffix == ".tmp" and target.suffix == ".npy"
    assert source.parent == target.parent == tmp_path
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("text", ["", "   ", "\n\t"])
def test_empty_input_is_rejected(tmp_path: Path, text: str) -> None:
    inner = FakeEmbedder()
    with pytest.raises(ValueError, match="text 1"):
        CachedEmbedder(inner, tmp_path).encode(["a", text])
    assert inner.calls == []
    assert list(tmp_path.iterdir()) == []


def test_duplicate_inputs_return_identical_rows_in_order(tmp_path: Path) -> None:
    inner = FakeEmbedder()
    rows = CachedEmbedder(inner, tmp_path).encode(["b", "a", "b"])
    assert inner.calls == [["b", "a"]]
    np.testing.assert_array_equal(rows, FakeEmbedder().encode(["b", "a", "b"]))
    np.testing.assert_array_equal(rows[0], rows[2])


def test_no_texts_give_no_rows(tmp_path: Path) -> None:
    rows = CachedEmbedder(FakeEmbedder(), tmp_path).encode([])
    assert rows.shape == (0, 8) and rows.dtype == np.float32


class _BadEmbedder(FakeEmbedder):
    def __init__(self, spoil) -> None:
        super().__init__()
        self._spoil = spoil

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        return self._spoil(super().encode(texts))


def _second_row_nan(rows: np.ndarray) -> np.ndarray:
    rows[1] = np.nan
    return rows


@pytest.mark.parametrize(
    "spoil",
    [_second_row_nan, lambda rows: rows[:1], lambda rows: rows[:, :4]],
    ids=["nan", "missing-row", "dimension"],
)
def test_bad_batch_is_not_cached(tmp_path: Path, spoil) -> None:
    with pytest.raises(EmbeddingBackendError):
        CachedEmbedder(_BadEmbedder(spoil), tmp_path).encode(["a", "b"])
    assert list(tmp_path.iterdir()) == []
