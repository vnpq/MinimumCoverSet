"""Object-oriented facade for minimum set cover algorithms."""

from .model import SetCoverInstance, SubsetName
from .branch_and_bound import branch_and_bound_cover
from .brute_force import brute_force_cover
from .dynamic_programming import dynamic_programming_cover
from .greedy import greedy_cover

class MinimumCoverSet:
    """Run different minimum set cover algorithms on one instance."""

    def __init__(self, instance: SetCoverInstance) -> None:
        self.instance = instance

    def greedy(self) -> tuple[SubsetName, ...]:
        return greedy_cover(self.instance)

    def brute_force(self) -> tuple[SubsetName, ...]:
        return brute_force_cover(self.instance)

    def dynamic_programming(self) -> tuple[SubsetName, ...]:
        return dynamic_programming_cover(self.instance)

    def branch_and_bound(self) -> tuple[SubsetName, ...]:
        return branch_and_bound_cover(self.instance)


MinimunCoverSet = MinimumCoverSet
