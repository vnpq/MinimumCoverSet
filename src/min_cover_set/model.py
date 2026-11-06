"""Data model and validation for set cover instances."""

from dataclasses import dataclass
from collections.abc import Collection, Mapping
from typing import Hashable

Element = Hashable
SubsetName = Hashable


@dataclass(frozen=True)
class SetCoverInstance:
    """A universe and named subsets whose union should cover that universe."""

    universe: frozenset[Element]
    subsets: Mapping[SubsetName, frozenset[Element]]

    @classmethod
    def from_collections(
        cls,
        universe: Collection[Element],
        subsets: Mapping[SubsetName, Collection[Element]],
    ) -> "SetCoverInstance":
        normalized_universe = frozenset(universe)
        normalized_subsets = {
            name: frozenset(elements) for name, elements in subsets.items()
        }
        unknown = set().union(*normalized_subsets.values()) - normalized_universe
        if unknown:
            raise ValueError(f"subsets contain elements outside the universe: {unknown}")
        if not normalized_universe:
            return cls(normalized_universe, normalized_subsets)
        covered = set().union(*normalized_subsets.values())
        missing = normalized_universe - covered
        if missing:
            raise ValueError(f"uncoverable universe elements: {missing}")
        return cls(normalized_universe, normalized_subsets)

