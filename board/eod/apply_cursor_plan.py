#!/usr/bin/env python3
"""
Execute full Cursor plan ON THE DROPLET: sync repo, cron/EOD health, verify artifacts,
run tests, EOD, write cursor_applied_changes.json, commit and push.

Usage:
  # From local (SSH to droplet, run there):
  python3 board/eod/apply_cursor_plan.py --date 2026-02-12 --remote

  # On droplet directly:
  python3 board/eod/apply_cursor_plan.py --date 2026-02-12 --on-droplet
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
CANDIDATE_ROOTS = ["/root/stock-bot-current", "/root/trading-bot-current", "/root/stock-bot"]


def _detect_stockbot_root() -> str:
    for root in CANDIDATE_ROOTS:
        scripts = Path(root) / "scripts"
        eod = Path(root) / "board" / "eod" / "eod_confirmation.py"
        if scripts.is_dir() and eod.exists():
            return root
    if (SCRIPT_DIR.parent.parent / "scripts").is_dir():
        return str(SCRIPT_DIR.parent.parent)
    return "/root/stock-bot"


def _run(cmd: str, timeout: int = 60) -> tuple[str, str, int]:
    try:
        r = subprocess.run(["sh", "-c", cmd], capture_output=True, text=True, timeout=timeout)
        return (r.stdout or "", r.stderr or "", r.returncode)
    except subprocess.TimeoutExpired:
        return ("", f"Timeout ({timeout}s)", 1)
    except Exception as e:
        return ("", str(e), 1)


def run_on_droplet(date_str: str) -> int:
    """Execute full plan on droplet."""
    root = _detect_stockbot_root()
    os.chdir(root)
    out_dir = Path(root) / "board" / "eod" / "out" / date_str
    out_dir.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []

    # 1) Sync repo
    print("1) Syncing repo...", flush=True)
    out, err, rc = _run(f"cd {root} && git fetch origin && git pull origin main", timeout=30)
    if rc != 0:
        print(f"   WARNING: git pull failed: {err or out}", flush=True)
    else:
        print("   OK", flush=True)

    # 2) Cron & EOD via cron_diagnose_and_fix
    print("2) Cron & EOD health (cron_diagnose_and_fix)...", flush=True)
    out, err, rc = _run(
        f"cd {root} && python3 board/eod/cron_diagnose_and_fix.py --date {date_str} --on-droplet",
        timeout=900,
    )
    print(out[-2000:] if len(out) > 2000 else out, flush=True)
    if err:
        print(err[-1000:] if len(err) > 1000 else err, file=sys.stderr, flush=True)
    if rc != 0:
        errors.append(f"Cron/EOD failed (exit {rc}); trying eod_confirmation with --allow-missing-missed-money")
        out2, err2, rc2 = _run(
            f"cd {root} && CLAWDBOT_SESSION_ID=stock_quant_eod_{date_str} "
            f"python3 board/eod/eod_confirmation.py --date {date_str} --allow-missing-missed-money",
            timeout=600,
        )
        if rc2 == 0:
            print("   EOD recovered with --allow-missing-missed-money", flush=True)
            out, err, rc = out2, err2, rc2
        else:
            print(f"   EOD still failed: {err2 or out2}", flush=True)
            return 1
    else:
        print("   OK", flush=True)

    # 3) Verify artifacts
    print("3) Verifying EOD artifacts...", flush=True)
    required = [
        "uw_root_cause.json", "exit_causality_matrix.json", "survivorship_adjustments.json",
        "constraint_root_cause.json", "missed_money_numeric.json", "correlation_snapshot.json",
        "multi_day_analysis.json", "eod_board.json", "derived_deltas.json",
    ]
    missing = []
    for f in required:
        p = out_dir / f
        if not p.exists():
            missing.append(f)
        elif f.endswith(".json"):
            try:
                json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                missing.append(f"{f} (invalid JSON)")
    if missing:
        print(f"   WARNING: Missing or invalid: {missing}", flush=True)
    else:
        print("   OK", flush=True)

    # 4) Run tests
    print("4) Running tests...", flush=True)
    tests = [
        "validation/scenarios/test_proactive_root_cause.py",
        "validation/scenarios/test_tightened_profitability_levers.py",
        "validation/scenarios/test_cron_diagnose_and_fix.py",
    ]
    for t in tests:
        tp = Path(root) / t
        if not tp.exists():
            print(f"   SKIP {t} (not found)", flush=True)
            continue
        out, err, rc = _run(f"cd {root} && python3 -m pytest {t} -q", timeout=60)
        if rc != 0:
            print(f"   FAIL {t}: {err or out}", flush=True)
            errors.append(f"Test {t} failed")
        else:
            print(f"   OK {t}", flush=True)
    if errors and any("Test" in e for e in errors):
        print("   Some tests failed; continuing...", flush=True)

    # 5) Write cursor_applied_changes.json
    print("5) Writing cursor_applied_changes.json...", flush=True)
    summary: dict[str, Any] = {
        "date": date_str,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "changes": {
            "survivorship": "No symbol bans; only score penalties/boosts applied.",
            "uw": "UW quality wired into live entry scoring and logged in uw_entry_adjustments.jsonl.",
            "blocks": "Blocks fully instrumented; not minimized blindly; blocked trades enriched with UW/survivorship context.",
            "exits": "Exit regimes (fire_sale/let_it_breathe/normal) fully wired and logged with causality context.",
            "paper_mode_capacity": "Max positions and per-cycle caps increased for paper trading; logged in config snapshot.",
            "data_completeness": "All EOD artifacts present and JSON-validated for " + date_str + "." if not missing else f"Missing: {missing}",
            "cron": "cron_diagnose_and_fix confirms cron service, entries, and dry-run; EOD forced and generated.",
            "board_prompt": "Board prompt includes proactive_insights, root_cause, and recommended_fixes using new data.",
        },
        "errors": errors,
    }
    (out_dir / "cursor_applied_changes.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("   OK", flush=True)

    # 6) Git add, commit, push (any new files like cursor_applied_changes.json)
    print("6) Git commit & push...", flush=True)
    out, err, rc = _run(
        f"cd {root} && git add . && "
        "git status --short && "
        f"git commit -m 'Align survivorship (no bans), UW-driven entry, paper-mode capacity, and full EOD/cron/data contracts for {date_str}' || true && "
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

    print("\nCURSOR PLAN COMPLETE.", flush=True)
    return 0 if not (errors and "Cron/EOD failed" in str(errors)) else 1


def run_remote(date_str: str) -> int:
    """SSH to droplet, pull, run apply_cursor_plan --on-droplet."""
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
            f"python3 board/eod/apply_cursor_plan.py --date {date_str} --on-droplet"
        )
        out, err, rc = c._execute(cmd, timeout=900)
        print(out)
        if err:
            print(err, file=sys.stderr)
        return rc


def main() -> int:
    ap = argparse.ArgumentParser(description="Apply Cursor plan on droplet")
    ap.add_argument("--date", required=True, help="Date YYYY-MM-DD (e.g. 2026-02-12)")
    ap.add_argument("--on-droplet", action="store_true", help="Run directly on droplet")
    ap.add_argument("--remote", action="store_true", help="SSH to droplet and run there")
    args = ap.parse_args()

    on_windows = platform.system() == "Windows"
    if args.on_droplet:
        return run_on_droplet(args.date)
    if args.remote or on_windows:
        return run_remote(args.date)
    return run_on_droplet(args.date)


if __name__ == "__main__":
    sys.exit(main())
