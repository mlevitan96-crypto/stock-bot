#!/usr/bin/env python3
"""One-shot: SSH to droplet and run epoch reset + restart (run from dev machine)."""
from __future__ import annotations

import subprocess
import sys

REMOTE = r"""set -e
cd /root/stock-bot
git pull --ff-only origin main
mkdir -p reports/archive
STAMP=$(date -u +%F_%H%M)
if ls logs/*.jsonl >/dev/null 2>&1; then
  tar -czvf "reports/archive/logs_pre_v2_live_${STAMP}.tar.gz" logs/*.jsonl
  truncate -s 0 logs/*.jsonl
fi
mkdir -p state
echo '{}' > state/alpaca_10trade_harvester_sent.json
echo '{}' > state/alpaca_100trade_sent.json
echo '{}' > state/alpaca_milestone_250_state.json
rm -f state/alpaca_milestone_integrity_arm.json
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
cat > state/epoch_state.json <<EOF
{"started_at_utc": "${NOW}", "fired_milestones": []}
EOF
sudo systemctl restart stock-bot.service
systemctl is-active stock-bot.service
systemctl status stock-bot.service --no-pager -l | head -n 30
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
    print("Running:", " ".join(cmd[:6]), "<remote bash>", flush=True)
    r = subprocess.run(cmd, check=False)
    return int(r.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
