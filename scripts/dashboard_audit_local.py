#!/usr/bin/env python3
"""
Local dashboard audit script for the droplet (runs ON the droplet, not via SSH).
Called by the nightly systemd timer or manually.

Env:
  DASHBOARD_AUDIT_ARCHIVE=1  — archive reports to reports/dashboard_audits/YYYY-MM-DD/
  EXPECTED_GIT_COMMIT        — (optional) set to detect PROCESS_DRIFT

Usage: python3 scripts/dashboard_audit_local.py
"""
from __future__ import annotations

import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REPORTS_DIR = REPO / "reports"
AUDITS_DIR = REPORTS_DIR / "dashboard_audits"

REPORT_NAMES = [
    "DASHBOARD_ENDPOINT_AUDIT.md",
    "DASHBOARD_TELEMETRY_DIAGNOSIS.md",
    "DASHBOARD_PANEL_INVENTORY.md",
]


def main() -> int:
    # Set EXPECTED_GIT_COMMIT from current repo HEAD if not already set
    if not os.getenv("EXPECTED_GIT_COMMIT"):
        import subprocess
        try:
            r = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=REPO,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if r.returncode == 0 and r.stdout:
                os.environ["EXPECTED_GIT_COMMIT"] = r.stdout.strip()
        except Exception:
            pass

    # Run the audit script
    sys.path.insert(0, str(REPO / "scripts"))
    import dashboard_endpoint_audit
    rc = dashboard_endpoint_audit.main()

    # Archive if requested
    archive_mode = os.getenv("DASHBOARD_AUDIT_ARCHIVE", "").strip() in ("1", "true", "yes")
    if archive_mode:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        archive_dir = AUDITS_DIR / today
        archive_dir.mkdir(parents=True, exist_ok=True)

        # Copy reports to archive
        for name in REPORT_NAMES:
            src = REPORTS_DIR / name
            if src.exists():
                shutil.copy2(src, archive_dir / name)
                print(f"[ARCHIVE] {name} -> {archive_dir.relative_to(REPO)}/")

        # Read verdict from audit report
        audit_md = REPORTS_DIR / "DASHBOARD_ENDPOINT_AUDIT.md"
        pass_count = warn_count = fail_count = 0
        running_commit = ""
        if audit_md.exists():
            text = audit_md.read_text(encoding="utf-8")
            for line in text.splitlines():
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 3 and parts[1] in ("PASS", "WARN", "FAIL") and parts[2].isdigit():
                    n = int(parts[2])
                    if parts[1] == "PASS":
                        pass_count = n
                    elif parts[1] == "WARN":
                        warn_count = n
                    else:
                        fail_count = n
                if "Running dashboard commit:" in line:
                    running_commit = line.split(":")[-1].strip().replace("**", "")[:12]

        # Append to index
        index_path = AUDITS_DIR / "index.md"
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        verdict = "PASS" if fail_count == 0 else "FAIL"
        line = f"| {today} | {ts} | {pass_count} | {warn_count} | {fail_count} | {verdict} | {running_commit} |\n"

        # Create index header if missing
        if not index_path.exists():
            header = (
                "# Dashboard Audit Index\n\n"
                "| Date | Timestamp | PASS | WARN | FAIL | Verdict | Commit |\n"
                "|------|-----------|------|------|------|---------|--------|\n"
            )
            index_path.write_text(header, encoding="utf-8")

        with open(index_path, "a", encoding="utf-8") as f:
            f.write(line)
        print(f"[ARCHIVE] Appended verdict to index.md: {verdict}")

    return rc


if __name__ == "__main__":
    sys.exit(main())
