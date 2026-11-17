import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from min_cover_set.io import instance_from_dict, load_instance, parse_orlibrary

ROOT = Path(__file__).resolve().parents[1]


class IOTests(unittest.TestCase):
    def test_orlibrary_rows_preserve_column_names(self):
        instance = parse_orlibrary("3 3\n1 1 1\n2 1 2\n1 2\n2 2 3\n")
        self.assertEqual(instance.universe, frozenset(range(3)))
        self.assertEqual(instance.subsets,
                         {"S1": frozenset({0}), "S2": frozenset({0, 1, 2}),
                          "S3": frozenset({2})})
        self.assertEqual(parse_orlibrary("0 0").universe, frozenset())

    def test_bad_orlibrary_data(self):
        for text in ["", "2", "-1 2", "1 1 2 1 1", "1 1 1 1",
                     "1 2 1 1 2 1 1", "1 1 1 1 2", "1 1 1 1 0",
                     "1 1 1 -1", "1 1 1 0", "0 0 9", "x y"]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_orlibrary(text)

    def test_json_shape_costs_and_unhashable_elements(self):
        valid = {"universe": [1], "subsets": {"A": [1]}, "costs": {"A": 1}}
        self.assertEqual(instance_from_dict(valid).universe, frozenset({1}))
        for payload in [[], {}, {"universe": [], "subsets": []},
                        {"universe": [1], "subsets": {"A": 1}},
                        {**valid, "costs": {"A": 2}}, {**valid, "costs": {}},
                        {**valid, "costs": {"A": True}},
                        {"universe": [[1]], "subsets": {"A": [[1]]}}]:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                instance_from_dict(payload)

    def test_loader_bom_and_explicit_format(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "instance.data"
            path.write_text('\ufeff{"universe": [], "subsets": {}}', encoding="utf-8")
            self.assertEqual(load_instance(path, format="json").universe, frozenset())
            with self.assertRaises(ValueError):
                load_instance(path, format="unsupported")


class CLITests(unittest.TestCase):
    def run_cli(self, *arguments):
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(ROOT / "src")
        return subprocess.run([sys.executable, "-m", "min_cover_set.cli", *arguments],
                              cwd=ROOT, env=environment, capture_output=True, text=True)

    def test_all_algorithms_report_actual_sets_and_cardinality(self):
        for name in ("greedy", "greedy_pruned", "randomized_greedy",
                     "brute_force", "dp", "branch_and_bound"):
            with self.subTest(algorithm=name):
                process = self.run_cli("examples/basic.json", "--algorithm", name)
                self.assertEqual(process.returncode, 0, process.stderr)
                result = json.loads(process.stdout)
                self.assertEqual(result["cardinality"], len(result["selected"]))
                self.assertEqual(result["cardinality"], 2)
                self.assertTrue(result["valid"])

    def test_generation_output_and_separate_solver_seed(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "nested/generated.json"
            generated = self.run_cli("--generate-elements", "8", "--generate-subsets", "10",
                                     "--seed", "42", "--output", str(path))
            self.assertEqual(generated.returncode, 0, generated.stderr)
            self.assertEqual(len(load_instance(path).universe), 8)
            solved = self.run_cli(str(path), "--algorithm", "randomized_greedy",
                                  "--solver-seed", "7", "--restarts", "4", "--rcl-size", "2")
            self.assertEqual(solved.returncode, 0, solved.stderr)
            self.assertEqual(json.loads(solved.stdout)["parameters"],
                             {"seed": 7, "restarts": 4, "rcl_size": 2})

    def test_generation_requires_both_sizes(self):
        result = self.run_cli("--generate-elements", "2")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must be used together", result.stderr)


if __name__ == "__main__":
    unittest.main()
