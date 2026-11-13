"""Execute the team notebook in a fresh kernel and check its observable results.

Install the project's ``notebook`` extra first. No notebook output is overwritten
unless an explicit --output path is supplied.
"""

import argparse
import json
import os
from pathlib import Path
import sys

import nbformat
from nbclient import NotebookClient


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks/minimum_cover_set_evaluation.ipynb"


def execute_in_process(notebook, working_directory):
    """Run cells through IPython when the host cannot start a socket-based kernel.

    This checks cell semantics and rich displays, not Jupyter's transport/UI.
    Each script invocation starts a new process; this mode has no cell timeout.
    """
    from IPython.terminal.interactiveshell import TerminalInteractiveShell
    from IPython.utils.capture import capture_output

    shell = TerminalInteractiveShell.instance()
    shell.display_formatter.active_types = ["text/plain", "text/html", "image/png"]
    original_directory = Path.cwd()
    try:
        os.chdir(working_directory)
        for cell in notebook.cells:
            if cell.cell_type != "code":
                continue
            with capture_output() as captured:
                result = shell.run_cell(cell.source, store_history=True)
            if not result.success:
                raise result.error_before_exec or result.error_in_exec
            cell.execution_count = result.execution_count
            cell.outputs = []
            for name in ("stdout", "stderr"):
                content = getattr(captured, name)
                if content:
                    cell.outputs.append(nbformat.v4.new_output("stream", name=name, text=content))
            for output in captured.outputs:
                cell.outputs.append(nbformat.v4.new_output(
                    "display_data", data=output.data, metadata=output.metadata))
        notebook.metadata.language_info.version = sys.version.split()[0]
        notebook.metadata["compatibility_execution"] = {"mode": "in_process_ipython"}
    finally:
        os.chdir(original_directory)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--empty", action="store_true", help="exercise the empty universe")
    parser.add_argument("--from-notebooks", action="store_true",
                        help="use notebooks/ as the kernel working directory")
    parser.add_argument("--output", type=Path, help="save the freshly executed notebook")
    parser.add_argument("--in-process", action="store_true",
                        help="check cells with IPython without kernel sockets (no timeout)")
    args = parser.parse_args()
    notebook = nbformat.read(NOTEBOOK, as_version=4)
    for cell in notebook.cells:
        if cell.cell_type == "code":
            cell.outputs = []
            cell.execution_count = None
    if args.empty:
        config = next(cell for cell in notebook.cells
                      if cell.cell_type == "code" and "NUM_ELEMENTS = 20" in cell.source)
        config.source = config.source.replace("NUM_ELEMENTS = 20", "NUM_ELEMENTS = 0")

    checks = f"""
import json
import math
assert Path(sys.prefix).resolve() == Path({sys.prefix!r}).resolve(), "wrong kernel environment"
expected = {{"Greedy", "Greedy + cleanup", "Randomized Greedy", "Brute Force",
            "Dynamic Programming", "Branch and Bound"}}
assert len(results_df) == 6 and set(results_df["algorithm"]) == expected
assert bool(results_df["valid"].all())
for row in results_df.to_dict("records"):
    validate_cover(instance, row["solution"])
    assert row["selected"] == len(row["solution"])
    for field in ("accuracy", "optimality_gap_pct", "runtime_ms"):
        assert math.isfinite(row[field]), (row["algorithm"], field)
sizes = results_df.set_index("algorithm")["selected"].to_dict()
assert sizes["Brute Force"] == sizes["Branch and Bound"] == sizes["Dynamic Programming"]
assert optimal_size <= sizes["Randomized Greedy"] <= sizes["Greedy + cleanup"] <= sizes["Greedy"]
if not instance.universe:
    assert all(size == 0 for size in sizes.values())
    assert bool((results_df["accuracy"] == 1).all())
    assert bool((results_df["optimality_gap_pct"] == 0).all())
print("NOTEBOOK_CHECK:" + json.dumps({{"selected": sizes, "optimal_size": optimal_size,
      "valid": True, "finite_metrics": True, "python": sys.version.split()[0]}}))
"""
    notebook.cells.append(nbformat.v4.new_code_cell(checks))
    working_directory = ROOT / "notebooks" if args.from_notebooks else ROOT
    if args.in_process:
        execute_in_process(notebook, working_directory)
    else:
        notebook.metadata.pop("compatibility_execution", None)
        NotebookClient(
            notebook, timeout=120, startup_timeout=30, kernel_name="python3",
            resources={"metadata": {"path": str(working_directory)}},
        ).execute()
    check_cell = notebook.cells.pop()
    marker = "NOTEBOOK_CHECK:"
    summary = next(
        json.loads(output.text.split(marker, 1)[1])
        for output in check_cell.outputs
        if output.output_type == "stream" and marker in output.text
    )
    plots = sum(
        "image/png" in output.get("data", {})
        for cell in notebook.cells if cell.cell_type == "code"
        for output in cell.outputs
    )
    if not plots:
        raise AssertionError("the notebook did not render its comparison plot")
    summary.update(case="empty" if args.empty else "default",
                   working_directory="notebooks" if args.from_notebooks else "root",
                   executed_code_cells=sum(cell.cell_type == "code" for cell in notebook.cells),
                   rendered_plots=plots,
                   execution_mode="in_process_ipython" if args.in_process else "jupyter_kernel")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        nbformat.write(notebook, args.output)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
