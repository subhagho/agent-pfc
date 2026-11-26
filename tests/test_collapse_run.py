from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import numpy as np
import pytest
from fake_embedder import FakeEmbedder
from probe_fixture import write_probe_set

from agent_pfc.domain import (
    Method,
    MethodVariant,
    PassCriterion,
    ProbeSet,
    QueryTrack,
    Split,
)
from agent_pfc.experiments import collapse
from agent_pfc.experiments.collapse import (
    HarnessError,
    RunResult,
    UnreviewedProbeSetError,
    run_collapse,
)
from agent_pfc.experiments.config import RunConfig
from agent_pfc.probes.loading import load_probe_set

CONFIG = RunConfig(dimensions=(64, 128))


def _probes(tmp_path: Path, reviewed: bool = False) -> ProbeSet:
    return load_probe_set(write_probe_set(tmp_path, reviewed=reviewed))


def _embedders(aliases: dict[str, str] | None = None) -> list[FakeEmbedder]:
    return [FakeEmbedder(d, aliases) for d in CONFIG.dimensions]


def _by_key(run: RunResult):
    return {(r.variant, r.dimension, r.track, r.split): r for r in run.results}


def test_default_config() -> None:
    config = RunConfig()
    assert config.criterion == PassCriterion(0.95, 0.90)
    assert config.dimensions == (256, 512, 1024)
    assert [(v.method, v.weight) for v in config.variants] == [
        (Method.C0, None),
        *((Method.C1, w) for w in (0.25, 0.5, 0.75, 1.0)),
        *((Method.C2, w) for w in (0.25, 0.5, 0.75)),
        (Method.C4, None),
        (Method.C5, None),
    ]
    with pytest.raises(FrozenInstanceError):
        config.criterion = PassCriterion(0.1, 0.1)  # type: ignore[misc]


def test_every_variant_track_split_and_dimension_once(tmp_path: Path) -> None:
    run = run_collapse(_probes(tmp_path), _embedders(), CONFIG, draft=True)
    expected = len(CONFIG.variants) * 2 * len(QueryTrack) * len(Split)
    assert len(run.results) == len(_by_key(run)) == expected
    assert all(r.query_count == 5 for r in run.results)
    assert run.config is CONFIG
    assert [f.dimension for f in run.fingerprints] == [64, 128]
    assert sorted(run.probe_hashes) == ["operations.jsonl", "queries.jsonl"]


def test_interpolation_at_one_and_c3_are_aliases(tmp_path: Path) -> None:
    run = run_collapse(_probes(tmp_path), _embedders(), CONFIG, draft=True)
    computed = {r.variant for r in run.results}
    names = dict(run.config.aliases)
    assert names[MethodVariant(Method.C2, 1.0)] == MethodVariant(Method.C0)
    for weight in CONFIG.weights:
        c3 = MethodVariant(Method.C3, weight)
        assert names[c3] == MethodVariant(Method.C1, weight)
    assert computed.isdisjoint(names)
    assert computed.issuperset(names.values())


def test_each_text_is_embedded_once_per_dimension(tmp_path: Path) -> None:
    embedders = _embedders()
    run_collapse(_probes(tmp_path), embedders, CONFIG, draft=True)
    for embedder in embedders:
        (call,) = embedder.calls
        assert len(call) == len(set(call))


def test_control_yields_all_ties(tmp_path: Path) -> None:
    run = run_collapse(_probes(tmp_path), _embedders(), CONFIG, draft=True)
    control = [r for r in run.results if r.variant.method == Method.C5]
    assert len(control) == 2 * len(QueryTrack) * len(Split)
    for result in control:
        assert result.accuracy == 0.0 and result.worst_pair == 0.0
        assert [row[-1] for row in result.confusion] == [1, 1, 1, 1, 1]


def test_control_that_separates_modalities_fails_the_run(
    tmp_path: Path, monkeypatch
) -> None:
    render = collapse.stored_texts

    def leaking(operation, variant):
        if variant.method == Method.C5:
            return (operation.contextual_text,)
        return render(operation, variant)

    monkeypatch.setattr(collapse, "stored_texts", leaking)
    probes = _probes(tmp_path)
    config = replace(CONFIG, dimensions=(64,))
    # The leaked texts are embedded because the run collects what it renders.
    with pytest.raises(HarnessError, match="C5 control"):
        run_collapse(probes, [FakeEmbedder(64)], config, draft=True)


def test_draft_run_states_no_verdict(tmp_path: Path) -> None:
    for reviewed in (False, True):
        probes = _probes(tmp_path / str(reviewed), reviewed)
        run = run_collapse(probes, _embedders(), CONFIG, draft=True)
        assert run.draft and run.verdict is None
        assert run.probes_reviewed is reviewed


def test_unreviewed_set_needs_the_draft_option(tmp_path: Path) -> None:
    embedders = _embedders()
    with pytest.raises(UnreviewedProbeSetError):
        run_collapse(_probes(tmp_path), embedders, CONFIG)
    assert all(e.calls == [] for e in embedders)


def _perfect_aliases(probes: ProbeSet) -> dict[str, str]:
    """Each query text gets the vector of its operation's contextual text."""
    stored = {o.key: o.contextual_text for o in probes.operations}
    return {q.text: stored[q.expected_key] for q in probes.queries}


@pytest.mark.parametrize(("separable", "passed"), [(True, True), (False, False)])
def test_reviewed_run_states_a_verdict(
    tmp_path: Path, separable: bool, passed: bool
) -> None:
    probes = _probes(tmp_path, reviewed=True)
    # Without aliases a fake vector says nothing about the text.
    aliases = _perfect_aliases(probes) if separable else None
    run = run_collapse(probes, _embedders(aliases), CONFIG)
    assert not run.draft and run.verdict is not None
    assert run.verdict.passed is passed
    assert run.verdict.criterion == CONFIG.criterion
    assert run.verdict.confirm.split == Split.CONFIRM
    assert run.verdict.confirm.track == QueryTrack.NATURAL
    if separable:
        assert run.verdict.select.accuracy == 1.0
        assert run.verdict.select.dimension == 64


def test_tracks_are_computed_independently(tmp_path: Path) -> None:
    probes = _probes(tmp_path)
    changed = replace(
        probes,
        queries=tuple(
            replace(q, synonym_term=f"other {q.synonym_term}") for q in probes.queries
        ),
    )
    first = _by_key(run_collapse(probes, _embedders(), CONFIG, draft=True))
    second = _by_key(run_collapse(changed, _embedders(), CONFIG, draft=True))
    differing = {key for key in first if first[key] != second[key]}
    assert differing
    # Synonym terms only reach the symmetric track of C1 and C4.
    assert {(key[0].method, key[2]) for key in differing} <= {
        (Method.C1, QueryTrack.SYMMETRIC),
        (Method.C4, QueryTrack.SYMMETRIC),
    }


@pytest.mark.parametrize(
    ("embedders", "message"),
    [
        ([FakeEmbedder(64)], "dimensions"),
        ([FakeEmbedder(64), FakeEmbedder(64), FakeEmbedder(128)], "dimensions"),
    ],
)
def test_embedders_must_match_the_dimensions(tmp_path, embedders, message) -> None:
    with pytest.raises(ValueError, match=message):
        run_collapse(_probes(tmp_path), embedders, CONFIG, draft=True)


def test_embedders_must_be_the_same_encoder(tmp_path: Path) -> None:
    embedders = _embedders()
    embedders[1].fingerprint = replace(embedders[1].fingerprint, model_digest="new")
    with pytest.raises(ValueError, match="differ in more than"):
        run_collapse(_probes(tmp_path), embedders, CONFIG, draft=True)
    assert all(e.calls == [] for e in embedders)
    assert np.dtype(embedders[0].fingerprint.dtype) == np.float32
