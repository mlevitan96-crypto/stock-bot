#!/usr/bin/env python3
"""
Run Phase 1 audit (services, APIs, Alpaca alignment) on droplet and record results.
Writes reports/audit/PHASE1_DROPLET_RESULTS.md and optionally PHASE1_ALPACA_ALIGNMENT.json.

Usage:
  python scripts/run_phase1_audit_on_droplet.py [--out-dir PATH] [--skip-alpaca]
  With DROPLET_* env or droplet_config.json: runs via DropletClient.
  Without droplet config: prints commands to run manually on droplet.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def run_local() -> tuple[dict, str]:
    """Generate commands and placeholder result when not connected to droplet."""
    commands = [
        ("systemctl is-active stock-bot.service", "Service status"),
        ("systemctl is-active uw-flow-daemon.service", "UW daemon status"),
        ("systemctl show stock-bot.service -p Environment --no-pager 2>/dev/null | tr ' ' '\\n' | grep -E '^[A-Z_]+=' | sed 's/=.*/=***/'", "Env (masked)"),
        ("journalctl -u stock-bot.service --since '1 hour ago' --no-pager 2>/dev/null | tail -50", "Recent logs"),
        ("ls -la state/equity_governance_loop_state.json 2>/dev/null; cat state/equity_governance_loop_state.json 2>/dev/null | head -5", "Governance state"),
    ]
    out = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "local_placeholder",
        "stock_bot_active": None,
        "uw_daemon_active": None,
        "alpaca_alignment": None,
        "commands": [{"cmd": c[0], "description": c[1]} for c in commands],
    }
    md = "# Phase 1 Audit — Droplet Results (placeholder)\n\nRun on droplet via DropletClient or SSH.\n\n"
    md += "## Commands to run on droplet\n\n```bash\n"
    for c, desc in commands:
        md += f"# {desc}\n{c}\n\n"
    md += "```\n"
    return out, md


def run_via_droplet(skip_alpaca: bool) -> tuple[dict, str]:
    """Run Phase 1 checks via DropletClient and capture Alpaca alignment."""
    try:
        from droplet_client import DropletClient
    except ImportError:
        return run_local()

    client = DropletClient()
    project_dir = client.config.get("project_dir", "/root/stock-bot").rstrip("/")
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "droplet",
        "project_dir": project_dir,
        "stock_bot_active": None,
        "uw_daemon_active": None,
        "env_keys_present": [],
        "log_tail": "",
        "alpaca_alignment": None,
    }

    # Service status
    out, _, rc = client._execute("systemctl is-active stock-bot.service 2>/dev/null || echo inactive", timeout=10)
    results["stock_bot_active"] = out.strip() == "active" if out else False
    out2, _, _ = client._execute("systemctl is-active uw-flow-daemon.service 2>/dev/null || echo inactive", timeout=10)
    results["uw_daemon_active"] = out2.strip() == "active" if out2 else False

    # Env (masked)
    out3, _, _ = client._execute(
        "systemctl show stock-bot.service -p Environment --no-pager 2>/dev/null | tr ' ' '\\n' | grep -E '^[A-Z_]+=' | sed 's/=.*/=***/'",
        timeout=10,
    )
    results["env_keys_present"] = [line.split("=")[0] for line in (out3 or "").strip().split("\n") if "=" in line]

    # Log tail
    out4, _, _ = client._execute(
        f"journalctl -u stock-bot.service --since '1 hour ago' --no-pager 2>/dev/null | tail -30",
        timeout=15,
    )
    results["log_tail"] = (out4 or "")[-2000:]

    # Alpaca alignment: positions count, cash, equity (no secrets) via alpaca_alignment_snapshot.py
    if not skip_alpaca:
        try:
            pos_out, _, _ = client._execute_with_cd(
                "python3 scripts/alpaca_alignment_snapshot.py 2>/dev/null || echo '{\"error\":\"snapshot_failed\"}'",
                timeout=20,
            )
            if pos_out and pos_out.strip().startswith("{"):
                results["alpaca_alignment"] = json.loads(pos_out.strip())
            else:
                results["alpaca_alignment"] = {"raw": (pos_out or "")[:500]}
        except Exception as e:
            results["alpaca_alignment"] = {"error": str(e)}

    # Build markdown
    md = "# Phase 1 Audit — Droplet Results\n\n"
    md += f"**Generated:** {results['timestamp']}\n\n"
    md += "## Services\n\n"
    md += f"- **stock-bot.service:** {results['stock_bot_active']}\n"
    md += f"- **uw-flow-daemon.service:** {results['uw_daemon_active']}\n\n"
    md += "## Env keys (masked)\n\n"
    md += ", ".join(results.get("env_keys_present") or []) or "(none captured)\n"
    md += "\n\n## Alpaca alignment\n\n"
    if results.get("alpaca_alignment"):
        md += "```json\n" + json.dumps(results["alpaca_alignment"], indent=2) + "\n```\n\n"
    else:
        md += "(skipped or unavailable)\n\n"
    md += "## Log tail (last 30 lines)\n\n```\n" + (results.get("log_tail") or "(none)") + "\n```\n"
    return results, md


def main() -> int:
    ap = argparse.ArgumentParser(description="Run Phase 1 audit on droplet and record results")
    ap.add_argument("--out-dir", type=Path, default=REPO / "reports" / "audit", help="Output directory")
    ap.add_argument("--skip-alpaca", action="store_true", help="Do not run Alpaca alignment check")
    args = ap.parse_args()
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    has_droplet = bool(os.getenv("DROPLET_HOST") or (REPO / "droplet_config.json").exists())
    if has_droplet:
        try:
            data, md = run_via_droplet(args.skip_alpaca)
        except Exception as e:
            data = {"timestamp": datetime.now(timezone.utc).isoformat(), "error": str(e), "source": "droplet_error"}
            md = f"# Phase 1 Audit — Error\n\n{e}\n"
    else:
        data, md = run_local()

    (out_dir / "PHASE1_DROPLET_RESULTS.md").write_text(md, encoding="utf-8")
    with (out_dir / "PHASE1_DROPLET_RESULTS.json").open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    if data.get("alpaca_alignment"):
        with (out_dir / "PHASE1_ALPACA_ALIGNMENT.json").open("w", encoding="utf-8") as f:
            json.dump(data["alpaca_alignment"], f, indent=2)
    print(f"Wrote {out_dir / 'PHASE1_DROPLET_RESULTS.md'} and .json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
