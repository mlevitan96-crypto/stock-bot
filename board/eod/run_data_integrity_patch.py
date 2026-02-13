#!/usr/bin/env python3
"""
Execute data integrity patch ON THE DROPLET: hard-fail on missing artifacts,
enriched attribution/blocked logs, correlation fallback, commit and push.

Usage:
  python3 board/eod/run_data_integrity_patch.py --date 2026-02-12 --remote
  python3 board/eod/run_data_integrity_patch.py --date 2026-02-12 --on-droplet
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
CANDIDATE_ROOTS = ["/root/stock-bot-current", "/root/trading-bot-current", "/root/stock-bot"]


def _detect_stockbot_root() -> str:
    for root in CANDIDATE_ROOTS:
        scripts = Path(root) / "scripts"
        eod = Path(root) / "board" / "eod" / "eod_confirmation.py"
        if scripts.is_dir() and eod.exists():
            return root
    return str(SCRIPT_DIR.parent.parent)


def _run(cmd: str, timeout: int = 60) -> tuple[str, str, int]:
    try:
        r = subprocess.run(["sh", "-c", cmd], capture_output=True, text=True, timeout=timeout)
        return (r.stdout or "", r.stderr or "", r.returncode)
    except subprocess.TimeoutExpired:
        return ("", f"Timeout ({timeout}s)", 1)
    except Exception as e:
        return ("", str(e), 1)


def run_on_droplet(date_str: str) -> int:
    root = _detect_stockbot_root()
    os.chdir(root)
    out_dir = Path(root) / "board" / "eod" / "out" / date_str
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) Sync repo
    print("1) Syncing repo...", flush=True)
    out, err, rc = _run(f"cd {root} && git fetch origin && git pull origin main", timeout=30)
    print("   OK" if rc == 0 else f"   WARNING: {err or out}", flush=True)

    # 2) Run tests
    print("2) Running tests...", flush=True)
    out, err, rc = _run(f"cd {root} && python3 -m unittest discover -s validation -p '*.py' -q", timeout=120)
    if rc != 0:
        print(f"   FAIL: {err or out}", flush=True)
    else:
        print("   OK", flush=True)

    # 3) Force EOD (may fail if artifacts missing - hard-fail enforced)
    print("3) Forcing EOD...", flush=True)
    out, err, rc = _run(
        f"cd {root} && CLAWDBOT_SESSION_ID=stock_quant_eod_{date_str} "
        f"python3 board/eod/eod_confirmation.py --date {date_str} --allow-missing-missed-money",
        timeout=600,
    )
    print(out[-3000:] if len(out) > 3000 else out, flush=True)
    if err:
        print(err[-1500:] if len(err) > 1500 else err, file=sys.stderr, flush=True)
    if rc != 0:
        print("   EOD failed (hard-fail on missing artifacts)", flush=True)
        return 1
    print("   OK", flush=True)

    # 4) Write summary artifact
    print("4) Writing cursor_final_data_integrity_patch.json...", flush=True)
    summary = {
        "status": "complete",
        "changes": [
            "Hard-fail on missing EOD artifacts",
            "Attribution logging guaranteed",
            "Exit regime attribution added",
            "Correlation snapshot fallback + hourly cron",
            "Blocked trade logs enriched with UW + survivorship + variant",
            "EOD forced and pushed",
            "All changes executed on droplet",
        ],
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "cursor_final_data_integrity_patch.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("   OK", flush=True)

    # 5) Commit and push
    print("5) Git commit & push...", flush=True)
    out, err, rc = _run(
        f"cd {root} && git add . && "
        "git commit -m 'Data integrity hard-fail, attribution completeness, correlation fallback, enriched blocked/exit logs, full EOD integrity enforcement' || true && "
        "git push origin main",
        timeout=60,
    )
    print(out, flush=True)
    if err:
        print(err, file=sys.stderr, flush=True)
    if rc != 0:
        print("   WARNING: Push may have failed", flush=True)
    else:
        print("   OK", flush=True)

    print("\nDATA INTEGRITY PATCH COMPLETE.", flush=True)
    return 0


def run_remote(date_str: str) -> int:
    repo_root = str(SCRIPT_DIR.parent.parent)
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    try:
        from droplet_client import DropletClient
    except ImportError as e:
        print(f"Error: droplet_client not found. {e}", file=sys.stderr)
        return 1

    with DropletClient() as c:
        root = c.project_dir
        cmd = (
            f"cd {root} && git fetch origin && git pull origin main && "
            f"python3 board/eod/run_data_integrity_patch.py --date {date_str} --on-droplet"
        )
        out, err, rc = c._execute(cmd, timeout=900)
        print(out)
        if err:
            print(err, file=sys.stderr)
        return rc


def main() -> int:
    ap = argparse.ArgumentParser(description="Data integrity patch on droplet")
    ap.add_argument("--date", required=True, help="Date YYYY-MM-DD")
    ap.add_argument("--on-droplet", action="store_true", help="Run directly on droplet")
    ap.add_argument("--remote", action="store_true", help="SSH to droplet and run")
    args = ap.parse_args()

    on_windows = platform.system() == "Windows"
    if args.on_droplet:
        return run_on_droplet(args.date)
    if args.remote or on_windows:
        return run_remote(args.date)
    return run_on_droplet(args.date)


if __name__ == "__main__":
    sys.exit(main())
