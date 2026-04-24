#!/usr/bin/env python3
"""Upload offline full data-path audit; run on Alpaca droplet (Linux only)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FILES = ["scripts/alpaca_offline_full_data_audit.py"]


def main() -> int:
    ap_argv = [a for a in sys.argv[1:] if a]
    sys.path.insert(0, str(REPO))
    from droplet_client import DropletClient

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
            c._execute(f"mkdir -p '{remote_root}/{'/'.join(rel.split('/')[:-1])}'", timeout=10)
            c.put_file(str(lp), rr)
            print("uploaded", rel)
        extra = " ".join(ap_argv)
        cmd = (
            f"cd {remote_root} && set -a && [ -f .env ] && . ./.env; set +a && "
            f"TRADING_BOT_ROOT={remote_root} {remote_root}/venv/bin/python3 "
            f"scripts/alpaca_offline_full_data_audit.py {extra}"
        )
        out, err, rc = c._execute(cmd, timeout=120)
        combined = (out or "") + (err or "")
        print(combined[-150000:] if len(combined) > 150000 else combined)
        if not combined.strip():
            print(
                "(no remote stdout/stderr — pull reports/ALPACA_OFFLINE_FULL_DATA_AUDIT_*.md from droplet)",
                file=sys.stderr,
            )
        print("exit:", rc)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
