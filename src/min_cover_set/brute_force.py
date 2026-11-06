"""Brute-force minimum set cover."""

from itertools import combinations

from .model import SetCoverInstance, SubsetName


def brute_force_cover(instance: SetCoverInstance) -> tuple[SubsetName, ...]:
    """Find an optimal cover by checking combinations in size order."""
    if not instance.universe:
        return ()
    candidates = tuple(
        (name, subset)
        for name, subset in instance.subsets.items()
        if subset & instance.universe
    )
    for size in range(1, len(candidates) + 1):
        for combination in combinations(candidates, size):
            covered = set().union(*(subset for _, subset in combination))
            if covered >= instance.universe:
                return tuple(name for name, _ in combination)
    raise ValueError("the instance cannot be covered")

