#!/usr/bin/env python3
"""
Offline feature backfill: add Vanguard Shadow / AI v1 columns + regime_id to archived
flattened ML cohort CSVs, then optionally merge with the current flat cohort.

- shadow_chop_block: historical US/Eastern chop window via telemetry.shadow_evaluator.shadow_chop_block_at
- ai_approved_v1: current XGBoost v1 model (models/vanguard_entry_filter_v1*.json) using CSV feature columns
- regime_id: snapshot entry regime label column from the flat schema (no RegimeRouter in-repo)

Inputs:
  --csv one or more flattened cohort CSV paths (e.g. extracted from reports/archive tarballs)
  --archive-glob optional glob under repo root for additional CSVs
  --from-tar optional paths to .tar.gz; any member matching *alpaca_ml_cohort*flat*.csv is read

Outputs:
  --out-enriched default reports/Alpaca/alpaca_ml_cohort_historical_enriched.csv
  --out-unified optional merged file (historical + --recent-csv) with aligned columns

Usage:
  PYTHONPATH=. python scripts/quant/archive_feature_backfill.py \\
    --csv reports/Gemini/alpaca_ml_cohort_flat.csv --max-rows 500 \\
    --recent-csv reports/Gemini/alpaca_ml_cohort_flat.csv --out-unified reports/Alpaca/alpaca_ml_cohort_unified.csv
"""
from __future__ import annotations

import argparse
import io
import json
import math
import sys
import tarfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

REGIME_LABEL_COL = (
    "mlf_direction_intel_embed_intel_snapshot_entry_regime_posture_regime_label"
)


def _parse_entry_ts(val: Any) -> Optional["datetime"]:
    from datetime import datetime, timezone

    if val is None or (isinstance(val, float) and math.isnan(val)):
        return None
    s = str(val).strip()
    if not s:
        return None
    try:
        s2 = s.replace("Z", "+00:00")
        d = datetime.fromisoformat(s2)
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d.astimezone(timezone.utc)
    except Exception:
        return None


def _float_feature(val: Any) -> float:
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return float("nan")
    if isinstance(val, (bool, np.bool_)):
        return 1.0 if val else 0.0
    if isinstance(val, (int, float, np.integer, np.floating)):
        try:
            x = float(val)
            return x
        except (TypeError, ValueError):
            return float("nan")
    s = str(val).strip()
    if s == "" or s.lower() in ("nan", "none", "null"):
        return float("nan")
    try:
        return float(s)
    except ValueError:
        return float("nan")


def _load_model_meta() -> Tuple[Optional[Any], Optional[dict], Optional[str]]:
    from telemetry.shadow_evaluator import _load_booster_and_meta

    return _load_booster_and_meta()


def _predict_ai_row(
    row: pd.Series,
    feature_names: Sequence[str],
    symbol: str,
    side: str,
    symbol_classes: List[str],
    side_classes: List[str],
    entry_dt,
) -> Tuple[Optional[bool], Optional[str]]:
    from telemetry.shadow_evaluator import predict_vanguard_ai_approved

    hod = float("nan")
    if entry_dt is not None:
        try:
            from zoneinfo import ZoneInfo

            et = ZoneInfo("America/New_York")
            loc = entry_dt.astimezone(et)
            hod = float(loc.hour)
        except Exception:
            hod = float("nan")

    vec: Dict[str, float] = {}
    for k in feature_names:
        if k == "hour_of_day":
            vec[k] = hod
        else:
            vec[k] = _float_feature(row.get(k))
    try:
        ok = bool(
            predict_vanguard_ai_approved(
                list(feature_names),
                symbol,
                side,
                symbol_classes,
                side_classes,
                vec,
            )
        )
        return ok, None
    except Exception as e:
        return None, str(e)[:400]


def _iter_csv_from_tar(tar_path: Path) -> Iterable[Tuple[str, pd.DataFrame]]:
    with tarfile.open(tar_path, "r:*") as tf:
        for m in tf.getmembers():
            if not m.isfile():
                continue
            name = m.name.replace("\\", "/")
            if "alpaca_ml_cohort" not in name or "flat" not in name.lower():
                continue
            if not name.lower().endswith(".csv"):
                continue
            f = tf.extractfile(m)
            if f is None:
                continue
            raw = f.read()
            yield f"{tar_path.name}::{name}", pd.read_csv(io.BytesIO(raw), low_memory=False)


def _gather_frames(
    root: Path,
    csv_paths: Sequence[str],
    archive_globs: Sequence[str],
    tar_paths: Sequence[str],
    max_rows: Optional[int],
) -> List[pd.DataFrame]:
    frames: List[pd.DataFrame] = []
    for p in csv_paths:
        path = Path(p)
        if not path.is_file():
            print(f"WARN: skip missing CSV {path}", flush=True)
            continue
        raw = pd.read_csv(path, low_memory=False, nrows=max_rows)
        try:
            label = str(path.resolve().relative_to(root))
        except ValueError:
            label = str(path.resolve())
        df = raw.assign(_source_file=label).copy()
        frames.append(df)
    for pattern in archive_globs:
        for path in sorted(root.glob(pattern)):
            if not path.is_file() or path.suffix.lower() != ".csv":
                continue
            raw = pd.read_csv(path, low_memory=False, nrows=max_rows)
            try:
                label = str(path.resolve().relative_to(root))
            except ValueError:
                label = str(path.resolve())
            df = raw.assign(_source_file=label).copy()
            frames.append(df)
    for tp in tar_paths:
        tpath = Path(tp)
        if not tpath.is_file():
            print(f"WARN: skip missing tar {tpath}", flush=True)
            continue
        for label, df in _iter_csv_from_tar(tpath.resolve()):
            if max_rows is not None:
                df = df.head(max_rows)
            df["_source_file"] = label
            frames.append(df)
    return frames


def _backfill_columns(df: pd.DataFrame) -> pd.DataFrame:
    from telemetry.shadow_evaluator import shadow_chop_block_at

    bst, meta, err = _load_model_meta()
    feature_names: List[str] = []
    symbol_classes: List[str] = []
    side_classes: List[str] = []
    if isinstance(meta, dict):
        feature_names = [str(x) for x in (meta.get("feature_names") or [])]
        symbol_classes = [str(x) for x in (meta.get("symbol_classes") or [])]
        side_classes = [str(x) for x in (meta.get("side_classes") or [])]

    chops: List[bool] = []
    ais: List[Any] = []
    ai_errs: List[Any] = []
    regime_ids: List[Any] = []

    for _, row in df.iterrows():
        entry_dt = _parse_entry_ts(row.get("entry_ts"))
        if entry_dt is not None:
            chops.append(bool(shadow_chop_block_at(entry_dt)))
        else:
            chops.append(False)

        if REGIME_LABEL_COL in row.index:
            regime_ids.append(row.get(REGIME_LABEL_COL))
        else:
            regime_ids.append(float("nan"))

        sym = str(row.get("symbol") or "").strip()
        side = str(row.get("side") or "long").strip().lower()
        if bst is None or err or not feature_names:
            ais.append(None)
            ai_errs.append(err or "no_model_meta")
            continue
        ai_ok, ai_err = _predict_ai_row(row, feature_names, sym, side, symbol_classes, side_classes, entry_dt)
        ais.append(ai_ok)
        ai_errs.append(ai_err)

    out = df.copy()
    out["shadow_chop_block"] = chops
    out["ai_approved_v1"] = ais
    out["ai_approved_v1_backfill_error"] = ai_errs
    out["regime_id"] = regime_ids
    return out


def merge_cohort_frames(
    historical: pd.DataFrame,
    recent: pd.DataFrame,
) -> Tuple[pd.DataFrame, int, int, int]:
    """Outer-align columns, concat historical then recent. Returns (merged, n_hist, n_recent, n_total)."""
    h = historical.copy()
    r = recent.copy()
    all_cols = sorted(set(h.columns) | set(r.columns))
    h2 = h.reindex(columns=all_cols)
    r2 = r.reindex(columns=all_cols)
    merged = pd.concat([h2, r2], axis=0, ignore_index=True)
    return merged, len(h2), len(r2), len(merged)


def main() -> int:
    ap = argparse.ArgumentParser(description="Backfill shadow/AI/regime_id onto archived ML cohort CSVs.")
    ap.add_argument("--root", type=Path, default=REPO, help="Repo root (default: auto)")
    ap.add_argument("--csv", action="append", default=[], help="Flattened cohort CSV path (repeatable)")
    ap.add_argument(
        "--archive-glob",
        action="append",
        default=[],
        help="Glob under repo for extra CSVs, e.g. reports/archive/**/*.csv",
    )
    ap.add_argument("--from-tar", action="append", default=[], help="Path to .tar.gz containing flat cohort CSVs")
    ap.add_argument("--max-rows", type=int, default=None, help="Cap rows per input (debug)")
    ap.add_argument(
        "--out-enriched",
        type=Path,
        default=REPO / "reports" / "Alpaca" / "alpaca_ml_cohort_historical_enriched.csv",
    )
    ap.add_argument(
        "--recent-csv",
        type=Path,
        default=REPO / "reports" / "Gemini" / "alpaca_ml_cohort_flat.csv",
        help="Current cohort CSV for merge",
    )
    ap.add_argument(
        "--out-unified",
        type=Path,
        default=None,
        help="If set, write merged historical+recent CSV here",
    )
    args = ap.parse_args()
    root = args.root.resolve()
    csvs = list(args.csv)
    if not csvs and not args.archive_glob and not args.from_tar:
        # Default: current flat file as demo source if nothing specified
        default_flat = root / "reports" / "Gemini" / "alpaca_ml_cohort_flat.csv"
        if default_flat.is_file():
            csvs = [str(default_flat)]
            print(f"No --csv provided; using default {default_flat}", flush=True)
        else:
            print("Provide --csv, --archive-glob, and/or --from-tar", file=sys.stderr)
            return 2

    frames = _gather_frames(root, csvs, args.archive_glob, args.from_tar, args.max_rows)
    if not frames:
        print("No input frames loaded.", file=sys.stderr)
        return 1

    hist_raw = pd.concat(frames, axis=0, ignore_index=True)
    if "trade_id" in hist_raw.columns:
        hist_raw = hist_raw.drop_duplicates(subset=["trade_id"], keep="last")
    n_hist_in = len(hist_raw)
    enriched = _backfill_columns(hist_raw)
    args.out_enriched.parent.mkdir(parents=True, exist_ok=True)
    enriched.to_csv(args.out_enriched, index=False)
    print(json.dumps({"historical_rows_in": n_hist_in, "historical_enriched_out": str(args.out_enriched)}, indent=2))

    n_unified = n_hist_in
    if args.out_unified is not None:
        if not args.recent_csv.is_file():
            print(f"WARN: recent CSV missing {args.recent_csv}; skip unified write", flush=True)
        else:
            recent = pd.read_csv(args.recent_csv, low_memory=False)
            merged, nh, nr, nt = merge_cohort_frames(enriched, recent)
            if "trade_id" in merged.columns:
                merged = merged.drop_duplicates(subset=["trade_id"], keep="last")
                nt = len(merged)
            args.out_unified.parent.mkdir(parents=True, exist_ok=True)
            merged.to_csv(args.out_unified, index=False)
            n_unified = nt
            print(
                json.dumps(
                    {
                        "unified_csv": str(args.out_unified),
                        "historical_rows": nh,
                        "recent_rows": nr,
                        "unified_total_rows": nt,
                    },
                    indent=2,
                )
            )

    print(
        f"\n--- BACKFILL SUMMARY ---\n"
        f"Historical rows re-scored (unique): {n_hist_in}\n"
        f"Enriched CSV: {args.out_enriched}\n"
        f"Unified total rows: {n_unified}\n"
        f"-------------------------\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
