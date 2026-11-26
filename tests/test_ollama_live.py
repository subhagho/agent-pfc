"""Contract check against the real local model. Skipped if it is not there."""

import json
import urllib.request

import numpy as np
import pytest

from agent_pfc.embeddings.ollama import DEFAULT_BASE_URL, OllamaEmbedder

MODEL = "qwen3-embedding:0.6b"
DIGEST = "ac6da0dfba84a81fdbfbaf330198c33cd77c4cdfc53e8bc50eb581914a15621d"
# More than one batch of distinct texts.
TEXTS = [f"record the outcome of step {number}" for number in range(40)]


def _unavailable() -> str | None:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(f"{DEFAULT_BASE_URL}/api/tags", timeout=5) as reply:
            names = [model["name"] for model in json.load(reply)["models"]]
    except OSError as error:
        return f"Ollama is unavailable at {DEFAULT_BASE_URL}: {error}"
    return None if MODEL in names else f"model {MODEL} is not installed"


@pytest.mark.parametrize("dimension", [256, 512, 1024])
def test_live_unit_vectors_in_input_order(dimension: int) -> None:
    reason = _unavailable()
    if reason:
        pytest.skip(reason)
    embedder = OllamaEmbedder(MODEL, DIGEST, dimension)
    rows = embedder.encode(TEXTS)

    assert rows.shape == (len(TEXTS), dimension) and rows.dtype == np.float32
    np.testing.assert_allclose(np.linalg.norm(rows, axis=1), 1.0, atol=1e-4)
    # Each row belongs to its own text, including across the batch boundary.
    for index in (0, 31, 32, 39):
        alone = embedder.encode([TEXTS[index]])[0]
        similarity = rows @ alone
        assert int(similarity.argmax()) == index
        assert similarity[index] > 0.999
