#!/usr/bin/env python3
"""Upload post-close deep dive + Telegram detect; install systemd; dry-run + enable timer."""
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FILES = [
    "scripts/alpaca_telegram_env_detect.py",
    "scripts/alpaca_postclose_deepdive.py",
    "deploy/systemd/alpaca-postclose-deepdive.service",
    "deploy/systemd/alpaca-postclose-deepdive.timer",
]


def main() -> int:
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
            c._execute(f"mkdir -p '{remote_root}/{'/'.join(rel.split('/')[:-1])}'", timeout=15)
            c.put_file(str(lp), rr)
            print("uploaded", rel)

        svc_local = f"{remote_root}/deploy/systemd/alpaca-postclose-deepdive.service"
        timer_local = f"{remote_root}/deploy/systemd/alpaca-postclose-deepdive.timer"

        install = f"""
set -e
cp -f '{svc_local}' /etc/systemd/system/alpaca-postclose-deepdive.service
cp -f '{timer_local}' /etc/systemd/system/alpaca-postclose-deepdive.timer
systemctl daemon-reload
systemctl enable alpaca-postclose-deepdive.timer
systemctl start alpaca-postclose-deepdive.timer
"""
        out, err, rc = c._execute(install, timeout=120)
        print((out or "") + (err or ""))
        if rc != 0:
            print("systemctl install exit:", rc, file=sys.stderr)
            return rc

        out2, err2, rc2 = c._execute(
            f"cd {remote_root} && TRADING_BOT_ROOT={remote_root} "
            f"{remote_root}/venv/bin/python3 scripts/alpaca_postclose_deepdive.py --dry-run --force",
            timeout=300,
        )
        print((out2 or "") + (err2 or ""))
        print("manual dry-run exit:", rc2)

        out3, err3, rc3 = c._execute(
            "systemctl list-timers alpaca-postclose-deepdive.timer --no-pager 2>&1; "
            "journalctl -u alpaca-postclose-deepdive.service -n 30 --no-pager 2>&1",
            timeout=60,
        )
        print((out3 or "") + (err3 or ""))

        print("\n=== PHASE 5 SUMMARY ===")
        out4, _, _ = c._execute(
            f"cd {remote_root} && TRADING_BOT_ROOT={remote_root} "
            f"{remote_root}/venv/bin/python3 scripts/alpaca_telegram_env_detect.py 2>&1",
            timeout=30,
        )
        print("Telegram env source (label):", (out4 or "").strip())
        print("systemd units: /etc/systemd/system/alpaca-postclose-deepdive.service|.timer")
        print("Timer: OnCalendar Mon..Fri 16:30 America/New_York (see unit)")
        print(
            "Manual run:",
            f"cd {remote_root} && TRADING_BOT_ROOT={remote_root} "
            f"./venv/bin/python3 scripts/alpaca_postclose_deepdive.py [--dry-run] [--force]",
        )
        print("Reports: /root/stock-bot/reports/ALPACA_POSTCLOSE_*.md")
        print("LIVE AND ARMED FOR TOMORROW (timer enabled; no trading changes)")
        return rc2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
