"""Command-line interface for minimum set cover."""

import argparse
import json
from pathlib import Path

from .min_cover_set import MinimumCoverSet
from .model import SetCoverInstance
from data_generator import generate_instance, instance_to_dict


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, nargs="?", help="JSON instance file")
    parser.add_argument(
        "--algorithm",
        choices=("greedy", "brute_force", "dp", "branch_and_bound"),
        default="greedy",
    )
    parser.add_argument("--generate-elements", type=int, help="generate this many elements")
    parser.add_argument("--generate-subsets", type=int, help="generate this many subsets")
    parser.add_argument("--density", type=float, default=0.3)
    parser.add_argument("--seed", type=int)
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
        payload = json.loads(args.input.read_text(encoding="utf-8"))
    instance = SetCoverInstance.from_collections(
        payload["universe"], payload["subsets"]
    )
    methods = {
        "greedy": "greedy",
        "brute_force": "brute_force",
        "dp": "dynamic_programming",
        "branch_and_bound": "branch_and_bound",
    }
    result = getattr(MinimumCoverSet(instance), methods[args.algorithm])()
    print(json.dumps({"algorithm": args.algorithm, "selected": list(result)}))


if __name__ == "__main__":
    main()
