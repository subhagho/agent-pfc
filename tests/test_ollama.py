import urllib.error
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from agent_pfc.embeddings.cache import CachedEmbedder
from agent_pfc.embeddings.errors import EmbeddingBackendError
from agent_pfc.embeddings.ollama import OllamaEmbedder

MODEL = "model:tag"
DIGEST = "abc123"


def _vector(text: str, dimension: int) -> list[float]:
    """A unit vector that names its text: one hot at the number in the text."""
    row = [0.0] * dimension
    row[int(text.removeprefix("t")) % dimension] = 1.0
    return row


class StubServer:
    def __init__(self) -> None:
        self.batches: list[list[str]] = []
        self.payloads: list[Mapping[str, Any]] = []
        self.urls: list[str] = []
        self.models: list[dict[str, Any]] = [
            {
                "name": MODEL,
                "digest": DIGEST,
                "details": {"quantization_level": "Q8_0"},
            }
        ]
        self.reply = lambda vectors: {"embeddings": vectors}

    def __call__(self, url: str, payload: Mapping[str, Any] | None) -> Any:
        self.urls.append(url)
        if url.endswith("/api/tags"):
            return {"models": self.models}
        if url.endswith("/api/version"):
            return {"version": "9.9"}
        assert payload is not None
        self.payloads.append(payload)
        self.batches.append(payload["input"])
        return self.reply([_vector(t, payload["dimensions"]) for t in payload["input"]])


def _embedder(server, **overrides: Any) -> OllamaEmbedder:
    settings: dict[str, Any] = {
        "model": MODEL,
        "model_digest": DIGEST,
        "dimension": 256,
        "transport": server,
    }
    return OllamaEmbedder(**{**settings, **overrides})


def test_batches_keep_order() -> None:
    server = StubServer()
    texts = [f"t{i}" for i in range(70)]
    rows = _embedder(server).encode(texts)

    assert [len(b) for b in server.batches] == [32, 32, 6]
    assert [t for b in server.batches for t in b] == texts
    assert rows.shape == (70, 256) and rows.dtype == np.float32
    assert rows.argmax(axis=1).tolist() == list(range(70))
    assert all(p["truncate"] is False and p["dimensions"] == 256 for p in server.payloads)


def test_fingerprint_comes_from_the_server() -> None:
    fingerprint = _embedder(StubServer()).fingerprint
    assert (fingerprint.model_digest, fingerprint.quantization) == (DIGEST, "Q8_0")
    assert (fingerprint.backend_name, fingerprint.backend_version) == ("ollama", "9.9")
    assert fingerprint.dimension == 256


def _spoil_last(change):
    return lambda vectors: {"embeddings": vectors[:-1] + [change(vectors[-1])]}


BAD_REPLIES = {
    "missing": lambda v: {"embeddings": v[:-1]},
    "extra": lambda v: {"embeddings": v + v[:1]},
    "no-field": lambda v: {},
    "not-object": lambda v: v,
    "wrong-size": _spoil_last(lambda row: row[:-1]),
    "nan": _spoil_last(lambda row: [float("nan")] + row[1:]),
    "infinite": _spoil_last(lambda row: [float("inf")] + row[1:]),
    "zero": _spoil_last(lambda row: [0.0] * len(row)),
    "not-unit": _spoil_last(lambda row: [2 * x for x in row]),
    "not-numbers": _spoil_last(lambda row: ["x"] * len(row)),
}


@pytest.mark.parametrize("reply", BAD_REPLIES.values(), ids=BAD_REPLIES.keys())
def test_bad_response_is_rejected(reply) -> None:
    server = StubServer()
    embedder = _embedder(server)
    server.reply = reply
    with pytest.raises(EmbeddingBackendError, match=MODEL):
        embedder.encode(["t1", "t2"])


def test_late_bad_batch_gives_no_result_and_no_cache(tmp_path: Path) -> None:
    server = StubServer()
    cached = CachedEmbedder(_embedder(server), tmp_path)

    def reply(vectors):
        return {"embeddings": vectors if len(server.batches) == 1 else []}

    server.reply = reply
    with pytest.raises(EmbeddingBackendError):
        cached.encode([f"t{i}" for i in range(40)])
    assert len(server.batches) == 2
    assert list(tmp_path.iterdir()) == []


def test_digest_mismatch_stops_before_encoding() -> None:
    server = StubServer()
    with pytest.raises(EmbeddingBackendError) as caught:
        _embedder(server, model_digest="other")
    assert DIGEST in str(caught.value) and "other" in str(caught.value)
    assert server.batches == []


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com:11434",
        "http://10.0.0.5:11434",
        "http://127.0.0.1.example.com",
        "http://127.0.0.1@example.com",
        "https://127.0.0.1:11434",
        "127.0.0.1:11434",
    ],
)
def test_non_loopback_url_is_rejected_without_a_request(url: str) -> None:
    server = StubServer()
    with pytest.raises(EmbeddingBackendError, match="loopback"):
        _embedder(server, base_url=url)
    assert server.urls == []


@pytest.mark.parametrize(
    "url", ["http://localhost:11434", "http://127.0.0.2", "http://[::1]:11434/"]
)
def test_loopback_url_is_accepted(url: str) -> None:
    _embedder(StubServer(), base_url=url)


@pytest.mark.parametrize(
    "failure",
    [
        urllib.error.URLError("connection refused"),
        urllib.error.HTTPError("u", 500, "boom", None, None),  # type: ignore[arg-type]
        TimeoutError("timed out"),
        ValueError("not JSON"),
    ],
    ids=["unreachable", "status", "timeout", "bad-json"],
)
def test_transport_failure_names_endpoint_and_model(failure: Exception) -> None:
    def server(url: str, payload: Any) -> Any:
        raise failure

    with pytest.raises(EmbeddingBackendError) as caught:
        _embedder(server)
    assert "127.0.0.1:11434" in str(caught.value) and MODEL in str(caught.value)


def test_unreachable_server_over_real_http() -> None:
    # Port 1 on loopback has no listener.
    with pytest.raises(EmbeddingBackendError, match="127.0.0.1:1,"):
        OllamaEmbedder(MODEL, DIGEST, 256, base_url="http://127.0.0.1:1", timeout=2)


def test_missing_model_names_endpoint_and_model() -> None:
    server = StubServer()
    server.models = []
    with pytest.raises(EmbeddingBackendError) as caught:
        _embedder(server)
    message = str(caught.value)
    assert "127.0.0.1:11434" in message and MODEL in message
    assert "not in the local model list" in message


def test_unsupported_dimension_and_empty_text_are_rejected() -> None:
    server = StubServer()
    with pytest.raises(ValueError, match="dimension"):
        _embedder(server, dimension=300)
    with pytest.raises(ValueError, match="empty"):
        _embedder(server).encode(["t1", " "])
    assert server.batches == []
