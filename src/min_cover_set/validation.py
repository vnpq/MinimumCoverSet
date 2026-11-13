"""Independent feasibility checks shared by experiments and heuristic cleanup."""

from collections.abc import Iterable

from .model import SetCoverInstance, SubsetName


def validate_cover(instance: SetCoverInstance, selected: Iterable[SubsetName]) -> None:
    """Raise ValueError for unknown names, duplicate names or missing coverage."""
    selected = tuple(selected)
    if len(set(selected)) != len(selected):
        raise ValueError("a subset cannot be selected more than once")
    if any(name not in instance.subsets for name in selected):
        raise ValueError("the cover contains an unknown subset name")
    covered = set().union(*(instance.subsets[name] for name in selected))
    if not covered >= instance.universe:
        raise ValueError("the selected subsets do not cover the universe")
