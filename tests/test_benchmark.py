import csv
import json
from pathlib import Path
import tempfile
import unittest

from min_cover_set.benchmark import run_experiments


class BenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.manifest = self.root / "manifest.json"
        self.output = self.root / "results"
        self.specification = {"name": "small", "family": "test",
                              "generate": {"num_elements": 4, "num_subsets": 4,
                                           "density": 1, "seed": 11}}

    def write_manifest(self, specification=None):
        self.manifest.write_text(json.dumps({"instances": [specification or self.specification]}),
                                 encoding="utf-8")

    def run_experiment(self, **options):
        return run_experiments(self.manifest, self.output, seeds=(0, 1), repeats=2,
                               restarts=2, **options)

    def test_unknown_references_are_not_treated_as_optima(self):
        self.write_manifest()
        metadata = self.run_experiment()
        self.assertEqual(metadata["measured_runs"], 6)
        self.assertTrue(metadata["all_covers_valid"])
        solutions = [json.loads(line) for line in
                     (self.output / "solutions.jsonl").read_text().splitlines()]
        self.assertEqual(len(solutions), 6)
        for result in solutions:
            self.assertEqual(result["cardinality"], len(result["selected"]))
            self.assertIsNone(result["optimality_gap_pct"])
            self.assertIsNone(result["gap_to_best_known_pct"])
            self.assertEqual(result["reference_kind"], "unknown")
        with (self.output / "summary.csv").open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row["optimality_gap_pct_mean"] == "" for row in rows))
        self.assertTrue(all(float(row["cardinality_sd"]) == 0 for row in rows))

    def test_best_known_gap_can_be_negative(self):
        self.specification["reference"] = {"kind": "best_known", "value": 2,
                                            "source": "synthetic test reference, not a literature claim"}
        self.write_manifest()
        self.run_experiment()
        first = json.loads((self.output / "solutions.jsonl").read_text().splitlines()[0])
        self.assertEqual(first["gap_to_best_known_pct"], -50)
        self.assertIsNone(first["optimality_gap_pct"])

    def test_exact_mode_cross_checks_and_measures_existing_solvers(self):
        self.write_manifest()
        metadata = self.run_experiment(exact=True)
        self.assertEqual(metadata["measured_runs"], 12)
        records = [json.loads(line) for line in
                   (self.output / "solutions.jsonl").read_text().splitlines()]
        self.assertEqual({record["algorithm"] for record in records},
                         {"greedy", "greedy_pruned", "randomized_greedy", "brute_force",
                          "branch_and_bound", "dynamic_programming"})
        self.assertTrue(all(record["reference_value"] == 1 for record in records))
        self.assertTrue(all(record["optimality_gap_pct"] == 0 for record in records))

    def test_large_exact_mode_is_rejected_before_output(self):
        self.specification["generate"]["num_elements"] = 17
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "n <= 16"):
            self.run_experiment(exact=True)
        self.assertFalse(self.output.exists())

    def test_reference_needs_source_and_cannot_contradict_a_solution(self):
        for reference in [{"kind": "optimal", "value": 1},
                          {"kind": "optimal", "value": 0, "source": "invalid"},
                          {"kind": "optimal", "value": 2, "source": "incorrect"}]:
            with self.subTest(reference=reference):
                self.specification["reference"] = reference
                self.write_manifest()
                with self.assertRaises(ValueError):
                    self.run_experiment()
                self.assertFalse(self.output.exists())

    def test_overwrite_is_explicit_and_preserves_unrelated_files(self):
        self.write_manifest()
        self.run_experiment()
        marker = self.output / "notes.txt"
        marker.write_text("keep")
        with self.assertRaisesRegex(ValueError, "--overwrite"):
            self.run_experiment()
        self.run_experiment(overwrite=True)
        self.assertEqual(marker.read_text(), "keep")

    def test_same_seeds_reproduce_solutions_and_fingerprints(self):
        self.specification["generate"]["density"] = 0.2
        self.write_manifest()
        self.run_experiment()
        before = [json.loads(line) for line in
                  (self.output / "solutions.jsonl").read_text().splitlines()]
        self.run_experiment(overwrite=True)
        after = [json.loads(line) for line in
                 (self.output / "solutions.jsonl").read_text().splitlines()]
        for first, second in zip(before, after):
            first.pop("time_ms")
            second.pop("time_ms")
            self.assertEqual(first, second)

    def test_duplicate_seeds_and_unseeded_data_rejected(self):
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "distinct seeds"):
            run_experiments(self.manifest, self.output, seeds=(1, 1))
        del self.specification["generate"]["seed"]
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "explicit integer seed"):
            self.run_experiment()


if __name__ == "__main__":
    unittest.main()
