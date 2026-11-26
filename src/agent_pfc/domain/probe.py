"""Records of a modality probe set."""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import NamedTuple

from agent_pfc.domain.modality import Modality


class Split(StrEnum):
    SELECT = "select"
    CONFIRM = "confirm"


class OperationKey(NamedTuple):
    """Identity of an operation."""

    concept: str
    modality: Modality


@dataclass(frozen=True)
class ProbeOperation:
    """A stored operation. The phase is data; validation checks it."""

    concept: str
    modality: Modality
    phase: int
    phase_modality_text: str
    contextual_text: str
    split: Split

    @property
    def key(self) -> OperationKey:
        return OperationKey(self.concept, self.modality)


@dataclass(frozen=True)
class ProbeQuery:
    """A query that expects the operation of `concept` with `modality`."""

    id: str
    concept: str
    modality: Modality
    text: str
    synonym_term: str

    @property
    def expected_key(self) -> OperationKey:
        return OperationKey(self.concept, self.modality)


@dataclass(frozen=True)
class ProbeSet:
    operations: tuple[ProbeOperation, ...]
    queries: tuple[ProbeQuery, ...]
    reviewed_by_user: bool
    file_hashes: Mapping[str, str]
