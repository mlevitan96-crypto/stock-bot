#!/usr/bin/env python3
"""Append adverse review proof to MONDAY_OPEN_READINESS_PROOF (heartbeat, cockpit mtime). Run locally, SSHs to droplet."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from droplet_client import DropletClient

def main():
    c = DropletClient()
    proof = Path(__file__).resolve().parents[2] / "reports" / "audit" / "MONDAY_OPEN_READINESS_PROOF_2026-03-08_2155"
    if not proof.exists():
        proof = Path(__file__).resolve().parents[2] / "reports" / "audit"
        proof.mkdir(parents=True, exist_ok=True)
        proof = proof / "adverse_review_latest"
        proof.mkdir(exist_ok=True)
    cmd = (
        "ls -la state/heartbeats 2>/dev/null | head -5; echo '---'; "
        "tail -3 logs/trading.log 2>/dev/null || true; echo '---'; "
        "stat -c '%y' reports/board/PROFITABILITY_COCKPIT.md 2>/dev/null || true"
    )
    out, err, _ = c._execute_with_cd(cmd, timeout=10)
    (proof / "adverse_review_heartbeat_cockpit.txt").write_text((out or "") + (err or ""), encoding="utf-8")
    print("Adverse review proof written to", proof / "adverse_review_heartbeat_cockpit.txt")
    return 0

if __name__ == "__main__":
    sys.exit(main())
