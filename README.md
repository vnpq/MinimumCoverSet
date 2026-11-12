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
    brute_force.py           # brute-force algorithm
    dynamic_programming.py   # dynamic-programming algorithm
    branch_and_bound.py      # branch-and-bound algorithm
    min_cover_set.py         # MinimumCoverSet class facade
    cli.py                   # command-line interface
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
instance is guaranteed to be valid.

## Running the Algorithms

Run any algorithm on a dataset:

```bash
python -m min_cover_set.cli examples/data.json --algorithm branch_and_bound
python -m min_cover_set.cli examples/data.json --algorithm greedy
python -m min_cover_set.cli examples/data.json --algorithm dp
python -m min_cover_set.cli examples/basic.json --algorithm brute_force
```

The result is printed as JSON:

```json
{
  "algorithm": "branch_and_bound",
  "selected": ["S2", "S4"]
}
```

## Evaluating Performance

Compare solution quality and runtime across all algorithms:

```bash
python src/evaluate.py examples/data.json
```

The evaluation reports:

- `selected`: number of subsets selected by the algorithm
- `optimal`: number of subsets in the brute-force reference solution
- `accuracy`: `optimal / selected`; an optimal solution has accuracy `1.0`
- `time_ms`: execution time of the algorithm in milliseconds

### Runtime Evaluation

The `time_ms` field can be used to compare the runtime of the algorithms on
the same input. A smaller value means the algorithm completed faster.

Example:

```json
{
  "brute_force": {
    "selected": 6,
    "optimal": 6,
    "accuracy": 1.0,
    "time_ms": 76.26
  },
  "branch_and_bound": {
    "selected": 6,
    "optimal": 6,
    "accuracy": 1.0,
    "time_ms": 2.23
  }
}
```
