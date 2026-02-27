#!/usr/bin/env python3
"""
Start stock-bot services on the droplet after a power cycle or upgrade.

Use this after you have powered the droplet back on (e.g. after resizing).
Run from your machine with droplet_config.json configured.

  python scripts/start_droplet_services.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def main() -> int:
    try:
        from droplet_client import DropletClient
    except ImportError:
        print("Need droplet_client and droplet_config.json", file=sys.stderr)
        return 1

    def run(cmd: str, timeout: int = 30) -> tuple[str, str, int]:
        return c._execute(cmd, timeout=timeout)

    with DropletClient() as c:
        print("Starting stock-bot.service ...")
        out, err, rc = run("sudo systemctl start stock-bot.service")
        if rc != 0:
            print("stderr:", err or "(none)")
            print("stdout:", out or "(none)")
        print("stock-bot.service started." if rc == 0 else "stock-bot.service start returned non-zero.")

        print("\nStarting uw-flow-daemon.service ...")
        out2, err2, rc2 = run("sudo systemctl start uw-flow-daemon.service")
        if rc2 != 0:
            print("stderr:", err2 or "(none)")
        print("uw-flow-daemon.service started." if rc2 == 0 else "uw-flow-daemon.service start returned non-zero (may already be running).")

        print("\nChecking status ...")
        out3, _, _ = run("systemctl is-active stock-bot.service 2>/dev/null || echo inactive")
        out4, _, _ = run("systemctl is-active uw-flow-daemon.service 2>/dev/null || echo inactive")
        print("  stock-bot.service:", (out3 or "").strip())
        print("  uw-flow-daemon.service:", (out4 or "").strip())

        print("\nStock-bot–related processes:")
        out5, _, _ = run(
            "ps -eo pid,pcpu,pmem,args --no-headers | grep -E 'main.py|dashboard|heartbeat|deploy_supervisor|uw_flow' | grep -v grep"
        )
        print(out5 or "(none)")

    print("\nDone. Run python scripts/list_droplet_processes.py for full inventory.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
