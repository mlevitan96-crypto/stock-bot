#!/usr/bin/env python3
"""Run trade visibility review on droplet and print or save the report."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from droplet_client import DropletClient

def main():
    c = DropletClient()
    # 48h window; write to reports/audit on droplet, then cat
    cmd = "cd /root/stock-bot && python3 scripts/trade_visibility_review.py --since-hours 48 --out reports/audit/TRADE_VISIBILITY_REVIEW_droplet.md 2>&1; cat reports/audit/TRADE_VISIBILITY_REVIEW_droplet.md 2>/dev/null || true"
    out, err, rc = c._execute_with_cd(cmd, timeout=60)
    print(out or "")
    if err:
        print(err, file=sys.stderr)
    return 0 if rc == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
