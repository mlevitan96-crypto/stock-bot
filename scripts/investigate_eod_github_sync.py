#!/usr/bin/env python3
"""
Investigate why EOD report didn't reach GitHub, then run EOD and push.
Run from local: SSH to droplet, detect repo root, check crontab/EOD out/push state, run EOD, push.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

try:
    from droplet_client import DropletClient
except ImportError as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)


def detect_root(c) -> str:
    out, _, _ = c._execute(
        "([ -d /root/stock-bot-current/scripts ] && echo /root/stock-bot-current) || echo /root/stock-bot",
        timeout=5,
    )
    return (out or "").strip() or "/root/stock-bot"


def main() -> int:
    ap = argparse.ArgumentParser(description="Investigate EOD sync on droplet, then run EOD and push")
    ap.add_argument("--date", default=None, help="Date YYYY-MM-DD (default: today UTC)")
    ap.add_argument("--investigate-only", action="store_true", help="Only collect evidence, do not run EOD")
    args = ap.parse_args()
    date_str = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    with DropletClient() as c:
        root = detect_root(c)

        def run(cmd: str, timeout: int = 60):
            return c._execute(f"cd {root} && {cmd}", timeout=timeout)

        print("=== EOD/GitHub sync investigation ===\n")
        print(f"Repo root: {root}")
        print(f"Target date: {date_str}\n")

        # 1) Crontab
        out, _, _ = run("crontab -l 2>/dev/null || echo '(no crontab)'", timeout=5)
        print("--- crontab ---")
        print((out or "").strip() or "(empty)")
        print()

        # 2) EOD out dirs
        out, _, _ = run("ls -la board/eod/out/ 2>/dev/null || echo 'board/eod/out missing'", timeout=5)
        print("--- board/eod/out/ ---")
        print((out or "").strip())
        out2, _, _ = run(f"ls -la board/eod/out/{date_str}/ 2>/dev/null || echo 'date dir missing'", timeout=5)
        print(f"--- board/eod/out/{date_str}/ ---")
        print((out2 or "").strip())
        print()

        # 3) Push failure state
        out, _, _ = run(f"cat state/eod_push_failed_{date_str}.json 2>/dev/null || echo 'no push-failed file'", timeout=5)
        print("--- state/eod_push_failed_*.json ---")
        print((out or "").strip())
        print()

        # 4) Git status and recent log
        run("git fetch origin", timeout=30)
        out, _, _ = run("git status -sb", timeout=5)
        print("--- git status -sb ---")
        print((out or "").strip())
        out, _, _ = run("git log -5 --oneline", timeout=5)
        print("\n--- git log -5 --oneline ---")
        try:
            print((out or "").strip())
        except UnicodeEncodeError:
            print((out or "").encode("ascii", errors="replace").decode("ascii"))
        print()

        if args.investigate_only:
            return 0

        # 5) Pull latest so EOD runs with current code
        print("=== Pulling latest main ===\n")
        run("git fetch origin && git pull --rebase --autostash origin main", timeout=60)

        # 6) Run EOD then push
        print("=== Running EOD and push ===\n")
        eod_cmd = (
            f"cd {root} && CLAWDBOT_SESSION_ID=stock_quant_eod_{date_str} "
            f"python3 board/eod/eod_confirmation.py --date {date_str} --allow-missing-missed-money"
        )
        out, err, rc = c._execute(eod_cmd, timeout=600)
        print(out or "")
        if err:
            print(err, file=sys.stderr)
        if rc != 0:
            print(f"EOD exit code: {rc}", file=sys.stderr)
            return rc

        # 7) If eod_confirmation doesn't push (e.g. push failed), try explicit push
        out, _, _ = run("git status -sb", timeout=5)
        if "ahead" in (out or ""):
            print("Repo ahead of origin; pushing...")
            push_out, push_err, push_rc = run("git push origin main", timeout=60)
            print(push_out or push_err)
            if push_rc != 0:
                return push_rc
        print("\nDone. EOD report for", date_str, "should be on GitHub.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
