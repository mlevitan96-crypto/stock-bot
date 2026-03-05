#!/usr/bin/env python3
"""Trigger deploy to droplet per MEMORY_BANK: git pull on droplet + restart service. SSH alias MUST be alpaca."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from droplet_client import DropletClient

def main():
    # Ethos: assert ssh alias is alpaca before deploy
    config_path = Path(__file__).resolve().parent.parent / "droplet_config.json"
    if config_path.exists():
        try:
            cfg = json.loads(config_path.read_text(encoding="utf-8"))
            if (cfg.get("host") or "").strip() != "alpaca":
                audit = Path(__file__).resolve().parent.parent / "reports" / "audit"
                audit.mkdir(parents=True, exist_ok=True)
                (audit / "ETHOS_VIOLATION.md").write_text(
                    "Deployment MUST use SSH alias alpaca. droplet_config.json host is not alpaca.\n",
                    encoding="utf-8",
                )
                print("ETHOS_VIOLATION: droplet_config.json host must be alpaca", file=sys.stderr)
                return 1
        except Exception as e:
            print(f"Config check failed: {e}", file=sys.stderr)
            return 1
    else:
        print("droplet_config.json not found", file=sys.stderr)
        return 1
    c = DropletClient()
    r = c.deploy()
    ok = r.get("success", False)
    for s in r.get("steps", []):
        name = s.get("name", "")
        res = s.get("result", {})
        step_ok = res.get("success", res.get("exit_code", 1) == 0)
        status = "OK" if step_ok else "FAIL"
        print(f"  {name}: {status}")
    if not ok:
        print("Error:", r.get("error", "deploy failed"))
        return 1
    # Write DEPLOYMENT_PROOF.md and DEPLOY_RUNTIME_CONTEXT.md
    import subprocess
    repo = Path(__file__).resolve().parent.parent
    rc = subprocess.call(
        [sys.executable, str(Path(__file__).resolve().parent / "audit" / "capture_deployment_proof.py")],
        cwd=repo,
    )
    if rc != 0:
        print("Warning: capture_deployment_proof exited", rc, file=sys.stderr)
    # CSA deploy audit: run CSA after deploy for every mission
    from datetime import datetime, timezone
    mission_id = "deploy_audit_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
    rc_csa = subprocess.call(
        [
            sys.executable,
            str(repo / "scripts" / "audit" / "run_chief_strategy_auditor.py"),
            "--mission-id", mission_id,
            "--context-json", str(repo / "reports" / "audit" / "deploy_runtime_context_data.json"),
            "--base-dir", str(repo),
        ],
        cwd=repo,
    )
    if rc_csa != 0:
        print("Warning: CSA deploy audit exited", rc_csa, file=sys.stderr)
    print("Deploy complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
