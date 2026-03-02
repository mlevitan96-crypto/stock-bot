#!/usr/bin/env python3
"""Fetch last run.jsonl lines and UW cache status from droplet. One-off diagnostic."""
import sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from droplet_client import DropletClient

def main():
    with DropletClient() as c:
        root_out, _, _ = c._execute(
            "([ -d /root/stock-bot-current/scripts ] && echo /root/stock-bot-current) || echo /root/stock-bot",
            timeout=10,
        )
        root = (root_out or "/root/stock-bot").strip().splitlines()[-1].strip()
        cd = "cd " + root
        out1, _, _ = c._execute(cd + " && tail -5 logs/run.jsonl 2>/dev/null || echo '[]'", timeout=10)
        out2, _, _ = c._execute(cd + " && ls -la data/uw_flow_cache.json 2>/dev/null || echo FILE_MISSING", timeout=10)
        out3, _, _ = c._execute(cd + " && wc -c data/uw_flow_cache.json 2>/dev/null || echo 0", timeout=10)
        out4, _, _ = c._execute(cd + " && tail -3 logs/worker_debug.log 2>/dev/null || echo NONE", timeout=10)
        print("=== Last 5 run.jsonl ===")
        print(out1 or "")
        print("=== data/uw_flow_cache.json ===")
        print(out2 or "")
        print(out3 or "")
        print("=== Last 3 worker_debug.log ===")
        print(out4 or "")

if __name__ == "__main__":
    main()
