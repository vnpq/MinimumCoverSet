# Benchmark data provenance

These nine files are original **unit-cost** OR-Library row-format instances:
E1–E5, CLR10, CLR11, CYC6 and CYC7. They belong to the E/CLR/CYC families listed
in the assignment's [USCP_instances collection](https://github.com/pinam45/USCP_instances).
The bytes were obtained from its original source,
[J. E. Beasley's OR-Library](https://people.brunel.ac.uk/~mastjjb/jeb/orlib/scpinfo.html).
No costs, rows, columns or subset names in the source files were rewritten.

`sources.json` records original URLs, retrieval time, dimensions and SHA-256
hashes. `python scripts/fetch_benchmarks.py` validates all costs, dimensions and
hashes; it downloads missing files and refuses changed bytes. The files are
included so the recorded experiments can run without network access.

The reader maps row `i` to element `i-1` and column `j` to named subset `Sj`.
The source header gives row count, column count, one cost per column, then the
count and one-based column IDs covering each row. Other formats and weighted
instances are rejected or unsupported; costs must not silently be replaced by one.

Reference values and exact source locations are recorded in
`experiments/benchmarks.json`: E1–E5 have reported optimum 5 (Nan Li, 2017, Table
1.4). CLR10=25, CLR11=23, CYC6=60 and CYC7=144 are treated conservatively as
**historical published best-known upper bounds** (Zahra Naji-Azimi, 2010, Table
1.5), not a claim of present-day records or proven optima. See the report for
source links and the two separate gap metrics.

The original sources attribute E to J. E. Beasley's 1987 set-covering collection
and CYC/CLR to T. Grossman and A. Wool's approximation-algorithm experiments.
Consult the linked source for the full bibliographic references.
