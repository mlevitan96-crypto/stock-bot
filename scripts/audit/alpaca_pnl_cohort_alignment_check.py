#!/usr/bin/env python3
"""
Verify workspace logs contain exit_attribution rows for each complete_trade_id in the session window.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

REPO = Path(__file__).resolve().parents[2]


def _parse_ts(s: Any) -> Optional[float]:
    if s is None:
        return None
    try:
        t = str(s).strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(t)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except Exception:
        return None


def _load_ids(path: Path) -> Tuple[List[str], Dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return [str(x) for x in raw], {}
    ids = raw.get("complete_trade_ids") or raw.get("trade_ids") or []
    return [str(x) for x in ids], raw


def _exit_index(root: Path) -> Dict[str, dict]:
    p = root / "logs" / "exit_attribution.jsonl"
    out: Dict[str, dict] = {}
    if not p.is_file():
        return out
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        tid = r.get("trade_id")
        if tid:
            out[str(tid)] = r
    return out


def _exits_in_window(root: Path, t0: float, t1: float) -> Tuple[int, List[str]]:
    p = root / "logs" / "exit_attribution.jsonl"
    n = 0
    tids: List[str] = []
    if not p.is_file():
        return 0, []
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = _parse_ts(r.get("timestamp"))
        if ts is None or not (t0 <= ts <= t1):
            continue
        n += 1
        if r.get("trade_id"):
            tids.append(str(r["trade_id"]))
    return n, tids


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--complete-trade-ids", type=Path, required=True)
    ap.add_argument("--window-start-epoch", type=float, required=True)
    ap.add_argument("--window-end-epoch", type=float, required=True)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--json-out", type=Path, default=None)
    args = ap.parse_args()
    root = args.root.resolve()
    ids, meta = _load_ids(args.complete_trade_ids)
    expected_n = int(meta.get("trades_complete", len(ids)) or len(ids))
    by_id = _exit_index(root)
    missing = [i for i in ids if i not in by_id]
    win_n, win_tids = _exits_in_window(root, args.window_start_epoch, args.window_end_epoch)
    id_set: Set[str] = set(ids)
    extras = [t for t in win_tids if t and t not in id_set]

    out_of_window: List[str] = []
    for i in ids:
        r = by_id.get(i)
        if not r:
            continue
        ts = _parse_ts(r.get("timestamp"))
        if ts is None or not (args.window_start_epoch <= ts <= args.window_end_epoch):
            out_of_window.append(i)

    if expected_n == 0:
        ok = len(ids) == 0 and win_n == 0
    else:
        ok = (
            len(ids) == expected_n
            and len(missing) == 0
            and len(out_of_window) == 0
            and len(ids) > 0
        )

    report: Dict[str, Any] = {
        "aligned": ok,
        "root": str(root),
        "window_start_epoch": args.window_start_epoch,
        "window_end_epoch": args.window_end_epoch,
        "cohort_trade_ids_count": len(ids),
        "expected_trades_complete": expected_n,
        "missing_trade_ids_in_exit_attribution": missing,
        "cohort_ids_exit_timestamp_outside_window": out_of_window,
        "exits_in_window_count": win_n,
        "window_trade_ids_sample": win_tids[:50],
        "extras_in_window_not_in_cohort": extras[:20],
    }
    print(json.dumps(report, indent=2))
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
