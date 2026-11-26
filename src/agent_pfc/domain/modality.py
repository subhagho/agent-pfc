"""Operation modalities and the phase each one carries."""

from collections.abc import Mapping
from enum import StrEnum
from types import MappingProxyType


class Modality(StrEnum):
    REQUIRED = "required"
    STRICT_REQUIRED = "strict_required"
    PERMITTED = "permitted"
    NOT_REQUIRED = "not_required"
    PROHIBITED = "prohibited"


# Several modalities share a phase, so a phase never identifies an operation.
PHASE_BY_MODALITY: Mapping[Modality, int] = MappingProxyType(
    {
        Modality.REQUIRED: 1,
        Modality.STRICT_REQUIRED: 2,
        Modality.PERMITTED: 1,
        Modality.NOT_REQUIRED: -1,
        Modality.PROHIBITED: -1,
    }
)
