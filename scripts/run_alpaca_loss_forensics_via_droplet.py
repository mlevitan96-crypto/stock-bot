#!/usr/bin/env python3
"""Run alpaca_loss_forensics_droplet.py on the Alpaca droplet via SSH (real data)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def main() -> int:
    from droplet_client import DropletClient

    ap = argparse.ArgumentParser()
    ap.add_argument("--no-pull", action="store_true")
    ap.add_argument("--max-trades", type=int, default=2000)
    ap.add_argument("--min-join-pct", type=float, default=80.0)
    args = ap.parse_args()
    c = DropletClient()
    proj = c.project_dir.replace("~", "/root")
    if not args.no_pull:
        o, e, rc = c._execute_with_cd("git fetch origin && git pull origin main", timeout=120)
        print("git:", (o or e or "")[:500])
    local_script = REPO / "scripts" / "alpaca_loss_forensics_droplet.py"
    remote_script = f"{proj.rstrip('/')}/scripts/alpaca_loss_forensics_droplet.py"
    try:
        c.put_file(str(local_script), remote_script)
        print("Uploaded alpaca_loss_forensics_droplet.py to droplet.")
    except Exception as ex:
        print(f"Upload failed (using droplet copy if present): {ex}")
    cmd = (
        f"cd {proj} && python3 scripts/alpaca_loss_forensics_droplet.py "
        f"--max-trades {args.max_trades} --min-join-pct {args.min_join_pct}"
    )
    out, err, rc = c._execute(cmd, timeout=600)
    print(out or "")
    if err:
        print("stderr:", err[:2000])
    # Fetch key reports to local workspace (optional)
    names = [
        "ALPACA_LOSS_FORENSICS_PROCESS_INVENTORY.md",
        "SRE_REVIEW_ALPACA_RUNTIME_HEALTH.md",
        "ALPACA_LOSS_FORENSICS_DATASET_FREEZE.md",
        "ALPACA_LOSS_FORENSICS_JOIN_COVERAGE.md",
        "ALPACA_LOSS_FORENSICS_AGGREGATE_METRICS.md",
        "ALPACA_LOSS_FORENSICS_DAY_BY_DAY.md",
        "ALPACA_LOSS_FORENSICS_LONG_SHORT.md",
        "ALPACA_LOSS_FORENSICS_ENTRY_CAUSES.md",
        "ALPACA_LOSS_FORENSICS_EXIT_CAUSES.md",
        "ALPACA_LOSS_FORENSICS_BLOCKED_COUNTERFACTUAL.md",
        "ALPACA_LOSS_FORENSICS_MARKET_CONTEXT.md",
        "CSA_REVIEW_ALPACA_LOSS_FORENSICS.md",
        "SRE_REVIEW_ALPACA_LOSS_FORENSICS.md",
        "ALPACA_LOSS_FORENSICS_BOARD_PACKET.md",
        "ALPACA_LOSS_FORENSICS_ACTION_BACKLOG.md",
    ]
    names.append("ALPACA_LOSS_FORENSICS_JOIN_BLOCKER_LATEST.md")
    for name in names:
        try:
            c.get_file(f"reports/audit/{name}", REPO / "reports" / "audit" / name)
        except Exception as ex:
            print(f"fetch {name}: {ex}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
