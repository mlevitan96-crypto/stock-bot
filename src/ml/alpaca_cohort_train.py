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
  PYTHONPATH=. python3 src/ml/alpaca_cohort_train.py --calibration-gate
  PYTHONPATH=. python3 src/ml/alpaca_cohort_train.py --calibration-gate-precision
"""
from __future__ import annotations

import argparse
import csv
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]

_TID_RE = re.compile(r"^open_([A-Z0-9]+)_(.+)$")


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
        from telemetry.ml_scoreflow_contract import mlf_scoreflow_component_column_names

        # Allowlist only canonical v2 composite keys (avoids sparse union columns from nested drift).
        cols = [c for c in mlf_scoreflow_component_column_names() if c in h]
        missing = set(mlf_scoreflow_component_column_names()) - set(cols)
        if missing:
            raise SystemExit(
                "CSV missing canonical scoreflow columns (re-run alpaca_ml_flattener): "
                + ", ".join(sorted(missing)[:8])
                + ("…" if len(missing) > 8 else "")
            )
        if "mlf_scoreflow_total_score" not in h:
            raise SystemExit("CSV missing mlf_scoreflow_total_score")
        return ["mlf_scoreflow_total_score"] + cols
    if mode == "strict_entry_snapshot":
        from telemetry.ml_scoreflow_contract import mlf_scoreflow_component_column_names

        cols = [c for c in mlf_scoreflow_component_column_names() if c in h]
        if len(cols) < len(mlf_scoreflow_component_column_names()):
            raise SystemExit("CSV missing canonical scoreflow columns for strict_entry_snapshot")
        if "mlf_scoreflow_total_score" not in h:
            raise SystemExit("CSV missing mlf_scoreflow_total_score")
        return ["mlf_scoreflow_total_score"] + cols
    raise SystemExit(f"Unknown --feature-mode: {mode}")


def _entry_epoch_from_flat_row(row: Dict[str, str]) -> Optional[float]:
    """Best-effort entry time as Unix epoch (UTC) for flat CSV rows."""
    raw = (row.get("strict_open_epoch_utc") or "").strip()
    if raw:
        try:
            return float(raw)
        except ValueError:
            pass
    tid = str(row.get("trade_id") or "").strip()
    m = _TID_RE.match(tid)
    if m:
        try:
            s = m.group(2).replace("Z", "+00:00")
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.timestamp()
        except Exception:
            pass
    et = (row.get("entry_ts") or "").strip()
    if et:
        try:
            s = et.replace("Z", "+00:00")
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.timestamp()
        except Exception:
            pass
    return None


def strict_ml_ready_count_since_cutoff(
    path: Path,
    cutoff_utc: datetime,
    *,
    feature_mode: str = "strict_scoreflow",
    require_join_tier: str | None = None,
    skip_neutral_no_join: bool = False,
) -> Tuple[int, Dict[str, Any]]:
    """
    Count strict ML-ready rows (same filter as load_and_filter) with entry time >= cutoff_utc.
    Telegram milestone watcher uses this Z count — not gross executions.
    """
    if cutoff_utc.tzinfo is None:
        cutoff_utc = cutoff_utc.replace(tzinfo=timezone.utc)
    cutoff_ts = cutoff_utc.timestamp()
    _headers, kept, stats = load_and_filter(
        path,
        feature_mode=feature_mode,
        require_join_tier=require_join_tier,
        skip_neutral_no_join=skip_neutral_no_join,
    )
    z_since = 0
    for row in kept:
        ep = _entry_epoch_from_flat_row(row)
        if ep is None or ep < cutoff_ts:
            continue
        z_since += 1
    meta: Dict[str, Any] = {
        **stats,
        "strict_ml_ready_since_cutoff": z_since,
        "strict_ml_ready_all_time_in_csv": stats["kept"],
        "cutoff_utc": cutoff_utc.isoformat(),
    }
    return z_since, meta


def load_and_filter(
    path: Path,
    *,
    feature_mode: str,
    require_join_tier: str | None = None,
    skip_neutral_no_join: bool = False,
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
        "dropped_neutral_no_join": 0,
        "dropped_feature_nan": 0,
        "kept": 0,
    }

    if not rows:
        return headers, [], stats

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
        if skip_neutral_no_join and str(row.get("mlf_scoreflow_features_neutral_no_join") or "").strip() in (
            "1",
            "true",
            "True",
        ):
            stats["dropped_neutral_no_join"] += 1
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
    ap.add_argument(
        "--calibration-gate",
        action="store_true",
        help="Harvester L2 calibration (full features) vs mlf_scoreflow_total_score; "
        "writes reports/Gemini/harvester_calibration_gate.json; exit 2 if PF gate fails.",
    )
    ap.add_argument(
        "--calibration-gate-precision",
        action="store_true",
        help="Precision narrow: congress+smile+sentiment, C=0.1, imputed weight 0.25; "
        "requires PF>=10%% lift AND positive CV; writes harvester_calibration_gate_precision.json.",
    )
    args = ap.parse_args()
    path = args.csv.resolve()
    if not path.is_file():
        print(f"Missing CSV: {path}", file=sys.stderr)
        return 1

    if args.calibration_gate_precision or args.calibration_gate:
        from src.ml.alpaca_harvester_calibration_gate import print_report, run_calibration_gate

        narrow = bool(args.calibration_gate_precision)
        jout = (
            REPO_ROOT / "reports" / "Gemini" / "harvester_calibration_gate_precision.json"
            if narrow
            else REPO_ROOT / "reports" / "Gemini" / "harvester_calibration_gate.json"
        )
        try:
            res = run_calibration_gate(
                path,
                json_out=jout,
                narrow_precision=narrow,
                l2_c=0.1 if narrow else None,
            )
        except Exception as e:
            print(f"Calibration gate failed: {e}", file=sys.stderr)
            return 1
        print_report(res.report)
        return 0 if res.promotion_ok else 2

    require_tier = "entry_snapshot" if args.feature_mode == "strict_entry_snapshot" else None
    headers, kept, stats = load_and_filter(
        path,
        feature_mode=args.feature_mode,
        require_join_tier=require_tier,
        skip_neutral_no_join=False,
    )

    print("=== Alpaca cohort strict gold-standard ingestion ===")
    print(f"csv: {path}")
    print(f"feature_mode: {args.feature_mode}")
    print(f"gross_rows: {stats['gross_rows']}")
    print(f"dropped_missing_or_nonfinite_pnl: {stats['dropped_missing_pnl']}")
    print(f"dropped_join_tier_mismatch: {stats['dropped_join_tier']}")
    print(f"dropped_neutral_no_join_flag: {stats['dropped_neutral_no_join']}")
    print(f"dropped_incomplete_or_nonfinite_features: {stats['dropped_feature_nan']}")
    print(f"ML_READY_ROWS: {stats['kept']}")

    if stats["gross_rows"] == 0:
        print("gross_rows=0 — empty cohort CSV; nothing to validate.")
        return 0

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
