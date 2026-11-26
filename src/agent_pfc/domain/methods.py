"""Composition method identifiers and query tracks."""

from dataclasses import dataclass
from enum import StrEnum


class Method(StrEnum):
    C0 = "C0"
    C1 = "C1"
    C2 = "C2"
    C3 = "C3"
    C4 = "C4"
    C5 = "C5"


@dataclass(frozen=True)
class MethodVariant:
    """A method and, for weighted methods only, its weight."""

    method: Method
    weight: float | None = None


class QueryTrack(StrEnum):
    NATURAL = "natural"
    SYMMETRIC = "symmetric"
