#!/usr/bin/env python3
"""Verify dashboard has Strategy column and wheel_state is readable on droplet."""
from pathlib import Path
import sys
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

def main():
    from droplet_client import DropletClient
    cmd = (
        "REPO=$( [ -d /root/stock-bot-current/scripts ] && echo /root/stock-bot-current || echo /root/stock-bot ); "
        "cd $REPO && "
        "echo '=== Dashboard has Strategy column? ===' && "
        "grep -n \"Strategy.*Symbol.*Side\" dashboard.py | head -3; "
        "echo '' && echo '=== wheel_state.json exists and open_csps? ===' && "
        "if [ -f state/wheel_state.json ]; then "
        "  python3 -c \"import json; d=json.load(open('state/wheel_state.json')); oc=d.get('open_csps') or {}; print('open_csps keys:', list(oc.keys())); print('open_csps total entries:', sum(len(v) if isinstance(v,list) else 1 for v in oc.values())); print('sample:', list(oc.items())[:1])\"; "
        "else echo 'state/wheel_state.json NOT FOUND'; fi; "
        "echo '' && echo '=== Which process runs dashboard? ===' && "
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
