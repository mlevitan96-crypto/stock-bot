#!/usr/bin/env python3
"""Run Phase 0-1 capture on droplet; print markdown chunks to stdout for evidence assembly."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from droplet_client import DropletClient


def main() -> int:
    c = DropletClient()
    out: dict[str, str] = {}

    out["head"] = c.execute_command("cd /root/stock-bot && git rev-parse HEAD", 30).get("stdout", "")
    out["et"] = c.execute_command("TZ=America/New_York date +%Y-%m-%d", 30).get("stdout", "").strip() or "unknown"

    out["systemctl"] = c.execute_command(
        "systemctl status stock-bot --no-pager -l 2>&1 | head -70", 60
    ).get("stdout", "")

    out["show"] = c.execute_command(
        "systemctl show stock-bot -p ExecStart -p Environment -p FragmentPath 2>&1", 30
    ).get("stdout", "")

    out["ps"] = c.execute_command("ps aux | grep stock-bot | grep -v grep | head -25", 30).get("stdout", "")

    out["journal"] = c.execute_command(
        "journalctl -u stock-bot --since '36 hours ago' --no-pager 2>&1 | tail -n 800",
        240,
    ).get("stdout", "")

    out["profit_run"] = c.execute_command(
        "cd /root/stock-bot && PYTHONPATH=. python3 scripts/audit/run_alpaca_profit_discovery_campaign.py --root /root/stock-bot 2>&1",
        600,
    ).get("stdout", "")

    # Phase 1: find candidates
    find_cmds = [
        (
            "uw_names",
            "find /root/stock-bot/logs /root/stock-bot/reports /root/stock-bot/artifacts /tmp -type f "
            "2>/dev/null | grep -iE 'uw|unusual|whale|flow|dark|imbalance|signal.context|score.snapshot|spi|bar|candle|ohlc' "
            "| head -200",
        ),
        (
            "sig_ctx_stat",
            "stat -c '%n %s %y' /root/stock-bot/logs/signal_context.jsonl 2>&1; wc -l /root/stock-bot/logs/signal_context.jsonl 2>&1",
        ),
        (
            "bars_stat",
            "stat -c '%n %s %y' /root/stock-bot/artifacts/market_data/alpaca_bars.jsonl 2>&1; "
            "find /root/stock-bot/data/bars_cache -type f 2>/dev/null | head -20",
        ),
        (
            "spi_glob",
            "find /root/stock-bot/reports -name 'ALPACA_SPI*.md' -o -name '*SPI*.md' 2>/dev/null | head -40",
        ),
        (
            "score_snap_wc",
            "wc -l /root/stock-bot/logs/score_snapshot.jsonl 2>&1; head -n 2 /root/stock-bot/logs/score_snapshot.jsonl 2>&1",
        ),
        (
            "uw_cache",
            "ls -lah /root/stock-bot/state/uw_cache 2>&1 | head -30",
        ),
        (
            "run_jsonl_sample",
            "grep -i 'signal_context\\|uw_' /root/stock-bot/logs/run.jsonl 2>/dev/null | tail -n 3 | head -c 4000 || true",
        ),
    ]
    phase1: dict[str, str] = {}
    for name, cmd in find_cmds:
        phase1[name] = c.execute_command(cmd, 120).get("stdout", "")

    bundle = {"phase0": out, "phase1": phase1}
    dest = Path(__file__).resolve().parents[2] / "reports" / "daily" / out["et"] / "evidence" / "_PROFIT_V2_DROPLET_RAW.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    print(str(dest))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
