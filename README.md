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
- **Brute force**: checks subset combinations and returns an optimal solution.
- **Dynamic programming**: uses a bitmask-based state representation.
- **Branch and bound**: exact search with pruning to reduce the search space (branch-on-elements).
- **Binary branch and bound**: 0-1 decision tree search per subset (branch-on-subsets with suffix-feasibility pruning).

The exact algorithms guarantee a minimum-cardinality cover. Their runtime can
grow quickly as the input size increases, so they are most suitable for small
or medium-sized instances.

## Project Structure

```text
src/
  data_generator.py          # reproducible random input generation
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
    binary_branch_and_bound.py # binary 0-1 branch-and-bound algorithm
    min_cover_set.py         # MinimumCoverSet class facade
tests/                       # correctness, exact-oracle and benchmark checks
experiments/                 # reproducible experiment manifests
data/benchmarks/              # nine original unit-cost inputs and SHA-256 hashes
notebooks/                   # interactive comparison of six methods
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

## Generating Input Data

Run `notebooks/01_generate_data.ipynb` to create reproducible JSON instances
under `data/`. Every generated element is assigned to at least one subset.

For reproducible experiments with larger inputs, use the benchmark runner. Exact
methods are opt-in and restricted to small inputs; the default is Greedy and
randomized Greedy:

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

The notebooks follow the manifests in `experiments/`: the first materializes
generated cases as JSON under `data/experiment_instances/`, and the second runs
the benchmark runner for exact and scalable experiment groups. Results are
written under `results/` and include runtime, cardinality, validation and
reference-aware summaries:

```bash
python -m pip install -e ".[notebook]"
jupyter notebook notebooks/01_generate_data.ipynb
jupyter notebook notebooks/02_evaluate_results.ipynb
```

The optional extra installs Jupyter and its kernel as well as the plotting
libraries. The core algorithms need only the Python standard library.
The notebooks write generated data to `data/` and evaluation results to
`results/` in the repository.

## Greedy and randomized greedy

Greedy repeatedly selects the subset covering the most currently uncovered
universe elements. Equal gains use the largest `repr(subset_name)`; results
contain subset names in selection order. The unweighted algorithm provides an
`H_n` approximation bound, with `H_n <= 1 + ln(n)` for a nonempty universe.

Randomized greedy first computes a feasible cleaned Greedy baseline. Each
restart chooses uniformly among the `rcl_size` subsets with the highest positive
marginal coverage until all elements are covered. It then removes redundant
subsets sequentially, updating coverage counts after every removal. Only a
strictly smaller complete cover replaces the incumbent.

- Defaults: `seed=0`, `restarts=30`, `rcl_size=3`.
- A private random generator advances across restarts; the global RNG is unchanged.
- `restarts=0` returns the baseline; `rcl_size=1` uses deterministic construction.
- Cleanup produces an inclusion-minimal cover, which need not be optimal.
- Cardinalities satisfy `OPT <= randomized_greedy <= greedy`.
- Exact solvers are used as independent references on small instances.

The test suite covers all 512 incidence matrices of size 3×3, generated small
instances, seed reproducibility and benchmark output.
Benchmark summaries distinguish proven optima from historical best-known upper
bounds; missing references remain unset. References and original input hashes
are recorded in `experiments/benchmarks.json` and `data/benchmarks/sources.json`.
Generated experiment outputs belong in `results/`.
