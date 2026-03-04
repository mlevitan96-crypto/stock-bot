#!/usr/bin/env python3
"""Capture deployed_commit and health verification from droplet via DropletClient, write deployment_proof_data.json and DEPLOYMENT_PROOF.md."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main() -> int:
    try:
        from droplet_client import DropletClient
    except ImportError:
        print("DropletClient not found", file=sys.stderr)
        return 1
    audit_dir = REPO / "reports" / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    data = {
        "deployed_commit": "",
        "droplet_host": "alpaca",
        "deploy_completed_at": now,
        "telemetry_health_verified_at": "",
        "learning_readiness_verified_at": "",
    }
    with DropletClient() as c:
        out, _, rc = c._execute_with_cd("git rev-parse HEAD 2>/dev/null || true", timeout=10)
        if rc == 0 and out:
            data["deployed_commit"] = out.strip()[:12]
        code_out, _, _ = c._execute(
            "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5000/api/telemetry_health 2>/dev/null || echo 000",
            timeout=10,
        )
        if (code_out or "").strip() == "200":
            data["telemetry_health_verified_at"] = now
        code_out2, _, _ = c._execute(
            "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5000/api/learning_readiness 2>/dev/null || echo 000",
            timeout=10,
        )
        if (code_out2 or "").strip() == "200":
            data["learning_readiness_verified_at"] = now
    json_path = audit_dir / "deployment_proof_data.json"
    json_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    # Runtime context for deploy (deployed_commit, deploy_ts)
    ctx_path = audit_dir / "deploy_runtime_context_data.json"
    ctx_path.write_text(
        json.dumps({"deployed_commit": data["deployed_commit"], "deploy_ts": now}, indent=2),
        encoding="utf-8",
    )
    import subprocess
    r = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "audit" / "write_deployment_proof.py"), str(REPO)],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        print(r.stderr or r.stdout, file=sys.stderr)
    r2 = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "audit" / "write_deploy_runtime_context.py"), str(REPO)],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    if r2.returncode != 0:
        print(r2.stderr or r2.stdout, file=sys.stderr)
        return r2.returncode
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
