#!/usr/bin/env python3
"""Force droplet /root/stock-bot to match origin/main (resolves pull conflicts from local edits)."""
from __future__ import annotations

import subprocess
import sys

REMOTE = r"""set -e
cd /root/stock-bot
git fetch origin main
# Remove untracked duplicate that blocks checkout of tracked telemetry/shadow_evaluator.py
if [ -f telemetry/shadow_evaluator.py ]; then
  git ls-files --error-unmatch telemetry/shadow_evaluator.py >/dev/null 2>&1 || rm -f telemetry/shadow_evaluator.py
fi
git reset --hard origin/main
git status -sb | head -n 5
test -f models/vanguard_v2_profit_agent.json && echo V2_MODEL_OK
test -f telemetry/vanguard_ml_runtime.py && echo VANGUARD_RUNTIME_OK
sudo systemctl restart stock-bot.service
systemctl is-active stock-bot.service
systemctl status stock-bot.service --no-pager -l | head -n 22
"""


def main() -> int:
    cmd = [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=60",
        "root@alpaca",
        "bash",
        "-lc",
        REMOTE,
    ]
    return int(subprocess.run(cmd, check=False).returncode)


if __name__ == "__main__":
    raise SystemExit(main())
