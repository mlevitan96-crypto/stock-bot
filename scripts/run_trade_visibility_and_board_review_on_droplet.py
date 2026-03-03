#!/usr/bin/env python3
"""
Run on droplet: (1) trade visibility review (48h), (2) board persona review.
Fetch both reports to local reports/audit and reports/governance.

Usage: python scripts/run_trade_visibility_and_board_review_on_droplet.py
"""
from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main() -> int:
    try:
        from droplet_client import DropletClient
    except ImportError:
        print("droplet_client not found; run from repo root", file=sys.stderr)
        return 1

    proj = "/root/stock-bot"
    with DropletClient() as c:
        # 1) Trade visibility (48h)
        print("Running trade visibility review (48h) on droplet...", file=sys.stderr)
        cmd1 = f"cd {proj} && python3 scripts/trade_visibility_review.py --since-hours 48 --out reports/audit/TRADE_VISIBILITY_REVIEW_droplet.md 2>&1"
        out1, err1, rc1 = c._execute(cmd1, timeout=60)
        print(out1 or "")
        if err1:
            print(err1, file=sys.stderr)
        if rc1 != 0:
            print("Trade visibility script exited with", rc1, file=sys.stderr)

        # 2) Board persona review
        print("\nRunning board persona review on droplet...", file=sys.stderr)
        cmd2 = f"cd {proj} && python3 scripts/governance/run_board_persona_review.py --base-dir . --out-dir reports/governance 2>&1"
        out2, err2, rc2 = c._execute(cmd2, timeout=90)
        print(out2 or "")
        if err2:
            print(err2, file=sys.stderr)
        if rc2 != 0:
            print("Board persona review exited with", rc2, file=sys.stderr)

        # 3) Fetch reports to local
        (REPO / "reports" / "audit").mkdir(parents=True, exist_ok=True)
        (REPO / "reports" / "governance").mkdir(parents=True, exist_ok=True)

        # Trade visibility report
        try:
            content, _, _ = c._execute(f"cat {proj}/reports/audit/TRADE_VISIBILITY_REVIEW_droplet.md 2>/dev/null || true", timeout=10)
            if content and content.strip():
                dest = REPO / "reports" / "audit" / "TRADE_VISIBILITY_REVIEW_droplet.md"
                dest.write_text(content, encoding="utf-8")
                print(f"\nFetched trade visibility -> {dest}", file=sys.stderr)
        except Exception as e:
            print(f"Could not fetch trade visibility report: {e}", file=sys.stderr)

        # Board review latest
        for name in ["board_review_latest.md", "board_review_latest.json"]:
            try:
                content, _, _ = c._execute(f"cat {proj}/reports/governance/{name} 2>/dev/null || true", timeout=10)
                if content and content.strip():
                    dest = REPO / "reports" / "governance" / name
                    dest.write_text(content, encoding="utf-8")
                    print(f"Fetched {name} -> {dest}", file=sys.stderr)
            except Exception as e:
                print(f"Could not fetch {name}: {e}", file=sys.stderr)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    print(f"\nDone at {ts} UTC. Data and board output in reports/audit/ and reports/governance/.", file=sys.stderr)
    return 0 if (rc1 == 0 and rc2 == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
