#!/usr/bin/env python3
"""
ALP-IX-007: Alpaca ML cohort — UW × macro interaction expansion (mlx_* prefix).

Reads a flattened cohort CSV (e.g. reports/Gemini/alpaca_ml_cohort_flat_UW.csv), multiplies
``uw_gamma_skew`` and ``uw_tide_score`` against selected macro drivers, and writes an expanded CSV.

Macro drivers (first matching column name in the header):
  - ``mlf_scoreflow_total_score`` (exact)
  - first header containing ``vxx_vxz_ratio``
  - first header containing ``futures_direction_delta``

Each product column: ``mlx_<uw_col>_x_<slug(macro_header)>`` with finite-float coercion and 0.0 fill.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

_UW_COLS = ("uw_gamma_skew", "uw_tide_score")


def _finite_float(x: Any) -> float:
    if x is None:
        return 0.0
    s = str(x).strip()
    if s == "" or s.lower() in ("none", "null", "nan"):
        return 0.0
    try:
        v = float(s)
    except (TypeError, ValueError):
        return 0.0
    return v if math.isfinite(v) else 0.0


def _slug_header(h: str, *, max_len: int = 72) -> str:
    s = re.sub(r"[^a-zA-Z0-9_]+", "_", h).strip("_")
    if len(s) > max_len:
        s = s[-max_len:].lstrip("_")
    return s or "macro"


def _resolve_macro_columns(headers: Sequence[str]) -> List[Tuple[str, str]]:
    """Returns list of (logical_name, header) for each macro column to interact."""
    hset = list(headers)
    found: List[Tuple[str, str]] = []

    if "mlf_scoreflow_total_score" in hset:
        found.append(("mlf_scoreflow_total_score", "mlf_scoreflow_total_score"))

    for h in hset:
        if "vxx_vxz_ratio" in h:
            found.append(("vxx_vxz_ratio", h))
            break

    for h in hset:
        if "futures_direction_delta" in h:
            found.append(("futures_direction_delta", h))
            break

    return found


def expand_interactions(
    rows: List[Dict[str, str]],
    headers: List[str],
) -> Tuple[List[str], List[Dict[str, str]]]:
    macros = _resolve_macro_columns(headers)
    if len(macros) < 3:
        missing = {"mlf_scoreflow_total_score", "vxx_vxz_ratio", "futures_direction_delta"} - {
            m[0] for m in macros
        }
        raise SystemExit(
            "Could not resolve all macro columns for ALP-IX-007. "
            f"Found: {[m[1] for m in macros]}. Missing logical: {sorted(missing)}"
        )

    pairs: List[Tuple[str, str, str]] = []
    seen_col: set[str] = set()
    for uw in _UW_COLS:
        if uw not in headers:
            raise SystemExit(f"CSV missing required UW column {uw!r}")
        for logical, macro_h in macros:
            stem = _slug_header(logical)
            col = f"mlx_{uw}_x_{stem}"
            base = col
            n = 0
            while col in seen_col:
                n += 1
                col = f"{base}_{n}"
            seen_col.add(col)
            pairs.append((col, uw, macro_h))

    out_rows: List[Dict[str, str]] = []
    for r in rows:
        out = dict(r)
        for col, uw, macro_h in pairs:
            u = _finite_float(r.get(uw))
            m = _finite_float(r.get(macro_h))
            out[col] = f"{u * m:.10g}"
        out_rows.append(out)

    out_headers = list(headers) + [p[0] for p in pairs]
    return out_headers, out_rows


def main() -> int:
    ap = argparse.ArgumentParser(description="ALP-IX-007: expand UW×macro interactions (mlx_*).")
    ap.add_argument(
        "--in-csv",
        type=Path,
        default=REPO_ROOT / "reports" / "Gemini" / "alpaca_ml_cohort_flat_UW.csv",
        help="Input flattened cohort CSV.",
    )
    ap.add_argument(
        "--out-csv",
        type=Path,
        default=REPO_ROOT / "reports" / "Gemini" / "alpaca_ml_cohort_flat_UW_IX.csv",
        help="Output CSV with mlx_* interaction columns appended.",
    )
    args = ap.parse_args()
    inp = args.in_csv.resolve()
    outp = args.out_csv.resolve()
    if not inp.is_file():
        print(f"Missing input: {inp}", file=sys.stderr)
        return 1

    with inp.open("r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.DictReader(f)
        headers = list(reader.fieldnames or [])
        rows = [dict(x) for x in reader]

    out_headers, out_rows = expand_interactions(rows, headers)
    outp.parent.mkdir(parents=True, exist_ok=True)
    with outp.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=out_headers, extrasaction="ignore")
        w.writeheader()
        for r in out_rows:
            w.writerow({h: r.get(h, "") for h in out_headers})

    added = [h for h in out_headers if h.startswith("mlx_")]
    print(
        json.dumps(
            {
                "in_csv": str(inp),
                "out_csv": str(outp),
                "rows": len(out_rows),
                "mlx_columns": added,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
