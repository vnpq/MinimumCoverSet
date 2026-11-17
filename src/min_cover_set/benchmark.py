"""Reproducible experiments; exact solvers are opt-in and restricted to small inputs."""

import argparse
from collections import defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import statistics
import subprocess
import sys
import tempfile
import time

from data_generator import generate_instance
from .io import load_instance
from .min_cover_set import MinimumCoverSet
from .model import SetCoverInstance
from .validation import validate_cover


def _fingerprint(instance: SetCoverInstance) -> str:
    # JSON/OR-Library names are strings and elements are scalar hashable values.
    # Include subset insertion order: it is part of tie-breaking for equal reprs.
    data = {
        "universe": sorted(instance.universe, key=repr),
        "subsets": [(name, sorted(values, key=repr))
                    for name, values in instance.subsets.items()],
    }
    return hashlib.sha256(json.dumps(data, ensure_ascii=False).encode()).hexdigest()


def _reference(value):
    if value is None:
        return {"kind": "unknown", "value": None, "source": ""}
    if not isinstance(value, dict) or value.get("kind") not in ("optimal", "best_known"):
        raise ValueError("reference.kind must be optimal or best_known")
    if type(value.get("value")) is not int or value["value"] < 0:
        raise ValueError("reference.value must be a nonnegative integer")
    if not isinstance(value.get("source"), str) or not value["source"].strip():
        raise ValueError("a reference requires an explicit source")
    return dict(value)


def _load_manifest(path: Path, exact: bool):
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("instances"), list):
        raise ValueError("manifest must contain an instances array")
    if not payload["instances"]:
        raise ValueError("manifest contains no instances")
    entries, names = [], set()
    for specification in payload["instances"]:
        if not isinstance(specification, dict):
            raise ValueError("each instance specification must be an object")
        name = specification.get("name")
        if not isinstance(name, str) or not name or name in names:
            raise ValueError("instance names must be nonempty and unique")
        names.add(name)
        if ("path" in specification) == ("generate" in specification):
            raise ValueError("each instance needs exactly one of path or generate")
        if "generate" in specification:
            generation = specification["generate"]
            if not isinstance(generation, dict) or type(generation.get("seed")) is not int:
                raise ValueError("generated instances require an explicit integer seed")
            instance = generate_instance(**generation)
        else:
            instance = load_instance(path.parent / specification["path"],
                                     format=specification.get("format", "auto"))
        reference = _reference(specification.get("reference"))
        if reference["value"] is not None and (
            (bool(instance.universe) and reference["value"] == 0)
            or (not instance.universe and reference["value"] != 0)
            or reference["value"] > len(instance.subsets)
        ):
            raise ValueError(f"invalid reference cardinality for {name}")
        if exact and (len(instance.universe) > 16 or len(instance.subsets) > 20):
            raise ValueError("--exact requires n <= 16 and m <= 20 for EVERY instance")
        entries.append((specification, instance, reference))
    return payload, entries


def _gap(cardinality, reference):
    value = reference["value"]
    if value is None:
        return None
    if value == 0:
        return 0.0
    return 100 * (cardinality - value) / value


def summarize(records):
    """Aggregate independent solver seeds and repeated deterministic timings."""
    grouped = defaultdict(list)
    greedy_sizes = {}
    for record in records:
        grouped[(record["instance"], record["algorithm"])].append(record)
        if record["algorithm"] == "greedy":
            greedy_sizes[record["instance"]] = record["cardinality"]
    summaries = []
    fixed = ("instance", "family", "n", "m", "density", "instance_sha256",
             "algorithm", "reference_kind", "reference_value", "reference_source")
    for (name, _), group in grouped.items():
        result = {key: group[0][key] for key in fixed}
        sizes = [item["cardinality"] for item in group]
        times = [item["time_ms"] for item in group]
        result.update({
            "runs": len(group), "cardinality_min": min(sizes),
            "cardinality_mean": statistics.mean(sizes), "cardinality_max": max(sizes),
            "cardinality_sd": statistics.stdev(sizes) if len(sizes) > 1 else 0.0,
            "time_ms_mean": statistics.mean(times),
            "time_ms_median": statistics.median(times),
            "time_ms_sd": statistics.stdev(times) if len(times) > 1 else 0.0,
            "improvement_vs_greedy_pct": (
                100 * (greedy_sizes[name] - statistics.mean(sizes)) / greedy_sizes[name]
                if greedy_sizes[name] else 0.0),
        })
        for metric in ("optimality_gap_pct", "gap_to_best_known_pct"):
            values = [item[metric] for item in group if item[metric] is not None]
            result[metric + "_mean"] = statistics.mean(values) if values else None
        summaries.append(result)
    return summaries


def _environment():
    root = Path(__file__).resolve().parents[2]
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                              capture_output=True, text=True, check=True).stdout.strip()
        dirty = bool(subprocess.run(["git", "status", "--porcelain"], cwd=root,
                                    capture_output=True, text=True, check=True).stdout)
    except (OSError, subprocess.CalledProcessError):
        head, dirty = None, None
    sources = {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
               for path in sorted((root / "src").rglob("*.py"))}
    cpu = platform.processor()
    cpuinfo = Path("/proc/cpuinfo")
    if not cpu and cpuinfo.exists():
        cpu = next((line.split(":", 1)[1].strip() for line in cpuinfo.read_text().splitlines()
                    if line.startswith("model name")), "")
    return {"python": sys.version, "platform": platform.platform(),
            "python_hash_seed": os.environ.get("PYTHONHASHSEED", "random"),
            "cpu": cpu, "logical_cpus": os.cpu_count(),
            "git_head": head, "git_dirty": dirty, "source_sha256": sources}


def _csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run_experiments(manifest, output, *, seeds=tuple(range(20)), restarts=30,
                    rcl_size=3, repeats=3, exact=False, overwrite=False):
    """Run a manifest serially, validate every cover, then publish four result files.

    Unknown references remain blank in CSV. A best-known value is an upper bound,
    not an optimum: its gap may legitimately be negative. --exact derives a proven
    reference via the team's exhaustive solver and also times all three exact methods.
    """
    manifest, output = Path(manifest), Path(output)
    seeds = tuple(seeds)
    if not seeds or any(type(seed) is not int or seed < 0 for seed in seeds):
        raise ValueError("seeds must be nonempty nonnegative integers")
    if len(set(seeds)) != len(seeds):
        raise ValueError("use distinct seeds for independent randomized runs")
    if type(repeats) is not int or repeats < 1:
        raise ValueError("repeats must be a positive integer")
    # Validate heuristic parameters before doing any experiment or writing files.
    MinimumCoverSet(SetCoverInstance.from_collections([], {})).randomized_greedy(
        seed=seeds[0], restarts=restarts, rcl_size=rcl_size)
    if output.exists() and (not output.is_dir() or (any(output.iterdir()) and not overwrite)):
        raise ValueError("output exists and is not empty; choose a new directory or --overwrite")
    payload, entries = _load_manifest(manifest, exact)
    metadata = _environment()
    metadata.update({
        "started_utc": datetime.now(timezone.utc).isoformat(), "manifest": payload,
        "manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
        "configuration": {"seeds": seeds, "restarts": restarts, "rcl_size": rcl_size,
                          "deterministic_repeats": repeats, "exact": exact,
                          "warmups_per_algorithm": 1, "schedule_seed": 0},
        "timing": "perf_counter_ns; complete solver call including baseline and cleanup; "
                  "excludes parsing, generation, reference computation and external validation",
    })
    records, solutions = [], []
    for specification, instance, reference in entries:
        solver = MinimumCoverSet(instance)
        if exact:
            oracle = solver.brute_force()
            validate_cover(instance, oracle)
            if reference["kind"] == "optimal" and reference["value"] != len(oracle):
                raise ValueError("provided optimal reference disagrees with exhaustive search")
            reference = {"kind": "optimal", "value": len(oracle),
                         "source": "exhaustive search: min_cover_set.brute_force"}
        algorithms = {"greedy": solver.greedy, "greedy_pruned": solver.greedy_pruned}
        if exact:
            algorithms.update({"brute_force": solver.brute_force,
                               "branch_and_bound": solver.branch_and_bound,
                               "dynamic_programming": solver.dynamic_programming})
        # One warm-up per method; never counted as a measured run.
        for method in algorithms.values():
            validate_cover(instance, method())
        validate_cover(instance, solver.randomized_greedy(
            seed=seeds[0], restarts=restarts, rcl_size=rcl_size))
        jobs = [(name, repetition, None) for name in algorithms for repetition in range(repeats)]
        jobs.extend(("randomized_greedy", index, seed) for index, seed in enumerate(seeds))
        random.Random(0).shuffle(jobs)
        n, m = len(instance.universe), len(instance.subsets)
        identity = {"instance": specification["name"], "family": specification.get("family", ""),
                    "n": n, "m": m,
                    "density": sum(map(len, instance.subsets.values())) / (n * m) if n * m else 0.0,
                    "instance_sha256": _fingerprint(instance)}
        for name, repetition, seed in jobs:
            start = time.perf_counter_ns()
            if name == "randomized_greedy":
                selected = solver.randomized_greedy(seed=seed, restarts=restarts, rcl_size=rcl_size)
            else:
                selected = algorithms[name]()
            elapsed = (time.perf_counter_ns() - start) / 1_000_000
            validate_cover(instance, selected)
            if reference["kind"] == "optimal" and len(selected) < reference["value"]:
                raise ValueError("solution contradicts the stated optimal reference")
            if exact and name in ("brute_force", "branch_and_bound", "dynamic_programming"):
                if len(selected) != reference["value"]:
                    raise ValueError("exact algorithms disagree")
            gap = _gap(len(selected), reference)
            record = {**identity, "algorithm": name, "run": repetition, "solver_seed": seed,
                      "restarts": restarts if seed is not None else None,
                      "rcl_size": rcl_size if seed is not None else None,
                      "cardinality": len(selected), "time_ms": elapsed, "valid": True,
                      "reference_kind": reference["kind"], "reference_value": reference["value"],
                      "reference_source": reference["source"],
                      "optimality_gap_pct": gap if reference["kind"] == "optimal" else None,
                      "gap_to_best_known_pct": gap if reference["kind"] == "best_known" else None}
            records.append(record)
            solutions.append({**record, "selected": list(selected)})
    metadata.update({"finished_utc": datetime.now(timezone.utc).isoformat(),
                     "instances": len(entries), "measured_runs": len(records),
                     "all_covers_valid": True})
    summary = summarize(records)
    output.mkdir(parents=True, exist_ok=True)
    # Stage first; overwrite only these four files, leaving unrelated files intact.
    with tempfile.TemporaryDirectory(dir=output.parent) as directory:
        stage = Path(directory)
        _csv(stage / "runs.csv", records)
        _csv(stage / "summary.csv", summary)
        (stage / "solutions.jsonl").write_text(
            "".join(json.dumps(solution, ensure_ascii=False) + "\n" for solution in solutions),
            encoding="utf-8")
        (stage / "environment.json").write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        for path in stage.iterdir():
            path.replace(output / path.name)
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(range(20)))
    parser.add_argument("--restarts", type=int, default=30)
    parser.add_argument("--rcl-size", type=int, default=3)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--exact", action="store_true",
                        help="include exact methods, only if n <= 16 and m <= 20")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    try:
        metadata = run_experiments(args.manifest, args.output, seeds=args.seeds,
                                   restarts=args.restarts, rcl_size=args.rcl_size,
                                   repeats=args.repeats, exact=args.exact, overwrite=args.overwrite)
    except (ValueError, TypeError, OSError) as exc:
        parser.error(str(exc))
    print(json.dumps({"instances": metadata["instances"], "runs": metadata["measured_runs"],
                      "all_covers_valid": True, "output": str(args.output)}))


if __name__ == "__main__":
    main()
