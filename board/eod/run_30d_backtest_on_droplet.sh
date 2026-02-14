#!/bin/bash
# ============================================================
# FULL 30-DAY BACKTEST (RUN ON DROPLET ONLY)
# ============================================================
# - Syncs repo, writes config, runs replay from logs
# - Writes backtests/30d/backtest_*.jsonl and backtest_summary.json
# - Optionally pushes results to GitHub and writes summary for Mark
# ============================================================

set -e
ROOT="/root/stock-bot-current"
[ -d "$ROOT" ] || ROOT="/root/trading-bot-current"
[ -d "$ROOT" ] || ROOT="/root/stock-bot"
cd "$ROOT"

echo "=== 1) SYNC REPO ==="
git fetch --all
git checkout main
git pull --rebase || true

echo "=== 2) DEFINE BACKTEST WINDOW (LAST 30 DAYS) ==="
python3 scripts/write_30d_backtest_config.py

echo "=== 3) RUN THE BACKTEST ==="
python3 scripts/run_30d_backtest_droplet.py

echo "=== 4) SUMMARY ARTIFACT FOR REVIEW ==="
SUMMARY="backtests/30d/backtest_summary.json"
REVIEW="backtests/30d/backtest_review_for_mark.md"
if [ -f "$SUMMARY" ]; then
  echo "Backtest complete. Summary: $SUMMARY"
  # Generate a short markdown for Mark
  python3 - << 'PY'
import json
from pathlib import Path
p = Path("backtests/30d/backtest_summary.json")
if p.exists():
    d = json.loads(p.read_text())
    out = Path("backtests/30d/backtest_review_for_mark.md")
    lines = [
        "# 30-Day Backtest Review",
        "",
        f"- **Window:** {d.get('window_start')} to {d.get('window_end')}",
        f"- **Trades:** {d.get('trades_count')}",
        f"- **Exits:** {d.get('exits_count')}",
        f"- **Blocks:** {d.get('blocks_count')}",
        f"- **Total P&L USD:** {d.get('total_pnl_usd')}",
        f"- **Win rate %:** {d.get('win_rate_pct')}",
        "",
        "## Exit reasons",
        "```",
        json.dumps(d.get("exit_reason_counts", {}), indent=2),
        "```",
        "",
        "## Block reasons",
        "```",
        json.dumps(d.get("block_reason_counts", {}), indent=2),
        "```",
        "",
        f"Generated: {d.get('generated_at')}",
    ]
    out.write_text("\n".join(lines))
    print("Wrote", out)
PY
fi

echo "=== 5) OPTIONAL: PUSH TO GITHUB ==="
if [ -n "${PUSH_BACKTEST_RESULTS:-}" ] && [ "$PUSH_BACKTEST_RESULTS" = "1" ]; then
  git add backtests/config/ backtests/30d/ 2>/dev/null || true
  git status --short
  git commit -m "Backtest 30d: replay from logs, summary and artifacts" || true
  git push origin main || true
  echo "Pushed backtest results to origin/main"
else
  echo "Set PUSH_BACKTEST_RESULTS=1 to commit and push backtest artifacts"
fi

echo "=== DONE ==="
