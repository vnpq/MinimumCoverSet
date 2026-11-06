"""Reproducible random data generation for set cover experiments."""

import random

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


def instance_to_dict(instance: SetCoverInstance) -> dict[str, object]:
    """Convert an instance to the JSON shape accepted by the CLI."""
    return {
        "universe": sorted(instance.universe),
        "subsets": {
            str(name): sorted(elements)
            for name, elements in instance.subsets.items()
        },
    }
