#!/usr/bin/env python3
"""
Run Exit Trace Write-Health PROOF on droplet, then fetch proof + verdict to local.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
AUDIT = REPO / "reports" / "audit"


def main() -> int:
    try:
        from droplet_client import DropletClient
    except ImportError as e:
        print(f"DropletClient not available: {e}", file=sys.stderr)
        return 1
    client = DropletClient()
    cmd = "python3 scripts/audit/run_exit_trace_write_proof_on_droplet.py"
    out, err, rc = client._execute_with_cd(cmd, timeout=180)
    print(out or "")
    if err:
        print(err, file=sys.stderr)
    names = []
    for line in (out or "").splitlines():
        line = line.strip()
        if "PROOF written:" in line:
            names.append(line.split("PROOF written:")[-1].strip())
        elif "VERDICT written:" in line:
            names.append(line.split("VERDICT written:")[-1].strip())
    # Fallback: if stdout wasn't captured, discover latest proof and verdict on droplet
    if not names:
        proof_out, _, _ = client._execute_with_cd(
            "ls reports/audit/EXIT_TRACE_WRITE_PROOF_*.md 2>/dev/null | tail -1",
            timeout=10,
        )
        verdict_out, _, _ = client._execute_with_cd(
            "ls reports/audit/CSA_EXIT_TRACE_WRITE_VERDICT_*.json 2>/dev/null | tail -1",
            timeout=10,
        )
        for raw in (proof_out, verdict_out):
            line = (raw or "").strip().splitlines()[-1].strip() if raw else ""
            if line:
                names.append(Path(line).name)
    for remote in names:
        if not remote:
            continue
        cat_out, _, _ = client._execute_with_cd(f"cat reports/audit/{remote} 2>/dev/null || true", timeout=10)
        if not (cat_out or "").strip():
            continue
        local_path = AUDIT / remote
        local_path.parent.mkdir(parents=True, exist_ok=True)
        if remote.endswith(".json"):
            local_path.write_text(cat_out, encoding="utf-8")
        else:
            local_path.write_text(cat_out, encoding="utf-8")
        print("Fetched", local_path)
    return rc


if __name__ == "__main__":
    sys.exit(main())
