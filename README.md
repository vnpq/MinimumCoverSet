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

MacOS
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Window 
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
```



## Generating Input Data

Generate a reproducible random instance:
MacOS
```bash
python -m min_cover_set.cli \
  --generate-elements 100 \
  --generate-subsets 20 \
  --density 0.3 \
  --seed 42 \
  --output data.json
```
Window
```bash
python -m min_cover_set.cli --generate-elements 100 --generate-subsets 20 --density 0.3 --seed 42 --output data.json
```

Every generated element is assigned to at least one subset, so the generated
instance is valid.

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
python -m min_cover_set.cli data.json --algorithm greedy
python -m min_cover_set.cli data.json --algorithm brute_force
python -m min_cover_set.cli data.json --algorithm dp
python -m min_cover_set.cli data.json --algorithm branch_and_bound
```

The result is printed as JSON:

```json
{
  "algorithm": "greedy",
  "selected": ["S4", "S2"]
}
```

## Evaluating Performance

Compare solution quality and runtime:
Window
```bash
python -m min_cover_set.evaluate data.json
```


The evaluation reports:

- `selected`: number of subsets selected by the algorithm
- `optimal`: number of subsets in the brute-force reference solution
- `accuracy`: `optimal / selected`; an optimal solution has accuracy `1.0`
- `time_ms`: execution time in milliseconds
