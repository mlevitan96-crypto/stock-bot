#!/usr/bin/env python3
"""
Profitability decile test: bucket flattened ML cohort trades by entry composite score,
report PnL by decile, and summarize monotonicity (Spearman: decile rank vs mean PnL).

Read-only. Default input: reports/Gemini/alpaca_ml_cohort_flat.csv (from alpaca_ml_flattener).
"""
from __future__ import annotations

import argparse
import csv
import math
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _infer_repo_root() -> Path:
    env = os.environ.get("ALPACA_ROOT") or os.environ.get("STOCKBOT_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    p = Path(__file__).resolve()
    if p.parent.name == "analysis" and p.parent.parent.name == "scripts":
        return p.parent.parent.parent
    return Path.cwd()


REPO_ROOT = _infer_repo_root()
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np
from scipy.stats import spearmanr


def _safe_float(x: Any) -> Optional[float]:
    if x is None or (isinstance(x, str) and not str(x).strip()):
        return None
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(v):
        return None
    return v


def _entry_score(row: Dict[str, str]) -> Optional[float]:
    """Primary: mlf_scoreflow_total_score; fallback: sum of mlf_scoreflow_components_*."""
    total = _safe_float(row.get("mlf_scoreflow_total_score"))
    imputed = str(row.get("mlf_scoreflow_total_score_imputed", "")).strip() in ("1", "true", "True")
    if total is not None and not imputed:
        return total
    if total is not None and imputed:
        return total
    s = 0.0
    n = 0
    for k, v in row.items():
        if not k.startswith("mlf_scoreflow_components_"):
            continue
        fv = _safe_float(v)
        if fv is not None:
            s += fv
            n += 1
    if n == 0:
        return total
    return s


def _equal_frequency_deciles(scores: np.ndarray) -> np.ndarray:
    """Decile labels 0..9 (0 = lowest scores). Equal-count bins (last decile absorbs remainder)."""
    n = len(scores)
    order = np.argsort(scores, kind="mergesort")
    out = np.zeros(n, dtype=np.int64)
    for d in range(10):
        lo = (d * n) // 10
        hi = ((d + 1) * n) // 10 if d < 9 else n
        out[order[lo:hi]] = d
    return out


def load_cohort_rows(path: Path) -> Tuple[List[Dict[str, str]], List[float], List[float]]:
    rows: List[Dict[str, str]] = []
    scores: List[float] = []
    pnls: List[float] = []
    if not path.is_file():
        return rows, scores, pnls
    with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return rows, scores, pnls
        for raw in reader:
            if not raw:
                continue
            pnl = _safe_float(raw.get("realized_pnl_usd"))
            sc = _entry_score(raw)
            if pnl is None or sc is None:
                continue
            rows.append(raw)
            scores.append(sc)
            pnls.append(pnl)
    return rows, scores, pnls


def main() -> int:
    ap = argparse.ArgumentParser(description="Decile PnL analysis on flattened ML cohort CSV.")
    ap.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Repo root (defaults to ALPACA_ROOT / STOCKBOT_ROOT / inferred from script path / cwd).",
    )
    ap.add_argument(
        "--csv",
        type=Path,
        default=None,
        help="Path to alpaca_ml_cohort_flat.csv (default: <root>/reports/Gemini/alpaca_ml_cohort_flat.csv).",
    )
    args = ap.parse_args()
    root = (args.root or REPO_ROOT).resolve()
    path = (args.csv or (root / "reports" / "Gemini" / "alpaca_ml_cohort_flat.csv")).resolve()

    rows, scores_l, pnls_l = load_cohort_rows(path)
    n = len(rows)

    if not path.is_file() or n == 0:
        print("# Alpaca decile PnL analysis")
        print()
        print("**Awaiting new post-purge trade data to calculate deciles.**")
        print()
        print(f"- Expected cohort file: `{path}` (repo root: `{root}`)")
        print("- Regenerate after trades exist: `PYTHONPATH=. python3 scripts/telemetry/alpaca_ml_flattener.py --root <repo>`")
        return 0

    scores = np.array(scores_l, dtype=np.float64)
    pnls = np.array(pnls_l, dtype=np.float64)
    dec = _equal_frequency_deciles(scores)

    per_dec: Dict[int, Dict[str, Any]] = {
        d: {"wins": 0, "count": 0, "sum_pnl": 0.0, "score_min": math.inf, "score_max": -math.inf}
        for d in range(10)
    }
    for i in range(n):
        d = int(dec[i])
        per_dec[d]["count"] += 1
        per_dec[d]["sum_pnl"] += float(pnls[i])
        if pnls[i] > 0:
            per_dec[d]["wins"] += 1
        per_dec[d]["score_min"] = min(per_dec[d]["score_min"], float(scores[i]))
        per_dec[d]["score_max"] = max(per_dec[d]["score_max"], float(scores[i]))

    dec_indices = np.arange(10, dtype=np.float64)
    mean_pnls = np.array(
        [
            (per_dec[d]["sum_pnl"] / per_dec[d]["count"]) if per_dec[d]["count"] else float("nan")
            for d in range(10)
        ],
        dtype=np.float64,
    )
    mask = np.isfinite(mean_pnls) & np.array([per_dec[d]["count"] > 0 for d in range(10)])
    if mask.sum() >= 2:
        rho, pval = spearmanr(dec_indices[mask], mean_pnls[mask])
        rho_f = float(rho) if rho == rho else 0.0
        pval_f = float(pval) if pval == pval else 1.0
    else:
        rho_f, pval_f = 0.0, 1.0

    # Adjacent weak monotonicity: consecutive decile indices (d vs d+1) where both populated
    adj_pairs = 0
    adj_inc = 0
    for d in range(9):
        if per_dec[d]["count"] and per_dec[d + 1]["count"]:
            adj_pairs += 1
            if mean_pnls[d + 1] >= mean_pnls[d]:
                adj_inc += 1
    adj_mono = (adj_inc / adj_pairs) if adj_pairs else None

    print("# Alpaca profitability decile analysis")
    print()
    print(f"- **Trades analyzed:** {n}")
    print(f"- **Cohort file:** `{path}`")
    print(f"- **Score used:** `mlf_scoreflow_total_score` (fallback: sum of `mlf_scoreflow_components_*`)")
    zero_frac = float(np.mean(np.abs(scores) < 1e-9))
    if zero_frac > 0.15:
        print(
            f"- **Data quality:** {100.0 * zero_frac:.1f}% of trades have score ≈ 0 (neutral / imputed / missing join). "
            "Decile ranks are partly **ties**, not a clean conviction ladder."
        )
    print()
    print("## Decile table (decile 0 = weakest scores, 9 = strongest)")
    print()
    print("| Decile | Trade count | Win rate % | Mean PnL ($) | Total PnL ($) | Score min | Score max |")
    print("|--------|-------------|------------|--------------|---------------|-----------|-----------|")
    for d in range(10):
        c = per_dec[d]["count"]
        if c == 0:
            print(f"| {d} | 0 | — | — | — | — | — |")
            continue
        wr = 100.0 * per_dec[d]["wins"] / c
        mean_p = per_dec[d]["sum_pnl"] / c
        tot = per_dec[d]["sum_pnl"]
        smin = per_dec[d]["score_min"]
        smax = per_dec[d]["score_max"]
        print(
            f"| {d} | {c} | {wr:.1f} | {mean_p:.4f} | {tot:.4f} | {smin:.4f} | {smax:.4f} |"
        )
    print()
    print("## Monotonicity")
    print()
    print(
        f"- **Spearman ρ (decile index vs mean PnL):** {rho_f:.4f} (two-sided p ≈ {pval_f:.4g} on non-empty deciles)"
    )
    if adj_mono is not None:
        print(f"- **Adjacent non-decreasing rate (weak):** {adj_mono:.2%} across populated decile steps")
    print()
    print("## Quant verdict (heuristic, not investment advice)")
    print()
    if n < 40:
        print(
            "- **Sample:** Very small cohort; deciles are thin. Any pattern is **not** statistically credible."
        )
    if rho_f > 0.3 and pval_f < 0.1 and n >= 40:
        print(
            "- **Edge signal:** Mean PnL tends to rise with score decile (positive monotonicity). "
            "Worth deeper OOS testing and cost-adjusted attribution — **not** proof of tradable alpha alone."
        )
    elif rho_f < -0.2:
        print(
            "- **Inverted / perverse:** Higher scores associate with **worse** mean PnL in this slice. "
            "Signal logic or join quality should be treated as suspect until reconciled."
        )
    else:
        print(
            "- **Random-walk-like:** Weak or flat relationship between score decile and mean PnL. "
            "This cohort does **not** demonstrate a clear monotonic edge from the composite score alone."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
