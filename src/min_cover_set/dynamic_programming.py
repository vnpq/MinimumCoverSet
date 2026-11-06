"""Bitmask dynamic programming for minimum set cover."""

from .model import SetCoverInstance, SubsetName


def dynamic_programming_cover(
    instance: SetCoverInstance,
) -> tuple[SubsetName, ...]:
    """Find an optimal cover using dynamic programming over covered elements."""
    if not instance.universe:
        return ()
    elements = tuple(instance.universe)
    full_mask = (1 << len(elements)) - 1
    candidates = tuple(
        (name, sum(1 << index for index, element in enumerate(elements) if element in subset))
        for name, subset in instance.subsets.items()
        if subset & instance.universe
    )
    dp: dict[int, tuple[SubsetName, ...]] = {0: ()}
    for name, subset_mask in candidates:
        for mask, selected in tuple(dp.items()):
            new_mask = mask | subset_mask
            proposed = selected + (name,)
            if new_mask not in dp or len(proposed) < len(dp[new_mask]):
                dp[new_mask] = proposed
    if full_mask not in dp:
        raise ValueError("the instance cannot be covered")
    return dp[full_mask]

