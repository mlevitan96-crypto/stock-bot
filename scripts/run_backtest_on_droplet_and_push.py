#!/usr/bin/env python3
"""
Run the 30-day backtest ON THE DROPLET and push results to GitHub.
Uses DropletClient (SSH). Requires droplet_config.json and paramiko.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    try:
        from droplet_client import DropletClient
    except ImportError as e:
        print(f"Error: {e}. Install paramiko and ensure droplet_config.json exists.", file=sys.stderr)
        return 1

    # Droplet project dir: try common roots per MEMORY_BANK
    with DropletClient() as c:
        root = c.project_dir
        # Run: sync repo, write config, run backtest, then push results
        cmd = (
            f"cd {root} 2>/dev/null || cd /root/stock-bot-current 2>/dev/null || cd /root/stock-bot && "
            "git stash push -m 'pre-backtest' || true && "
            "git fetch --all && git checkout main && git pull --rebase origin main && "
            "export OUT_DIR_PREFIX=30d_after_signal_engine_block3f && "
            "bash board/eod/run_30d_backtest_on_droplet.sh"
        )
        print("Running on droplet:", cmd[:120], "...")
        out, err, rc = c._execute(cmd, timeout=300)
        print(out)
        if err:
            print(err, file=sys.stderr)
        if rc != 0:
            print(f"Exit code: {rc}", file=sys.stderr)
            return rc
    print("Backtest on droplet complete; results pushed to GitHub.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
