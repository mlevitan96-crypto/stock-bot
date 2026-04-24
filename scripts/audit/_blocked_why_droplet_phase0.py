#!/usr/bin/env python3
"""Run Phase 0 discovery on droplet; write reports/daily/<ET>/evidence/_BLOCKED_WHY_PHASE0_RAW.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from droplet_client import DropletClient


def main() -> int:
    c = DropletClient()
    cmds = [
        ("et", "TZ=America/New_York date +%Y-%m-%d"),
        ("head", "cd /root/stock-bot && git rev-parse HEAD"),
        ("status", "systemctl status stock-bot --no-pager -l 2>&1 | head -80"),
        ("cat", "systemctl cat stock-bot 2>&1 | head -120"),
        (
            "show",
            "systemctl show stock-bot -p Environment -p EnvironmentFiles -p EnvironmentFile -p FragmentPath 2>&1",
        ),
        (
            "journal",
            "journalctl -u stock-bot --since '36 hours ago' --no-pager 2>&1 | tail -n 800",
        ),
        (
            "find_blocked",
            "cd /root/stock-bot && find . -maxdepth 4 -type f \\( -name '*blocked*jsonl' -o -name '*blocked*json' \\) 2>/dev/null",
        ),
        (
            "rg_blocked",
            "cd /root/stock-bot && rg -l blocked_trades -S . 2>/dev/null | head -80",
        ),
        (
            "find_exit",
            "cd /root/stock-bot && find . -type f \\( -name '*exit*attribution*' -o -name '*trade*ledger*' -o -name '*fills*' -o -name '*orders*' \\) 2>/dev/null | head -80",
        ),
        (
            "find_bars",
            "cd /root/stock-bot && find artifacts -type f \\( -name '*bars*jsonl' -o -name '*ohlc*' -o -name '*candles*' \\) 2>/dev/null",
        ),
        (
            "find_snap",
            "cd /root/stock-bot && find . -type f \\( -name '*score_snapshot*' -o -name '*signal_context*' -o -name '*uw*context*' \\) 2>/dev/null | head -50",
        ),
        (
            "stat_blocked",
            "stat -c '%n %s %y' /root/stock-bot/state/blocked_trades.jsonl 2>&1; wc -l /root/stock-bot/state/blocked_trades.jsonl 2>&1",
        ),
        (
            "stat_exit",
            "stat -c '%n %s %y' /root/stock-bot/logs/exit_attribution.jsonl 2>&1; wc -l /root/stock-bot/logs/exit_attribution.jsonl 2>&1",
        ),
        (
            "stat_bars",
            "stat -c '%n %s %y' /root/stock-bot/artifacts/market_data/alpaca_bars.jsonl 2>&1; wc -l /root/stock-bot/artifacts/market_data/alpaca_bars.jsonl 2>&1",
        ),
    ]
    out: dict = {}
    for k, cmd in cmds:
        timeout = 300 if k == "journal" else 120
        r = c.execute_command(cmd, timeout)
        out[k] = {
            "exit_code": r.get("exit_code"),
            "stdout": (r.get("stdout") or "")[:800000],
            "stderr": (r.get("stderr") or "")[:8000],
        }
    et = (out.get("et") or {}).get("stdout", "").strip() or "unknown"
    dest = (
        Path(__file__).resolve().parents[2]
        / "reports"
        / "daily"
        / et
        / "evidence"
        / "_BLOCKED_WHY_PHASE0_RAW.json"
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(et, dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
