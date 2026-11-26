"""The criterion a run must meet, fixed before any embedding."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PassCriterion:
    min_accuracy: float
    min_pairwise_accuracy: float
