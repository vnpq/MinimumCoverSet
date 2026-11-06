"""Greedy approximation for minimum set cover."""

from .model import SetCoverInstance, SubsetName


def greedy_cover(instance: SetCoverInstance) -> tuple[SubsetName, ...]:
    """Return a cover by repeatedly selecting the subset with best gain."""
    uncovered = set(instance.universe)
    selected: list[SubsetName] = []
    available = dict(instance.subsets)

    while uncovered:
        name, subset = max(
            available.items(),
            key=lambda item: (len(item[1] & uncovered), repr(item[0])),
        )
        gain = subset & uncovered
        if not gain:
            raise ValueError("the instance cannot be covered")
        selected.append(name)
        uncovered -= gain
        del available[name]
    return tuple(selected)

