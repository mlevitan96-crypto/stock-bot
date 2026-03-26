# Alpaca learning-ready — CSA final verdict

**TS:** `20260327_0200Z`

## Binary verdict

### **STILL_BLOCKED**

## Why FORWARD_CERTIFIED / LEARNING_READY is not chosen

| Hard criterion | Status |
|----------------|--------|
| A) Non-vacuous strict cohort (econ>0, entered signal) | **PASS** (replay era: 89 closes; non_vacuous true in cert bundle) |
| B) `trades_incomplete == 0` | **FAIL** — **6** incomplete |
| C) Parity econ vs unified (0 tolerance) | **PASS** — 89 == 89 |
| D) 15 traces join cleanly | **PASS** — sampled from completes only |
| E) Droplet proof | **PASS** — see index below |
| F) Binary CSA | This document |

## Consolidated blocker table

| trade_id | Missing legs | Raw economic close exists? | Recoverable? | Fix required |
|----------|--------------|----------------------------|--------------|--------------|
| open_PFE_2026-03-26T14:29:25.977370+00:00 | entry intent join, unified entry, orders canonical, exit_intent | Yes (exit_attribution) | Yes | Additive telemetry rows or emitter path fix |
| open_QQQ_2026-03-26T15:10:28.882493+00:00 | same | Yes | Yes | same |
| open_WMT_2026-03-26T15:10:28.883737+00:00 | same | Yes | Yes | same |
| open_HOOD_2026-03-26T15:51:38.174449+00:00 | same | Yes | Yes | same |
| open_LCID_2026-03-26T15:51:38.396698+00:00 | same | Yes | Yes | same |
| open_CAT_2026-03-26T16:34:40.245664+00:00 | same | Yes | Yes | same |

## Labels

- **CODE_COMPLETE_REPLAY:** cohort and parity proven under explicit replay era (see `ALPACA_CERT_RUN_REPLAY_20260327_0200Z.json`).
- **LIVE_FORWARD_PENDING:** deploy-anchored poll vacuous within captured window (`ALPACA_CERT_RUN_LIVE_20260327_0200Z.json`).

## Evidence index

| Artifact |
|----------|
| `reports/ALPACA_DROPLET_CERT_MISSION_20260327_0200Z.json` |
| `reports/audit/ALPACA_STRICT_ERA_POLICY_CSA_20260327_0200Z.md` |
| `reports/audit/ALPACA_DROPLET_SERVICE_DISCOVERY_20260327_0200Z.md` |
| `reports/audit/ALPACA_DROPLET_SERVICE_HEALTH_20260327_0200Z.md` |
| `reports/audit/ALPACA_NONVACUOUS_MECHANISMS_IMPL_20260327_0200Z.md` |
| `reports/audit/ALPACA_CERT_RUN_REPLAY_20260327_0200Z.md` + `.json` |
| `reports/audit/ALPACA_CERT_RUN_LIVE_20260327_0200Z.md` + `.json` |
| `reports/audit/ALPACA_STRICT_GATE_RESULT_20260327_0200Z.md` + `.json` |
| `reports/audit/ALPACA_PARITY_RESULT_20260327_0200Z.md` + `.json` |
| `reports/audit/ALPACA_TRACE_SET_20260327_0200Z.md` + `.json` |
| `reports/audit/ALPACA_REPAIR_LOOP_i0_20260327_0200Z.md` |
| `reports/ALPACA_REPAIR_LOOP_i0_20260327_0200Z.json` |
| `reports/audit/ALPACA_LEARNING_READY_ADVERSARIAL_20260327_0200Z.md` |

## Post-push note

Droplet `git reset` during this run landed on **`1c2c946`** (pre–this commit). After pushing this change set, re-run `run_alpaca_droplet_learning_cert_final.py` so the droplet picks up the latest scripts via `git fetch/reset`.
