# Alpaca Telegram — Trade-Count Milestones (Phase 1)

**Mission:** One-time alerts when TRADES_FROZEN reaches key trade-count thresholds.  
**Authority:** CSA, SRE. READ-ONLY.  
**Date:** 2026-03-18.

---

## 1. Milestones (Configured)

| Id  | Trade count | Meaning | Next unlocked action |
|-----|-------------|---------|----------------------|
| **T1** | 100  | Data pipeline liveness confirmed | Basic PnL/regime analysis; loss causality on small set. |
| **T2** | 500  | Minimum viable dataset reached | Full loss causality; counterfactual sampling; profit discovery viable. |
| **T3** | 2000 | Full quant inference unlocked | Full counterfactuals; 30–60 min profit lab; robustness; board packet. |

---

## 2. One-Time Semantics

- Each milestone **fires at most once** per deployment/state file.
- **State persistence:** Persist which thresholds have already been alerted (e.g. `state/alpaca_telegram_milestones.json` or equivalent) so that:
  - On a run that produces TRADES_FROZEN with N rows, compare N to T1, T2, T3.
  - For each threshold where N ≥ threshold and the threshold has **not** yet been recorded as “alerted”, send the alert and then record that threshold as alerted.
- **Idempotent:** Re-running the pipeline with the same or larger TRADES_FROZEN does not re-send alerts for thresholds already recorded.

---

## 3. State File (Recommended)

- **Path:** `state/alpaca_telegram_milestones.json`
- **Schema (example):**
  ```json
  {
    "trade_count_milestones_sent": [100, 500],
    "last_trade_count": 500,
    "last_updated_utc": "2026-03-18T12:00:00+00:00"
  }
  ```
- **Logic:** After building TRADES_FROZEN, read current trade count. For each threshold in [100, 500, 2000], if trade_count >= threshold and threshold not in `trade_count_milestones_sent`, send Telegram alert and append threshold to `trade_count_milestones_sent`; write file.

---

## 4. Coverage vs MEMORY_BANK Bar

- **MEMORY_BANK bar:** min_trades 200, min_final_exits 200, min join coverage 98% (see ALPACA_QUANT_JOIN_COVERAGE, pipeline defaults).
- Each alert should include whether current run **meets** or **does not meet** the bar (e.g. “Coverage: below bar (join 0%, override used)” or “Coverage: meets bar”). See ALPACA_TELEGRAM_MESSAGE_FORMAT.md.
