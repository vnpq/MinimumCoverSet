# Minimum Set Cover

## Project Overview

This project provides a small Python implementation of the **Minimum Set
Cover** problem.

Given a universe of elements and a collection of subsets, the goal is to
select the smallest possible number of subsets whose union contains every
element in the universe.

The project is intended as a clear base repository for studying and comparing
different set cover algorithms. It includes both exact algorithms and a
greedy approximation algorithm, together with tools for generating input data
and measuring solution quality and runtime.

## Algorithms

- **Greedy**: fast approximation algorithm.
- **Randomized greedy**: multiple randomized constructions with redundancy removal;
  keeps a pruned Greedy baseline, so its cover is never larger than Greedy's.
- **Greedy + cleanup**: deterministic ablation (`greedy_pruned`) for comparison.
- **Brute force**: checks subset combinations and returns an optimal solution.
- **Dynamic programming**: uses a bitmask-based state representation.
- **Branch and bound**: exact search with pruning to reduce the search space.

The exact algorithms guarantee a minimum-cardinality cover. Their runtime can
grow quickly as the input size increases, so they are most suitable for small
or medium-sized instances.

## Project Structure

```text
src/
  data_generator.py          # reproducible random input generation
  evaluate.py                # solution accuracy and runtime evaluation
  min_cover_set/
    model.py                 # input model and validation
    greedy.py                # greedy approximation
    heuristic.py             # multi-start randomized greedy and cleanup
    validation.py            # independent cover validation
    io.py                    # named JSON and unit-cost OR-Library reader
    benchmark.py             # seeded experiments and reference-aware statistics
    brute_force.py           # brute-force algorithm
    dynamic_programming.py   # dynamic-programming algorithm
    branch_and_bound.py      # branch-and-bound algorithm
    min_cover_set.py         # MinimumCoverSet class facade
    cli.py                   # command-line interface
tests/                       # correctness, exact-oracle, parser and CLI checks
experiments/                 # reproducible experiment manifests
data/benchmarks/              # nine original unit-cost inputs and SHA-256 hashes
notebooks/                   # interactive comparison of all six methods
```

## Installation

Create a virtual environment and install the project in editable mode:

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

### Windows (PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
```

### Windows (Command Prompt - cmd)

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -e .
```

## Input Format

Input files use JSON with a universe and named subsets:

```json
{
  "universe": ["a", "b", "c", "d"],
  "subsets": {
    "S1": ["a", "b"],
    "S2": ["b", "c"],
    "S3": ["c", "d"],
    "S4": ["a", "d"]
  }
}
```

## Running the Algorithms

Run the command-line interface with a selected algorithm:

```bash
python -m min_cover_set.cli examples/basic.json --algorithm greedy
python -m min_cover_set.cli examples/basic.json --algorithm randomized_greedy --solver-seed 0 --restarts 30 --rcl-size 3
python -m min_cover_set.cli examples/basic.json --algorithm brute_force
python -m min_cover_set.cli examples/basic.json --algorithm dp
python -m min_cover_set.cli examples/basic.json --algorithm branch_and_bound
```

The result is printed as JSON:

```json
{
  "algorithm": "greedy",
  "selected": ["S4", "S2"],
  "cardinality": 2,
  "valid": true,
  "parameters": {}
}
```

## Generating Input Data

Generate a reproducible random instance. By default, generated data is saved
to `examples/data.json`:

### macOS / Linux

```bash
python -m min_cover_set.cli \
  --generate-elements 100 \
  --generate-subsets 20 \
  --density 0.3 \
  --seed 42
```

### Windows (PowerShell)

```powershell
python -m min_cover_set.cli --generate-elements 100 --generate-subsets 20 --density 0.3 --seed 42
```

Every generated element is assigned to at least one subset, so the generated
instance is valid. `--seed` controls data generation; `--solver-seed` separately
controls randomized search. The generator assigns an owner before adding elements
elsewhere with probability `density`, so expected actual density is
`density + (1 - density) / num_subsets`.

Generation saves the file and exits. A bare `--output sample.json` is saved as
`examples/sample.json`; a path such as `--output data/sample.json` is used as
provided. Run a solver in a separate command:

```bash
min-cover-set examples/data.json --algorithm randomized_greedy --solver-seed 0
```

## Evaluating Performance

Compare solution quality and runtime across all six methods. Without an input,
the evaluator uses `examples/data.json`, falling back to `examples/basic.json`:

```bash
python src/evaluate.py
python src/evaluate.py examples/data.json
python src/evaluate.py examples/basic.json --solver-seed 7 --restarts 30 --rcl-size 3
```

This convenience command always calls the exact solvers, without a size limit
or timeout. Use the benchmark runner below for larger inputs.

The evaluation reports:

- `selected`: number of subsets selected by the algorithm
- `optimal`: number of subsets in the brute-force reference solution
- `accuracy`: `optimal / selected`; an optimal solution has accuracy `1.0`
- `time_ms`: execution time in milliseconds
- `optimality_gap_pct`: percentage excess over the exhaustive optimum
- `valid`: independent coverage validation succeeded

For reproducible experiments with larger inputs, use the benchmark runner. Exact
methods are opt-in and restricted to small inputs; the default is Greedy, pruned
Greedy and randomized Greedy:

```bash
python -m unittest discover -s tests -v
python scripts/fetch_benchmarks.py
python -m min_cover_set.benchmark experiments/small_exact.json --exact --output results/small_exact
python -m min_cover_set.benchmark experiments/artificial.json --output results/artificial
python -m min_cover_set.benchmark experiments/benchmarks.json --output results/benchmarks
```

The runner uses 20 independent solver seeds and 3 deterministic timing repeats by
default. It writes raw runs, summary statistics, actual selected subset names and
environment metadata. Use a new output directory or explicitly pass `--overwrite`.
Only unit-cost OR-Library row-format data are accepted; weighted inputs are rejected.

## Jupyter Notebook

The interactive evaluation notebook introduces the project, generates a
reproducible dataset, runs all algorithms, compares their results, and
visualizes solution size and runtime. It includes Greedy, Greedy + cleanup,
Randomized Greedy, Brute Force, Dynamic Programming and Branch and Bound:

```bash
python -m pip install -e ".[notebook]"
jupyter notebook notebooks/minimum_cover_set_evaluation.ipynb
```

The optional extra installs Jupyter and its kernel as well as the plotting
libraries. The core algorithms need only the Python standard library.
The notebook works from the repository root or `notebooks/`. Its default
20-element, 12-subset example is a demonstration with one timing per method,
not a statistical benchmark. Re-execute it automatically with:

```bash
python scripts/check_notebook.py
python scripts/check_notebook.py --empty --from-notebooks
```

For environments that do not permit kernel sockets, add `--in-process` to check
cell execution and rich displays through IPython. This mode does not check the
Jupyter transport/UI and has no per-cell timeout.

## Greedy and randomized greedy

Greedy repeatedly selects the subset covering the most currently uncovered
universe elements. Equal gains use the largest `repr(subset_name)`; results
contain subset names in selection order. The unweighted algorithm provides an
`H_n` approximation bound, with `H_n <= 1 + ln(n)` for a nonempty universe.

Randomized greedy first computes a feasible Greedy + cleanup baseline. Each
restart chooses uniformly among the `rcl_size` subsets with the highest positive
marginal coverage until all elements are covered. It then removes redundant
subsets sequentially, updating coverage counts after every removal. Only a
strictly smaller complete cover replaces the incumbent.

- Defaults: `seed=0`, `restarts=30`, `rcl_size=3`.
- A private random generator advances across restarts; the global RNG is unchanged.
- `restarts=0` returns the baseline; `rcl_size=1` uses deterministic construction.
- Cleanup produces an inclusion-minimal cover, which need not be optimal.
- Cardinalities satisfy `OPT <= randomized_greedy <= greedy_pruned <= greedy`.
- Exact solvers are used as independent references on small instances.

The test suite covers all 512 incidence matrices of size 3×3, 100 generated
small instances, CLI/data parsing, seed reproducibility and benchmark output.
Benchmark summaries distinguish proven optima from historical best-known upper
bounds; missing references remain unset. References and original input hashes
are recorded in `experiments/benchmarks.json` and `data/benchmarks/sources.json`.
Generated experiment outputs belong in `results/`.
