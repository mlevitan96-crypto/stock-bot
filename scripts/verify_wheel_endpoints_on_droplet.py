#!/usr/bin/env python3
"""Verify /api/stockbot/closed_trades and /api/stockbot/wheel_analytics on droplet."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from droplet_client import DropletClient

def main():
    cmd = (
        "cd /root/stock-bot && set -a && source .env 2>/dev/null && set +a && "
        "curl -s -o /dev/null -w '%{http_code}' -u \"$DASHBOARD_USER:$DASHBOARD_PASS\" "
        "http://127.0.0.1:5000/api/stockbot/closed_trades"
    )
    c = DropletClient()
    out, err, rc = c._execute(cmd, timeout=15)
    ct_ok = out and out.strip() == "200"
    cmd2 = (
        "cd /root/stock-bot && set -a && source .env 2>/dev/null && set +a && "
        "curl -s -o /dev/null -w '%{http_code}' -u \"$DASHBOARD_USER:$DASHBOARD_PASS\" "
        "http://127.0.0.1:5000/api/stockbot/wheel_analytics"
    )
    out2, err2, rc2 = c._execute(cmd2, timeout=15)
    wa_ok = out2 and out2.strip() == "200"
    c.close()
    print("closed_trades:", "200 OK" if ct_ok else f"got {out}")
    print("wheel_analytics:", "200 OK" if wa_ok else f"got {out2}")
    return 0 if (ct_ok and wa_ok) else 1

if __name__ == "__main__":
    sys.exit(main())
