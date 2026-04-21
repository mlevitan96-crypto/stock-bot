#!/usr/bin/env python3
"""
Audit orders.jsonl for a calendar day (America/New_York): compare naive row counts vs unique order_ids.

Usage (repo root):
  PYTHONPATH=. python scripts/audit/audit_orders_jsonl_daily_dedup.py --date 2026-04-20
  PYTHONPATH=. python scripts/audit/audit_orders_jsonl_daily_dedup.py --date 2026-04-20 --path /root/stock-bot/logs/orders.jsonl
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None  # type: ignore


def _parse_ts(rec: dict) -> float | None:
    for k in ("timestamp", "_ts", "ts"):
        v = rec.get(k)
        if v is None:
            continue
        if isinstance(v, (int, float)):
            return float(v)
        s = str(v).strip().replace("Z", "+00:00")
        try:
            t = datetime.fromisoformat(s)
            if t.tzinfo is None:
                from datetime import timezone as _tz

                t = t.replace(tzinfo=_tz.utc)
            return t.timestamp()
        except Exception:
            continue
    return None


def _naive_fill_like(rec: dict) -> bool:
    """Legacy dashboard heuristic (intentionally over-counts)."""
    st = str(rec.get("status", "")).lower()
    typ = str(rec.get("type", "")).lower()
    if st == "filled" or typ == "fill":
        return True
    fq = rec.get("filled_qty")
    if fq not in (None, 0, "0", ""):
        try:
            return float(fq) > 0
        except Exception:
            return True
    return False


def _order_id(rec: dict) -> str | None:
    for k in ("order_id", "id", "client_order_id"):
        v = rec.get(k)
        if v is None:
            continue
        s = str(v).strip()
        if s:
            return s
    return None


def _terminal_filled(rec: dict) -> bool:
    st = str(rec.get("status", "")).strip().lower()
    if st == "filled":
        return True
    act = str(rec.get("action", "")).strip().lower()
    if act in ("submit_limit_filled", "submit_limit_final_filled"):
        return True
    if act == "close_position":
        try:
            if float(rec.get("filled_qty") or 0) > 0:
                return True
        except Exception:
            pass
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit orders.jsonl naive vs deduped counts for one ET calendar day.")
    ap.add_argument("--date", required=True, help="Target calendar day YYYY-MM-DD (America/New_York).")
    ap.add_argument("--path", type=Path, default=Path("logs/orders.jsonl"), help="Path to orders.jsonl")
    args = ap.parse_args()

    target = date.fromisoformat(args.date)
    path = args.path.resolve()
    if not path.is_file():
        print(f"Missing file: {path}")
        return 1

    et = ZoneInfo("America/New_York") if ZoneInfo else None
    naive_rows: list[dict[str, Any]] = []
    naive_by_day: defaultdict[date, int] = defaultdict(int)
    strict_ids: defaultdict[date, set[str]] = defaultdict(set)

    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = _parse_ts(rec)
            if ts is None:
                continue
            if et:
                d = datetime.fromtimestamp(ts, tz=et).date()
            else:
                from datetime import timezone as _u

                d = datetime.fromtimestamp(ts, tz=_u.utc).date()
            if d != target:
                continue

            if _naive_fill_like(rec):
                naive_rows.append(rec)
                naive_by_day[d] += 1
            if _terminal_filled(rec):
                oid = _order_id(rec)
                if oid:
                    strict_ids[d].add(oid)

    n_naive = naive_by_day.get(target, 0)
    n_unique = len(strict_ids.get(target, set()))
    oids_naive = []
    for r in naive_rows:
        o = _order_id(r)
        if o:
            oids_naive.append(o)

    print(f"File: {path}")
    print(f"Target day (ET): {target.isoformat()}")
    print(f"Naive fill-like ROW count (legacy heuristic): {n_naive}")
    print(f"Strict unique order_ids (terminal filled + id present): {n_unique}")
    print(f"Distinct order_ids seen on naive rows: {len(set(oids_naive))}")
    if n_naive:
        print(f"Example order_ids (first 12): {list(dict.fromkeys(oids_naive))[:12]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
