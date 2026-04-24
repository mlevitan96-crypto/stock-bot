#!/usr/bin/env python3
"""
Run long/short verification on droplet and print report.
Uploads scripts/verify_long_short_on_droplet.py, runs it on droplet (with droplet env/logs), prints output.

Usage: python scripts/run_verify_long_short_on_droplet.py [--last 200]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--last", type=int, default=200, help="Last N trades/signals")
    args = ap.parse_args()
    try:
        from droplet_client import DropletClient
    except ImportError:
        print("droplet_client not found; run from repo root", file=sys.stderr)
        return 1

    proj = "/root/stock-bot"
    script = REPO / "scripts" / "verify_long_short_on_droplet.py"
    if not script.exists():
        print(f"Script not found: {script}", file=sys.stderr)
        return 1

    with DropletClient() as c:
        c._execute(f"mkdir -p {proj}/scripts")
        c.put_file(script, f"{proj}/scripts/verify_long_short_on_droplet.py")
        cmd = f"cd {proj} && python3 scripts/verify_long_short_on_droplet.py --base-dir . --last {args.last}"
        out, err, rc = c._execute(cmd, timeout=60)
        # Avoid UnicodeEncodeError on Windows console (cp1252)
        try:
            print(out)
        except UnicodeEncodeError:
            print(out.encode("ascii", errors="replace").decode("ascii"))
        if err:
            print(err, file=sys.stderr)
        if rc != 0:
            print("Script exited with", rc, file=sys.stderr)
            return rc
    return 0


if __name__ == "__main__":
    sys.exit(main())
