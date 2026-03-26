# Alpaca Diagnostic Promotion — End-of-Window Review

**Status:** **PENDING** — evaluation window not closed at document creation (**2026-03-20**).

**Tag:** `PROMOTED_DIAGNOSTIC_ALPACA_SCORE_DETERIORATION_EMPHASIS`

---

## When to fill this in

After **48–72 trading hours** (see [ALPACA_DIAGNOSTIC_PROMOTION_EVAL_CRITERIA.md](./ALPACA_DIAGNOSTIC_PROMOTION_EVAL_CRITERIA.md)):

1. Slice `logs/exit_attribution.jsonl` to **post-`activated_utc`** rows (`state/alpaca_diagnostic_promotion.json`).
2. Run focused PnL + attribution review (mean loss, drawdown, `exit_reason_code` mix, `v2_exit_components` emphasis on `score_deterioration`).
3. Record decision: **KEEP** | **MODIFY** | **REVERT**.

---

## Template (complete after window)

### Metrics (post-deploy vs baseline)

| Metric | Baseline | Window |
|--------|----------|--------|
| Trades (n) | | |
| Mean pnl (all) | | |
| Mean pnl (losers only) | | |
| % `intel_deterioration` | | |
| % `hold` | | |

### Decision

| Field | Value |
|-------|--------|
| **Decision** | A) KEEP / B) MODIFY / C) REVERT |
| **Rationale** | |
| **Next action** | |

---

*Placeholder — update after evaluation window completes.*
