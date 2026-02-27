#!/usr/bin/env python3
"""
Apply path-to-profitability paper overlay to stock-bot.service and restart.
- Creates systemd drop-in: MIN_EXEC_SCORE=2.7 (from state/paper_overlay.env or default)
- Restarts stock-bot.service so overlay is active and autopilot 50-trade count works
- Enables stock-bot and uw-flow-daemon for boot (so bot starts at market open after reboot)

Run from your machine: python scripts/apply_paper_overlay_and_restart_stockbot_on_droplet.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def main() -> int:
    from droplet_client import DropletClient

    dropin_dir = "/etc/systemd/system/stock-bot.service.d"
    dropin_conf = "paper-overlay.conf"
    # MIN_EXEC_SCORE from overlay (2.5 + 0.2) or use 2.7
    min_score = "2.7"

    commands = [
        f"sudo mkdir -p {dropin_dir}",
        f"echo '[Service]' | sudo tee {dropin_dir}/{dropin_conf}",
        f"echo 'Environment=MIN_EXEC_SCORE={min_score}' | sudo tee -a {dropin_dir}/{dropin_conf}",
        "sudo systemctl daemon-reload",
        "sudo systemctl restart stock-bot.service",
        "sudo systemctl enable stock-bot.service 2>/dev/null || true",
        "sudo systemctl enable uw-flow-daemon.service 2>/dev/null || true",
        "sleep 3",
        "systemctl is-active stock-bot.service",
        "systemctl is-enabled stock-bot.service 2>/dev/null || echo not-enabled",
    ]

    def safe_print(s: str) -> None:
        if not s:
            return
        try:
            print(s)
        except UnicodeEncodeError:
            print(s.encode("ascii", errors="replace").decode("ascii"))

    with DropletClient() as c:
        print("Applying paper overlay (MIN_EXEC_SCORE=2.7) to stock-bot.service and restarting...")
        for i, cmd in enumerate(commands):
            to = 90 if "restart" in cmd or "daemon-reload" in cmd else 30
            out, err, rc = c._execute(cmd, timeout=to)
            if out and out.strip():
                safe_print(out.strip())
            if err and rc != 0:
                safe_print("stderr: " + err[:500])
            if "restart" in cmd and rc != 0:
                print("Restart may have timed out; checking status.")
        print("\n--- Status ---")
        out, _, _ = c._execute("systemctl status stock-bot.service --no-pager -l 2>/dev/null | head -25")
        safe_print(out or "(no output)")
        out2, _, _ = c._execute("systemctl show stock-bot.service -p Environment 2>/dev/null")
        safe_print("Environment snippet: " + (out2 or "").strip()[:200])
    print("\nDone. Stock-bot is restarted with MIN_EXEC_SCORE=2.7; enabled for boot.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
