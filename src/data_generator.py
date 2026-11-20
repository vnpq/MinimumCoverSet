"""Reproducible random data generation for set cover experiments."""

import random
import math

from min_cover_set.model import SetCoverInstance


def generate_instance(
    num_elements: int,
    num_subsets: int,
    density: float = 0.3,
    seed: int | None = None,
) -> SetCoverInstance:
    """Generate a valid random set cover instance."""
    if num_elements < 0:
        raise ValueError("num_elements must be non-negative")
    if num_subsets < 0:
        raise ValueError("num_subsets must be non-negative")
    if num_elements and not num_subsets:
        raise ValueError("num_subsets must be positive for a non-empty universe")
    if not 0 <= density <= 1:
        raise ValueError("density must be between 0 and 1")

    rng = random.Random(seed)
    elements = tuple(range(num_elements))
    subsets: dict[str, set[int]] = {
        f"S{index + 1}": set() for index in range(num_subsets)
    }
    for element in elements:
        owner = rng.randrange(num_subsets)
        subsets[f"S{owner + 1}"].add(element)
        for name, subset in subsets.items():
            if name != f"S{owner + 1}" and rng.random() < density:
                subset.add(element)
    return SetCoverInstance.from_collections(elements, subsets)


def generate_geographic_instance(
    grid_width: int,
    grid_height: int,
    num_tower_candidates: int,
    coverage_radius: float,
    seed: int,
) -> SetCoverInstance:
    """Generate a geometric wireless-tower instance for the Rhône-Alpes application."""
    if grid_width < 1 or grid_height < 1:
        raise ValueError("grid_width and grid_height must be positive")
    if num_tower_candidates < 1:
        raise ValueError("num_tower_candidates must be positive")
    if coverage_radius < 0:
        raise ValueError("coverage_radius must be nonnegative")

    rng = random.Random(seed)
    targets = {(x, y) for y in range(grid_height) for x in range(grid_width)}
    universe = tuple(sorted(targets))

    if num_tower_candidates == grid_width * grid_height:
        towers = list(universe)
    else:
        towers = rng.sample(list(universe), num_tower_candidates)
        # Requiring only the first tower owner for every target guarantees full coverage.
        towers = sorted(towers)

    subsets = {}
    for index, tower in enumerate(towers, start=1):
        covered = {
            target for target in targets
            if math.dist(tower, target) <= coverage_radius
        }
        subsets[f"tower_{index}"] = covered

    # Assign each target to a nearest tower as an owner. This guarantees complete
    # coverage even for small radii or sparse candidate placements.
    for target in targets:
        nearest = min(towers, key=lambda tower: (math.dist(tower, target), tower))
        index = towers.index(nearest) + 1
        subsets[f"tower_{index}"].add(target)

    return SetCoverInstance.from_collections(universe, subsets)


def instance_to_dict(instance: SetCoverInstance) -> dict[str, object]:
    """Convert an instance to the JSON shape accepted by the CLI."""
    return {
        "universe": sorted(instance.universe),
        "subsets": {
            str(name): sorted(elements)
            for name, elements in instance.subsets.items()
        },
    }
