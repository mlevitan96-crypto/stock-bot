#!/usr/bin/env python3
"""
During market hours: confirm canonical JSONL sinks are receiving writes (mtime + last-row timestamps).

Run on droplet (repo root):
  python3 scripts/audit/alpaca_live_telemetry_freshness.py
  python3 scripts/audit/alpaca_live_telemetry_freshness.py --max-age-sec 3600

Exit 0 if Alpaca clock reports market open AND core logs are fresher than --max-age-sec
(default 1h — idle engines may not touch run/orders every few minutes).
Exit 1 otherwise (still prints diagnostic lines to stdout).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parent.parent.parent
os.chdir(REPO)
sys.path.insert(0, str(REPO))


def _last_ts_hint(path: Path) -> Optional[str]:
    last = None
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            sz = f.tell()
            f.seek(max(0, sz - 131072))
            for line in f.read().decode("utf-8", errors="replace").splitlines():
                if not line.strip():
                    continue
                try:
                    j = json.loads(line)
                    for k in ("ts", "timestamp", "event_ts", "generated_at_utc", "time", "utc_ts"):
                        v = j.get(k)
                        if v:
                            last = str(v)[:120]
                            break
                except Exception:
                    pass
    except Exception:
        pass
    return last


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-age-sec", type=int, default=3600, help="Core logs must be newer than this (default 1h).")
    args = ap.parse_args()

    try:
        from dotenv import load_dotenv  # type: ignore

        load_dotenv(REPO / ".env")
        import alpaca_trade_api as tradeapi  # type: ignore

        from main import Config

        api = tradeapi.REST(Config.ALPACA_KEY, Config.ALPACA_SECRET, Config.ALPACA_BASE_URL, api_version="v2")
        clk = api.get_clock()
        is_open = bool(getattr(clk, "is_open", False))
        print(
            "ALPACA_CLOCK",
            json.dumps(
                {"is_open": is_open, "timestamp": str(getattr(clk, "timestamp", "") or "")},
            ),
        )
    except Exception as e:
        print("ALPACA_CLOCK_ERROR", str(e)[:300])
        is_open = False

    now = time.time()
    core = [
        "logs/run.jsonl",
        "logs/orders.jsonl",
        "logs/system_events.jsonl",
    ]
    extended = [
        "logs/attribution.jsonl",
        "logs/exit_attribution.jsonl",
        "logs/positions.jsonl",
        "logs/signal_context.jsonl",
        "logs/pnl_reconciliation.jsonl",
    ]
    all_rels = core + extended
    worst_core_age: Optional[float] = None
    core_missing = False
    for rel in all_rels:
        p = REPO / rel
        if not p.is_file():
            print(rel, "MISSING")
            if rel in core:
                core_missing = True
            continue
        age = now - p.stat().st_mtime
        if rel in core:
            worst_core_age = age if worst_core_age is None else max(worst_core_age, age)
        hint = _last_ts_hint(p)
        print(f"{rel} mtime_age_sec={int(age)} last_row_ts_hint={hint!r}")

    ok_live = (
        not core_missing
        and worst_core_age is not None
        and worst_core_age <= args.max_age_sec
    )
    if is_open and ok_live:
        print(
            "LIVE_TELEMETRY_VERDICT",
            json.dumps({"pass": True, "max_age_sec": args.max_age_sec, "worst_core_mtime_age_sec": int(worst_core_age)}),
        )
        return 0
    print(
        "LIVE_TELEMETRY_VERDICT",
        json.dumps(
            {
                "pass": False,
                "max_age_sec": args.max_age_sec,
                "market_open": is_open,
                "worst_core_mtime_age_sec": int(worst_core_age) if worst_core_age is not None else None,
                "note": "If market is open but FAIL: engine may be idle (no intents/orders) — surfaces still OK for next activity.",
            },
        ),
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
