#!/usr/bin/env python3
"""Write reports/audit/DEPLOYMENT_PROOF.md from deployed_commit, droplet host, verification timestamps."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

def main() -> int:
    base = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    proof_path = base / "reports" / "audit" / "DEPLOYMENT_PROOF.md"
    # Optional: read from a JSON written by caller
    data_path = base / "reports" / "audit" / "deployment_proof_data.json"
    if data_path.exists():
        try:
            data = json.loads(data_path.read_text(encoding="utf-8"))
        except Exception:
            data = {}
    else:
        data = {}
    deployed_commit = data.get("deployed_commit", "")
    droplet_host = data.get("droplet_host", "alpaca")
    telemetry_health_ts = data.get("telemetry_health_verified_at", "")
    learning_readiness_ts = data.get("learning_readiness_verified_at", "")
    deploy_ts = data.get("deploy_completed_at", datetime.now(timezone.utc).isoformat())
    proof_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Deployment proof",
        "",
        f"**Generated (UTC):** {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Deployed commit",
        "",
        deployed_commit or "(not captured)",
        "",
        "## Droplet host",
        "",
        droplet_host,
        "",
        "## Verification timestamps",
        "",
        f"- **Deploy completed:** {deploy_ts}",
        f"- **/api/telemetry_health verified:** {telemetry_health_ts or 'N/A'}",
        f"- **/api/learning_readiness verified:** {learning_readiness_ts or 'N/A'}",
        "",
    ]
    proof_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {proof_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
