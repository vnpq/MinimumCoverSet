"""Regression checks for the team's updated CLI, evaluator and sample data."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from min_cover_set import SetCoverInstance
from min_cover_set.io import load_instance


ROOT = Path(__file__).resolve().parents[1]
EVALUATE_SPEC = importlib.util.spec_from_file_location("evaluate", ROOT / "src/evaluate.py")
EVALUATE_MODULE = importlib.util.module_from_spec(EVALUATE_SPEC)
EVALUATE_SPEC.loader.exec_module(EVALUATE_MODULE)
evaluate = EVALUATE_MODULE.evaluate
METHODS = {"greedy", "greedy_pruned", "randomized_greedy", "brute_force",
           "dynamic_programming", "branch_and_bound"}


class UpdatedRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.cwd = Path(self.temporary.name)

    def run_command(self, *arguments):
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(ROOT / "src")
        return subprocess.run(
            [sys.executable, *map(str, arguments)], cwd=self.cwd, env=environment,
            capture_output=True, text=True, timeout=30,
        )

    def generate(self, *arguments):
        return self.run_command(
            "-m", "min_cover_set.cli", "--generate-elements", "12",
            "--generate-subsets", "8", "--seed", "42", *arguments,
        )

    def write_instance(self, relative, universe, subsets):
        path = self.cwd / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"universe": universe, "subsets": subsets}),
                        encoding="utf-8")
        return path

    def evaluate_cli(self, *arguments):
        result = self.run_command(ROOT / "src/evaluate.py", *arguments)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(set(payload), METHODS)
        self.assertTrue(all(row["valid"] for row in payload.values()))
        return payload

    def test_generation_default_saves_and_exits(self):
        result = self.generate()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(),
                         "Generated instance successfully saved to examples/data.json")
        path = self.cwd / "examples/data.json"
        instance = load_instance(path)
        self.assertEqual((len(instance.universe), len(instance.subsets)), (12, 8))
        self.assertTrue(path.read_bytes().endswith(b"\n"))

    def test_generation_bare_filename_and_nested_relative_path(self):
        for argument, expected in [("custom.json", "examples/custom.json"),
                                   ("data/custom.json", "data/custom.json")]:
            with self.subTest(output=argument):
                result = self.generate("--output", argument)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(),
                                 f"Generated instance successfully saved to {expected}")
                self.assertEqual(len(load_instance(self.cwd / expected).universe), 12)
        self.assertFalse((self.cwd / "custom.json").exists())
        self.assertFalse((self.cwd / "examples/data/custom.json").exists())

    def test_evaluate_prefers_data_and_accepts_more_than_16_elements(self):
        self.write_instance("examples/basic.json", [], {})
        self.write_instance("examples/data.json", list(range(20)),
                            {"all": list(range(20))})
        results = self.evaluate_cli()
        self.assertTrue(all(row["selected"] == 1 for row in results.values()))

    def test_evaluate_falls_back_to_basic(self):
        self.write_instance("examples/basic.json", [0, 1], {"a": [0], "b": [1]})
        results = self.evaluate_cli()
        self.assertTrue(all(row["selected"] == 2 for row in results.values()))

    def test_evaluate_explicit_path_overrides_default(self):
        self.write_instance("examples/data.json", [0], {"all": [0]})
        explicit = self.write_instance("chosen.json", [], {})
        results = self.evaluate_cli(explicit)
        self.assertTrue(all(row["selected"] == 0 for row in results.values()))

    def test_evaluate_reports_missing_input(self):
        result = self.run_command(ROOT / "src/evaluate.py")
        self.assertEqual(result.returncode, 2)
        self.assertIn("provide an input JSON file or generate examples/data.json first",
                      result.stderr)

    def test_evaluate_legacy_fields_and_empty_universe(self):
        for instance in [load_instance(ROOT / "examples/basic.json"),
                         SetCoverInstance.from_collections([], {})]:
            with self.subTest(n=len(instance.universe)):
                results = evaluate(instance)
                self.assertEqual(set(results), METHODS)
                for row in results.values():
                    self.assertTrue({"selected", "optimal", "accuracy", "time_ms"}
                                    <= row.keys())
                    self.assertEqual(row["selected"], row["optimal"])
                    self.assertEqual(row["accuracy"], 1.0)
                    self.assertEqual(row["optimality_gap_pct"], 0.0)
                    self.assertTrue(row["valid"])

    def test_evaluate_passes_solver_parameters(self):
        path = ROOT / "examples/randomized_improvement.json"
        baseline = self.evaluate_cli(path, "--restarts", "0")
        improved = self.evaluate_cli(path, "--solver-seed", "0", "--restarts", "30",
                                     "--rcl-size", "3")
        self.assertEqual(baseline["randomized_greedy"]["selected"], 4)
        self.assertEqual(improved["randomized_greedy"]["selected"], 3)

    def test_uploaded_data_cross_checks_all_methods(self):
        instance = load_instance(ROOT / "examples/data.json")
        self.assertEqual((len(instance.universe), len(instance.subsets)), (100, 20))
        results = evaluate(instance)
        for method in ("brute_force", "branch_and_bound", "dynamic_programming"):
            self.assertEqual(results[method]["selected"], 6)
        for row in results.values():
            self.assertTrue(row["valid"])
            self.assertGreaterEqual(row["selected"], 6)
        self.assertLessEqual(results["randomized_greedy"]["selected"],
                             results["greedy_pruned"]["selected"])
        self.assertLessEqual(results["greedy_pruned"]["selected"],
                             results["greedy"]["selected"])

    def test_generate_then_evaluate_with_default_paths(self):
        result = self.generate()
        self.assertEqual(result.returncode, 0, result.stderr)
        results = self.evaluate_cli()
        optimum = results["brute_force"]["selected"]
        self.assertEqual(results["branch_and_bound"]["selected"], optimum)
        self.assertEqual(results["dynamic_programming"]["selected"], optimum)


if __name__ == "__main__":
    unittest.main()
