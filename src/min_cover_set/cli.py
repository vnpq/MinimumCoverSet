"""Command-line interface for minimum set cover."""

import argparse
import json
from pathlib import Path

from .min_cover_set import MinimumCoverSet
from .io import load_instance
from .validation import validate_cover
from data_generator import generate_instance, instance_to_dict


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, nargs="?", help="JSON or unit-cost OR-Library file")
    parser.add_argument(
        "--algorithm",
        choices=("greedy", "greedy_pruned", "randomized_greedy", "brute_force", "dp", "branch_and_bound"),
        default="greedy",
    )
    parser.add_argument("--generate-elements", type=int, help="generate this many elements")
    parser.add_argument("--generate-subsets", type=int, help="generate this many subsets")
    parser.add_argument("--density", type=float, default=0.3)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--solver-seed", type=int, default=0,
                        help="heuristic seed, separate from the generator's --seed")
    parser.add_argument("--restarts", type=int, default=30)
    parser.add_argument("--rcl-size", type=int, default=3)
    parser.add_argument("--format", choices=("auto", "json", "orlib"), default="auto")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("examples/data.json"),
        help="write generated data to JSON (default: examples/data.json)",
    )
    args = parser.parse_args()
    if args.generate_elements is not None or args.generate_subsets is not None:
        if args.generate_elements is None or args.generate_subsets is None:
            parser.error("--generate-elements and --generate-subsets must be used together")
        generated = generate_instance(
            args.generate_elements, args.generate_subsets, args.density, args.seed
        )
        payload = instance_to_dict(generated)
        output_path = args.output
        if len(output_path.parts) == 1:
            output_path = Path("examples") / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"Generated instance successfully saved to {output_path}")
        return
    elif args.input is None:
        parser.error("provide an input JSON file or generation options")
    else:
        instance = load_instance(args.input, format=args.format)
    methods = {
        "greedy": "greedy",
        "greedy_pruned": "greedy_pruned",
        "randomized_greedy": "randomized_greedy",
        "brute_force": "brute_force",
        "dp": "dynamic_programming",
        "branch_and_bound": "branch_and_bound",
    }
    method = getattr(MinimumCoverSet(instance), methods[args.algorithm])
    options = ({"seed": args.solver_seed, "restarts": args.restarts,
                "rcl_size": args.rcl_size} if args.algorithm == "randomized_greedy" else {})
    result = method(**options)
    validate_cover(instance, result)
    print(json.dumps({"algorithm": args.algorithm, "selected": list(result),
                      "cardinality": len(result), "valid": True,
                      "parameters": options}))


if __name__ == "__main__":
    main()
