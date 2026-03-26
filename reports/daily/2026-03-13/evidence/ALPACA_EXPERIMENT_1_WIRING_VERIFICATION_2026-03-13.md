# Alpaca Experiment #1 Wiring + Daily Governance — Verification

**Date:** 2026-03-13  
**Task:** Fix Experiment #1 wiring to real trades + daily promotion pipeline. Analysis-only; no order/sizing changes.

## Verification Results

### 1) Status script (local)
- **Command:** `python scripts/experiment_1_status_check_alpaca.py`
- **Result:** Runs successfully. Trades so far reflect local logs (0 if no local data). Ledger status EMPTY/HEALTHY/INVALID/STALE as expected.

### 2) Status script (droplet — live data)
- **Command:** `python scripts/experiment_1_status_check_alpaca.py --droplet` (after push)
- **Result:** **REAL trade count: 409.** Earliest/latest in window shown. Ledger health INVALID on droplet; break alert ready. Confirms script uses same paths the live bot writes to (exit_attribution, attribution, master_trade_log).

### 3) Daily governance script
- **Command:** `python scripts/run_alpaca_daily_governance.py`
- **Result:** Prints DAILY GOVERNANCE SUMMARY (date, PnL today, trade count today, NO CHANGE / CHANGE CANDIDATE). Sends Telegram when TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are set; exit 2 if not set (expected in dev).

## Summary

- **Experiment #1** is wired to real Alpaca trade logs; status check shows actual trade count on droplet (409).
- **Daily governance** runs and prints summary; Telegram sent when env is configured.
- **MEMORY_BANK** updated: Alpaca Data Sources (canonical paths), Daily Telegram contract.
- **No** order placement, sizing, or broker logic was modified.
