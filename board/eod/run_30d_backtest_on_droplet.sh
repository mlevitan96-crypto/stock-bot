#!/bin/bash
# ============================================================
# RUN 30-DAY BACKTEST ON DROPLET (AFTER INTEL OVERHAUL)
# ============================================================
# 0) Repo root on droplet
# 1) Pull latest
# 2) Run full test suite
# 3) Run 30-day backtest into timestamped OUT_DIR
# 4) Validate artifacts
# 5) Commit and push results
# 6) Write summary artifact for Mark
# ============================================================

set -e
ROOT="/root/stock-bot-current"
[ -d "$ROOT" ] || ROOT="/root/trading-bot-current"
[ -d "$ROOT" ] || ROOT="/root/stock-bot"
cd "$ROOT"

echo "=== 0) REPO ROOT ==="
pwd
echo "Root: $ROOT"

echo "=== 1) PULL LATEST ==="
git fetch --all
git checkout main
git pull --rebase || true

echo "=== 2) RUN FULL TEST SUITE ==="
python3 -m unittest discover -s validation -p "test_*.py" || true

echo "=== 3) RUN 30-DAY BACKTEST ==="
OUT_DIR="backtests/30d_after_intel_overhaul_$(date +%Y%m%d_%H%M%S)"
export OUT_DIR
mkdir -p "$OUT_DIR"
python3 scripts/run_30d_backtest_droplet.py --out "$OUT_DIR"

echo "=== 4) VALIDATE ARTIFACTS ==="
python3 - << 'EOF'
import os, sys

out = os.environ.get("OUT_DIR", "")
if not out:
    print("ERROR: OUT_DIR not set")
    sys.exit(1)

required = [
    os.path.join(out, "backtest_trades.jsonl"),
    os.path.join(out, "backtest_exits.jsonl"),
    os.path.join(out, "backtest_blocks.jsonl"),
    os.path.join(out, "backtest_summary.json"),
    os.path.join(out, "backtest_pnl_curve.json"),
]
missing = [f for f in required if not os.path.exists(f)]
if missing:
    print("ERROR: Missing backtest artifacts:", missing)
    sys.exit(1)

print("SUCCESS: All backtest artifacts present.")
EOF

echo "=== 5) COMMIT AND PUSH ==="
git add "$OUT_DIR"
git status --short
git commit -m "30-day backtest after intelligence overhaul — $(date)" || true
git push origin main || true

echo "=== 6) WRITE SUMMARY FOR MARK ==="
python3 - << 'EOF'
import json, os, time

out = os.environ.get("OUT_DIR", "")
if not out:
    print("WARN: OUT_DIR not set, skipping summary")
else:
    summary = {
        "status": "complete",
        "timestamp": int(time.time()),
        "notes": "30-day backtest executed on droplet after intelligence overhaul.",
        "artifacts": {
            "trades": f"{out}/backtest_trades.jsonl",
            "exits": f"{out}/backtest_exits.jsonl",
            "blocks": f"{out}/backtest_blocks.jsonl",
            "summary": f"{out}/backtest_summary.json",
            "pnl_curve": f"{out}/backtest_pnl_curve.json",
        },
    }
    path = f"{out}/backtest_run_summary.json"
    with open(path, "w") as f:
        json.dump(summary, f, indent=2)
    print("Backtest summary written:", path)
EOF

echo "=== DONE ==="
