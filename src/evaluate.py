"""Evaluate set cover algorithms by solution quality and runtime."""

import argparse
import json
import time
from pathlib import Path
from typing import Callable

from min_cover_set import MinimumCoverSet, SetCoverInstance


Algorithm = Callable[[], tuple[object, ...]]


def evaluate(instance: SetCoverInstance) -> dict[str, dict[str, float | int | bool]]:
    """Compare algorithms against the brute-force optimal solution.

    Accuracy is the ratio ``optimal_size / solution_size``. It is 1.0 when
    the algorithm finds a minimum-cardinality cover.
    """
    cover = MinimumCoverSet(instance)
    optimal = cover.brute_force()
    optimal_size = len(optimal)
    algorithms: dict[str, Algorithm] = {
        "brute_force": cover.brute_force,
        "greedy": cover.greedy,
        "dynamic_programming": cover.dynamic_programming,
        "branch_and_bound": cover.branch_and_bound,
    }
    results: dict[str, dict[str, float | int | bool]] = {}

    for name, algorithm in algorithms.items():
        start = time.perf_counter()
        selected = algorithm()
        elapsed_ms = (time.perf_counter() - start) * 1000
        results[name] = {
            "selected": len(selected),
            "optimal": optimal_size,
            "accuracy": optimal_size / len(selected) if selected else 1.0,
            "time_ms": elapsed_ms,
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
    args = parser.parse_args()
    input_file = args.input
    if input_file is None:
        if Path("examples/data.json").exists():
            input_file = Path("examples/data.json")
        elif Path("examples/basic.json").exists():
            input_file = Path("examples/basic.json")
        else:
            parser.error("provide an input JSON file or generate examples/data.json first")
    payload = json.loads(input_file.read_text(encoding="utf-8"))
    instance = SetCoverInstance.from_collections(
        payload["universe"], payload["subsets"]
    )
    print(json.dumps(evaluate(instance), indent=2))


if __name__ == "__main__":
    main()
