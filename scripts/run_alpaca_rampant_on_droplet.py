#!/usr/bin/env python3
"""Upload rampant analysis script; run on Alpaca droplet (writes reports/ only)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FILES = ["scripts/alpaca_rampant_analysis_mission.py"]


def main() -> int:
    sys.path.insert(0, str(REPO))
    from droplet_client import DropletClient

    tag = os.environ.get("ALPACA_REPORT_TAG", "").strip()
    if not tag:
        from datetime import datetime, timezone

        tag = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
    env_prefix = f"export ALPACA_REPORT_TAG={tag} && "

    with DropletClient() as c:
        proj = c.project_dir.replace("~", "/root").rstrip("/")
        forced = os.environ.get("DROPLET_TRADING_ROOT", "").strip()
        remote_root = forced.rstrip("/") if forced else proj
        for rel in FILES:
            lp = REPO / rel
            if not lp.is_file():
                print("missing", rel, file=sys.stderr)
                return 2
            rr = f"{remote_root}/{rel}".replace("\\", "/")
            c._execute(f"mkdir -p '{remote_root}/scripts'", timeout=10)
            c.put_file(str(lp), rr)
            print("uploaded", rel)

        base = (
            f"cd {remote_root} && set -a && [ -f .env ] && . ./.env; set +a && "
            f"TRADING_BOT_ROOT={remote_root} {env_prefix}"
        )
        out, err, rc = c._execute(
            base + f"{remote_root}/venv/bin/python3 scripts/alpaca_rampant_analysis_mission.py",
            timeout=300,
        )
        combined = (out or "") + (err or "")
        print(combined[-120000:] if len(combined) > 120000 else combined)
        print("rampant exit:", rc)
        return rc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
