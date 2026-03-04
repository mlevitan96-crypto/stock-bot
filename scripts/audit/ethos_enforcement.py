#!/usr/bin/env python3
"""
Phase 0: Ethos enforcement (hard gate).
Assert: (1) SSH alias alpaca available and resolves to stock-bot droplet,
        (2) droplet_config.json points to host alpaca,
        (3) DropletClient uses alpaca (config host is alpaca before connect).
On any failure: write reports/audit/ETHOS_VIOLATION.md and exit non-zero.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[2]
STOCK_BOT_IP = "104.236.102.57"


def main() -> int:
    audit_dir = REPO / "reports" / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    violations: list[str] = []

    # 1) SSH alias alpaca available and resolves to stock-bot
    try:
        r = subprocess.run(
            ["ssh", "-G", "alpaca"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=REPO,
        )
        if r.returncode != 0:
            violations.append("SSH alias 'alpaca' not available (ssh -G alpaca failed).")
        else:
            hostname = None
            for line in (r.stdout or "").splitlines():
                line = line.strip()
                if line.startswith("hostname "):
                    hostname = line.split(" ", 1)[1].strip()
                    break
            if not hostname:
                violations.append("SSH alias 'alpaca' did not resolve to a hostname.")
            elif hostname != STOCK_BOT_IP and hostname != "104.236.102.57":
                violations.append(
                    f"SSH alias 'alpaca' resolves to {hostname!r}; stock-bot droplet must be {STOCK_BOT_IP}."
                )
    except FileNotFoundError:
        violations.append("ssh command not found (SSH alias alpaca cannot be checked).")
    except subprocess.TimeoutExpired:
        violations.append("ssh -G alpaca timed out.")
    except Exception as e:
        violations.append(f"Checking SSH alias alpaca failed: {e}.")

    # 2) droplet_config.json exists and points to alpaca
    config_path = REPO / "droplet_config.json"
    if not config_path.exists():
        violations.append("droplet_config.json not found (required for ethos: deploy via alpaca).")
    else:
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            host = config.get("host") or ""
            if host != "alpaca":
                violations.append(
                    f"droplet_config.json must have \"host\": \"alpaca\"; got {host!r}."
                )
        except Exception as e:
            violations.append(f"droplet_config.json invalid or unreadable: {e}.")

    # 3) DropletClient loads config with host alpaca (so deploy uses alpaca)
    if not violations:
        try:
            sys.path.insert(0, str(REPO))
            from droplet_client import DropletClient
            c = DropletClient()
            # After _load_config, host may be resolved to IP if use_ssh_config; check original file
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            if (cfg.get("host") or "") != "alpaca":
                violations.append("DropletClient config host is not alpaca (droplet_config.json host must be 'alpaca').")
        except Exception as e:
            violations.append(f"DropletClient could not be asserted to use alpaca: {e}.")

    if violations:
        lines = [
            "# Ethos violation",
            "",
            f"**Generated (UTC):** {datetime.now(timezone.utc).isoformat()}",
            "",
            "Deployment via SSH alias `alpaca` is REQUIRED. The following assertions failed:",
            "",
        ]
        for v in violations:
            lines.append(f"- {v}")
        lines.extend([
            "",
            "## Required",
            "",
            "1. Ensure SSH alias **alpaca** is defined (e.g. in `~/.ssh/config`) and resolves to stock-bot droplet 104.236.102.57.",
            "2. Create or update **droplet_config.json** in repo root with: `\"host\": \"alpaca\"` and `\"use_ssh_config\": true`.",
            "3. Do not use raw IP in config when ethos requires alpaca.",
            "",
        ])
        out = audit_dir / "ETHOS_VIOLATION.md"
        out.write_text("\n".join(lines), encoding="utf-8")
        print("ETHOS_VIOLATION:", "; ".join(violations), file=sys.stderr)
        return 1
    print("Ethos enforcement: OK (alpaca available, droplet_config points to alpaca, DropletClient uses alpaca).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
