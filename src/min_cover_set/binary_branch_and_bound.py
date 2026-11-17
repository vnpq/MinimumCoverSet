"""Binary (0-1) branch-and-bound minimum set cover."""

from .greedy import greedy_cover
from .model import SetCoverInstance, SubsetName


def binary_branch_and_bound_cover(
    instance: SetCoverInstance,
) -> tuple[SubsetName, ...]:
    """Return a minimum-cardinality cover using binary branch-and-bound."""
    if not instance.universe:
        return ()

    candidates = [
        (name, subset & instance.universe)
        for name, subset in instance.subsets.items()
        if subset & instance.universe
    ]
    candidates.sort(key=lambda item: (-len(item[1]), repr(item[0])))
    n = len(candidates)

    suffix_union: list[set] = [set()] * (n + 1)
    for i in range(n - 1, -1, -1):
        suffix_union[i] = suffix_union[i + 1] | candidates[i][1]

    if suffix_union[0] != instance.universe:
        raise ValueError("the instance cannot be covered")

    try:
        best: tuple[SubsetName, ...] | None = greedy_cover(instance)
    except ValueError:
        best = None

    def search(idx: int, uncovered: set, chosen: tuple[SubsetName, ...]) -> None:
        nonlocal best
        if not uncovered:
            if best is None or len(chosen) < len(best):
                best = chosen
            return
        if idx >= n or (best is not None and len(chosen) >= len(best)):
            return

        largest_gain = max(
            (len(subset & uncovered) for _, subset in candidates[idx:]),
            default=0,
        )
        if largest_gain == 0:
            return
        lower_bound = (len(uncovered) + largest_gain - 1) // largest_gain
        if best is not None and len(chosen) + lower_bound >= len(best):
            return

        name, subset = candidates[idx]
        gain = subset & uncovered
        if gain:
            search(idx + 1, uncovered - gain, chosen + (name,))
        if uncovered.issubset(suffix_union[idx + 1]):
            search(idx + 1, uncovered, chosen)

    search(0, set(instance.universe), ())
    if best is None:
        raise ValueError("the instance cannot be covered")
    return best
