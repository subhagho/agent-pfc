"""Embeddings from a local Ollama server.

Only loopback servers are accepted, and neither proxies nor redirects are
followed, so text is never sent off the machine.
"""

import http.client
import ipaddress
import json
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping, Sequence
from typing import Any
from urllib.parse import urlsplit

import numpy as np

from agent_pfc.embeddings.errors import EmbeddingBackendError
from agent_pfc.embeddings.protocol import (
    EncoderFingerprint,
    require_texts,
    vector_fault,
)

DEFAULT_BASE_URL = "http://127.0.0.1:11434"
SUPPORTED_DIMENSIONS = (256, 512, 1024)
MAX_BATCH = 32
# No instruction or template is added to the text.
TEXT_CONVENTION = "raw"

# (url, JSON payload for a POST or None for a GET) -> decoded JSON reply
Transport = Callable[[str, Mapping[str, Any] | None], Any]


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args: Any, **kwargs: Any) -> None:
        return None


def _http_transport(timeout: float) -> Transport:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect)

    def send(url: str, payload: Mapping[str, Any] | None) -> Any:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"}
        )
        with opener.open(request, timeout=timeout) as reply:
            return json.load(reply)

    return send


def _is_loopback(url: str) -> bool:
    parts = urlsplit(url)
    if parts.scheme != "http" or parts.hostname is None:
        return False
    if parts.hostname == "localhost":
        return True
    try:
        return ipaddress.ip_address(parts.hostname).is_loopback
    except ValueError:
        return False


class OllamaEmbedder:
    """An embedder pinned to one installed model digest and one dimension."""

    def __init__(
        self,
        model: str,
        model_digest: str,
        dimension: int,
        base_url: str = DEFAULT_BASE_URL,
        transport: Transport | None = None,
        timeout: float = 120.0,
    ) -> None:
        if dimension not in SUPPORTED_DIMENSIONS:
            raise ValueError(
                f"dimension {dimension} is not one of {SUPPORTED_DIMENSIONS}"
            )
        self._model = model
        self._base_url = base_url.rstrip("/")
        if not _is_loopback(self._base_url):
            raise self._error("the base URL is not a loopback http address")
        self._transport = transport or _http_transport(timeout)

        entry = self._installed_model()
        if entry.get("digest") != model_digest:
            raise self._error(
                f"installed digest {entry.get('digest')} differs from "
                f"configured digest {model_digest}"
            )
        version = self._request("/api/version").get("version")
        quantization = (entry.get("details") or {}).get("quantization_level")
        if not version or not quantization:
            raise self._error("the server reports no version or quantization")
        self.fingerprint = EncoderFingerprint(
            model_name=model,
            model_digest=model_digest,
            quantization=quantization,
            backend_name="ollama",
            backend_version=version,
            dimension=dimension,
            text_convention=TEXT_CONVENTION,
            dtype="float32",
        )

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        require_texts(texts)
        rows = np.empty((len(texts), self.fingerprint.dimension), np.float32)
        for start in range(0, len(texts), MAX_BATCH):
            batch = list(texts[start : start + MAX_BATCH])
            rows[start : start + len(batch)] = self._encode_batch(batch)
        return rows

    def _encode_batch(self, batch: list[str]) -> list[np.ndarray]:
        reply = self._request(
            "/api/embed",
            {
                "model": self._model,
                "input": batch,
                "dimensions": self.fingerprint.dimension,
                # Fail on an over-long text instead of embedding part of it.
                "truncate": False,
            },
        )
        vectors = reply.get("embeddings")
        if not isinstance(vectors, list) or len(vectors) != len(batch):
            count = len(vectors) if isinstance(vectors, list) else "no"
            raise self._error(f"{count} vectors returned for {len(batch)} texts")
        rows = []
        for vector in vectors:
            try:
                row = np.asarray(vector, dtype=np.float32)
            except (TypeError, ValueError) as error:
                raise self._error("a vector is not a list of numbers") from error
            fault = vector_fault(row, self.fingerprint)
            if fault:
                raise self._error(f"bad vector: {fault}")
            rows.append(row)
        return rows

    def _installed_model(self) -> Mapping[str, Any]:
        models = self._request("/api/tags").get("models")
        for entry in models if isinstance(models, list) else []:
            if isinstance(entry, dict) and entry.get("name") == self._model:
                return entry
        raise self._error("the model is not in the local model list")

    def _request(
        self, path: str, payload: Mapping[str, Any] | None = None
    ) -> Mapping[str, Any]:
        try:
            reply = self._transport(f"{self._base_url}{path}", payload)
        except urllib.error.HTTPError as error:
            raise self._error(f"{path} answered HTTP {error.code}") from error
        except (OSError, http.client.HTTPException, ValueError) as error:
            raise self._error(f"{path} failed: {error}") from error
        if not isinstance(reply, dict):
            raise self._error(f"{path} returned no JSON object")
        return reply

    def _error(self, reason: str) -> EmbeddingBackendError:
        return EmbeddingBackendError(
            f"Ollama at {self._base_url}, model {self._model}: {reason}"
        )
