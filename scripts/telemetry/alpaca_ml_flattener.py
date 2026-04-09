#!/usr/bin/env python3
"""
Flatten Alpaca Harvester-era exit_attribution.jsonl for ML training.

Joins entry-time composite/features from logs/entry_snapshots.jsonl on entry_order_id (primary);
falls back to logs/scoring_flow.jsonl wide join when no snapshot exists.

Reads closed trades with open instant strictly on/after STRICT_EPOCH_START, dedupes by trade_id
(last row wins), flattens nested ML blobs with mlf_* column prefix, writes CSV.

Usage (repo root):
  PYTHONPATH=. python3 scripts/telemetry/alpaca_ml_flattener.py --root /root/stock-bot
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from bisect import bisect_right
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from telemetry.alpaca_strict_completeness_gate import STRICT_EPOCH_START  # noqa: E402
from telemetry.ml_scoreflow_contract import (  # noqa: E402
    mlf_scoreflow_component_column_names,
    normalize_composite_components_for_ml,
)
from utils.era_cut import learning_excluded_for_exit_record  # noqa: E402

TID_RE = re.compile(r"^open_([A-Z0-9]+)_(.+)$")
ML_BLOB_KEYS = ("entry_uw", "v2_exit_components", "direction_intel_embed")

# Wide join: last composite_calculated for symbol with ts in [entry - lookback, entry].
SCOREFLOW_LOOKBACK_SEC_DEFAULT = 4 * 3600


def _parse_iso_ts(raw: Any) -> Optional[float]:
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    try:
        s = s.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except (TypeError, ValueError):
        return None


def _open_epoch_from_trade_id(tid: Any) -> Optional[float]:
    m = TID_RE.match(str(tid or "").strip())
    if not m:
        return None
    return _parse_iso_ts(m.group(2))


def _iter_jsonl(path: Path) -> Iterator[dict]:
    if not path.is_file():
        return
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(o, dict):
                yield o


def _flatten_leaves(obj: Any, prefix: str = "") -> Dict[str, Any]:
    """Nested dicts -> underscore paths; scalars only at leaves. Lists -> JSON string."""
    out: Dict[str, Any] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            safe = str(k).replace(".", "_")
            p = f"{prefix}_{safe}" if prefix else safe
            out.update(_flatten_leaves(v, p))
    elif isinstance(obj, list):
        key = prefix or "list"
        try:
            out[key] = json.dumps(obj, separators=(",", ":"), default=str)[:4000]
        except TypeError:
            out[key] = str(obj)[:4000]
    elif obj is None:
        out[prefix] = ""
    elif isinstance(obj, bool):
        out[prefix] = obj
    elif isinstance(obj, (int, float, str)):
        out[prefix] = obj
    else:
        out[prefix] = str(obj)
    return out


def _prefix_mlf(flat: Dict[str, Any], stem: str) -> Dict[str, Any]:
    return {f"mlf_{stem}_{k}": v for k, v in flat.items()}


def _load_entry_snapshots_by_order(path: Path) -> Dict[str, dict]:
    """Last row wins per Alpaca order_id (join key = exit_attribution.entry_order_id)."""
    by_oid: Dict[str, dict] = {}
    for r in _iter_jsonl(path):
        if (r.get("msg") or "") != "entry_snapshot":
            continue
        oid = str(r.get("order_id") or "").strip()
        if not oid or oid.upper().startswith("AUDIT-DRYRUN"):
            continue
        by_oid[oid] = r
    return by_oid


def _snapshot_join_keys(rec: dict) -> List[str]:
    keys: List[str] = []
    for k in ("entry_order_id", "entry_orderId"):
        v = rec.get(k)
        if v is not None and str(v).strip():
            keys.append(str(v).strip())
    return keys


def _load_scoring_composite_index(
    path: Path,
) -> Dict[str, Tuple[List[float], List[Dict[str, Any]], List[float]]]:
    """
    Per symbol: sorted timestamps, parallel list of component dicts and total scores.
    """
    by_sym: Dict[str, List[Tuple[float, Dict[str, Any], float]]] = {}
    for r in _iter_jsonl(path):
        if (r.get("msg") or "") != "composite_calculated":
            continue
        sym = str(r.get("symbol") or "").upper().strip()
        if not sym:
            continue
        ts = _parse_iso_ts(r.get("ts"))
        if ts is None:
            continue
        comp = r.get("components")
        if not isinstance(comp, dict):
            comp = {}
        try:
            score = float(r.get("score")) if r.get("score") is not None else float("nan")
        except (TypeError, ValueError):
            score = float("nan")
        by_sym.setdefault(sym, []).append((ts, comp, score))
    out: Dict[str, Tuple[List[float], List[Dict[str, Any]], List[float]]] = {}
    for sym, rows in by_sym.items():
        rows.sort(key=lambda x: x[0])
        merged: List[Tuple[float, Dict[str, Any], float]] = []
        for t, c, s in rows:
            if merged and merged[-1][0] == t:
                merged[-1] = (t, c, s)  # same-ts: last line wins
            else:
                merged.append((t, c, s))
        ts_list = [x[0] for x in merged]
        comps = [x[1] for x in merged]
        scores = [x[2] for x in merged]
        out[sym] = (ts_list, comps, scores)
    return out


def _last_known_composite_wide(
    index: Dict[str, Tuple[List[float], List[Dict[str, Any]], List[float]]],
    symbol: str,
    entry_epoch: Optional[float],
    lookback_sec: float = SCOREFLOW_LOOKBACK_SEC_DEFAULT,
    *,
    allow_unbounded_fallback: bool = True,
) -> Tuple[Optional[float], Optional[Dict[str, Any]], Optional[float], str]:
    """
    Last Known Score: newest composite_calculated with ts <= entry_epoch and
    entry_epoch - ts <= lookback_sec (default 4h).

    If ``allow_unbounded_fallback`` and nothing falls in the window, use the newest
    composite still <= entry (may be older than lookback). Tier is recorded on the row.
    """
    if entry_epoch is None:
        return None, None, None, "none"
    sym = symbol.upper().strip()
    if not sym:
        return None, None, None, "none"
    bucket = index.get(sym)
    if not bucket:
        return None, None, None, "none"
    ts_list, comps, scores = bucket
    lo = float(entry_epoch) - float(lookback_sec)
    i = bisect_right(ts_list, float(entry_epoch)) - 1
    if i < 0:
        return None, None, None, "none"
    if ts_list[i] >= lo:
        return ts_list[i], comps[i], scores[i], "4h_window"
    if allow_unbounded_fallback:
        return ts_list[i], comps[i], scores[i], "unbounded_fallback"
    return None, None, None, "none"


def _dedupe_exit_rows(rows: List[dict]) -> List[dict]:
    """Last row wins per trade_id (SRE-EDGE-001 style)."""
    by_tid: Dict[str, dict] = {}
    order: List[str] = []
    for r in rows:
        tid = str(r.get("trade_id") or "").strip()
        if not tid:
            continue
        if tid not in by_tid:
            order.append(tid)
        by_tid[tid] = r
    return [by_tid[t] for t in order]


def _filter_strict_cohort(rec: dict, floor_epoch: float) -> bool:
    if learning_excluded_for_exit_record(rec):
        return False
    oep = _open_epoch_from_trade_id(rec.get("trade_id"))
    if oep is None:
        oep = _parse_iso_ts(rec.get("entry_ts") or rec.get("entry_timestamp"))
    if oep is None:
        return False
    return oep >= float(floor_epoch)


def _base_trade_fields(rec: dict) -> Dict[str, Any]:
    side = rec.get("position_side") or rec.get("side") or ""
    pnl = rec.get("pnl")
    if pnl is None:
        pnl = rec.get("realized_pnl_usd")
    hld = rec.get("time_in_trade_minutes")
    if hld is None:
        sec = (rec.get("exit_quality_metrics") or {}).get("time_in_trade_sec")
        if sec is not None:
            try:
                hld = float(sec) / 60.0
            except (TypeError, ValueError):
                hld = None
    return {
        "symbol": rec.get("symbol"),
        "side": side,
        "realized_pnl_usd": pnl,
        "holding_time_minutes": hld,
        "trade_id": rec.get("trade_id"),
        "trade_key": rec.get("trade_key") or rec.get("canonical_trade_id"),
        "entry_ts": rec.get("entry_ts") or rec.get("entry_timestamp"),
        "exit_ts": rec.get("exit_ts") or rec.get("timestamp"),
        "entry_price": rec.get("entry_price"),
        "exit_price": rec.get("exit_price") or rec.get("price"),
        "qty": rec.get("qty"),
        "variant_id": rec.get("variant_id"),
        "composite_version": rec.get("composite_version"),
        "strict_open_epoch_utc": _open_epoch_from_trade_id(rec.get("trade_id")),
    }


def _entry_epoch_for_scoring(rec: dict, row: Dict[str, Any]) -> Optional[float]:
    """Prefer entry_ts on row, then raw record timestamps, then open instant from trade_id."""
    t = _parse_iso_ts(row.get("entry_ts"))
    if t is not None:
        return t
    t = _parse_iso_ts(rec.get("entry_ts") or rec.get("entry_timestamp"))
    if t is not None:
        return t
    return _open_epoch_from_trade_id(rec.get("trade_id"))


def build_rows(
    root: Path,
    floor_epoch: float,
    scoring_index: Optional[Dict[str, Tuple[List[float], List[Dict[str, Any]], List[float]]]],
    entry_snap_index: Optional[Dict[str, dict]] = None,
    *,
    scoreflow_lookback_sec: float = SCOREFLOW_LOOKBACK_SEC_DEFAULT,
    scoreflow_unbounded_fallback: bool = True,
) -> List[Dict[str, Any]]:
    exit_path = root / "logs" / "exit_attribution.jsonl"
    raw = list(_iter_jsonl(exit_path))
    deduped = _dedupe_exit_rows(raw)
    out: List[Dict[str, Any]] = []
    for rec in deduped:
        if not _filter_strict_cohort(rec, floor_epoch):
            continue
        row: Dict[str, Any] = _base_trade_fields(rec)
        entry_epoch = _entry_epoch_for_scoring(rec, row)
        sym_join = (
            str(rec.get("symbol_normalized") or rec.get("symbol") or row.get("symbol") or "")
            .upper()
            .strip()
        )

        snap: Optional[dict] = None
        if entry_snap_index:
            for ek in _snapshot_join_keys(rec):
                snap = entry_snap_index.get(ek)
                if snap:
                    break

        for blob_key in ML_BLOB_KEYS:
            blob = rec.get(blob_key)
            if isinstance(blob, dict) and blob:
                flat = _flatten_leaves(blob)
                stem = blob_key.replace(".", "_")
                row.update(_prefix_mlf(flat, stem))

        row["mlf_ml_feature_source"] = "none"
        if snap:
            row["mlf_ml_feature_source"] = "entry_snapshot"
            row["mlf_scoreflow_join_tier"] = "entry_snapshot"
            row["mlf_scoreflow_lookback_sec_applied"] = scoreflow_lookback_sec
            tss = _parse_iso_ts(snap.get("timestamp_utc"))
            if tss is not None:
                row["mlf_scoreflow_snapshot_ts_epoch"] = tss
                row["mlf_scoreflow_snapshot_age_sec"] = (
                    float(entry_epoch) - float(tss) if entry_epoch is not None else ""
                )
            comp = snap.get("components")
            comp_norm = normalize_composite_components_for_ml(comp if isinstance(comp, dict) else {})
            row.update(_prefix_mlf(_flatten_leaves(comp_norm), "scoreflow_components"))
            tot_raw = snap.get("composite_score")
            try:
                tot = float(tot_raw) if tot_raw is not None else float("nan")
            except (TypeError, ValueError):
                tot = float("nan")
            if tot == tot:
                row["mlf_scoreflow_total_score"] = tot
            else:
                row["mlf_scoreflow_total_score"] = round(sum(comp_norm.values()), 6)
                row["mlf_scoreflow_total_score_imputed"] = 1
        elif scoring_index:
            _ts_c, comp, tot, tier = _last_known_composite_wide(
                scoring_index,
                sym_join,
                entry_epoch,
                lookback_sec=scoreflow_lookback_sec,
                allow_unbounded_fallback=scoreflow_unbounded_fallback,
            )
            row["mlf_ml_feature_source"] = (
                "scoreflow_wide" if tier not in (None, "none") else "none"
            )
            row["mlf_scoreflow_lookback_sec_applied"] = scoreflow_lookback_sec
            row["mlf_scoreflow_join_tier"] = tier
            if _ts_c is not None:
                row["mlf_scoreflow_snapshot_ts_epoch"] = _ts_c
                row["mlf_scoreflow_snapshot_age_sec"] = (
                    float(entry_epoch) - float(_ts_c) if entry_epoch is not None else ""
                )
            comp_norm = normalize_composite_components_for_ml(comp if isinstance(comp, dict) else {})
            row.update(_prefix_mlf(_flatten_leaves(comp_norm), "scoreflow_components"))
            if tot is not None and tot == tot:  # not NaN
                row["mlf_scoreflow_total_score"] = tot
            else:
                row["mlf_scoreflow_total_score"] = round(sum(comp_norm.values()), 6)
                row["mlf_scoreflow_total_score_imputed"] = 1
        else:
            # No entry_snapshot row and no scoring_flow index (or index miss): finite neutral
            # scoreflow vector — strict ML gate needs numeric columns; flag for downstream filters.
            comp_norm = normalize_composite_components_for_ml({})
            row.update(_prefix_mlf(_flatten_leaves(comp_norm), "scoreflow_components"))
            row["mlf_scoreflow_total_score"] = 0.0
            row["mlf_scoreflow_total_score_imputed"] = 1
            row["mlf_scoreflow_features_neutral_no_join"] = 1
            row.setdefault("mlf_scoreflow_join_tier", "none")
        out.append(row)
    return out


def _collect_headers(rows: List[Dict[str, Any]]) -> List[str]:
    base = [
        "symbol",
        "side",
        "realized_pnl_usd",
        "holding_time_minutes",
        "trade_id",
        "trade_key",
        "entry_ts",
        "exit_ts",
        "entry_price",
        "exit_price",
        "qty",
        "variant_id",
        "composite_version",
        "strict_open_epoch_utc",
    ]
    extras = sorted({k for r in rows for k in r.keys() if k not in base})
    return base + extras


def main() -> int:
    ap = argparse.ArgumentParser(description="Alpaca ML cohort flattener (Harvester era).")
    ap.add_argument("--root", type=Path, default=REPO_ROOT, help="Repo root (default: inferred).")
    ap.add_argument(
        "--floor-epoch",
        type=float,
        default=float(STRICT_EPOCH_START),
        help="Include trades with open instant >= this UTC epoch (default: STRICT_EPOCH_START).",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help=f"Output CSV (default: reports/Gemini/alpaca_ml_cohort_flat.csv under --root).",
    )
    ap.add_argument(
        "--no-scoring-flow",
        action="store_true",
        help="Skip logs/scoring_flow.jsonl composite join.",
    )
    ap.add_argument(
        "--no-entry-snapshots",
        action="store_true",
        help="Skip logs/entry_snapshots.jsonl (use only scoring_flow wide join).",
    )
    ap.add_argument(
        "--scoreflow-lookback-sec",
        type=float,
        default=float(SCOREFLOW_LOOKBACK_SEC_DEFAULT),
        help="Preferred max age (seconds) of last composite before entry (default: 14400 = 4h).",
    )
    ap.add_argument(
        "--no-scoreflow-unbounded-fallback",
        action="store_true",
        help="If set, do not use older-than-lookback composites when nothing falls in the 4h window.",
    )
    args = ap.parse_args()
    root = args.root.resolve()
    out_path = (args.out or (root / "reports" / "Gemini" / "alpaca_ml_cohort_flat.csv")).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    scoring_path = root / "logs" / "scoring_flow.jsonl"
    scoring_index = None if args.no_scoring_flow else _load_scoring_composite_index(scoring_path)

    entry_snap_path = root / "logs" / "entry_snapshots.jsonl"
    entry_snap_index = (
        None
        if args.no_entry_snapshots
        else _load_entry_snapshots_by_order(entry_snap_path)
    )

    rows = build_rows(
        root,
        args.floor_epoch,
        scoring_index,
        entry_snap_index,
        scoreflow_lookback_sec=args.scoreflow_lookback_sec,
        scoreflow_unbounded_fallback=not args.no_scoreflow_unbounded_fallback,
    )
    headers = list(_collect_headers(rows))
    # Strict ML cohort (alpaca_cohort_train) allowlist — always present in header even if 0 rows.
    for _c in mlf_scoreflow_component_column_names():
        if _c not in headers:
            headers.append(_c)
    for _t in ("mlf_scoreflow_total_score", "mlf_scoreflow_total_score_imputed"):
        if _t not in headers:
            headers.append(_t)

    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({h: r.get(h, "") for h in headers})

    n = len(rows)
    if n:
        tot_col = "mlf_scoreflow_total_score"
        from_snap = sum(1 for r in rows if r.get("mlf_ml_feature_source") == "entry_snapshot")
        from_sf = sum(1 for r in rows if r.get("mlf_ml_feature_source") == "scoreflow_wide")
        if entry_snap_index is not None:
            print(
                f"entry_snapshot_join_pct: {100.0 * from_snap / n:.2f} ({from_snap}/{n}) "
                f"[primary: logs/entry_snapshots.jsonl on entry_order_id]"
            )
        with_snap = sum(1 for r in rows if r.get("mlf_scoreflow_snapshot_ts_epoch") not in (None, ""))
        with_tot = sum(
            1
            for r in rows
            if r.get(tot_col) not in (None, "")
            and str(r.get(tot_col)).strip() != ""
        )
        in_4h = sum(1 for r in rows if r.get("mlf_scoreflow_join_tier") == "4h_window")
        fb = sum(1 for r in rows if r.get("mlf_scoreflow_join_tier") == "unbounded_fallback")
        es_tier = sum(1 for r in rows if r.get("mlf_scoreflow_join_tier") == "entry_snapshot")
        if scoring_index is not None or entry_snap_index is not None:
            print(
                f"scoreflow_snapshot_coverage_pct: {100.0 * with_snap / n:.2f} ({with_snap}/{n}) "
                f"[entry_snapshot_tier={es_tier}; wide 4h_tier={in_4h} fallback_tier={fb}; "
                f"scoreflow_lookback={args.scoreflow_lookback_sec:.0f}s; unbounded_fallback="
                f"{'off' if args.no_scoreflow_unbounded_fallback else 'on'}; scoreflow_wide_rows={from_sf}]"
            )
        print(f"scoreflow_total_score_populated_pct: {100.0 * with_tot / n:.2f} ({with_tot}/{n})")
    print(f"wrote {n} rows -> {out_path}")
    print(f"floor_epoch={args.floor_epoch} STRICT_EPOCH_START={STRICT_EPOCH_START}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
