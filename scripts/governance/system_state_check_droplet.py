#!/usr/bin/env python3
"""System state check on droplet: service, overlays, attribution health, logs."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))


def main() -> int:
    from droplet_client import DropletClient

    failures = []
    with DropletClient() as c:
        # 1) stock-bot.service active
        out, _, rc = c._execute("systemctl is-active stock-bot.service 2>/dev/null || true", timeout=15)
        active = (out or "").strip().lower() == "active"
        if not active:
            failures.append("stock-bot.service not active")
        print(f"stock-bot.service: {'active' if active else 'NOT ACTIVE'}")

        # 2) Overlays loaded (exit + entry)
        out, _, _ = c._execute("systemctl show stock-bot.service -p Environment --no-pager 2>/dev/null || true")
        env = (out or "").strip()
        has_min_exec = "MIN_EXEC_SCORE" in env
        has_gov_tuning = "GOVERNED_TUNING_CONFIG" in env
        print(f"MIN_EXEC_SCORE in env: {has_min_exec}")
        print(f"GOVERNED_TUNING_CONFIG in env: {has_gov_tuning}")
        out2, _, _ = c._execute("ls /etc/systemd/system/stock-bot.service.d/ 2>/dev/null || true")
        print(f"Drop-ins: {(out2 or '').strip() or 'none'}")

        # 3) Rebuild baseline and check joined_count, total_losing_trades
        c._execute(
            "cd /root/stock-bot && python3 scripts/analysis/run_effectiveness_reports.py "
            "--start 2026-02-01 --end $(date -u +%Y-%m-%d) --out-dir reports/effectiveness_baseline_blame 2>&1 | tail -5",
            timeout=120,
        )
        out3, _, _ = c._execute(
            "cd /root/stock-bot && python3 -c \""
            "import json, os\n"
            "p = 'reports/effectiveness_baseline_blame/effectiveness_aggregates.json'\n"
            "j = json.load(open(p)) if os.path.exists(p) else {}\n"
            "print('joined_count', j.get('joined_count', 0))\n"
            "p2 = 'reports/effectiveness_baseline_blame/entry_vs_exit_blame.json'\n"
            "j2 = json.load(open(p2)) if os.path.exists(p2) else {}\n"
            "print('total_losing_trades', j2.get('total_losing_trades', 0))\"",
            timeout=15,
        )
        joined = 0
        losing = 0
        for line in (out3 or "").splitlines():
            parts = line.strip().split()
            if len(parts) >= 2:
                if parts[0] == "joined_count":
                    joined = int(parts[1])
                elif parts[0] == "total_losing_trades":
                    losing = int(parts[1])
        print(f"Baseline joined_count: {joined} (need >= 30)")
        print(f"Baseline total_losing_trades: {losing} (need >= 5)")
        if joined < 30:
            failures.append("joined_count < 30")
        if losing < 5:
            failures.append("total_losing_trades < 5")

        # 4) Logs readable
        out4, _, _ = c._execute(
            "cd /root/stock-bot && test -r logs/attribution.jsonl && test -r logs/exit_attribution.jsonl && echo OK || echo MISSING",
            timeout=5,
        )
        logs_ok = "OK" in (out4 or "")
        print(f"Logs (attribution, exit_attribution) readable: {logs_ok}")
        if not logs_ok:
            failures.append("logs not readable or missing")

    if failures:
        print("FAILURES:", failures)
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
