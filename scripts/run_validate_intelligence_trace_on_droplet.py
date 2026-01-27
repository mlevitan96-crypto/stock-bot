#!/usr/bin/env python3
"""
Run validate_intelligence_trace_dryrun.py on droplet and pull reports.

Uploads script, runs it on droplet (writes to droplet logs/ and reports/),
pulls SAMPLE_INTELLIGENCE_TRACES.md and INTELLIGENCE_TRACE_VERDICT.md to local reports/.

Usage:
  python scripts/run_validate_intelligence_trace_on_droplet.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REMOTE_ROOT = "/root/stock-bot"


def main() -> int:
    sys.path.insert(0, str(REPO))
    from droplet_client import DropletClient

    client = DropletClient()
    try:
        ssh = client._connect()
        sftp = ssh.open_sftp()
    except Exception as e:
        print(f"[FAIL] Cannot connect to droplet: {e}", file=sys.stderr)
        return 1

    local_script = REPO / "scripts" / "validate_intelligence_trace_dryrun.py"
    remote_script = f"{REMOTE_ROOT}/scripts/validate_intelligence_trace_dryrun.py"
    if local_script.exists():
        sftp.put(str(local_script), remote_script)
        print("[OK] Uploaded validate_intelligence_trace_dryrun.py")
    else:
        print(f"[FAIL] Missing {local_script}", file=sys.stderr)
        return 1

    cmd = f"cd {REMOTE_ROOT} && python3 scripts/validate_intelligence_trace_dryrun.py"
    print(f"[RUN] {cmd}")
    out, err, rc = client._execute(cmd, timeout=60)
    if out:
        print(out)
    if err:
        print(err, file=sys.stderr)

    reports_local = REPO / "reports"
    reports_local.mkdir(parents=True, exist_ok=True)
    for name in ["SAMPLE_INTELLIGENCE_TRACES.md", "INTELLIGENCE_TRACE_VERDICT.md", "INTELLIGENCE_TRACE_DROPLET_DEPLOYMENT_PROOF.md"]:
        remote = f"{REMOTE_ROOT}/reports/{name}"
        local = reports_local / name
        try:
            sftp.get(remote, str(local))
            print(f"[OK] Fetched {name}")
        except FileNotFoundError:
            print(f"[WARN] Missing {name}")

    return rc


if __name__ == "__main__":
    sys.exit(main())
