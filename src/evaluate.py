"""Evaluate set cover algorithms by solution quality and runtime."""

import argparse
import json
import time
from pathlib import Path
from typing import Callable

from min_cover_set import MinimumCoverSet, SetCoverInstance
from min_cover_set.io import load_instance
from min_cover_set.validation import validate_cover


Algorithm = Callable[[], tuple[object, ...]]


def evaluate(instance: SetCoverInstance, *, seed: int = 0, restarts: int = 30,
             rcl_size: int = 3) -> dict[str, dict[str, float | int | bool]]:
    """Compare algorithms against the brute-force optimal solution.

    Accuracy is the ratio ``optimal_size / solution_size``. It is 1.0 when
    the algorithm finds a minimum-cardinality cover. ``time_ms`` measures the
    runtime of each algorithm call in milliseconds. This convenience evaluator
    runs exact solvers without a size limit or timeout, as in the team repository.
    Use the benchmark runner's default heuristic-only mode for large instances.
    """
    cover = MinimumCoverSet(instance)
    optimal = cover.brute_force()
    optimal_size = len(optimal)
    algorithms: dict[str, Algorithm] = {
        "brute_force": cover.brute_force,
        "greedy": cover.greedy,
        "greedy_pruned": cover.greedy_pruned,
        "randomized_greedy": lambda: cover.randomized_greedy(
            seed=seed, restarts=restarts, rcl_size=rcl_size),
        "dynamic_programming": cover.dynamic_programming,
        "branch_and_bound": cover.branch_and_bound,
    }
    results: dict[str, dict[str, float | int | bool]] = {}

    for name, algorithm in algorithms.items():
        start = time.perf_counter()
        selected = algorithm()
        elapsed_ms = (time.perf_counter() - start) * 1000
        validate_cover(instance, selected)
        results[name] = {
            "selected": len(selected),
            "optimal": optimal_size,
            "accuracy": optimal_size / len(selected) if selected else 1.0,
            "time_ms": elapsed_ms,
            "optimality_gap_pct": 100 * (len(selected) - optimal_size) / optimal_size if optimal_size else 0.0,
            "valid": True,
        }
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input",
        type=Path,
        nargs="?",
        default=None,
        help="JSON instance file (default: examples/data.json or examples/basic.json)",
    )
    parser.add_argument("--solver-seed", type=int, default=0)
    parser.add_argument("--restarts", type=int, default=30)
    parser.add_argument("--rcl-size", type=int, default=3)
    args = parser.parse_args()
    input_file = args.input
    if input_file is None:
        if Path("examples/data.json").exists():
            input_file = Path("examples/data.json")
        elif Path("examples/basic.json").exists():
            input_file = Path("examples/basic.json")
        else:
            parser.error("provide an input JSON file or generate examples/data.json first")
    instance = load_instance(input_file)
    print(json.dumps(evaluate(instance, seed=args.solver_seed, restarts=args.restarts,
                              rcl_size=args.rcl_size), indent=2))


if __name__ == "__main__":
    main()
