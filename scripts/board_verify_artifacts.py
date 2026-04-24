#!/usr/bin/env python3
"""Verify all board review artifacts exist on droplet."""
import sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

def main():
    from droplet_client import DropletClient
    proj = "/root/stock-bot"
    board = proj + "/reports/board"
    artifacts = [
        "30d_comprehensive_review.json",
        "30d_comprehensive_review.md",
        "last387_comprehensive_review.json",
        "last387_comprehensive_review.md",
        "COMPARATIVE_REVIEW_30D_vs_LAST387.json",
        "COMPARATIVE_REVIEW_30D_vs_LAST387.md",
    ]
    c = DropletClient()
    print("=== PHASE 6 — ARTIFACTS ON DROPLET ===")
    all_ok = True
    for f in artifacts:
        out, _, rc = c._execute(f"test -f {board}/{f} && echo OK || echo MISSING")
        status = (out or "").strip()
        if status != "OK":
            all_ok = False
        print(f"  {f}: {status}")
    print("All artifacts present." if all_ok else "Some artifacts missing.")
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
