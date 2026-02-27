#!/usr/bin/env python3
"""
Start live paper trading on the droplet via SSH.
Uses droplet_config.json. Runs ALL commands ON THE DROPLET.
"""
from __future__ import annotations

import argparse
import platform
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent


def run_remote(date_str: str, dry_eod_only: bool = False, overlay_path: str | None = None) -> int:
    """SSH to droplet and execute start_live_paper_run flow. If overlay_path is set, start paper with GOVERNED_TUNING_CONFIG."""
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    try:
        from droplet_client import DropletClient
    except ImportError as e:
        print(f"Error: droplet_client not found. {e}", file=sys.stderr)
        return 1

    eod_cmd = "--dry-run" if dry_eod_only else "--allow-missing-missed-money"
    env_export = f"export GOVERNED_TUNING_CONFIG={overlay_path}; " if overlay_path else ""
    run_cmd = f"{env_export}LOG_LEVEL=INFO python3 main.py" if overlay_path else "LOG_LEVEL=INFO python3 main.py"
    overlay_for_state = overlay_path or ""

    if dry_eod_only:
        cmd = (
            f"cd /root/stock-bot-current 2>/dev/null || cd /root/trading-bot-current 2>/dev/null || cd /root/stock-bot && "
            "echo '1) Git' && git status && git pull --rebase origin main && "
            f"echo '2) EOD dry-run' && python3 board/eod/eod_confirmation.py --date {date_str} {eod_cmd} && "
            "echo 'DONE (dry-run only, no live start)'"
        )
    else:
        state_py = (
            "python3 -c \"import json,os,time; d=os.path.join('state','live_paper_run_state.json'); "
            "os.makedirs(os.path.dirname(d),exist_ok=True); "
            "details={'trading_mode':'paper','process':'python3 main.py','session':'stock_bot_paper_run','governed_tuning_config':'%s'}; "
            "json.dump({'status':'live_paper_run_started','timestamp':int(time.time()),'details':details}, open(d,'w'), indent=2); "
            "print('live_paper_run_state.json written')\" && "
        ) % overlay_for_state
        cmd = (
            f"cd /root/stock-bot-current 2>/dev/null || cd /root/trading-bot-current 2>/dev/null || cd /root/stock-bot && "
            "echo '1) Git status + pull' && git status && git rev-parse --abbrev-ref HEAD && git pull --rebase origin main && "
            "echo '2) Paper mode check' && (grep -E 'ALPACA|APCA_API' .env 2>/dev/null | head -3 || echo '.env OK') && "
            f"echo '3) EOD sanity' && python3 board/eod/eod_confirmation.py --date {date_str} {eod_cmd} && "
            "echo '4) Kill old tmux' && tmux kill-session -t stock_bot_paper_run 2>/dev/null || true && "
            f"echo '5) Start tmux' && tmux new-session -d -s stock_bot_paper_run 'cd /root/stock-bot-current 2>/dev/null || cd /root/trading-bot-current 2>/dev/null || cd /root/stock-bot; {run_cmd}' && "
            "sleep 5 && echo '6) Verify' && tmux ls 2>/dev/null && ps aux | grep 'python3 main.py' | grep -v grep || echo 'process check' && "
            "python3 -c \"import os; paths=['logs/attribution.jsonl','logs/exit_attribution.jsonl','logs/run.jsonl','state/blocked_trades.jsonl']; [print(p+': PRESENT '+str(os.path.getsize(p))) if os.path.exists(p) else print(p+': MISSING') for p in paths]\" && "
            + state_py
            + "echo 'DONE: Live paper run started'"
        )

    with DropletClient() as c:
        out, err, rc = c._execute(cmd, timeout=300)
        print(out)
        if err:
            print(err, file=sys.stderr)
        return rc


def main() -> int:
    ap = argparse.ArgumentParser(description="Start live paper run on droplet")
    ap.add_argument("--date", default="2026-02-12", help="Date for EOD sanity check (YYYY-MM-DD)")
    ap.add_argument("--dry-eod-only", action="store_true", help="Only run EOD dry-run, do not start live loop")
    ap.add_argument("--remote", action="store_true", help="SSH to droplet (default on Windows)")
    ap.add_argument("--overlay", default=None, help="Overlay path for GOVERNED_TUNING_CONFIG (e.g. config/tuning/overlays/exit_score_weight_tune.json)")
    args = ap.parse_args()

    on_windows = platform.system() == "Windows"
    if args.remote or on_windows:
        return run_remote(args.date, dry_eod_only=args.dry_eod_only, overlay_path=args.overlay)
    return run_remote(args.date, dry_eod_only=args.dry_eod_only, overlay_path=args.overlay)


if __name__ == "__main__":
    sys.exit(main())
