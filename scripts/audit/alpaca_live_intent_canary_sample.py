#!/usr/bin/env python3
"""Sample entry_decision_made rows after deploy floor; emit JSON summary for evidence."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _parse_ts(rec: dict) -> float | None:
    from telemetry.alpaca_strict_completeness_gate import _parse_iso_ts

    for k in ("ts", "timestamp"):
        t = _parse_iso_ts(rec.get(k))
        if t is not None:
            return t
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--floor-ts", type=float, required=True, dest="floor_ts")
    ap.add_argument("--min-rows", type=int, default=20)
    ap.add_argument("--max-wait-sec", type=int, default=0, help="If >0, poll run.jsonl until min-rows or timeout")
    ap.add_argument("--poll-interval-sec", type=int, default=30)
    args = ap.parse_args()
    import time

    logs = args.root.resolve() / "logs" / "run.jsonl"
    deadline = time.time() + max(0, args.max_wait_sec)

    def scan() -> List[dict]:
        rows: List[dict] = []
        if not logs.is_file():
            return rows
        with logs.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("event_type") != "entry_decision_made":
                    continue
                t = _parse_ts(rec)
                if t is None or t <= float(args.floor_ts):
                    continue
                rows.append(rec)
        return rows

    rows = scan()
    while args.max_wait_sec > 0 and len(rows) < args.min_rows and time.time() < deadline:
        time.sleep(max(1, args.poll_interval_sec))
        rows = scan()

    good = 0
    blocker = 0
    bad = 0
    redacted: List[Dict[str, Any]] = []
    for rec in rows[-50:]:
        st = str(rec.get("entry_intent_status") or "")
        synth = bool(rec.get("strict_backfilled") or rec.get("strict_backfill_trade_id") or rec.get("entry_intent_synthetic") is True)
        if synth:
            bad += 1
            continue
        if st == "OK":
            good += 1
        elif st == "MISSING_INTENT_BLOCKER":
            blocker += 1
        else:
            bad += 1
        if len(redacted) < 3:
            redacted.append(
                {
                    "symbol": rec.get("symbol"),
                    "trade_id": rec.get("trade_id"),
                    "entry_intent_status": st,
                    "entry_intent_synthetic": rec.get("entry_intent_synthetic"),
                    "entry_intent_source": rec.get("entry_intent_source"),
                    "has_signal_trace": bool(rec.get("signal_trace")),
                    "entry_score_total": rec.get("entry_score_total"),
                    "entry_score_components_keys": list((rec.get("entry_score_components") or {}).keys())[:12]
                    if isinstance(rec.get("entry_score_components"), dict)
                    else None,
                }
            )

    out = {
        "floor_ts": args.floor_ts,
        "sample_total_post_floor": len(rows),
        "count_good_ok": good,
        "count_missing_intent_blocker": blocker,
        "count_synthetic_or_other": bad,
        "example_rows_redacted": redacted,
        "wait_used_sec": max(0, args.max_wait_sec),
    }
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
