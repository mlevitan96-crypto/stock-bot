#!/usr/bin/env python3
"""
Kill duplicate or orphan stock-bot processes on the droplet.

Discovers:
- Orphan main.py (e.g. the one in tmux/pts, not under deploy_supervisor)
- Multiple uw_flow_daemon.py (if > 1 running)

Default: dry run (print what would be killed).
Use --kill to send SIGTERM. Use --also-uw to also stop all uw_flow_daemon
so you can start a single instance via: systemctl start uw-flow-daemon.service
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def main() -> int:
    parser = argparse.ArgumentParser(description="Kill duplicate/orphan stock-bot processes on droplet")
    parser.add_argument("--kill", action="store_true", help="Actually send SIGTERM to discovered PIDs")
    parser.add_argument("--also-uw", action="store_true", help="Also stop all uw_flow_daemon (so you can start one via systemd)")
    args = parser.parse_args()

    try:
        from droplet_client import DropletClient
    except ImportError:
        print("Need droplet_client and droplet_config.json", file=sys.stderr)
        return 1

    def run(cmd: str, timeout: int = 15) -> str:
        out, err, rc = c._execute(cmd, timeout=timeout)
        return ((out or "").strip() + ("\n" + (err or "").strip() if err else "")).strip()

    with DropletClient() as c:
        # Orphan main.py: has tty pts/* (tmux) instead of ? (supervised)
        discover_main = (
            "ps -eo pid,tty,args --no-headers | grep 'main.py' | grep -v grep | awk '$2 != \"?\" {print $1}'"
        )
        main_pids = run(discover_main).strip().splitlines()
        main_pids = [p.strip() for p in main_pids if p.strip()]

        # All uw_flow_daemon PIDs (for --also-uw we kill all so user can start one via systemd)
        discover_uw = "pgrep -f 'uw_flow_daemon.py' || true"
        uw_pids = run(discover_uw).strip().splitlines()
        uw_pids = [p.strip() for p in uw_pids if p.strip()]

        to_kill = []
        if main_pids:
            to_kill.extend(("main.py (orphan)", main_pids))
        if args.also_uw and uw_pids:
            to_kill.extend(("uw_flow_daemon.py", uw_pids))

        if not main_pids and not (args.also_uw and uw_pids):
            print("No duplicate/orphan processes found.")
            if not args.also_uw and uw_pids:
                print(f"  (uw_flow_daemon: {len(uw_pids)} running; use --also-uw to stop all and start one via systemd)")
            return 0

        # Summary
        print("Discovered:")
        if main_pids:
            detail = run(f"ps -o pid,pcpu,pmem,etime,args -p {','.join(main_pids)} 2>/dev/null")
            print("  Orphan main.py (not under supervisor, e.g. tmux):")
            print(detail)
        if args.also_uw and uw_pids:
            detail = run(f"ps -o pid,pcpu,pmem,etime,args -p {','.join(uw_pids)} 2>/dev/null")
            print("  uw_flow_daemon.py (will stop all so you can start one via systemctl):")
            print(detail)

        if not args.kill:
            print("\nDry run. To kill these processes run with --kill")
            if main_pids:
                print(f"  Would kill PIDs: {', '.join(main_pids)}")
            if args.also_uw and uw_pids:
                print(f"  Would kill uw_flow_daemon PIDs: {', '.join(uw_pids)}")
            return 0

        all_pids = main_pids + (uw_pids if args.also_uw else [])
        for pid in all_pids:
            if not pid.isdigit():
                continue
            run(f"kill {pid}")
            print(f"  Sent SIGTERM to PID {pid}")

        print("Done.")
        if args.also_uw and uw_pids:
            print("Start one UW daemon via: ssh <droplet> 'sudo systemctl start uw-flow-daemon.service'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
