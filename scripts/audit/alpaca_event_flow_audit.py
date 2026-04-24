#!/usr/bin/env python3
"""
Read-only event flow audit for Alpaca logs (run on droplet or locally).
Outputs JSON to stdout. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import random
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Set


def parse_ts(d: Any) -> Optional[float]:
    if d is None:
        return None
    if isinstance(d, (int, float)):
        return float(d)
    s = str(d).strip().replace("Z", "+00:00")
    try:
        t = datetime.fromisoformat(s)
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        return t.astimezone(timezone.utc).timestamp()
    except Exception:
        return None


def iter_jsonl(path: Path) -> Iterator[dict]:
    if not path.is_file():
        return
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--hours", type=int, default=72)
    ap.add_argument("--sample-size", type=int, default=10)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Write the same JSON payload to this file (UTF-8).",
    )
    args = ap.parse_args()
    root = args.root.resolve()
    logs = root / "logs"
    cutoff = datetime.now(timezone.utc) - timedelta(hours=args.hours)
    cut_ts = cutoff.timestamp()

    unified_path = logs / "alpaca_unified_events.jsonl"
    run_path = logs / "run.jsonl"
    orders_path = logs / "orders.jsonl"
    exit_path = logs / "exit_attribution.jsonl"

    u_counts: Counter = Counter()
    unified_entries_by_tid: Dict[str, dict] = {}
    unified_exits_terminal_by_tid: Dict[str, dict] = {}
    for r in iter_jsonl(unified_path):
        ts = parse_ts(r.get("timestamp") or r.get("ts"))
        if ts is not None and ts < cut_ts:
            continue
        et = r.get("event_type") or r.get("type")
        u_counts[str(et or "<none>")] += 1
        if et == "alpaca_entry_attribution":
            tid = r.get("trade_id")
            if tid:
                unified_entries_by_tid[str(tid)] = r
        elif et == "alpaca_exit_attribution":
            tid = r.get("trade_id")
            if tid and r.get("terminal_close"):
                unified_exits_terminal_by_tid[str(tid)] = r

    run_counts: Counter = Counter()
    trade_intent_entered: List[dict] = []
    canonical_resolved: List[dict] = []
    for r in iter_jsonl(run_path):
        ts = parse_ts(r.get("timestamp") or r.get("ts") or r.get("_ts"))
        if isinstance(r.get("_ts"), (int, float)) and ts is None:
            ts = float(r["_ts"])
        if ts is not None and ts < cut_ts:
            continue
        et = r.get("event_type")
        if not et:
            continue
        run_counts[str(et)] += 1
        if et == "trade_intent" and str(r.get("decision_outcome", "")).lower() == "entered":
            run_counts["trade_intent_entered"] += 1
            trade_intent_entered.append(r)
        if et == "canonical_trade_id_resolved":
            canonical_resolved.append(r)

    o_counts: Counter = Counter()
    orders_by_ct: Dict[str, List[dict]] = defaultdict(list)
    for r in iter_jsonl(orders_path):
        ts = parse_ts(r.get("timestamp") or r.get("_ts") or r.get("ts"))
        if ts is not None and ts < cut_ts:
            continue
        o_counts["orders_rows"] += 1
        ct = r.get("canonical_trade_id")
        if ct:
            orders_by_ct[str(ct)].append(r)
        st = str(r.get("status", "")).lower()
        typ = str(r.get("type", "")).lower()
        if st == "filled" or typ == "fill" or (r.get("filled_qty") not in (None, 0, "0")):
            o_counts["rows_marked_filled_or_fill_type"] += 1
        if typ == "order" or r.get("order_id"):
            o_counts["rows_with_order_type_or_id"] += 1

    exit_closes: List[dict] = []
    for r in iter_jsonl(exit_path):
        ts = parse_ts(r.get("timestamp"))
        if ts is not None and ts < cut_ts:
            continue
        exit_closes.append(r)

    trade_ids = [str(x.get("trade_id")) for x in exit_closes if x.get("trade_id")]
    if not trade_ids:
        # Legacy exit_attribution rows may omit trade_id; fall back to unified entry keys for tracing.
        trade_ids = list(unified_entries_by_tid.keys())
    random.seed(args.seed)
    sample: List[str] = random.sample(trade_ids, min(args.sample_size, len(trade_ids))) if trade_ids else []

    tid_re = re.compile(r"^open_([A-Z0-9]+)_(.+)$")
    traces: List[dict] = []
    for tid in sample:
        u_ent = unified_entries_by_tid.get(tid)
        u_ex = unified_exits_terminal_by_tid.get(tid)
        ex_row = next((x for x in exit_closes if str(x.get("trade_id")) == tid), None)
        ct_keys: Set[str] = set()
        if u_ex:
            for k in (u_ex.get("trade_key"), u_ex.get("canonical_trade_id")):
                if k:
                    ct_keys.add(str(k))
        if ex_row:
            for k in (ex_row.get("trade_key"), ex_row.get("canonical_trade_id")):
                if k:
                    ct_keys.add(str(k))
        order_hits = sum(len(orders_by_ct[k]) for k in ct_keys if k in orders_by_ct)
        traces.append(
            {
                "trade_id": tid,
                "has_exit_attribution": ex_row is not None,
                "has_unified_entry": u_ent is not None,
                "has_unified_exit_terminal_close": u_ex is not None,
                "canonical_keys_sample": sorted(ct_keys)[:4],
                "orders_rows_matching_canonical_keys": order_hits,
            }
        )

    n_exit = len(exit_closes)
    n_uni_term = len(unified_exits_terminal_by_tid)
    n_uni_ent = u_counts.get("alpaca_entry_attribution", 0)
    n_entered = run_counts.get("trade_intent_entered", 0)

    out: Dict[str, Any] = {
        "root": str(root),
        "window_hours": args.hours,
        "cutoff_utc": cutoff.isoformat(),
        "unified_path": str(unified_path),
        "unified_event_counts": dict(u_counts),
        "run_event_counts": dict(run_counts),
        "orders_heuristic_counts": dict(o_counts),
        "exit_attribution_closes_in_window": n_exit,
        "unified_terminal_close_distinct_trade_ids": n_uni_term,
        "ratios": {
            "unified_terminal_to_exit_attribution": (n_uni_term / n_exit) if n_exit else None,
            "unified_entry_rows_to_trade_intent_entered": (n_uni_ent / n_entered) if n_entered else None,
        },
        "random_trade_traces": traces,
        "notes": [
            "entry_decision_made is proxied by trade_intent decision_outcome=entered and/or alpaca_entry_attribution.",
            "execution submit/fill proxied by orders.jsonl rows in window (see heuristic counts).",
        ],
    }
    text = json.dumps(out, indent=2)
    print(text)
    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
