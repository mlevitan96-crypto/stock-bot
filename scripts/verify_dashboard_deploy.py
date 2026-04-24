#!/usr/bin/env python3
"""Verify dashboard code on droplet exposes Strategy column and core API paths exist."""
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def main():
    from droplet_client import DropletClient

    cmd = (
        "REPO=$( [ -d /root/stock-bot-current/scripts ] && echo /root/stock-bot-current || echo /root/stock-bot ); "
        "cd $REPO && "
        "echo '=== Dashboard positions table header? ===' && "
        "grep -n \"Strategy\" dashboard.py | head -5; "
        "echo '' && echo '=== Sample API (localhost) ===' && "
        "curl -s -o /dev/null -w 'closed_trades:%{http_code}\\n' http://127.0.0.1:5000/api/stockbot/closed_trades; "
        "curl -s -o /dev/null -w 'sre_health:%{http_code}\\n' http://127.0.0.1:5000/api/sre/health; "
        "echo '' && echo '=== dashboard processes ===' && "
        "ps aux | grep dashboard | grep -v grep"
    )
    with DropletClient() as c:
        out, err, rc = c._execute(cmd, timeout=30)
    print(out or "")
    if err:
        print("STDERR:", err)
    return 0


if __name__ == "__main__":
    sys.exit(main())
