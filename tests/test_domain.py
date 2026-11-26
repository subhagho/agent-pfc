from agent_pfc.domain import (
    PHASE_BY_MODALITY,
    Modality,
    OperationKey,
    ProbeOperation,
    ProbeQuery,
    Split,
)


def _operation(concept: str, modality: Modality) -> ProbeOperation:
    return ProbeOperation(
        concept=concept,
        modality=modality,
        phase=PHASE_BY_MODALITY[modality],
        phase_modality_text="phase text",
        contextual_text="contextual text",
        split=Split.SELECT,
    )


def test_modality_phase_table_and_operation_identity() -> None:
    assert dict(PHASE_BY_MODALITY) == {
        Modality.REQUIRED: 1,
        Modality.STRICT_REQUIRED: 2,
        Modality.PERMITTED: 1,
        Modality.NOT_REQUIRED: -1,
        Modality.PROHIBITED: -1,
    }

    required = _operation("log", Modality.REQUIRED)
    permitted = _operation("log", Modality.PERMITTED)
    other_concept = _operation("retry", Modality.REQUIRED)

    # Same concept and phase, yet two operations.
    assert required.phase == permitted.phase
    assert required.key != permitted.key
    assert required.key != other_concept.key

    query = ProbeQuery(
        id="q1",
        concept="log",
        modality=Modality.PERMITTED,
        text="may log",
        synonym_term="allowed",
    )
    assert query.expected_key == permitted.key == OperationKey("log", Modality.PERMITTED)
