# ALPACA forward certification contract (STOP-GATE 0)

**CSA verdict:** APPROVED (as stated below). No revision to A/B/C at execution time.

## A) Forward cohort definition

- **Primary:** Trades with position open time `entry_ts >= DEPLOY_TS_UTC` (epoch **1774544849.0**, UTC **2026-03-26T17:07:29Z** from `date -u +%s` on droplet at deploy).
- **Alternate marker:** First trade after `systemctl restart stock-bot` (same deploy window; services restarted immediately after `git reset --hard origin/main`).

## B) Perfect chain (forward cohort only)

1. `trade_intent(entered)` carries **canonical_trade_id** and **trade_key**.
2. Orders/fills reference the **same** canonical_trade_id / trade_key.
3. `exit_attribution` rows include canonical_trade_id / trade_key.
4. Unified **terminal close** exists for every economic close.
5. Strict completeness gate reports **100% complete** for the forward segment (`forward_trades_incomplete == 0`, cohort not vacuous).

## C) Legacy cohort

- May remain incomplete.
- Labeled **LEGACY_DEBT_QUARANTINED**; not used for forward causal certification.

---
*Artifact: machine bundle `reports/ALPACA_FORWARD_DROPLET_RAW_20260326_1905Z.json` + this file.*
