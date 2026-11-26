"""What a collapse run computes and what it must meet."""

from dataclasses import dataclass

from agent_pfc.domain import Method, MethodVariant, PassCriterion

CRITERION = PassCriterion(min_accuracy=0.95, min_pairwise_accuracy=0.90)
WEIGHTS = (0.25, 0.5, 0.75, 1.0)
DIMENSIONS = (256, 512, 1024)


@dataclass(frozen=True)
class RunConfig:
    """Fixed before the run: nothing in it can change once embedding starts."""

    criterion: PassCriterion = CRITERION
    weights: tuple[float, ...] = WEIGHTS
    dimensions: tuple[int, ...] = DIMENSIONS

    @property
    def variants(self) -> tuple[MethodVariant, ...]:
        """The variants that are computed. C2 at weight 1 is C0, so it is not."""
        return (
            MethodVariant(Method.C0),
            *(MethodVariant(Method.C1, weight) for weight in self.weights),
            *(MethodVariant(Method.C2, w) for w in self.weights if w != 1.0),
            MethodVariant(Method.C4),
            MethodVariant(Method.C5),
        )

    @property
    def aliases(self) -> tuple[tuple[MethodVariant, MethodVariant], ...]:
        """(name, computed variant) pairs that share one result."""
        interpolation = (
            ((MethodVariant(Method.C2, 1.0), MethodVariant(Method.C0)),)
            if 1.0 in self.weights
            else ()
        )
        # For operations C3 is defined as the same formula as C1.
        weighted = tuple(
            (MethodVariant(Method.C3, weight), MethodVariant(Method.C1, weight))
            for weight in self.weights
        )
        return interpolation + weighted
