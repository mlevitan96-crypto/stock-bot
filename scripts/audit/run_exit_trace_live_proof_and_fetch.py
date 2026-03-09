#!/usr/bin/env python3
"""
Run Exit Trace LIVE PROOF on droplet, then fetch the three artifacts to local.
Execute from repo root. Uses DropletClient; timeout allows 130s wait for sampling.
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
    # Run proof on droplet (long timeout: 130s wait + run)
    cmd = "python3 scripts/audit/run_exit_trace_live_proof_on_droplet.py"
    out, err, rc = client._execute_with_cd(cmd, timeout=180)
    print(out or "")
    if err:
        print(err, file=sys.stderr)
    # Parse script output for artifact names (PROOF written: X.md etc.)
    names = []
    for line in (out or "").splitlines():
        line = line.strip()
        if "PROOF written:" in line:
            names.append(line.split("PROOF written:")[-1].strip())
        elif "SAMPLE written:" in line:
            names.append(line.split("SAMPLE written:")[-1].strip())
        elif "VERDICT written:" in line:
            names.append(line.split("VERDICT written:")[-1].strip())
    fetched = []
    for remote in names:
        if not remote or remote in ("PROOF_MD", "SAMPLE_JSON", "VERDICT_JSON"):
            continue
        cat_out, _, _ = client._execute_with_cd(f"cat reports/audit/{remote} 2>/dev/null || true", timeout=10)
        if not (cat_out or "").strip():
            continue
        local_path = AUDIT / remote
        local_path.parent.mkdir(parents=True, exist_ok=True)
        if remote.endswith(".json"):
            try:
                json.loads(cat_out)
            except json.JSONDecodeError:
                cat_out = cat_out.strip()
            local_path.write_text(cat_out, encoding="utf-8")
        else:
            local_path.write_text(cat_out, encoding="utf-8")
        fetched.append(str(local_path))
        print("Fetched", local_path)
    if not fetched:
        # Fallback: most recent by mtime
        list_out, _, _ = client._execute_with_cd(
            "ls -t reports/audit/EXIT_TRACE_LIVE_PROOF_*.md reports/audit/EXIT_TRACE_SAMPLE_*.json reports/audit/CSA_EXIT_TRACE_VERDICT_*.json 2>/dev/null | head -3",
            timeout=10,
        )
        for line in (list_out or "").strip().splitlines():
            remote = line.strip().split("/")[-1] if "/" in line else line.strip()
            if not remote:
                continue
            cat_out, _, _ = client._execute_with_cd(f"cat reports/audit/{remote} 2>/dev/null || true", timeout=10)
            if (cat_out or "").strip():
                local_path = AUDIT / remote
                local_path.parent.mkdir(parents=True, exist_ok=True)
                if remote.endswith(".json"):
                    local_path.write_text(cat_out, encoding="utf-8")
                else:
                    local_path.write_text(cat_out, encoding="utf-8")
                fetched.append(str(local_path))
                print("Fetched", local_path)
    return rc


if __name__ == "__main__":
    sys.exit(main())
