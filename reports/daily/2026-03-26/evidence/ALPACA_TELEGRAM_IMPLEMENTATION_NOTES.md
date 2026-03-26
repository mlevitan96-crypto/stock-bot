# Alpaca Telegram — Implementation & Safety (Phase 4)

**Mission:** Implementation rules and fail-closed behavior. READ-ONLY scope enforced.  
**Authority:** SRE.  
**Date:** 2026-03-18.

---

## 1. Rules

| Rule | Description |
|------|-------------|
| **Read trade count from TRADES_FROZEN** | Count = number of data rows in the CSV (excluding header). Do not use any other source for milestone logic. |
| **No impact on execution paths** | Telegram send must not affect trading, order submission, pipeline step success/failure, or DATA_READY logic. If send fails, pipeline (or calling script) continues; no exception propagated to execution. |
| **Fail-closed if Telegram send fails** | On send failure (network, API error, missing env): **log only**. Do not crash, do not block pipeline, do not retry indefinitely. Optional: write to a log file or system_events.jsonl that send was skipped or failed. |
| **READ-ONLY scope** | No modification of trading state, positions, or paper promotion. Alerts are observability only. |

---

## 2. Credentials

- **Source:** Environment only. `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`. No secrets in code or repo.
- **Missing:** If either unset, skip send and log (e.g. stderr or `Telegram skipped: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set`). Align with existing `send_telegram()` in `scripts/alpaca_edge_2000_pipeline.py`.

---

## 3. Where to Integrate

- **Trade-count milestones:** After pipeline step1 (build TRADES_FROZEN) completes, before or after step2. Read `reports/alpaca_edge_2000_<TS>/TRADES_FROZEN.csv` row count; read/write `state/alpaca_telegram_milestones.json`; for each threshold not yet sent, send message and update state.
- **Analysis completion:** Either (a) at end of pipeline steps that produce each artifact, or (b) from a separate script that checks for presence of artifact paths and sends one message per phase (with optional idempotency).

---

## 4. Existing Code Reference

- **Send function:** `scripts/alpaca_edge_2000_pipeline.py` — `send_telegram(text: str) -> bool`. Uses env; returns False if skip/fail; does not raise.
- **Verification:** `scripts/verify_telegram_env.py` — checks TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID at runtime.
- **Pipeline flag:** `--no-telegram` disables Telegram in pipeline; milestone logic can respect same flag so operators can disable all Telegram.

---

## 5. Safety Summary

- **No execution impact:** Alerts do not change orders, positions, or promotion.
- **No secrets in code:** Credentials from environment only.
- **Fail-closed:** Send failure → log only, no crash, no block.
- **Deterministic:** Same TRADES_FROZEN count and state file → same milestone sends (idempotent after state update).
