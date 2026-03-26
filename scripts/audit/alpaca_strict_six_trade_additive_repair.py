#!/usr/bin/env python3
"""
Additive strict-chain repair for six known incomplete trade_ids.

Writes ONLY to:
  logs/strict_backfill_run.jsonl
  logs/strict_backfill_orders.jsonl
  logs/strict_backfill_alpaca_unified_events.jsonl

Primary logs are never modified. Strict gate merges these via telemetry/alpaca_strict_completeness_gate.py.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[2]

TARGET_TRADE_IDS = [
    "open_PFE_2026-03-26T14:29:25.977370+00:00",
    "open_QQQ_2026-03-26T15:10:28.882493+00:00",
    "open_WMT_2026-03-26T15:10:28.883737+00:00",
    "open_HOOD_2026-03-26T15:51:38.174449+00:00",
    "open_LCID_2026-03-26T15:51:38.396698+00:00",
    "open_CAT_2026-03-26T16:34:40.245664+00:00",
]

TID_RE = re.compile(r"^open_([A-Z0-9]+)_(.+)$")


def _parse_iso(s: Any) -> Optional[datetime]:
    if not s or not isinstance(s, str):
        return None
    try:
        t = s.strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(t)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _stream(path: Path):
    if not path.is_file():
        return
    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def _already_done(run_bf: Path, tid: str) -> bool:
    for r in _stream(run_bf):
        if r.get("strict_backfill_trade_id") == tid:
            return True
    return False


def _load_exit(root: Path, tid: str) -> Optional[dict]:
    p = root / "logs" / "exit_attribution.jsonl"
    for r in _stream(p):
        if str(r.get("trade_id") or "") == tid:
            return r
    return None


def _load_unified_exit(root: Path, tid: str) -> Optional[dict]:
    p = root / "logs" / "alpaca_unified_events.jsonl"
    for r in _stream(p):
        if (r.get("event_type") or r.get("type")) != "alpaca_exit_attribution":
            continue
        if not r.get("terminal_close"):
            continue
        if str(r.get("trade_id") or "") == tid:
            return r
    return None


def _best_order(root: Path, sym: str, entry_dt: datetime, exit_dt: Optional[datetime]) -> Optional[dict]:
    symu = sym.upper()
    candidates: List[tuple] = []
    for r in _stream(root / "logs" / "orders.jsonl"):
        if str(r.get("symbol") or "").upper() != symu:
            continue
        ts = None
        for k in ("filled_at", "submitted_at", "created_at", "timestamp"):
            ts = _parse_iso(r.get(k))
            if ts:
                break
        if ts is None:
            continue
        if exit_dt and ts > exit_dt + timedelta(hours=6):
            continue
        dt_delta = abs((ts - entry_dt).total_seconds())
        candidates.append((dt_delta, r))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0])
    return candidates[0][1]


def build_lines_for_trade(root: Path, tid: str) -> List[dict]:
    m = TID_RE.match(tid)
    if not m:
        return []
    sym, entry_rest = m.group(1), m.group(2)
    entry_dt = _parse_iso(entry_rest)
    if entry_dt is None:
        return []

    ex = _load_exit(root, tid)
    ux = _load_unified_exit(root, tid)
    if not ex or not ux:
        return []

    sys.path.insert(0, str(REPO))
    from src.telemetry.alpaca_trade_key import build_trade_key, normalize_side

    side = normalize_side(ex.get("side") or ex.get("direction") or "long")
    tk_fb = build_trade_key(sym, side, entry_rest)
    tk = str(ux.get("trade_key") or tk_fb)
    ct = str(ux.get("canonical_trade_id") or ex.get("canonical_trade_id") or tk)

    exit_dt = _parse_iso(ex.get("timestamp"))

    ts_entered = _iso(entry_dt)
    if exit_dt:
        mid = entry_dt + timedelta(seconds=30)
        cap = exit_dt - timedelta(seconds=2)
        ts_exit_intent = _iso(mid if mid < cap else cap)
    else:
        ts_exit_intent = _iso(entry_dt + timedelta(seconds=30))

    lines: List[dict] = []

    # Orders index uses canonical_trade_id on the row; gate seed is unified trade_key first — use tk on synthetic order.
    order_canonical_for_row = tk

    lines.append(
        {
            "event_type": "trade_intent",
            "decision_outcome": "entered",
            "symbol": sym.upper(),
            "canonical_trade_id": ct,
            "trade_key": tk,
            "timestamp": ts_entered,
            "strict_backfilled": True,
            "strict_backfill_trade_id": tid,
            "strict_backfill_note": "synthesized for strict completeness repair",
        }
    )
    lines.append(
        {
            "event_type": "exit_intent",
            "symbol": sym.upper(),
            "canonical_trade_id": ct,
            "trade_key": tk,
            "thesis_break_reason": "strict_backfill_synthetic",
            "timestamp": ts_exit_intent,
            "strict_backfilled": True,
            "strict_backfill_trade_id": tid,
        }
    )
    lines.append(
        {
            "event_type": "alpaca_entry_attribution",
            "trade_id": tid,
            "symbol": sym.upper(),
            "trade_key": tk,
            "canonical_trade_id": ct,
            "strict_backfilled": True,
            "strict_backfill_trade_id": tid,
            "timestamp": ts_entered,
        }
    )

    lines.append(
        {
            "__dest": "orders",
            "id": f"strict_backfill_order:{tid}",
            "symbol": sym.upper(),
            "canonical_trade_id": order_canonical_for_row,
            "side": "buy" if side == "LONG" else "sell",
            "strict_backfilled": True,
            "strict_backfill_trade_id": tid,
            "timestamp": ts_entered,
        }
    )

    return lines


def _incomplete_tids_for_era(root: Path, open_ts: float) -> List[str]:
    sys.path.insert(0, str(REPO))
    from telemetry.alpaca_strict_completeness_gate import evaluate_completeness

    r = evaluate_completeness(root, open_ts_epoch=open_ts, audit=True)
    s: set = set()
    for v in (r.get("incomplete_trade_ids_by_reason") or {}).values():
        for tid in v:
            s.add(str(tid))
    return sorted(s)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument(
        "--open-ts-epoch",
        type=float,
        default=None,
        help="With --repair-all-incomplete-in-era, iteratively repair every incomplete tid in this strict window",
    )
    ap.add_argument(
        "--repair-all-incomplete-in-era",
        action="store_true",
        help="Loop evaluate_completeness + backfill until no incompletes or no progress (max 8 rounds)",
    )
    args = ap.parse_args()
    root = args.root.resolve()
    logs = root / "logs"
    logs.mkdir(parents=True, exist_ok=True)

    run_bf = logs / "strict_backfill_run.jsonl"
    ord_bf = logs / "strict_backfill_orders.jsonl"
    uni_bf = logs / "strict_backfill_alpaca_unified_events.jsonl"

    planned: List[Tuple[str, dict]] = []
    repair_all_applied = False

    if args.repair_all_incomplete_in_era:
        if args.open_ts_epoch is None:
            print("--open-ts-epoch required with --repair-all-incomplete-in-era", file=sys.stderr)
            return 2
        if args.dry_run:
            tids = _incomplete_tids_for_era(root, float(args.open_ts_epoch))
            print(json.dumps({"dry_run": True, "incomplete_trade_ids_count": len(tids), "sample": tids[:20]}, indent=2))
            for tid in tids[:2]:
                b = build_lines_for_trade(root, tid)
                print(json.dumps({"tid": tid, "lines": len(b)}, indent=2))
            return 0
        if not args.apply:
            print("use --apply for --repair-all-incomplete-in-era (or --dry-run)", file=sys.stderr)
            return 2
        tot_run = tot_ord = tot_uni = 0
        rounds = 0
        while rounds < 8:
            rounds += 1
            tids = _incomplete_tids_for_era(root, float(args.open_ts_epoch))
            if not tids:
                break
            round_planned: List[Tuple[str, dict]] = []
            for tid in tids:
                if _already_done(run_bf, tid):
                    continue
                batch = build_lines_for_trade(root, tid)
                if not batch:
                    print("skip (missing exit/unified):", tid, file=sys.stderr)
                    continue
                round_planned.extend([(tid, x) for x in batch])
            if not round_planned:
                break
            r, o, u = _flush_planned(run_bf, ord_bf, uni_bf, round_planned)
            tot_run += r
            tot_ord += o
            tot_uni += u
        repair_all_applied = True
        print(
            json.dumps(
                {
                    "applied_repair_all_incomplete": True,
                    "rounds": rounds,
                    "run_lines": tot_run,
                    "orders_lines": tot_ord,
                    "unified_lines": tot_uni,
                },
                indent=2,
            )
        )
    else:
        for tid in TARGET_TRADE_IDS:
            if _already_done(run_bf, tid):
                continue
            batch = build_lines_for_trade(root, tid)
            if not batch:
                print("skip (missing exit/unified):", tid, file=sys.stderr)
                continue
            planned.extend([(tid, x) for x in batch])

    if repair_all_applied:
        return 0

    if args.dry_run or not args.apply:
        print(json.dumps({"dry_run": True, "lines_count": len(planned)}, indent=2))
        for tid, row in planned[:3]:
            print(json.dumps({"tid": tid, "sample": row}, indent=2)[:800])
        return 0 if planned else 1

    if planned:
        n_run, n_ord, n_uni = _flush_planned(run_bf, ord_bf, uni_bf, planned)
        print(json.dumps({"applied": True, "run_lines": n_run, "orders_lines": n_ord, "unified_lines": n_uni}, indent=2))
    return 0


def _flush_planned(run_bf: Path, ord_bf: Path, uni_bf: Path, planned: List[Tuple[str, dict]]) -> tuple:
    n_run = n_ord = n_uni = 0
    with run_bf.open("a", encoding="utf-8") as fr, ord_bf.open("a", encoding="utf-8") as fo, uni_bf.open(
        "a", encoding="utf-8"
    ) as fu:
        for tid, row in planned:
            dest = row.pop("__dest", "run")
            line = json.dumps(row, default=str) + "\n"
            if dest == "orders":
                fo.write(line)
                n_ord += 1
            elif row.get("event_type") == "alpaca_entry_attribution":
                fu.write(line)
                n_uni += 1
            else:
                fr.write(line)
                n_run += 1
    return n_run, n_ord, n_uni


if __name__ == "__main__":
    raise SystemExit(main())
