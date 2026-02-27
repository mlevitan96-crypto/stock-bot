#!/usr/bin/env python3
"""
Enable EXPECTANCY_GATE_TRUTH_LOG=1 and SIGNAL_SCORE_BREAKDOWN_LOG=1 in stock-bot
systemd service on the droplet, restart, optionally wait for 200 gate truth + 100
breakdown lines, then run full investigation and fetch. Use when 0 trades and
we need signal-level proof. Requires droplet_config.json and SSH (sudo on droplet).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def main() -> int:
    try:
        from droplet_client import DropletClient
    except Exception as e:
        print(f"DropletClient not available: {e}", file=sys.stderr)
        return 1

    pd = "~/stock-bot"
    with DropletClient() as c:
        # 1) Enable truth logs in systemd (requires sudo)
        override_cmd = (
            "sudo mkdir -p /etc/systemd/system/stock-bot.service.d && "
            "echo '[Service]' | sudo tee /etc/systemd/system/stock-bot.service.d/override.conf && "
            "echo 'Environment=\"EXPECTANCY_GATE_TRUTH_LOG=1\"' | sudo tee -a /etc/systemd/system/stock-bot.service.d/override.conf && "
            "echo 'Environment=\"SIGNAL_SCORE_BREAKDOWN_LOG=1\"' | sudo tee -a /etc/systemd/system/stock-bot.service.d/override.conf"
        )
        out, err, rc = c._execute(f"cd {pd} && {override_cmd}", timeout=15)
        if rc != 0:
            print("Override write failed:", out, err, file=sys.stderr)
        else:
            print("Override written.")
        reload_cmd = "sudo systemctl daemon-reload && sudo systemctl restart stock-bot"
        out2, err2, rc2 = c._execute(reload_cmd, timeout=20)
        if rc2 != 0:
            print("Daemon-reload/restart failed:", out2, err2, file=sys.stderr)
        else:
            print("stock-bot restarted with truth log env vars.")
        # 2) Wait for 200 + 100 lines (poll every 30s, max 30 min)
        need_gate, need_break = 200, 100
        deadline = time.monotonic() + 30 * 60
        while time.monotonic() < deadline:
            out, _, _ = c._execute(
                f"cd {pd} && wc -l logs/expectancy_gate_truth.jsonl logs/signal_score_breakdown.jsonl 2>/dev/null || echo '0 0'",
                timeout=10,
            )
            n_gate, n_break = 0, 0
            if out:
                parts = out.strip().split()
                if len(parts) >= 2:
                    try:
                        n_gate = int(parts[0])
                        n_break = int(parts[1]) if len(parts) > 2 else 0
                    except Exception:
                        pass
            if n_gate >= need_gate and n_break >= need_break:
                print(f"Truth logs ready: gate={n_gate}, breakdown={n_break}")
                break
            print(f"Waiting for truth logs: gate={n_gate}/{need_gate}, breakdown={n_break}/{need_break}")
            time.sleep(30)
        # 3) Run report scripts and fetch
        FETCHED_DIR = REPO / "reports" / "investigation" / "fetched"
        FETCHED_DIR.mkdir(parents=True, exist_ok=True)
        for cmd in [
            "python3 scripts/expectancy_gate_truth_report_200_on_droplet.py",
            "python3 scripts/signal_score_breakdown_summary_on_droplet.py",
            "python3 scripts/signal_pipeline_deep_dive_on_droplet.py --symbols SPY,QQQ,COIN,NVDA,TSLA --n 25 --window-hours 168",
            "python3 scripts/signal_coverage_and_waste_report_on_droplet.py",
            "python3 scripts/full_signal_review_on_droplet.py --days 7",
            "python3 scripts/run_closed_loops_checklist_on_droplet.py",
        ]:
            out, err, rc = c._execute(f"cd {pd} && {cmd}", timeout=120)
            if out:
                print(out[:400])
        to_fetch = [
            ("reports/signal_review/expectancy_gate_truth_200.md", "expectancy_gate_truth_200.md"),
            ("reports/signal_review/signal_score_breakdown_summary.md", "signal_score_breakdown_summary.md"),
            ("reports/signal_review/SIGNAL_PIPELINE_DEEP_DIVE.md", "SIGNAL_PIPELINE_DEEP_DIVE.md"),
            ("reports/signal_review/SIGNAL_COVERAGE_AND_WASTE.md", "SIGNAL_COVERAGE_AND_WASTE.md"),
            ("reports/investigation/CLOSED_LOOPS_CHECKLIST.md", "CLOSED_LOOPS_CHECKLIST.md"),
        ]
        for remote, local_name in to_fetch:
            out, _, _ = c._execute(f"cat {pd}/{remote} 2>/dev/null || echo '__MISSING__'", timeout=15)
            content = (out or "").strip()
            if content and "__MISSING__" not in content:
                (FETCHED_DIR / local_name).write_text(content, encoding="utf-8")
                print(f"Fetched: {remote}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
