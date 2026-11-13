"""Plot mean cardinality with sample-SD error bars and complete solver runtime."""

import argparse
import csv
from pathlib import Path


def plot(summary: Path, output: Path):
    # Optional dependency only; solvers, experiments and tests use the standard library.
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    with summary.open(newline="", encoding="utf-8") as stream:
        records = list(csv.DictReader(stream))
    names = list(dict.fromkeys(row["instance"] for row in records))
    by_key = {(row["instance"], row["algorithm"]): row for row in records}
    methods = [("greedy", "Greedy", "#2563eb"),
               ("greedy_pruned", "Greedy + cleanup", "#d97706"),
               ("randomized_greedy", "Randomized greedy", "#15803d")]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), layout="constrained")
    for index, (method, label, color) in enumerate(methods):
        positions = [position + (index - 1) * 0.25 for position in range(len(names))]
        rows = [by_key[(name, method)] for name in names]
        axes[0].bar(positions, [float(row["cardinality_mean"]) for row in rows],
                    width=0.23, yerr=[float(row["cardinality_sd"]) for row in rows],
                    capsize=2, label=label, color=color)
        axes[1].bar(positions, [float(row["time_ms_mean"]) for row in rows],
                    width=0.23, color=color, label=label)
    axes[0].set_ylabel("Selected subsets (mean ± sample SD)")
    axes[0].set_title("Cover size: lower is better")
    axes[0].set_ylim(bottom=0)
    axes[1].set_ylabel("Complete solver time (ms, mean, log scale)")
    axes[1].set_title("Runtime: includes construction and cleanup")
    axes[1].set_yscale("log")
    for ax in axes:
        ax.set_xticks(range(len(names)), names, rotation=45, ha="right")
        ax.grid(axis="y", alpha=0.2)
        ax.set_axisbelow(True)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].legend(frameon=False, fontsize=9)
    fig.suptitle("Unit-cost E / CLR / CYC benchmarks", fontsize=15)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output.with_suffix(".png"), dpi=160)
    fig.savefig(output.with_suffix(".svg"))
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("summary", type=Path)
    parser.add_argument("--output", type=Path, required=True, help="output filename stem")
    args = parser.parse_args()
    plot(args.summary, args.output)
