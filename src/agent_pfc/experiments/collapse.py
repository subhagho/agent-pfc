"""The modality collapse run."""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

import numpy as np

from agent_pfc.composition.methods import compose
from agent_pfc.composition.rendering import stored_texts, symmetric_query_texts
from agent_pfc.domain import (
    Method,
    MethodVariant,
    ProbeOperation,
    ProbeQuery,
    ProbeSet,
    QueryTrack,
    Split,
)
from agent_pfc.embeddings.protocol import Embedder, EncoderFingerprint
from agent_pfc.evaluation.neutral import neutral_share
from agent_pfc.evaluation.ranking import score_queries
from agent_pfc.evaluation.results import CollapseResult, collapse_result
from agent_pfc.evaluation.verdict import Verdict, judge
from agent_pfc.experiments.config import RunConfig

# Embedded text -> its vector, for one dimension.
Vectors = Mapping[str, np.ndarray]


class HarnessError(RuntimeError):
    """The experiment itself is wrong, so its numbers mean nothing."""


class UnreviewedProbeSetError(ValueError):
    """Only a draft run may use a probe set the user has not reviewed."""


@dataclass(frozen=True)
class RunResult:
    config: RunConfig
    fingerprints: tuple[EncoderFingerprint, ...]
    probe_hashes: Mapping[str, str]
    probes_reviewed: bool
    draft: bool
    results: tuple[CollapseResult, ...]
    # None for a draft run, which states no verdict.
    verdict: Verdict | None


def run_collapse(
    probes: ProbeSet,
    embedders: Sequence[Embedder],
    config: RunConfig,
    draft: bool = False,
) -> RunResult:
    """Score every variant, track and split at every configured dimension.

    `embedders` holds one embedder per dimension, otherwise alike. Everything
    is checked before the first text is embedded.
    """
    if not (probes.reviewed_by_user or draft):
        raise UnreviewedProbeSetError(
            "the probe set is not reviewed by the user: only a draft run is allowed"
        )
    by_dimension = _by_dimension(embedders, config)
    results: list[CollapseResult] = []
    for dimension in config.dimensions:
        vectors = _embed(by_dimension[dimension], _texts(probes, config))
        for split in Split:
            results += _split_results(probes, config, dimension, split, vectors)
    return RunResult(
        config=config,
        fingerprints=tuple(by_dimension[d].fingerprint for d in config.dimensions),
        probe_hashes=dict(probes.file_hashes),
        probes_reviewed=probes.reviewed_by_user,
        draft=draft,
        results=tuple(results),
        verdict=None if draft else judge(results, config.criterion),
    )


def _by_dimension(
    embedders: Sequence[Embedder], config: RunConfig
) -> dict[int, Embedder]:
    by_dimension = {e.fingerprint.dimension: e for e in embedders}
    given = sorted(e.fingerprint.dimension for e in embedders)
    if given != sorted(config.dimensions):
        raise ValueError(
            f"embedders have dimensions {given}, the run needs "
            f"{sorted(config.dimensions)}"
        )
    encoders = {
        (
            f.model_name,
            f.model_digest,
            f.quantization,
            f.backend_name,
            f.backend_version,
            f.text_convention,
            f.dtype,
        )
        for f in (e.fingerprint for e in embedders)
    }
    if len(encoders) != 1:
        raise ValueError("embedders differ in more than their dimension")
    return by_dimension


def _texts(probes: ProbeSet, config: RunConfig) -> list[str]:
    """Every text the run needs, once each."""
    texts: list[str] = []
    for operation in probes.operations:
        texts.append(operation.concept)  # the neutral measure
        for variant in config.variants:
            texts += stored_texts(operation, variant)
    for query in probes.queries:
        texts.append(query.text)  # the natural track
        for variant in config.variants:
            texts += symmetric_query_texts(query, variant)
    return list(dict.fromkeys(texts))


def _embed(embedder: Embedder, texts: Sequence[str]) -> Vectors:
    return dict(zip(texts, embedder.encode(texts), strict=True))


def _split_results(
    probes: ProbeSet,
    config: RunConfig,
    dimension: int,
    split: Split,
    vectors: Vectors,
) -> list[CollapseResult]:
    operations = [o for o in probes.operations if o.split == split]
    concepts = {o.concept for o in operations}
    queries = [q for q in probes.queries if q.concept in concepts]
    concept_vectors = {concept: vectors[concept] for concept in sorted(concepts)}

    results = []
    for variant in config.variants:
        stored = {
            o.key: _composed(variant, o, stored_texts, vectors) for o in operations
        }
        neutral = neutral_share(concept_vectors, stored)
        query_vectors = {
            QueryTrack.NATURAL: [vectors[q.text] for q in queries],
            QueryTrack.SYMMETRIC: [
                _composed(variant, q, symmetric_query_texts, vectors) for q in queries
            ],
        }
        for track, rows in query_vectors.items():
            scored = score_queries(queries, np.stack(rows), stored)
            result = collapse_result(
                variant, dimension, track, split, scored, neutral
            )
            _check_control(result)
            results.append(result)
    return results


def _composed[Record: (ProbeOperation, ProbeQuery)](
    variant: MethodVariant,
    record: Record,
    render: Callable[[Record, MethodVariant], tuple[str, ...]],
    vectors: Vectors,
) -> np.ndarray:
    return compose(variant, [vectors[text] for text in render(record, variant)])


def _check_control(result: CollapseResult) -> None:
    """C5 sees only the concept, so it cannot tell any two modalities apart."""
    if result.variant.method != Method.C5:
        return
    ties = sum(row[-1] for row in result.confusion)
    if ties != result.query_count:
        raise HarnessError(
            f"the C5 control ranked {result.query_count - ties} of "
            f"{result.query_count} queries without a tie (dimension "
            f"{result.dimension}, {result.track} track, {result.split} split)"
        )
