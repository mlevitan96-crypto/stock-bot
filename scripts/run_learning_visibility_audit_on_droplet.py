#!/usr/bin/env python3
"""
Run the Learning & Visibility full audit ON THE DROPLET.

All data inspection and conclusions are produced on the droplet. This script
SSHs to the droplet, runs scripts/audit/run_learning_visibility_audit_on_droplet.py
with DROPLET_RUN=1, then prints the board synthesis and (if FAIL) blockers.

Usage: python scripts/run_learning_visibility_audit_on_droplet.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main() -> int:
    try:
        from droplet_client import DropletClient
    except ImportError:
        print("droplet_client not found; run from repo root.", file=sys.stderr)
        return 1

    proj = "/root/stock-bot"
    audit_script = REPO / "scripts" / "audit" / "run_learning_visibility_audit_on_droplet.py"
    if not audit_script.exists():
        print(f"Audit script not found: {audit_script}", file=sys.stderr)
        return 1

    with DropletClient() as c:
        # Ensure repo is up to date (audit script must be present)
        c._execute(f"cd {proj} && git fetch origin && git reset --hard origin/main 2>/dev/null || true", timeout=30)
        # Run audit on droplet with DROPLET_RUN=1
        cmd = f"cd {proj} && DROPLET_RUN=1 python3 scripts/audit/run_learning_visibility_audit_on_droplet.py"
        out, err, rc = c._execute(cmd, timeout=180)
        try:
            print(out)
        except UnicodeEncodeError:
            print(out.encode("ascii", errors="replace").decode("ascii"))
        if err:
            print(err, file=sys.stderr)

        # Fetch board synthesis
        syn_out, _, _ = c._execute(f"cat {proj}/reports/board/LEARNING_AND_VISIBILITY_FULL_AUDIT.md 2>/dev/null || echo 'File not found'", timeout=10)
        print("\n--- BOARD SYNTHESIS ---\n")
        print(syn_out or "(no content)")

        if rc != 0:
            block_out, _, _ = c._execute(f"cat {proj}/reports/audit/LEARNING_VISIBILITY_BLOCKERS.md 2>/dev/null || echo 'No blockers file'", timeout=10)
            if block_out and "Blockers" in block_out:
                print("\n--- BLOCKERS ---\n")
                print(block_out)
            return rc
    return 0


if __name__ == "__main__":
    sys.exit(main())
