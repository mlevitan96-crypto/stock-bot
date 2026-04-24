#!/usr/bin/env python3
"""
Set MIN_EXEC_SCORE for stock-bot.service on the droplet via a late-order systemd drop-in
(zzz- prefix so it overrides other fragments), daemon-reload, restart.

Usage:
  python scripts/apply_min_exec_score_on_droplet.py           # default 1.6
  python scripts/apply_min_exec_score_on_droplet.py 1.75      # explicit value
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def main() -> int:
    from droplet_client import DropletClient

    score = sys.argv[1] if len(sys.argv) > 1 else "1.6"
    dropin = "/etc/systemd/system/stock-bot.service.d/zzz-min-exec-score.conf"
    body = f"[Service]\nEnvironment=MIN_EXEC_SCORE={score}\n"
    import base64

    b64 = base64.b64encode(body.encode()).decode()
    cmds = [
        "sudo mkdir -p /etc/systemd/system/stock-bot.service.d",
        f"echo {b64} | base64 -d | sudo tee {dropin} > /dev/null",
        "sudo systemctl daemon-reload",
        "sudo systemctl restart stock-bot.service",
        "sleep 2",
        "systemctl is-active stock-bot.service",
        "systemctl show stock-bot.service -p Environment --no-pager",
    ]
    with DropletClient() as c:
        for cmd in cmds:
            to = 120 if "restart" in cmd else 45
            r = c.execute_command(cmd, timeout=to)
            if r.get("stdout", "").strip():
                print(r["stdout"].strip())
            if r.get("stderr", "").strip() and r.get("exit_code", 0) != 0:
                print("stderr:", r["stderr"][:800])
            if r.get("exit_code", 0) != 0 and "grep" not in cmd:
                print("failed:", cmd, "rc=", r.get("exit_code"))
                return 1
    print(f"Done. MIN_EXEC_SCORE should be {score} (verify grep line above).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
