"""The texts each method embeds, in the order `methods.compose` expects them.

C3 is the same formula as C1 for operations, so it has no rendering of its own.
"""

from agent_pfc.domain import Method, MethodVariant, ProbeOperation, ProbeQuery


def stored_texts(
    operation: ProbeOperation, variant: MethodVariant
) -> tuple[str, ...]:
    concept = operation.concept
    match variant.method:
        case Method.C0:
            return (operation.contextual_text,)
        case Method.C1:
            return (concept, operation.phase_modality_text)
        case Method.C2:
            return (concept, operation.contextual_text)
        case Method.C4:
            return (
                f"Operation: {concept}; Phase: {operation.phase:+d}; "
                f"Modality: {operation.phase_modality_text}",
            )
        case Method.C5:
            return (concept,)
    raise _not_rendered(variant)


def symmetric_query_texts(
    query: ProbeQuery, variant: MethodVariant
) -> tuple[str, ...]:
    """A query composed like a stored operation.

    Only the concept, synonym term and text are read: the query's modality is
    the answer, and a phase would give it away.
    """
    concept = query.concept
    match variant.method:
        case Method.C0:
            return (query.text,)
        case Method.C1:
            return (concept, query.synonym_term)
        case Method.C2:
            return (concept, query.text)
        case Method.C4:
            return (f"Operation: {concept}; Modality: {query.synonym_term}",)
        case Method.C5:
            return (concept,)
    raise _not_rendered(variant)


def _not_rendered(variant: MethodVariant) -> ValueError:
    return ValueError(f"method {variant.method} is not rendered for operations")
