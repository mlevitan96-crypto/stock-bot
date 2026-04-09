#!/usr/bin/env python3
"""
Alpaca Harvester cohort — strict gold-standard ingestion for ML (no live model deployment).

Loads flattened CSV from scripts/telemetry/alpaca_ml_flattener.py, drops any row with:
  - missing / non-finite realized_pnl_usd (no crypto-style silent PnL gaps)
  - NaN / empty required feature columns (no zero imputation before filtering)

Default: print-only (--dry-run). Use --fit only after explicit operator approval.

Usage (repo root):
  PYTHONPATH=. python3 src/ml/alpaca_cohort_train.py --csv reports/Gemini/alpaca_ml_cohort_flat.csv
  PYTHONPATH=. python3 src/ml/alpaca_cohort_train.py --feature-mode strict_scoreflow --fit
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]


def _finite_scalar(v: Any) -> bool:
    if v is None:
        return False
    s = str(v).strip()
    if s == "":
        return False
    try:
        return math.isfinite(float(s))
    except (TypeError, ValueError):
        return False


def _pick_feature_columns(headers: Sequence[str], mode: str) -> List[str]:
    h = list(headers)
    if mode == "strict_scoreflow":
        cols = [x for x in h if x.startswith("mlf_scoreflow_components_")]
        cols = sorted(cols)
        if "mlf_scoreflow_total_score" not in h:
            raise SystemExit("CSV missing mlf_scoreflow_total_score")
        return ["mlf_scoreflow_total_score"] + cols
    if mode == "strict_entry_snapshot":
        # Rows that were filled from entry_snapshots.jsonl use same mlf_scoreflow_* column names.
        cols = [x for x in h if x.startswith("mlf_scoreflow_components_")]
        return ["mlf_scoreflow_total_score"] + sorted(cols)
    raise SystemExit(f"Unknown --feature-mode: {mode}")


def load_and_filter(
    path: Path,
    *,
    feature_mode: str,
    require_join_tier: str | None = None,
) -> Tuple[List[str], List[Dict[str, str]], Dict[str, int]]:
    """
    Returns (headers, kept_rows, stats).
    """
    with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
        r = csv.DictReader(f)
        headers = list(r.fieldnames or [])
        rows = [dict(x) for x in r]

    stats = {
        "gross_rows": len(rows),
        "dropped_missing_pnl": 0,
        "dropped_join_tier": 0,
        "dropped_feature_nan": 0,
        "kept": 0,
    }

    if "realized_pnl_usd" not in headers:
        raise SystemExit("CSV missing realized_pnl_usd (required label)")

    feat_cols = _pick_feature_columns(headers, feature_mode)

    kept: List[Dict[str, str]] = []
    for row in rows:
        if not _finite_scalar(row.get("realized_pnl_usd")):
            stats["dropped_missing_pnl"] += 1
            continue
        if require_join_tier:
            if (row.get("mlf_scoreflow_join_tier") or "").strip() != require_join_tier:
                stats["dropped_join_tier"] += 1
                continue
        bad = False
        for c in feat_cols:
            if not _finite_scalar(row.get(c)):
                bad = True
                break
        if bad:
            stats["dropped_feature_nan"] += 1
            continue
        kept.append(row)
        stats["kept"] += 1

    return headers, kept, stats


def main() -> int:
    ap = argparse.ArgumentParser(description="Alpaca cohort strict ML ingestion (drop NaN/empty; no imputation).")
    ap.add_argument(
        "--csv",
        type=Path,
        default=REPO_ROOT / "reports" / "Gemini" / "alpaca_ml_cohort_flat.csv",
        help="Flattened cohort CSV (alpaca_ml_flattener output).",
    )
    ap.add_argument(
        "--feature-mode",
        choices=("strict_scoreflow", "strict_entry_snapshot"),
        default="strict_scoreflow",
        help="strict_scoreflow: require all mlf_scoreflow_components_* + total. "
        "strict_entry_snapshot: same columns but only rows with join tier entry_snapshot.",
    )
    ap.add_argument(
        "--fit",
        action="store_true",
        help="Fit a shallow sanity model (requires sklearn). Default is dry-run counts only.",
    )
    args = ap.parse_args()
    path = args.csv.resolve()
    if not path.is_file():
        print(f"Missing CSV: {path}", file=sys.stderr)
        return 1

    require_tier = "entry_snapshot" if args.feature_mode == "strict_entry_snapshot" else None
    headers, kept, stats = load_and_filter(path, feature_mode=args.feature_mode, require_join_tier=require_tier)

    print("=== Alpaca cohort strict gold-standard ingestion ===")
    print(f"csv: {path}")
    print(f"feature_mode: {args.feature_mode}")
    print(f"gross_rows: {stats['gross_rows']}")
    print(f"dropped_missing_or_nonfinite_pnl: {stats['dropped_missing_pnl']}")
    print(f"dropped_join_tier_mismatch: {stats['dropped_join_tier']}")
    print(f"dropped_incomplete_or_nonfinite_features: {stats['dropped_feature_nan']}")
    print(f"ML_READY_ROWS: {stats['kept']}")

    if stats["kept"] == 0:
        print("No rows passed strict filter; abort.", file=sys.stderr)
        return 2

    if not args.fit:
        print("\nDry-run only (no model). Pass --fit to train after explicit approval.")
        return 0

    try:
        import numpy as np
        from sklearn.tree import DecisionTreeClassifier
    except ImportError:
        print("Install scikit-learn and numpy for --fit.", file=sys.stderr)
        return 1

    feat_cols = _pick_feature_columns(headers, args.feature_mode)
    X = np.zeros((len(kept), len(feat_cols)), dtype=np.float64)
    y = np.zeros(len(kept), dtype=np.int64)
    for i, row in enumerate(kept):
        for j, c in enumerate(feat_cols):
            X[i, j] = float(row[c])
        y[i] = 1 if float(row["realized_pnl_usd"]) > 0 else 0

    clf = DecisionTreeClassifier(max_depth=3, min_samples_leaf=max(3, len(kept) // 50), random_state=42)
    clf.fit(X, y)
    print(f"\nSanity fit: DecisionTreeClassifier on {len(kept)} strict rows, {len(feat_cols)} features (NOT deployed).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
