#!/usr/bin/env python3
"""
Alpha 10 Massive Review: combinatorial clusters (size 3–4) over feature-group proxies vs binary label.

Reads ``alpha10_labeled_cohort.jsonl`` from ``prepare_training_data.py``.
Maps each column to one of 10 canonical "algorithms" by name heuristics (OFI, GEX, VAMP, …).
Per trade and per algorithm: aggregate = nanmean of z-scored member columns.
Per cluster: meta_score = row-wise nanmean of member algorithm aggregates.
Ranks clusters by |point-biserial correlation| with ``label`` (scipy); reports top-N and Markdown.

This is an offline exploratory screen — not a live gate.

Usage:
  PYTHONPATH=. python scripts/research/massive_alpha_review.py \\
    --in-jsonl reports/research/alpha10_labeled_cohort.jsonl \\
    --out-md reports/research/ALPHA_10_MASSIVE_REVIEW.md
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

import numpy as np

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from scipy import stats
except ImportError:
    stats = None  # type: ignore


# Ten canonical families — substring match on lower-cased column name (first matching group wins).
# Order matters: e.g. ``etf_flow`` column names contain ``flow`` — ETF must appear before FLOW.
# Keys in cohort JSONL are flattened ``snap_*`` / ``euw_*`` / ``xuw_*`` (see prepare_training_data.py).
ALPHA10_GROUPS: List[Tuple[str, Tuple[str, ...]]] = [
    (
        "OFI",
        (
            "ftd_pressure",
            "ftd",
            "institutional",
            "motif_bonus",
            "motif",
            "ofi",
            "order_flow",
            "orderflow",
            "delta_volume",
        ),
    ),
    ("GEX", ("gex", "gamma_exposure", "greeks_gamma", "dealer_gamma", "charm")),
    ("VAMP", ("freshness", "market_tide", "vamp", "volume_at", "vwap_dev", "vwap", "tide")),
    (
        "HMM",
        ("hmm", "regime_id", "regime_state", "markov", "hidden_state", "regime", "calendar"),
    ),
    # Before FLOW so ``snap_etf_flow`` / ``etf_flow`` do not match the generic ``flow`` token.
    ("ETF", ("etf_flow", "etf_", "sector_etf", "sector_alignment", "risk_on")),
    ("FLOW", ("shorts_squeeze", "squeeze_score", "squeeze", "shorts", "whale", "sweep", "urgency", "conviction", "flow_strength", "flow")),
    ("DARK", ("dark_pool", "darkpool", "darkpool_bias", "dp_", "block_net")),
    ("IV_SK", ("iv_", "skew", "smile", "percentile_iv", "iv_rank")),
    ("OI", ("oi_", "open_interest", "net_oi")),
    (
        "SENT",
        (
            "sentiment",
            "sentiment_score",
            "toxicity",
            "x_news",
            "congress_",
            "congress",
            "insider",
            "event",
            "earnings",
        ),
    ),
]


def _load_rows(path: Path) -> List[dict]:
    rows: List[dict] = []
    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def _all_feature_keys(rows: List[dict]) -> List[str]:
    keys: set[str] = set()
    for r in rows:
        fe = r.get("features")
        if isinstance(fe, dict):
            keys.update(str(k) for k in fe.keys())
    return sorted(keys)


def _assign_group(col: str) -> int:
    c = col.lower()
    for i, (_, pats) in enumerate(ALPHA10_GROUPS):
        for p in pats:
            if p in c:
                return i
    return -1


def _build_matrix(rows: List[dict], keys: Sequence[str]) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """X_all (n, F), y (n,), list of column names."""
    y = np.array([int(r.get("label", 0)) for r in rows], dtype=float)
    mat = np.full((len(rows), len(keys)), np.nan, dtype=float)
    for i, r in enumerate(rows):
        fe = r.get("features") if isinstance(r.get("features"), dict) else {}
        for j, k in enumerate(keys):
            v = fe.get(k)
            if v is None:
                continue
            try:
                x = float(v)
                if math.isfinite(x):
                    mat[i, j] = x
            except (TypeError, ValueError):
                continue
    return mat, y, list(keys)


def _nanmean_axis1_safe(block: np.ndarray) -> np.ndarray:
    """Mean along axis=1 ignoring NaNs; rows with no finite values → NaN (no RuntimeWarning)."""
    if block.ndim != 2:
        raise ValueError("expected 2d array")
    if block.shape[1] == 0:
        return np.full(block.shape[0], np.nan, dtype=float)
    sums = np.nansum(block, axis=1)
    counts = np.sum(np.isfinite(block), axis=1).astype(float)
    out = np.full(block.shape[0], np.nan, dtype=float)
    nz = counts > 0
    out[nz] = sums[nz] / counts[nz]
    return out


def _zscore_cols(X: np.ndarray) -> np.ndarray:
    out = np.array(X, dtype=float, copy=True)
    for j in range(out.shape[1]):
        col = out[:, j]
        m = np.nanmean(col)
        s = np.nanstd(col)
        if s and math.isfinite(s) and s > 1e-12:
            out[:, j] = (col - m) / s
        else:
            out[:, j] = np.where(np.isfinite(col), 0.0, np.nan)
    return out


def _algo_aggregate_matrix(Xz: np.ndarray, key_groups: List[int]) -> np.ndarray:
    """Return (n, 10) with nan where algo has no columns."""
    n = Xz.shape[0]
    A = np.full((n, len(ALPHA10_GROUPS)), np.nan, dtype=float)
    for g in range(len(ALPHA10_GROUPS)):
        idx = [j for j, gg in enumerate(key_groups) if gg == g]
        if not idx:
            continue
        block = Xz[:, idx]
        A[:, g] = _nanmean_axis1_safe(block)
    return A


def _cluster_meta(A: np.ndarray, combo: Tuple[int, ...]) -> np.ndarray:
    if not combo:
        return np.full(A.shape[0], np.nan, dtype=float)
    cols = A[:, list(combo)]
    return _nanmean_axis1_safe(cols)


def _biserial(y: np.ndarray, s: np.ndarray) -> Tuple[float, float]:
    if stats is None:
        return float("nan"), float("nan")
    m = np.isfinite(s) & np.isfinite(y)
    if int(np.sum(m)) < 8:
        return float("nan"), float("nan")
    r, p = stats.pointbiserialr(y[m], s[m])
    try:
        rp = float(r)
        pp = float(p)
        if not math.isfinite(rp):
            return float("nan"), float("nan")
        return rp, pp
    except Exception:
        return float("nan"), float("nan")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-jsonl", type=Path, required=True)
    ap.add_argument("--out-md", type=Path, default=_ROOT / "reports" / "research" / "ALPHA_10_MASSIVE_REVIEW.md")
    ap.add_argument("--top", type=int, default=25, help="Top clusters per size to list in Markdown")
    args = ap.parse_args()
    path = args.in_jsonl.resolve()
    if not path.is_file():
        print(f"Missing input: {path}", file=sys.stderr)
        return 2

    rows = _load_rows(path)
    if len(rows) < 10:
        print("Too few rows for combinatorial review.", file=sys.stderr)
        return 2

    keys = _all_feature_keys(rows)
    if not keys:
        print("No feature columns found.", file=sys.stderr)
        return 2

    key_groups = [_assign_group(k) for k in keys]
    dropped = sum(1 for g in key_groups if g < 0)
    X, y, _ = _build_matrix(rows, keys)
    Xz = _zscore_cols(X)
    A = _algo_aggregate_matrix(Xz, key_groups)

    results: List[Tuple[int, Tuple[int, ...], float, float, float]] = []
    # (size, combo, r, p, abs_r)
    for k in (3, 4):
        for combo in itertools.combinations(range(len(ALPHA10_GROUPS)), k):
            if not all(np.any(np.isfinite(A[:, j])) for j in combo):
                continue
            meta = _cluster_meta(A, combo)
            r, p = _biserial(y, meta)
            results.append((k, combo, r, p, abs(r) if math.isfinite(r) else -1.0))

    results.sort(key=lambda x: -x[4])

    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    lines: List[str] = []
    lines.append("# Alpha 10 — Massive offline review\n\n")
    lines.append(f"- **Input:** `{path}`  \n")
    lines.append(f"- **Trades:** {len(rows)}  \n")
    lines.append(f"- **Feature columns:** {len(keys)} (unassigned to any of 10 groups: {dropped})  \n")
    lines.append(f"- **Method:** z-score columns → group mean per `{len(ALPHA10_GROUPS)}` families → cluster mean → point-biserial vs `label`.  \n")
    if stats is None:
        lines.append("- **Warning:** `scipy` not installed; correlations skipped.  \n")
    lines.append("\n## 1) Canonical algorithm buckets (name heuristics)\n\n")
    lines.append("| ID | Name | Substring keys |\n")
    lines.append("|---:|------|----------------|\n")
    for i, (name, pats) in enumerate(ALPHA10_GROUPS):
        lines.append(f"| {i} | {name} | `{', '.join(pats)}` |\n")

    for k in (3, 4):
        sub = [t for t in results if t[0] == k][: int(args.top)]
        lines.append(f"\n## 2) Top {args.top} clusters (size {k}) by |ρ| (point-biserial)\n\n")
        lines.append("| Rank | Algorithms | ρ | p-value | |ρ| |\n")
        lines.append("|-----:|------------|--:|--------:|----:|\n")
        for rank, (_, combo, r, p, ar) in enumerate(sub, 1):
            names = " + ".join(ALPHA10_GROUPS[j][0] for j in combo)
            pr = f"{p:.4g}" if math.isfinite(p) else "NA"
            rr = f"{r:.4f}" if math.isfinite(r) else "NA"
            lines.append(f"| {rank} | {names} | {rr} | {pr} | {ar:.4f} |\n")

    lines.append("\n## 3) Coverage — finite rows per algorithm aggregate\n\n")
    lines.append("| Algorithm | finite % |\n")
    lines.append("|-----------|--------:|\n")
    for j, (name, _) in enumerate(ALPHA10_GROUPS):
        frac = float(np.mean(np.isfinite(A[:, j]))) * 100.0
        lines.append(f"| {name} | {frac:.1f}% |\n")

    lines.append("\n## 4) Interpretation (Quant / SRE)\n\n")
    lines.append(
        "- **Heuristic buckets** map many similarly named columns; refine mappings before production ML.\n"
        "- **Point-biserial** is a linear screen; interactions and nonlinearity are not modeled here.\n"
        "- **Look-ahead:** features are entry-time snapshots + `entry_uw` where present — verify no post-entry leakage for your modeling policy.\n"
    )

    args.out_md.write_text("".join(lines), encoding="utf-8")
    print(f"Wrote {args.out_md} ({len(results)} cluster scores evaluated)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
