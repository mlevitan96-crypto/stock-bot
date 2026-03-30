#!/usr/bin/env python3
"""
Alpaca Telegram + data integrity cycle (droplet). Read-only on strategy.

See MEMORY_BANK.md (Alpaca Telegram integrity) and config/alpaca_telegram_integrity.json.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
os.environ.setdefault("PYTHONPATH", str(REPO))


def main() -> int:
    ap = argparse.ArgumentParser(description="Alpaca Telegram integrity + milestone cycle")
    ap.add_argument("--root", type=Path, default=None, help="Repo root (default TRADING_BOT_ROOT or cwd)")
    ap.add_argument("--dry-run", action="store_true", help="No Telegram HTTP; print summary JSON")
    ap.add_argument("--skip-warehouse", action="store_true", help="Do not run truth warehouse mission")
    ap.add_argument("--no-self-heal", action="store_true", help="Skip mkdir / postclose try-restart")
    ap.add_argument("--send-test-milestone", action="store_true", help="Send [TEST] milestone template")
    ap.add_argument("--send-test-integrity", action="store_true", help="Send [TEST] integrity alert")
    args = ap.parse_args()
    root = args.root
    if root:
        os.environ["TRADING_BOT_ROOT"] = str(root.resolve())
    from telemetry.alpaca_telegram_integrity.runner_core import run_integrity_cycle

    out = run_integrity_cycle(
        root=root.resolve() if root else None,
        dry_run=args.dry_run,
        send_test_milestone=args.send_test_milestone,
        send_test_integrity=args.send_test_integrity,
        skip_warehouse=args.skip_warehouse,
        skip_self_heal=args.no_self_heal,
    )
    print(json.dumps(out, indent=2, default=str))
    rdir = Path(os.environ.get("TRADING_BOT_ROOT", str(REPO))).resolve()
    logf = rdir / "logs" / "alpaca_telegram_integrity.log"
    try:
        logf.parent.mkdir(parents=True, exist_ok=True)
        from datetime import datetime, timezone

        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        line = f"{ts} cycle_ok milestone_count={out.get('milestone', {}).get('unique_closed_trades', '')}\n"
        with logf.open("a", encoding="utf-8") as f:
            f.write(line)
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
