"""Regression, invariant and independent exact-oracle checks for the set cover solvers."""

from itertools import product
from pathlib import Path
import random
import unittest

from data_generator import generate_instance
from min_cover_set import MinimumCoverSet, MinimunCoverSet, SetCoverInstance
from min_cover_set.greedy import greedy_cover
from min_cover_set.heuristic import (
    greedy_pruned_cover, randomized_greedy_cover, remove_redundant,
)
from min_cover_set.io import load_instance
from min_cover_set.validation import validate_cover

ROOT = Path(__file__).resolve().parents[1]


class AlgorithmTests(unittest.TestCase):
    def setUp(self):
        self.trap = load_instance(ROOT / "examples/greedy_trap.json")

    def test_existing_facade_and_tie_rule(self):
        instance = load_instance(ROOT / "examples/basic.json")
        self.assertEqual(MinimumCoverSet(instance).greedy(), ("S4", "S2"))
        self.assertIs(MinimunCoverSet, MinimumCoverSet)
        # Names need not be strings or comparable to one another.
        mixed = SetCoverInstance.from_collections({1}, {1: {1}, "A": {1}})
        self.assertEqual(greedy_cover(mixed), (1,))

    def test_greedy_uses_new_coverage(self):
        instance = SetCoverInstance.from_collections(
            range(7), {"A": {0, 1, 2, 3, 4}, "B": {0, 1, 2, 5}, "C": {5, 6}}
        )
        self.assertEqual(greedy_cover(instance), ("A", "C"))

    def test_greedy_is_not_claimed_optimal(self):
        self.assertEqual(len(greedy_cover(self.trap)), 3)
        self.assertEqual(len(MinimumCoverSet(self.trap).brute_force()), 2)
        self.assertEqual(set(greedy_pruned_cover(self.trap)), {"S2", "S3"})

    def test_random_restarts_improve_beyond_cleanup(self):
        instance = load_instance(ROOT / "examples/randomized_improvement.json")
        self.assertEqual(len(greedy_cover(instance)), 4)
        self.assertEqual(len(greedy_pruned_cover(instance)), 4)
        self.assertEqual(len(randomized_greedy_cover(instance, seed=0)), 3)
        self.assertEqual(len(MinimumCoverSet(instance).brute_force()), 3)

    def test_cleanup_is_sequential_and_inclusion_minimal(self):
        instance = SetCoverInstance.from_collections(
            {0, 1}, {"A": {0, 1}, "B": {0, 1}, "C": set()}
        )
        result = remove_redundant(instance, ("A", "B", "C"))
        self.assertEqual(result, ("B",))
        validate_cover(instance, result)

    def test_cleanup_rejects_invalid_cover(self):
        for selected in [("unknown",), ("S1", "S1"), ("S1",)]:
            with self.subTest(selected=selected), self.assertRaises(ValueError):
                remove_redundant(self.trap, selected)

    def test_empty_universe_all_algorithms(self):
        instance = SetCoverInstance.from_collections([], {"empty": []})
        solver = MinimumCoverSet(instance)
        for method in [solver.greedy, solver.greedy_pruned, solver.randomized_greedy,
                       solver.brute_force, solver.branch_and_bound,
                       solver.dynamic_programming]:
            self.assertEqual(method(), ())

    def test_invalid_inputs_and_exhausted_candidates(self):
        for universe, subsets in [({0, 1}, {"A": {0}}), ({0}, {"A": {1}})]:
            with self.assertRaises(ValueError):
                SetCoverInstance.from_collections(universe, subsets)
        # Also guard callers that bypass the validated factory.
        for subsets in [{}, {"A": frozenset()}]:
            invalid = SetCoverInstance(frozenset({0}), subsets)
            with self.assertRaises(ValueError):
                greedy_cover(invalid)
            with self.assertRaises(ValueError):
                randomized_greedy_cover(invalid)

    def test_inputs_and_global_rng_unchanged(self):
        before = (self.trap.universe, dict(self.trap.subsets))
        state = random.getstate()
        greedy_cover(self.trap)
        randomized_greedy_cover(self.trap, seed=19)
        self.assertEqual(before, (self.trap.universe, dict(self.trap.subsets)))
        self.assertEqual(state, random.getstate())

    def test_reproducibility_and_budget_prefix(self):
        instance = generate_instance(30, 40, 0.15, seed=7)
        previous = len(greedy_pruned_cover(instance))
        for restarts in (0, 1, 5, 20):
            result = randomized_greedy_cover(instance, seed=73, restarts=restarts)
            self.assertEqual(result, randomized_greedy_cover(
                instance, seed=73, restarts=restarts))
            self.assertLessEqual(len(result), previous)
            previous = len(result)
        self.assertEqual(randomized_greedy_cover(instance, restarts=0),
                         greedy_pruned_cover(instance))
        self.assertEqual(randomized_greedy_cover(instance, rcl_size=1),
                         greedy_pruned_cover(instance))

    def test_invalid_parameters(self):
        for options in [{"seed": -1}, {"seed": True}, {"restarts": -1},
                        {"restarts": 1.5}, {"rcl_size": 0}, {"rcl_size": "3"}]:
            with self.subTest(options=options), self.assertRaises(ValueError):
                randomized_greedy_cover(self.trap, **options)

    def test_large_candidate_list_and_duplicate_sets(self):
        instance = SetCoverInstance.from_collections(
            {0, 1}, {"A": {0}, "B": {0}, "C": {1}, "D": set()})
        result = randomized_greedy_cover(instance, rcl_size=100)
        validate_cover(instance, result)
        self.assertEqual(len(result), 2)

    def assert_exact_and_heuristic_invariants(self, instance, seed):
        solver = MinimumCoverSet(instance)
        brute = solver.brute_force()
        bound = solver.branch_and_bound()
        dp = solver.dynamic_programming()
        greedy = solver.greedy()
        pruned = solver.greedy_pruned()
        randomized = solver.randomized_greedy(seed=seed, restarts=5)
        for result in (brute, bound, dp, greedy, pruned, randomized):
            validate_cover(instance, result)
            self.assertEqual(len(result), len(set(result)))
        self.assertEqual(len(brute), len(bound))
        self.assertEqual(len(brute), len(dp))
        self.assertLessEqual(len(brute), len(randomized))
        self.assertLessEqual(len(randomized), len(pruned))
        self.assertLessEqual(len(pruned), len(greedy))
        for result in (pruned, randomized):
            for index in range(len(result)):
                with self.assertRaises(ValueError):
                    validate_cover(instance, result[:index] + result[index + 1:])

    def test_all_512_three_by_three_incidence_matrices(self):
        feasible = 0
        for index, entries in enumerate(product((0, 1), repeat=9)):
            subsets = {f"S{j}": {i for i in range(3) if entries[i * 3 + j]}
                       for j in range(3)}
            with self.subTest(matrix=index):
                if set().union(*subsets.values()) != {0, 1, 2}:
                    with self.assertRaises(ValueError):
                        SetCoverInstance.from_collections(range(3), subsets)
                else:
                    feasible += 1
                    self.assert_exact_and_heuristic_invariants(
                        SetCoverInstance.from_collections(range(3), subsets), index)
        self.assertEqual(feasible, 343)

    def test_one_hundred_generated_instances_against_exact_algorithms(self):
        for seed in range(100):
            instance = generate_instance(
                seed % 9, 1 + seed % 10, (0, 0.1, 0.3, 0.7, 1.0)[seed % 5], seed)
            with self.subTest(seed=seed):
                self.assert_exact_and_heuristic_invariants(instance, seed)

    def test_wireless_example_matches_project_document(self):
        instance = load_instance(ROOT / "examples/wireless_towers.json")
        self.assertEqual(instance.universe, frozenset("ABCDEFGHIJ"))
        expected = ("ABCD", "CDEF", "EFG", "GHI", "AHJ", "BDIJ")
        self.assertEqual(list(instance.subsets.values()), list(map(frozenset, expected)))
        self.assert_exact_and_heuristic_invariants(instance, 0)
        # Any claimed optimum is cross-checked by three independent exact solvers.
        self.assertEqual(len(MinimumCoverSet(instance).brute_force()), 4)


if __name__ == "__main__":
    unittest.main()
