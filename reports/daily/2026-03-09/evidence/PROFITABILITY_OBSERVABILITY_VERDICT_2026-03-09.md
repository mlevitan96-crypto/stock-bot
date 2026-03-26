# Profitability Observability Verdict — Owner Synthesis

**Date:** 2026-03-09  
**Artifacts:** TELEMETRY_COVERAGE_AUDIT_2026-03-09.md, PROFITABILITY_INTELLIGENCE_GAPS_2026-03-09.md, SIGNAL_GRANULARITY_AND_GAPS_2026-03-09.json

---

## 1. Can we fully explain profitability today?

**Yes, with documented gaps.** We can:

- Reconstruct **entry** (attribution, signal_context, blocked_trades) and **exit** (exit_attribution, exit_reason, exit_quality_metrics, exit_decision_trace).
- Reconstruct **hold-period** state (exit_decision_trace: unrealized_pnl, composite_score, signal_decay, exit_conditions, signals.UW, volatility, trend).
- Explain **why we made or lost money** per trade: MFE, MAE, profit_giveback, signal state at exit, and (via trace) signal state at peak unrealized.
- Reconstruct **suppression** (blocked_trades, gate logs, B2 suppressed).

We **cannot** fully explain without joining trace + exit_attribution: sizing rationale, liquidity at exit, crowding, and post-exit price path are not in standard streams. For **paper** profitability, explanation is **sufficient**.

---

## 2. What telemetry is missing?

| Priority | Missing | Impact |
|----------|---------|--------|
| **Required** | Trace write failure detection | Trace is fail-open; we do not count or alert on write failures. |
| **Required** | None else for paper | Current set supports "why did we make/lose money?" |
| **Nice to have** | Latency at decision time | Score computation time, API latency, "time from signal to order" not captured. |
| **Nice to have** | Data freshness at decision time | "UW cache was stale at decision" not logged. |
| **Nice to have** | Cron/scheduler execution log | Append-only audit of "cron X ran at Y" (start/end/success). |
| **Nice to have** | Entry trigger type | "Score crossed threshold" vs "displacement" vs "scheduled" per entry. |

---

## 3. What signal granularity must be added?

| Priority | Add | Reason |
|----------|-----|--------|
| **Required** | None | All exit-contributing signals are in exit_decision_trace or exit_conditions (SIGNAL_GRANULARITY_AND_GAPS: fail_closed_status PASS). |
| **Nice to have** | Populate `signals.momentum` in trace | Momentum is used in exit urgency; currently trace has momentum: {}. |
| **Nice to have** | `beta_vs_spy` in trace | Volatility family; available in v2_inputs, not in trace. |
| **Nice to have** | UW velocity (flow change rate) | Would improve "why did flow reverse?" explainability. |

---

## 4. What new signals (if any) are justified?

| Signal | Justified? | Notes |
|--------|------------|--------|
| **Liquidity** (spread, depth, volume at order) | Yes, for live | For paper, optional. For live, would explain slippage and illiquid exits. |
| **Correlation / crowding** | Later | Would explain regime-like drawdowns; not required for single-strategy paper. |
| **Time-of-day / session segment** | Optional | Derivable from ts; first-class segment would help "open vs close" analysis. |
| **Vol-of-vol** | Optional | Explainability for vol regime; not in current exit logic. |
| **Post-exit price path** | Optional | Systematic "price N min after exit" for counterfactuals; replay can compute. |

**Justified for next phase:** (1) Trace write failure detection (telemetry). (2) Populate momentum in trace (granularity). (3) Liquidity at exit when moving toward live.

---

## 5. What should NOT be added yet?

- **Do not** add real-time latency SLAs or high-frequency telemetry before stabilizing trace and exit attribution consumption.
- **Do not** add new signal sources (e.g. alternative data) until UW + exit trace are fully consumed in learning/review pipelines.
- **Do not** add "regime_shift_event" log until we have a clear consumer (e.g. regime transition analytics).
- **Do not** chase correlation/crowding until we have multi-symbol or multi-strategy need.

---

## 6. Priority-ranked action list

### Required (do first)

1. **Add trace write failure detection:** On append_exit_decision_trace failure, log_event("exit_decision_trace", "write_failed", ...) and optionally increment a counter or write to a small audit file. Ensures we do not silently lose samples.
2. **No other required actions** for paper profitability observability.

### Nice to have (backlog)

3. Populate `signals.momentum` in exit_decision_trace from ExitSignalModel when available.  
4. Add `beta_vs_spy` to trace volatility payload.  
5. Log "entry_trigger_type" (score_crossed / displacement / scheduled) on attribution or signal_context.  
6. Optional: data_freshness_at_decision (e.g. uw_cache_age_sec at entry/exit).  
7. Optional: cron_execution.jsonl (run_id, schedule_name, start_ts, end_ts, success).

### Explicit non-actions

- No new signal *sources* until current signals are fully used in learning.  
- No latency SLAs or HF telemetry in this phase.  
- No regime_shift_event stream until there is a defined consumer.  
- No correlation/crowding telemetry until multi-strategy or crowding logic exists.

---

## 7. Verdict

**Profitability observability is sufficient for paper trading.** We can know why we make or lose money at the level of entry, hold, and exit; peak unrealized and signal state at peak are reconstructable from exit_decision_trace. Gaps are documented and prioritized; the only **required** follow-up is trace write failure detection. All other items are nice-to-have or explicit non-actions.

**Owner acceptance:** Proceed with exit learning and profitability reviews using current telemetry; implement trace write failure detection in the next deployment window.
