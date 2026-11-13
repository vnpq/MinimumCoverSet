"""Load existing named-subset JSON or unit-cost OR-Library row data."""

import json
from pathlib import Path

from .model import SetCoverInstance


def instance_from_dict(payload: dict) -> SetCoverInstance:
    if not isinstance(payload, dict) or not {"universe", "subsets"} <= payload.keys():
        raise ValueError("JSON must contain universe and subsets")
    if not isinstance(payload["universe"], list) or not isinstance(payload["subsets"], dict):
        raise ValueError("universe must be an array and subsets must be a named object")
    if any(not isinstance(values, list) for values in payload["subsets"].values()):
        raise ValueError("each named subset must be an array")
    if "costs" in payload:
        costs = payload["costs"]
        if not isinstance(costs, dict) or costs.keys() != payload["subsets"].keys():
            raise ValueError("costs must have exactly the same names as subsets")
        if any(type(cost) not in (int, float) or cost != 1 for cost in costs.values()):
            raise ValueError("only unweighted inputs with all costs = 1 are supported")
    try:
        return SetCoverInstance.from_collections(payload["universe"], payload["subsets"])
    except TypeError as exc:
        raise ValueError("universe and subset elements must be hashable JSON values") from exc


def parse_orlibrary(text: str) -> SetCoverInstance:
    """Rows, columns, column costs, then covering-column IDs for each row.

    Preserve source columns as S1, S2, ... and map row i to element i-1.
    Reject weighted data and malformed or trailing tokens. RAIL's column
    format and Steiner variants require their own explicit adapters.
    """
    try:
        tokens = iter(int(value) for value in text.split())
        rows, columns = next(tokens), next(tokens)
        if rows < 0 or columns < 0:
            raise ValueError("row and column counts must be nonnegative")
        costs = [next(tokens) for _ in range(columns)]
        if any(cost != 1 for cost in costs):
            raise ValueError("weighted input rejected: all column costs must equal 1")
        subsets = {f"S{j+1}": set() for j in range(columns)}
        for row in range(rows):
            count = next(tokens)
            if not 0 <= count <= columns:
                raise ValueError("invalid row coverage count")
            ids = [next(tokens) for _ in range(count)]
            if len(set(ids)) != count or any(not 1 <= j <= columns for j in ids):
                raise ValueError("duplicate or out-of-range column ID")
            for j in ids:
                subsets[f"S{j}"].add(row)
        if next(tokens, None) is not None:
            raise ValueError("unexpected trailing tokens")
    except StopIteration as exc:
        raise ValueError("truncated OR-Library input") from exc
    return SetCoverInstance.from_collections(range(rows), subsets)


def load_instance(path: str | Path, *, format: str = "auto") -> SetCoverInstance:
    path = Path(path)
    text = path.read_text(encoding="utf-8-sig")
    if format == "auto":
        format = "json" if path.suffix.lower() == ".json" else "orlib"
    if format == "json":
        return instance_from_dict(json.loads(text))
    if format == "orlib":
        return parse_orlibrary(text)
    raise ValueError("format must be auto, json or orlib")
