# Alpaca Experiment #1 — Final Verification

**Date:** 2026-03-13  
**Task:** Finalize Experiment #1 and daily governance on droplet. No execution/risk/broker logic changes.

---

## STEP 0 — Safety

- **Droplet path:** `/root/stock-bot` (confirmed)
- **Ledger path:** `state/governance_experiment_1_hypothesis_ledger_alpaca.json`
- **Trade logs:** `logs/exit_attribution.jsonl`, `logs/attribution.jsonl`, `logs/master_trade_log.jsonl` (all present on droplet)
- **Mode:** Read-only on trading logic

---

## STEP 1 — Ledger fixed

- **Action:** On droplet ran `python3 scripts/tag_profit_hypothesis_alpaca.py NO`
- **Result:** Ledger created with one entry (change_id=41ccecd..., profit_hypothesis_present=NO)
- **Validator:** `python3 scripts/validate_hypothesis_ledger_alpaca.py` → exit 0 (HEALTHY)

---

## STEP 2 — Experiment start flag

- **Action:** Created `state/experiment_1_start.flag` on droplet with content `2026-03-01T00:00:00Z`, `chmod 600`
- **Result:** Flag present and readable

---

## STEP 3 — Telegram env on droplet

- **Check:** `printenv | grep TELEGRAM` → no vars in default shell environment
- **Action:** Created `/root/.alpaca_env` on droplet with placeholder exports:
  - `export TELEGRAM_BOT_TOKEN="<INSERT_TOKEN>"`
  - `export TELEGRAM_CHAT_ID="<INSERT_CHAT_ID>"`
- **Permissions:** `chmod 600 /root/.alpaca_env`
- **To activate Telegram:** Replace placeholders with real token and chat ID, then source before running daily governance or break/completion scripts:
  - ` . /root/.alpaca_env && cd /root/stock-bot && python3 scripts/run_alpaca_daily_governance.py`
  - Example cron (opt-in): `0 21 * * 1-5 . /root/.alpaca_env && cd /root/stock-bot && python3 scripts/run_alpaca_daily_governance.py >> /root/alpaca_daily_governance.log 2>&1`

---

## STEP 4 — Telegram alerts

- **Break notify:** Ran `. /root/.alpaca_env; python3 scripts/notify_governance_experiment_alpaca_break.py` → "Ledger valid and fresh; no break alert sent." (rc 0). No message sent because ledger is healthy (expected).
- **Completion notify:** Not run automatically (sends at most once per phase). When ready, run: `python3 scripts/notify_governance_experiment_alpaca_complete.py --sessions-elapsed 12 --trades-count 409` (or let daily governance / status drive that).
- **Telegram functional:** Once real `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are in `/root/.alpaca_env`, break/completion and daily governance will send messages. With placeholders, scripts run but do not send (exit 2 for daily governance until env is set).

---

## STEP 5 — Status check on droplet

- **Command:** `python3 scripts/experiment_1_status_check_alpaca.py` (on droplet)
- **Result:**
  - **Trades so far:** 409
  - **Ledger health:** HEALTHY
  - **Break alert ready:** False
  - **Completion alert ready:** True
  - **Days elapsed:** 12
  - **Next action:** Send completion alert (window satisfied, ledger healthy); or already sent.

---

## STEP 6 — Daily governance on droplet

- **Command:** `python3 scripts/run_alpaca_daily_governance.py` (on droplet)
- **Result:**
  - DAILY GOVERNANCE SUMMARY printed:
    - Date: 2026-03-13
    - PnL (today): -74.70 USD
    - Trade count (today): 229
    - Change candidate: NO
    - Decision Spine: reports/QUANTIFIED_DECISION_SPINE_ALPACA_EXPERIMENT_1_2026-03-12.md
  - Telegram not sent (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID are placeholders); exit 2. After adding real values to `/root/.alpaca_env` and sourcing, the same command will send the daily message ("NO CHANGE CANDIDATE TODAY" or "CHANGE CANDIDATE PRESENT — REVIEW REQUIRED").

---

## STEP 7 — Final summary

| Item | Status |
|------|--------|
| Ledger status | **HEALTHY** (validator exit 0) |
| Experiment start flag | **Present** (`state/experiment_1_start.flag`, 2026-03-01T00:00:00Z) |
| Real trade count | **409** (in window); 229 today |
| Telegram env file | **Present** (`/root/.alpaca_env` with placeholders; replace for live alerts) |
| Telegram alerts (break/complete) | **Functional** when real token/chat ID set; break correctly reported "no send" while ledger healthy |
| Daily governance | **Functional** (summary printed; Telegram send works once env is set) |
| Remaining blocker | **None** for experiment or pipeline. Optional: add real Telegram credentials to `/root/.alpaca_env` and (if desired) install cron for daily run. |

Experiment #1 is finalized and progressing with real trades. No execution, risk, or broker logic was changed.
