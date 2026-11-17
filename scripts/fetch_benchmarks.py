"""Download nine original unit-cost OR-Library instances and verify their hashes."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

from min_cover_set.io import parse_orlibrary

BASE_URL = "https://people.brunel.ac.uk/~mastjjb/jeb/orlib/files/"
INSTANCES = {
    **{f"scpe{i}.txt": (50, 500) for i in range(1, 6)},
    "scpclr10.txt": (511, 210), "scpclr11.txt": (1023, 330),
    "scpcyc06.txt": (240, 192), "scpcyc07.txt": (672, 448),
}


def fetch(destination: Path):
    destination.mkdir(parents=True, exist_ok=True)
    lock_path = destination / "sources.json"
    previous = json.loads(lock_path.read_text()) if lock_path.exists() else None
    expected = {item["file"]: item["sha256"] for item in previous["files"]} if previous else {}
    files = []
    for filename, shape in INSTANCES.items():
        path, url = destination / filename, BASE_URL + filename
        if path.exists():
            raw = path.read_bytes()
        else:
            request = Request(url, headers={"User-Agent": "MinimumCoverSet/0.1 academic experiment"})
            with urlopen(request, timeout=30) as response:
                raw = response.read()
        digest = hashlib.sha256(raw).hexdigest()
        if filename in expected and digest != expected[filename]:
            raise ValueError(f"checksum mismatch for {filename}; original bytes have changed")
        instance = parse_orlibrary(raw.decode("utf-8-sig"))
        if (len(instance.universe), len(instance.subsets)) != shape:
            raise ValueError(f"unexpected dimensions for {filename}")
        if not path.exists():
            path.write_bytes(raw)
        files.append({"file": filename, "url": url, "sha256": digest,
                      "rows": shape[0], "columns": shape[1], "all_costs_one": True})
        print(f"{filename}: verified {shape[0]} elements, {shape[1]} subsets", flush=True)
    if previous is None:
        lock_path.write_text(json.dumps({
            "retrieved_utc": datetime.now(timezone.utc).isoformat(),
            "collection": "https://github.com/pinam45/USCP_instances",
            "original_source": "https://people.brunel.ac.uk/~mastjjb/jeb/orlib/scpinfo.html",
            "files": files,
        }, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path,
                        default=Path(__file__).resolve().parents[1] / "data/benchmarks")
    arguments = parser.parse_args()
    fetch(arguments.destination)
