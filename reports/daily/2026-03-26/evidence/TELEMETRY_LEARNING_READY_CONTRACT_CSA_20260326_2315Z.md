# Telemetry learning-ready contract (CSA) — canonical

**Timestamp:** `20260326_2315Z`  
**Venues:** Alpaca, Kraken (same contract shape; venue-specific leg definitions below).

## CSA approval

This contract is **approved** as the single definition of “learning-ready telemetry” for closure work. Gates are **not** relaxed to obtain green dashboards; fail-closed reporting is mandatory.

---

## A) Canonical identity

- **One** `canonical_trade_id` / `trade_key` family per economic trade, propagated across:
  - entry decision (`trade_intent` with `decision_outcome=entered` where applicable),
  - execution records (orders/fills or venue equivalent),
  - exit intent / economic closure,
  - unified terminal close event.
- **Venue notes:**
  - **Alpaca:** Join rule documented in `telemetry/alpaca_strict_completeness_gate.py` (`AUTHORITATIVE_JOIN_KEY_RULE`); alias expansion via `canonical_trade_id_resolved` in `logs/run.jsonl`.
  - **Kraken:** Contract applies **once** a Kraken-specific strict gate and key schema are implemented and checked into the repo (currently **not present** — see Kraken baseline).

## B) Required legs for learning cohort

| Leg | Alpaca (strict gate inputs) | Kraken (target state) |
|-----|------------------------------|------------------------|
| Entry decision (entered) | `logs/run.jsonl` `event_type=trade_intent`, `decision_outcome=entered` | TBD — no strict gate file |
| Execution | `logs/orders.jsonl` rows with `canonical_trade_id` | TBD |
| Exit / economic close | `logs/exit_attribution.jsonl` | TBD |
| Unified terminal | `logs/alpaca_unified_events.jsonl` exit rows with `terminal_close` | TBD |

## C) Joinability

- Strict chain join succeeds for **100%** of trades in the **learning cohort** (`trades_incomplete == 0` for that cohort).
- Segmentation (legacy vs forward vs replay) must be **documented** and applied consistently; no accidental mixing.

## D) Parity

- **Economic closes** (exit_attribution-style) **==** **unified terminal closes** for the same cohort, **0 tolerance**, unless CSA documents a named exception class (none approved here).

## E) Fail-closed truth

- Missing legs → **BLOCKED** / **PARTIAL** with explicit reason codes (no silent drops).
- Dashboards must not imply certification when strict eval is blocked.

## F) Proof modes

1. **CODE-COMPLETE:** Deterministic replay / reconstruction against bounded slices; must be rerunnable from repo scripts. **Vacuous forward live data does not block** code-complete work, but vacuous replay **does not** certify join quality.
2. **LIVE-FORWARD:** Required when claiming live non-vacuous certification; if forward cohort is vacuous, status must be **LIVE_FORWARD_PENDING** while code-complete may still progress.

---

*Artifacts: this file; baselines under `reports/ALPACA_BASELINE_20260326_2315Z.json`, `reports/KRAKEN_BASELINE_20260326_2315Z.json`.*
