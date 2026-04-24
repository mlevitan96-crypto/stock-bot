#!/usr/bin/env python3
"""
Run Alpaca 2000-trade edge discovery pipeline on the droplet (real data).
- Builds frozen dataset (TRADES_FROZEN.csv + ENTRY/EXIT_ATTRIBUTION_FROZEN.jsonl + INPUT_FREEZE.md).
- Optionally fetches bars with caching (--bars-rate-limit-safe); use --skip-bars to skip.
- Runs full pipeline; Telegram: start (count + hash), completion (board packet path + CSA verdict path).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def main() -> int:
    from droplet_client import DropletClient

    ap = argparse.ArgumentParser()
    ap.add_argument("--no-pull", action="store_true", help="Skip git pull")
    ap.add_argument("--no-telegram", action="store_true", help="Skip Telegram")
    ap.add_argument("--telegram-start", action="store_true", help="Send start Telegram only")
    ap.add_argument("--skip-bars", action="store_true", help="Skip bar-by-bar fetch (step 2)")
    ap.add_argument("--max-trades", type=int, default=2000, help="Max trades to freeze")
    ap.add_argument("--bars-resolution", default="1m", help="Bar resolution (1m, 5m, 1h, 1d)")
    ap.add_argument("--bars-batch-size", type=int, default=50, help="Sleep every N trades when fetching bars")
    args = ap.parse_args()
    c = DropletClient()
    proj = c.project_dir.replace("~", "/root")
    if not args.no_pull:
        out, err, rc = c._execute_with_cd("git fetch origin && git pull origin main", timeout=60)
        print("git pull:", (out or err or "")[:300])
    cmd = (
        f". /root/.alpaca_env 2>/dev/null; cd {proj} && python3 scripts/alpaca_edge_2000_pipeline.py "
        f"--exit-log logs/exit_attribution.jsonl --max-trades {args.max_trades} "
        f"--bars-resolution {args.bars_resolution} --bars-batch-size {args.bars_batch_size} --bars-rate-limit-safe"
    )
    if args.no_telegram:
        cmd += " --no-telegram"
    if args.telegram_start:
        cmd += " --telegram-start"
    if args.skip_bars:
        cmd += " --skip-bars"
    out, err, rc = c._execute(cmd, timeout=600)
    print(out or "")
    if err:
        print("stderr:", err[:1000])
    if rc != 0:
        return rc
    print("Pipeline complete on droplet. Fetch reports/alpaca_edge_2000_*, reports/ALPACA_EDGE_*.md, reports/audit/CSA_REVIEW_ALPACA_EDGE_*.md if needed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
