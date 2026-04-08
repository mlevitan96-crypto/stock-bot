#!/usr/bin/env python3
"""
Flatten Alpaca Harvester-era exit_attribution.jsonl (+ scoring_flow composite join) for ML training.

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
from utils.era_cut import learning_excluded_for_exit_record  # noqa: E402

TID_RE = re.compile(r"^open_([A-Z0-9]+)_(.+)$")
ML_BLOB_KEYS = ("entry_uw", "v2_exit_components", "direction_intel_embed")


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
        ts_list = [x[0] for x in rows]
        comps = [x[1] for x in rows]
        scores = [x[2] for x in rows]
        out[sym] = (ts_list, comps, scores)
    return out


def _nearest_composite_at_or_before(
    index: Dict[str, Tuple[List[float], List[Dict[str, Any]], List[float]]],
    symbol: str,
    entry_epoch: Optional[float],
) -> Tuple[Optional[float], Optional[Dict[str, Any]], Optional[float]]:
    if entry_epoch is None:
        return None, None, None
    sym = symbol.upper().strip()
    bucket = index.get(sym)
    if not bucket:
        return None, None, None
    ts_list, comps, scores = bucket
    i = bisect_right(ts_list, entry_epoch) - 1
    if i < 0:
        return None, None, None
    return ts_list[i], comps[i], scores[i]


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


def build_rows(
    root: Path,
    floor_epoch: float,
    scoring_index: Optional[Dict[str, Tuple[List[float], List[Dict[str, Any]], List[float]]]],
) -> List[Dict[str, Any]]:
    exit_path = root / "logs" / "exit_attribution.jsonl"
    raw = list(_iter_jsonl(exit_path))
    deduped = _dedupe_exit_rows(raw)
    out: List[Dict[str, Any]] = []
    for rec in deduped:
        if not _filter_strict_cohort(rec, floor_epoch):
            continue
        row: Dict[str, Any] = _base_trade_fields(rec)
        entry_epoch = _parse_iso_ts(row.get("entry_ts"))

        for blob_key in ML_BLOB_KEYS:
            blob = rec.get(blob_key)
            if isinstance(blob, dict) and blob:
                flat = _flatten_leaves(blob)
                stem = blob_key.replace(".", "_")
                row.update(_prefix_mlf(flat, stem))

        if scoring_index:
            _ts_c, comp, tot = _nearest_composite_at_or_before(
                scoring_index, str(row.get("symbol") or ""), entry_epoch
            )
            if comp:
                row.update(_prefix_mlf(_flatten_leaves(comp), "scoreflow_components"))
            if tot is not None and tot == tot:  # not NaN
                row["mlf_scoreflow_total_score"] = tot
            if _ts_c is not None:
                row["mlf_scoreflow_snapshot_ts_epoch"] = _ts_c
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
    args = ap.parse_args()
    root = args.root.resolve()
    out_path = (args.out or (root / "reports" / "Gemini" / "alpaca_ml_cohort_flat.csv")).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    scoring_path = root / "logs" / "scoring_flow.jsonl"
    scoring_index = None if args.no_scoring_flow else _load_scoring_composite_index(scoring_path)

    rows = build_rows(root, args.floor_epoch, scoring_index)
    headers = _collect_headers(rows)

    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({h: r.get(h, "") for h in headers})

    print(f"wrote {len(rows)} rows -> {out_path}")
    print(f"floor_epoch={args.floor_epoch} STRICT_EPOCH_START={STRICT_EPOCH_START}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
