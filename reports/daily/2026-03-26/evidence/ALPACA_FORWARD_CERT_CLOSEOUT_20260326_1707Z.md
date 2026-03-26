# ALPACA forward certification — CSA closeout (20260326_1707Z)

## Binary verdict

### **STILL_BLOCKED**

## Blockers (exact)

1. **Forward cohort vacuous:** `forward_economic_closes=0`, `forward_trade_intents_with_ct_and_tk=0` (post-DEPLOY window). Phase 2 minimums (**≥10 entered**, **≥10 economic closes**, or **60 minutes** observation) **not** satisfied.
2. **FORWARD_CHAIN_PERFECT:** `false` (`FORWARD_COHORT_VACUOUS: true` in strict gate JSON).
3. **Phase 3:** Cannot sample 15 `trade_id` traces; `trace_sample_size=0`.
4. **forward_incomplete:** Not meaningful proof when `forward_trades_seen=0`; certification requires a **non-vacuous** forward cohort per contract §B.

## Legacy

**LEGACY_DEBT_QUARANTINED** — historical incompletes are out of scope for forward proof; no claim is made that history is repaired.

## Evidence index

| Artifact |
|----------|
| `reports/ALPACA_FORWARD_DROPLET_RAW_20260326_1905Z.json` |
| `reports/audit/ALPACA_FORWARD_CERT_CONTRACT_20260326_1707Z.md` |
| `reports/audit/ALPACA_DEPLOY_20260326_1707Z.md` |
| `reports/audit/ALPACA_SERVICE_HEALTH_20260326_1707Z.md` |
| `reports/audit/ALPACA_FORWARD_COHORT_MARKER_20260326_1707Z.md` |
| `reports/audit/ALPACA_FORWARD_TRACE_20260326_1707Z.md` |
| `reports/ALPACA_FORWARD_TRACE_20260326_1707Z.json` |
| `reports/audit/ALPACA_FORWARD_PARITY_COUNTS_20260326_1707Z.md` |
| `reports/ALPACA_FORWARD_PARITY_COUNTS_20260326_1707Z.json` |
| `reports/audit/ALPACA_STRICT_GATE_FORWARD_20260326_1707Z.md` |
| `reports/ALPACA_STRICT_GATE_FORWARD_20260326_1707Z.json` |
| `reports/audit/ALPACA_FORWARD_ADVERSARIAL_REVIEW_20260326_1707Z.md` |
