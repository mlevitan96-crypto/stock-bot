#!/usr/bin/env python3
"""
Install weekday 09:00 America/New_York cron for ``scripts/run_uw_regime_matrix_refresh.py`` on the droplet.

Uses ``DropletClient`` (``droplet_config.json`` / ``DROPLET_HOST``). Idempotent: skips if
``run_uw_regime_matrix_refresh.py`` already appears in root's crontab.

Schedule: **Mon–Fri 09:00 Eastern** (``CRON_TZ=America/New_York``), pre-market buffer before RTH.

Usage (from dev machine with SSH to droplet configured):

  python scripts/install_uw_regime_cron_on_droplet.py

Optional env:

  UW_REGIME_CRON_HOUR=9   # default 9
  UW_REGIME_CRON_MIN=0    # default 0
"""
from __future__ import annotations

import base64
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

MARKER = "run_uw_regime_matrix_refresh.py"


def _cron_block(proj: str) -> str:
    hour = int(os.environ.get("UW_REGIME_CRON_HOUR", "9") or "9")
    minute = int(os.environ.get("UW_REGIME_CRON_MIN", "0") or "0")
    hour = max(0, min(23, hour))
    minute = max(0, min(59, minute))
    py = f"{proj}/venv/bin/python3"
    log = f"{proj}/logs/uw_regime_cron.log"
    line = (
        f"{minute} {hour} * * 1-5 cd {proj} && {py} scripts/run_uw_regime_matrix_refresh.py "
        f">> {log} 2>&1"
    )
    return (
        f"# stock-bot: UW regime matrix snapshot (Mon–Fri {hour:02d}:{minute:02d} America/New_York)\n"
        f"CRON_TZ=America/New_York\n"
        f"{line}\n"
    )


def main() -> int:
    try:
        from droplet_client import DropletClient
    except ImportError:
        print("droplet_client not found (run from repo root).", file=sys.stderr)
        return 1

    with DropletClient() as c:
        proj = str(c.project_dir or "~/stock-bot").replace("~", "/root")
        out0, err0, rc0 = c._execute(f"test -f {proj}/scripts/run_uw_regime_matrix_refresh.py && echo OK || echo MISSING", timeout=10)
        if "OK" not in (out0 or ""):
            print(
                "ERROR: run_uw_regime_matrix_refresh.py not on droplet. git pull main first.",
                file=sys.stderr,
            )
            return 1

        c._execute(f"mkdir -p {proj}/logs", timeout=10)

        out, _, _ = c._execute("crontab -l 2>/dev/null || true", timeout=10)
        existing = out or ""
        if MARKER in existing:
            print("UW regime matrix cron already present; no change.")
            out2, _, _ = c._execute("crontab -l 2>/dev/null | grep -F run_uw_regime_matrix_refresh || true", timeout=10)
            print((out2 or "").strip() or "(grep empty)")
            return 0

        block = _cron_block(proj)
        new_crontab = existing.rstrip() + "\n\n" + block
        b64 = base64.b64encode(new_crontab.encode("utf-8")).decode("ascii")
        cmd = (
            "python3 -c \"import base64,sys; "
            f"open('/tmp/uw_regime_cron.txt','wb').write(base64.b64decode('{b64}')); sys.exit(0)\" "
            "&& crontab /tmp/uw_regime_cron.txt && rm -f /tmp/uw_regime_cron.txt"
        )
        out2, err2, rc = c._execute(cmd, timeout=15)
        if rc != 0:
            print("Failed to install crontab:", out2, err2, file=sys.stderr)
            return 1

        print("Installed UW regime matrix weekday cron (America/New_York).")
        out3, _, _ = c._execute("crontab -l 2>/dev/null | grep -F run_uw_regime_matrix_refresh || true", timeout=10)
        print("Verification (grep):")
        print((out3 or "").strip() or "(empty — check crontab -l)")
        if MARKER not in (out3 or ""):
            print("WARNING: grep verification did not find marker.", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
