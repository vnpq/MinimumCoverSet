"""Greedy approximation for minimum set cover."""

from .model import SetCoverInstance, SubsetName


def greedy_cover(instance: SetCoverInstance) -> tuple[SubsetName, ...]:
    """Choose maximum new coverage; ties keep the existing largest-repr rule.

    Equal repr values retain mapping insertion order. No input is modified.
    A valid cover is returned, not a certificate of minimum cardinality.
    """
    uncovered = set(instance.universe)
    selected: list[SubsetName] = []
    available = dict(instance.subsets)

    while uncovered:
        if not available:
            raise ValueError("the instance cannot be covered")
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

