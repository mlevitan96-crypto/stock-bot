#!/usr/bin/env python3
"""
Run Signal Contribution & Monday Surprise Audit on droplet, then fetch artifacts to local.
Execute from repo root. Writes to local reports/audit and reports/board.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
AUDIT = REPO / "reports" / "audit"
BOARD = REPO / "reports" / "board"
DATE = datetime.now(timezone.utc).strftime("%Y-%m-%d")

ARTIFACTS = [
    (AUDIT, f"SIGNAL_REGISTRY_{DATE}.json"),
    (AUDIT, f"SIGNAL_CONTRIBUTION_TABLE_{DATE}.json"),
    (AUDIT, f"SIGNAL_CONTRIBUTION_AUDIT_{DATE}.md"),
    (AUDIT, f"MONDAY_SURPRISE_READINESS_{DATE}.md"),
    (AUDIT, f"CSA_SIGNAL_TRUTH_VERDICT_{DATE}.json"),
    (BOARD, f"INNOVATION_SIGNAL_BLINDSPOTS_{DATE}.md"),
    (BOARD, f"WEEKLY_SIGNAL_TRUTH_PACKET_{DATE}.md"),
]
BLOCKERS_FILE = (AUDIT, f"MONDAY_SURPRISE_BLOCKERS_{DATE}.md")


def main() -> int:
    from droplet_client import DropletClient
    client = DropletClient()
    pd = client.project_dir.replace("~", "/root") if (client.project_dir or "").startswith("~") else client.project_dir

    # Run audit on droplet
    cmd = f"DROPLET_RUN=1 python3 scripts/audit/run_signal_contribution_and_monday_surprise_audit.py"
    out, err, rc = client._execute_with_cd(cmd, timeout=120)
    print(out or "")
    if err:
        print(err, file=sys.stderr)
    if rc != 0:
        print("Audit script exited", rc, file=sys.stderr)
        # Still try to fetch any artifacts written

    # Fetch artifacts (cat from droplet and write local)
    for dir_path, name in ARTIFACTS:
        remote = f"reports/audit/{name}" if "audit" in str(dir_path) else f"reports/board/{name}"
        cat_out, _, _ = client._execute_with_cd(f"cat {remote} 2>/dev/null || true", timeout=10)
        if not (cat_out or "").strip():
            continue
        dir_path.mkdir(parents=True, exist_ok=True)
        out_path = dir_path / name
        if name.endswith(".json"):
            try:
                json.loads(cat_out)
            except json.JSONDecodeError:
                cat_out = cat_out.strip()
            out_path.write_text(cat_out, encoding="utf-8")
        else:
            out_path.write_text(cat_out, encoding="utf-8")
        print("Fetched", out_path)

    # Blockers file (optional)
    block_remote = f"reports/audit/MONDAY_SURPRISE_BLOCKERS_{DATE}.md"
    block_out, _, _ = client._execute_with_cd(f"cat {block_remote} 2>/dev/null || true", timeout=5)
    if (block_out or "").strip():
        AUDIT.mkdir(parents=True, exist_ok=True)
        (AUDIT / f"MONDAY_SURPRISE_BLOCKERS_{DATE}.md").write_text(block_out, encoding="utf-8")
        print("Fetched", AUDIT / f"MONDAY_SURPRISE_BLOCKERS_{DATE}.md")

    return rc


if __name__ == "__main__":
    sys.exit(main())
