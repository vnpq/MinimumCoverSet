"""Branch-and-bound minimum set cover."""

from .model import SetCoverInstance, SubsetName

def branch_and_bound_cover(
    instance: SetCoverInstance,
) -> tuple[SubsetName, ...]:
    """Return a minimum-cardinality cover using branch-and-bound search."""
    if not instance.universe:
        return ()
    candidates = [
        (name, subset & instance.universe)
        for name, subset in instance.subsets.items()
        if subset & instance.universe
    ]
    candidates.sort(key=lambda item: (-len(item[1]), repr(item[0])))
    best: tuple[SubsetName, ...] | None = None

    def search(uncovered: set, chosen: tuple[SubsetName, ...]) -> None:
        nonlocal best
        if not uncovered:
            if best is None or len(chosen) < len(best):
                best = chosen
            return
        if best is not None and len(chosen) >= len(best):
            return
        largest_gain = max(len(subset & uncovered) for _, subset in candidates)
        lower_bound = (len(uncovered) + largest_gain - 1) // largest_gain
        if best is not None and len(chosen) + lower_bound >= len(best):
            return
        element = min(
            uncovered,
            key=lambda item: sum(item in subset for _, subset in candidates),
        )
        for name, subset in candidates:
            if element in subset:
                search(uncovered - subset, chosen + (name,))

    search(set(instance.universe), ())
    if best is None:
        raise ValueError("the instance cannot be covered")
    return best
