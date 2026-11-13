"""Multi-start randomized greedy with sequential redundancy removal.

This module uses the repository's named-subset model and tuple return type.
The deterministic baseline and random construction use the same tie ordering.
"""

from collections.abc import Iterable
import random

from .greedy import greedy_cover
from .model import SetCoverInstance, SubsetName
from .validation import validate_cover


def remove_redundant(
    instance: SetCoverInstance, selected: Iterable[SubsetName]
) -> tuple[SubsetName, ...]:
    """Remove dispensable sets in selection order, preserving full coverage.

    Counts must be updated after EACH removal. One pass is enough because
    later deletions cannot make a previously indispensable set dispensable.
    The result is inclusion-minimal, not necessarily minimum-cardinality.
    """
    selected = tuple(selected)
    validate_cover(instance, selected)
    counts = dict.fromkeys(instance.universe, 0)
    for name in selected:
        for element in instance.subsets[name] & instance.universe:
            counts[element] += 1
    kept = []
    for name in selected:
        subset = instance.subsets[name] & instance.universe
        if all(counts[element] >= 2 for element in subset):
            for element in subset:
                counts[element] -= 1
        else:
            kept.append(name)
    return tuple(kept)


def greedy_pruned_cover(instance: SetCoverInstance) -> tuple[SubsetName, ...]:
    """Ablation: deterministic greedy followed only by redundancy removal."""
    return remove_redundant(instance, greedy_cover(instance))


def _randomized_construction(
    instance: SetCoverInstance, rng: random.Random, rcl_size: int
) -> tuple[SubsetName, ...]:
    uncovered = set(instance.universe)
    available = dict(instance.subsets)
    selected = []
    while uncovered:
        candidates = [
            (name, len(subset & uncovered))
            for name, subset in available.items()
        ]
        candidates = [item for item in candidates if item[1] > 0]
        if not candidates:
            raise ValueError("the instance cannot be covered")
        # Stable descending sort matches greedy's max(gain, repr(name)).
        candidates.sort(key=lambda item: (item[1], repr(item[0])), reverse=True)
        if rcl_size == 1:
            name = candidates[0][0]
        else:
            name = rng.choice(candidates[:rcl_size])[0]
        selected.append(name)
        uncovered.difference_update(available.pop(name))
    return tuple(selected)


def randomized_greedy_cover(
    instance: SetCoverInstance,
    *,
    seed: int = 0,
    restarts: int = 30,
    rcl_size: int = 3,
) -> tuple[SubsetName, ...]:
    """Keep the best of pruned greedy and ``restarts`` randomized covers.

    One private PRNG advances across all restarts. The baseline guarantees
    cardinality <= greedy on every feasible input. All initialization and
    pruning are part of this solver call and must be included in timings.
    """
    for name, value, minimum in (("seed", seed, 0), ("restarts", restarts, 0),
                                 ("rcl_size", rcl_size, 1)):
        if type(value) is not int or value < minimum:
            raise ValueError(f"{name} must be an integer >= {minimum}")
    best = greedy_pruned_cover(instance)
    if not instance.universe:
        return best
    rng = random.Random(seed)
    for _ in range(restarts):
        candidate = remove_redundant(
            instance, _randomized_construction(instance, rng, rcl_size)
        )
        if len(candidate) < len(best):
            best = candidate
    return best
