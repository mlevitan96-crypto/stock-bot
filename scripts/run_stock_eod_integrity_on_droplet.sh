#!/usr/bin/env bash
# Stock-bot EOD integrity + manifest on droplet.
# Run on droplet at REPO_DIR (default /root/trading-bot-current).
# 1) Manifest + integrity gate (eod_bundle_manifest.py)
# 2) If pass: run stock EOD quant officer (board/eod/run_stock_quant_officer_eod.py)
# 3) Commit manifest + EOD reports; push unless AUTO_COMMIT_PUSH=0
set -euo pipefail

REPO_DIR="${REPO_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$REPO_DIR" || exit 1

DATE="${1:-$(date -u +%Y-%m-%d)}"
export CLAWDBOT_SESSION_ID="${CLAWDBOT_SESSION_ID:-stock_quant_eod_${DATE}}"

echo "EOD integrity: REPO_DIR=$REPO_DIR DATE=$DATE"

git fetch origin
git pull --rebase --autostash origin main || true

# Phase 1: Manifest + integrity gate (hard contract)
python3 scripts/eod_bundle_manifest.py --date "$DATE" --base-dir "$REPO_DIR" || exit 1

# Phase 1b: Daily strategy reports + unified intelligence pack (reports/stockbot/YYYY-MM-DD/)
python3 scripts/generate_daily_strategy_reports.py --date "$DATE" || true
python3 scripts/run_stockbot_daily_reports.py --date "$DATE" --base-dir "$REPO_DIR" || true

# Phase 2: Stock EOD quant officer (produces quant_officer_eod_<DATE>.json|.md and/or stock_quant_officer_eod_*)
if [ -f "board/eod/run_stock_quant_officer_eod.py" ]; then
  python3 board/eod/run_stock_quant_officer_eod.py || true
else
  echo "No board/eod/run_stock_quant_officer_eod.py; skipping EOD memo generation."
fi

# Phase 2b: Signal/weight/exit inventory (reports/STOCK_SIGNAL_WEIGHT_EXIT_INVENTORY_<DATE>.md)
python3 scripts/generate_signal_weight_exit_inventory.py --date "$DATE" --base-dir "$REPO_DIR" || true

# Phase 3: Commit manifest + inventory + EOD outputs + scripts
git add reports/eod_manifests/EOD_MANIFEST_"${DATE}".json reports/eod_manifests/EOD_MANIFEST_"${DATE}".md || true
git add reports/STOCK_SIGNAL_WEIGHT_EXIT_INVENTORY_"${DATE}".md || true
git add reports/stockbot/"${DATE}"/* 2>/dev/null || true
git add scripts/eod_bundle_manifest.py scripts/generate_signal_weight_exit_inventory.py scripts/run_stock_eod_integrity_on_droplet.sh || true
git add board/eod/out/*.md board/eod/out/*.json 2>/dev/null || true
git status --short

git commit -m "Stock-bot: harden EOD data + inventory signals/weights/exits ${DATE}" || true

if [ "${AUTO_COMMIT_PUSH:-1}" = "1" ]; then
  git push origin main || true
  echo "Pushed to origin main."
else
  echo "AUTO_COMMIT_PUSH=0; skip push."
fi

echo "Done — EOD integrity + manifest ${DATE}."
