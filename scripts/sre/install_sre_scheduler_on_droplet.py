#!/usr/bin/env python3
"""
Install SRE anomaly scan to run every 10 minutes on the droplet.
Uses cron (reliable, survives restarts). Optionally systemd timer if available.
Writes reports/audit/SRE_SCHEDULER_PROOF.md (scheduler type, interval, last run timestamp).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

REMOTE_ROOT = "/root/stock-bot"
# Every 10 min; use venv python; log to logs/sre_anomaly_scan.log
CRON_LINE = "*/10 * * * * cd /root/stock-bot && /root/stock-bot/venv/bin/python scripts/sre/run_sre_anomaly_scan.py --base-dir . >> logs/sre_anomaly_scan.log 2>&1"


def main() -> int:
    audit_dir = REPO / "reports" / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)

    try:
        from droplet_client import DropletClient
    except ImportError:
        (audit_dir / "SRE_IMPLEMENTATION_BLOCKERS.md").write_text(
            "SRE scheduler install: DropletClient not found.\n",
            encoding="utf-8",
        )
        print("DropletClient not found", file=sys.stderr)
        return 1

    with DropletClient() as client:
        # Ensure log dir exists
        client._execute(f"mkdir -p {REMOTE_ROOT}/logs", timeout=5)
        # Remove any existing SRE scan cron line, add current
        out, err, rc = client._execute(
            f"(crontab -l 2>/dev/null | grep -v run_sre_anomaly_scan; echo '{CRON_LINE}') | crontab -",
            timeout=10,
        )
        if rc != 0:
            (audit_dir / "SRE_IMPLEMENTATION_BLOCKERS.md").write_text(
                "SRE scheduler: crontab install failed.\n",
                encoding="utf-8",
            )
            print("Crontab install failed", file=sys.stderr)
            return 1

        # Run one scan now to establish "last run" and SRE_STATUS
        client._execute(
            f"cd {REMOTE_ROOT} && /root/stock-bot/venv/bin/python scripts/sre/run_sre_anomaly_scan.py --base-dir . 2>&1",
            timeout=120,
        )
        # Fetch SRE_STATUS.json for last run timestamp
        content, _, _ = client._execute(f"cat {REMOTE_ROOT}/reports/audit/SRE_STATUS.json 2>/dev/null || true", timeout=5)
        last_run_ts = ""
        if content and content.strip():
            try:
                data = json.loads(content)
                last_run_ts = data.get("scan_ts", "")
            except Exception:
                pass
        if not last_run_ts:
            last_run_ts = datetime.now(timezone.utc).isoformat()

        deployed_commit = ""
        out, _, rc = client._execute(f"cd {REMOTE_ROOT} && git rev-parse HEAD 2>/dev/null || true", timeout=5)
        if rc == 0 and out:
            deployed_commit = out.strip()[:12]

    lines = [
        "# SRE scheduler proof",
        "",
        f"**Generated (UTC):** {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Scheduler type",
        "",
        "cron",
        "",
        "## Interval",
        "",
        "Every 10 minutes",
        "",
        "## Last run timestamp",
        "",
        last_run_ts,
        "",
        "## Deployed commit (at install time)",
        "",
        deployed_commit or "N/A",
        "",
        "## Cron line",
        "",
        "```",
        CRON_LINE,
        "```",
        "",
    ]
    (audit_dir / "SRE_SCHEDULER_PROOF.md").write_text("\n".join(lines), encoding="utf-8")
    print("SRE scheduler installed (cron every 10 min). SRE_SCHEDULER_PROOF.md written.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
