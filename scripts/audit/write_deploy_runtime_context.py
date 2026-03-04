#!/usr/bin/env python3
"""
Write reports/audit/DEPLOY_RUNTIME_CONTEXT.md on every deploy.
Records: ssh_alias_used (must be alpaca), resolved_host, project_dir, deployed_commit, deploy_ts.
Call after deploy; assert ssh_alias_used == alpaca or exit non-zero and write ETHOS_VIOLATION.md.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[2]
REQUIRED_SSH_ALIAS = "alpaca"


def main() -> int:
    base = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO
    audit_dir = base / "reports" / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)

    # Read droplet_config.json for alias and project_dir (before any overwrite)
    config_path = base / "droplet_config.json"
    ssh_alias_used = ""
    project_dir = "/root/stock-bot"
    if config_path.exists():
        try:
            cfg = json.loads(config_path.read_text(encoding="utf-8"))
            ssh_alias_used = (cfg.get("host") or "").strip()
            project_dir = (cfg.get("project_dir") or project_dir).strip()
        except Exception:
            pass

    if ssh_alias_used != REQUIRED_SSH_ALIAS:
        violation_path = audit_dir / "ETHOS_VIOLATION.md"
        violation_path.write_text(
            f"# Ethos violation\n\n"
            f"Deployment MUST use SSH alias `{REQUIRED_SSH_ALIAS}`. "
            f"droplet_config.json has `host`: {ssh_alias_used!r}. "
            f"Update to `\"host\": \"{REQUIRED_SSH_ALIAS}\"` and re-run deploy.\n",
            encoding="utf-8",
        )
        print(f"ETHOS_VIOLATION: ssh alias must be {REQUIRED_SSH_ALIAS}, got {ssh_alias_used!r}", file=sys.stderr)
        return 1

    # Resolved host from ssh -G alpaca
    resolved_host = ""
    try:
        r = subprocess.run(
            ["ssh", "-G", REQUIRED_SSH_ALIAS],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=base,
        )
        if r.returncode == 0:
            for line in (r.stdout or "").splitlines():
                line = line.strip()
                if line.startswith("hostname "):
                    resolved_host = line.split(" ", 1)[1].strip()
                    break
    except Exception:
        pass

    # deployed_commit and deploy_ts: pass via JSON file written by caller, or use placeholders
    data_path = audit_dir / "deploy_runtime_context_data.json"
    deployed_commit = ""
    deploy_ts = datetime.now(timezone.utc).isoformat()
    if data_path.exists():
        try:
            data = json.loads(data_path.read_text(encoding="utf-8"))
            deployed_commit = data.get("deployed_commit", "")
            deploy_ts = data.get("deploy_ts", deploy_ts)
        except Exception:
            pass

    out_path = audit_dir / "DEPLOY_RUNTIME_CONTEXT.md"
    out_path.write_text(
        "# Deploy runtime context\n\n"
        f"**Generated (UTC):** {deploy_ts}\n\n"
        "## SSH alias used\n\n"
        f"{ssh_alias_used}\n\n"
        "## Resolved host\n\n"
        f"{resolved_host or '(could not resolve)'}\n\n"
        "## Project dir\n\n"
        f"{project_dir}\n\n"
        "## Deployed commit\n\n"
        f"{deployed_commit or '(not captured)'}\n\n"
        "## Deploy timestamp\n\n"
        f"{deploy_ts}\n",
        encoding="utf-8",
    )
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
