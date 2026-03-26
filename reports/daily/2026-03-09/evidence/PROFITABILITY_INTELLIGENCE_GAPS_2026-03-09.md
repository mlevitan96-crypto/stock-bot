# Profitability Intelligence Gaps — CSA + Strategic

**Date:** 2026-03-09  
**Purpose:** Economic decision observability and strategic "what are we missing?" FAIL CLOSED if any profitable window cannot be reconstructed or any loss cannot be causally explained.

---

## Part A — Economic decision observability (CSA)

### A.1 Entry

| Question | Can we? | Evidence / gap |
|----------|--------|-----------------|
| Reconstruct the decision *as it happened*? | Partially | Attribution has entry_score, symbol, side, ts; signal_context has full signal state at decision. Blocked trades in state/blocked_trades.jsonl with reason and score. |
| Know what information was available at that moment? | Partially | Intel snapshot entry (intel_snapshot_entry.jsonl) when capture runs; UW cache at poll time. We do not log "exact cache slice used for this entry decision" with timestamp. |
| Explain why this decision made or lost money? | Only after exit | Entry alone cannot explain PnL; we need exit attribution + exit_quality_metrics (MFE, MAE, giveback) and exit_decision_trace for "signal at peak vs at exit". |

**Gap:** Entry decision is reconstructable from attribution + signal_context + blocked_trades; we do not persist "the exact composite inputs (v2_uw_inputs, regime) at the moment of go/no-go" in a single record per candidate.

---

### A.2 Sizing

| Question | Can we? | Evidence / gap |
|----------|--------|-----------------|
| Reconstruct sizing decision? | Partially | Position size is config (POSITION_SIZE_USD); orders log and attribution have qty. We do not log "why this size" (e.g. risk limit, diversification cap) per order. |
| Explain why this size? | No | No dedicated "sizing_reason" or "sizing_inputs" (available buying power, max_positions, theme notional) per fill. |

**Gap:** Sizing is deterministic from config; we cannot reconstruct "what constraints were binding" at sizing time without re-running risk logic.

---

### A.3 Hold

| Question | Can we? | Evidence / gap |
|----------|--------|-----------------|
| Reconstruct hold-period state over time? | Yes | Exit decision trace: per-position samples (unrealized_pnl, composite_score, signal_decay, exit_conditions, signals.UW, volatility, trend) every N sec. |
| Know what information was available at each moment? | Yes | Trace has signals and exit_conditions at sample time. |
| Explain why we held vs exited? | Yes | exit_eligible and exit_conditions show why we did not exit; when we do exit, exit_attribution has exit_reason. |

**Gap:** Trace is sampled (default 60s); between samples we do not have continuous state. For "peak unrealized" we have trace samples so we can approximate peak from max(unrealized_pnl) over samples.

---

### A.4 Exit

| Question | Can we? | Evidence / gap |
|----------|--------|-----------------|
| Reconstruct the exit decision as it happened? | Yes | Exit attribution: exit_reason, exit_reason_code, v2_exit_reason; exit_decision_trace has last sample before exit (if trace written that cycle). |
| Know what information was available at exit? | Yes | Exit attribution has v2_exit_*, exit_quality_metrics; trace has signal state at sample time. |
| Explain why this exit made or lost money? | Partially | MFE, MAE, profit_giveback answer "good entry exited badly?" We have signal state at exit. We do not have "signal state at peak unrealized" in the same trade record unless we join trace to exit by trade_id and take max(unrealized_pnl) row. |

**Explicit verification:**

- **Peak unrealized vs exit timing:** Yes — trace gives unrealized_pnl over time; we can find peak sample and compare to exit_ts.
- **Signal state at peak:** Yes — trace row with max(unrealized_pnl) has signals and exit_conditions at that time.
- **Exit eligibility timeline:** Yes — trace has exit_eligible and exit_conditions per sample.
- **Post-exit counterfactuals:** Partial — we have exit_quality_metrics and post_exit_excursion (if bars provided); we do not systematically log "price N minutes after exit" for all trades.

**Gap:** Post-exit price path is not in a standard telemetry stream; backtests/replay can compute it from bars.

---

### A.5 Suppression (CI, max_positions)

| Question | Can we? | Evidence / gap |
|----------|--------|-----------------|
| Reconstruct why a trade was suppressed? | Yes | blocked_trades.jsonl (reason, score); gate.jsonl; B2 suppressed log. |
| Know what information was available at suppression time? | Partially | Blocked record has score/symbol; we do not always have full signal snapshot for "would-have-been entry". |

**Gap:** Blocked trades have reason and score; full "signal state at block" is in signal_context only if that code path logs it.

---

## Part B — Strategic "what are we missing?" (Strategic Analyst + Adversarial)

### B.1 Dimensions of market behavior we may be blind to

- **Regime shifts:** Regime is in composite and exit (regime_label, market_regime). We do not have a dedicated "regime_shift_event" log (e.g. transition RISK_ON → RISK_OFF with timestamp). Regime changes are implicit in snapshot/trend over time.
- **Liquidity cliffs:** We do not log spread, depth, or volume-at-time-of-order per execution. Liquidity is not a first-class signal in the registry.
- **Crowding:** We do not have correlation/crowding metrics per symbol or portfolio-level "crowding score" in telemetry. Signal correlation cache exists but is not in exit_decision_trace.
- **Time-based decay:** Hold_minutes and time_in_trade are captured; "time-of-day at entry/exit" is derivable from ts. We do not have "session segment" (open, mid, close) or "day-of-week" as logged dimensions in trace.
- **Volatility-of-volatility:** Realized vol (20d, 5d) is in trace and v2_inputs; we do not log vol-of-vol or VIX term structure at decision time.

### B.2 Signals that would improve *explainability* (not just performance)

- **Why did we enter at this exact time?** — Log "trigger" (e.g. score crossed threshold this cycle, or displacement, or scheduled). Today we have score and gate; we do not have "trigger type" per entry.
- **Why did we exit at this exact time?** — We have exit_reason and exit_conditions; adding "primary_trigger" (e.g. signal_decay vs flow_reversal vs time) is in build_composite_close_reason; full decomposition is in v2_exit_components. **Sufficient.**
- **Was the market regime different at peak vs at exit?** — Trace has trend.regime per sample; we can compare regime at peak sample vs exit sample. **Possible.**
- **Was liquidity worse at exit?** — Not captured. Adding spread or volume at exit would improve explainability for "slippage" or "illiquid exit."

### B.3 Adversarial challenges

- **Unknown unknowns:** We may be missing: (1) order book imbalance at decision time; (2) correlation of our exit with other participants (crowding); (3) news/earnings at exit (calendar is in UW but not in trace). 
- **Assumption challenge:** "Exit decision trace is representative" — it is sampled every 60s; we might miss the exact moment exit_eligible flipped. Mitigation: 60s is sufficient for "signal state at peak" approximation.
- **Lossy path:** Trace write is fail-open; we could lose samples under load. No counter or alert. **Recommendation:** Add a "trace_write_fail" log_event and optional counter.

---

## Part C — Fail-closed summary

- **Any profitable window cannot be reconstructed?** No — we have attribution, exit_attribution, trace, and exit_quality_metrics; we can reconstruct PnL and approximate peak and signal at peak.
- **Any loss cannot be causally explained?** Partially — we can explain "exit reason" and "signal state at exit"; we can approximate "signal at peak." We cannot explain "liquidity at exit" or "crowding" without new signals. For paper trading, causal explanation of loss is **sufficient** for entry/exit/signal state; gaps are in sizing rationale, post-exit price path, and liquidity/crowding.

**CSA verdict:** Economic decision observability is **sufficient for paper profitability analysis** with documented gaps (sizing rationale, trace write detection, liquidity/crowding, post-exit price stream). Strategic blind spots are documented; none are required for "can we know why we make or lose money?" at current paper-only scope.
