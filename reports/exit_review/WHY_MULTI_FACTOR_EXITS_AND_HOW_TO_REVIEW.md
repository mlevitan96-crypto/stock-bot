# Why Multi-Factor Exits Matter and How to Review Them

**Context:** Exits were appearing in logs as only `signal_decay(0.xx)` despite the codebase having a full multi-factor exit model. We were losing money daily in part because (1) exit attribution was missing the other factors, and (2) the decision path was dominated by a single decay check. This doc explains what was wrong, what’s fixed, and how to review exits so they improve.

---

## 1. Why You Only Saw “Signal Decay”

### Bug (now fixed)

- **`compute_exit_score_v2`** returns 5 values: `(exit_score, components, reason, attribution_components, reason_code)`.
- **main.py** was unpacking those 5 values, but **`src/exit/exit_score_v2.py`** only returned 3. That raised `ValueError` inside the exit-intel `try` block, which was caught by a broad `except`, so **`exit_intel_by_symbol` was never set** for any symbol.
- On close, **metadata["v2_exit"]** was therefore empty, so **`log_exit_attribution`** wrote records with no `v2_exit_components` or `v2_exit_score`. The only thing left in the composite close reason was **signal_decay**, which is set later in the same loop when `decay_ratio < decay_threshold`.

**Fix:** `exit_score_v2.py` now returns all 5 values (including attribution_components and reason_code). After deploy, new closes will have full v2 exit components in `logs/exit_attribution.jsonl` and in the last-5-trades report.

---

## 2. What Multi-Factor Exit Signals Exist

The system has **three** exit-decision layers; only the last one was both triggering often and visible in logs.

### A. Exit pressure v3 (multi-factor, opt-in)

- **Env:** `EXIT_PRESSURE_ENABLED=1` (or `true` / `yes`).
- **Module:** `src/exit/exit_pressure_v3.compute_exit_pressure`.
- **Inputs:** entry vs now scores, UW inputs (flow, darkpool, sentiment), regime, sector, vol, PnL, high water, age.
- **Output:** pressure score, decision (e.g. CLOSE_NORMAL, CLOSE_URGENT), component list, close_reason, exit_reason_code.
- **Use:** If decision is CLOSE_* and hold floor is satisfied, position is added to close list and the loop continues (so signal_decay is not the only label).

### B. V2 exit score (multi-factor, always computed, high bar to trigger)

- **Module:** `src/exit/exit_score_v2.compute_exit_score_v2`.
- **Components:** flow_deterioration, darkpool_deterioration, sentiment_deterioration, score_deterioration, regime_shift, sector_shift, vol_expansion, thesis_invalidated, earnings_risk, overnight_flow_risk.
- **Weights (into 0–1 score):** flow 20%, score_det 25%, sentiment 10%, darkpool 10%, regime_shift 10%, vol_exp 10%, thesis_invalidated 10%, sector_shift 5%.
- **Trigger:** Only adds to close if **v2_exit_score >= 0.80** (very high). So in practice, most closes were not driven by this path.
- **Attribution:** Now that the unpack bug is fixed, this block always populates **exit_intel_by_symbol[symbol]** with v2_exit_components and reason_code, so they are written to exit_attribution even when the actual close is triggered by signal_decay.

### C. Binary checks (what was firing and visible)

- **Order in code:** stop_loss → **signal_decay** (decay_ratio < decay_threshold) → profit_target → trail_stop.
- **Signal decay:** Uses `get_effective_decay_threshold(exit_regime, base=0.60)` and variant `decay_ratio_threshold`; if `current_composite_score / entry_score < threshold`, we set `exit_signals["signal_decay"]` and later `close_reason = build_composite_close_reason(exit_signals)`. So the **only** exit signal often present in `exit_signals` when we closed was signal_decay, and that’s what you saw.

Other signals (flow_reversal, drawdown, momentum_reversal, regime_protection, stale_*, etc.) are supported by `build_composite_close_reason` but only appear in the string when they’re set earlier in the loop. If the loop never sets them (e.g. exit pressure and v2 trigger are skipped or don’t fire), the composite reason stays “signal_decay(0.xx)”.

---

## 3. Why We Should Review Exits

- **P&L:** Daily losses are partly from exiting too early or on a single factor (decay) instead of a blend (flow, regime, vol, score deterioration).
- **Visibility:** Without v2_exit_components in the log, we couldn’t see which of flow/regime/score_det/etc. were actually high at exit; that’s fixed for new runs.
- **Tuning:** Exit review (effectiveness, giveback, counterfactuals) needs rich exit reasons and components so we can tune weights and thresholds (decay, v2, pressure) instead of guessing.

---

## 4. How to Review Exits (concrete steps)

| Action | Where / how |
|--------|-----------------|
| **1. Confirm v2 exit in logs** | After deploying the exit_score_v2 fix, run `scripts/report_last_5_trades.py` on the droplet. You should see **v2_exit_components** and **v2_exit_score** populated for new closes. |
| **2. Enable multi-factor trigger (optional)** | Set **EXIT_PRESSURE_ENABLED=1** on the droplet so CLOSE_NORMAL/CLOSE_URGENT can trigger from pressure, not only from signal_decay. Thresholds: EXIT_PRESSURE_NORMAL (default 0.55), EXIT_PRESSURE_URGENT (default 0.80). |
| **3. Lower v2 exit bar (optional)** | In `main.py`, the v2 trigger is `if float(v2_exit_score) >= 0.80`. You can lower (e.g. 0.65) so more exits are explicitly “v2_exit(reason)” and attribution shows the full component mix. |
| **4. Run effectiveness reports** | `scripts/analysis/run_effectiveness_reports.py` (e.g. `--last-n 200`) on droplet; use **exit_effectiveness.json** and **entry_vs_exit_blame** to see which exit reasons and components correlate with loss/giveback. |
| **5. Use existing exit review pipeline** | Bar-based grid search and board review: see **reports/exit_review/EXIT_IMPROVEMENT_PLAN.md** (parameter grid, simulation, ranking, PROMOTE_TOP_CONFIG). |
| **6. Tune decay threshold** | `board/eod/exit_regimes.get_effective_decay_threshold` and variant `decay_ratio_threshold` / `min_hold_minutes_before_decay_exit`. Softer threshold = fewer pure signal_decay exits; harder = more holds. |

---

## 5. Summary

- **Why only signal_decay:** Unpack bug in exit intel path prevented v2 exit data from being stored; composite close reason then only had signal_decay from the binary check.
- **Fix:** `exit_score_v2` now returns (score, components, reason, attribution_components, reason_code); exit attribution will log full v2 components for every close.
- **Why review exits:** To reduce daily losses by making exits multi-factor (pressure/v2) and data-driven (effectiveness, giveback, grid search).
- **How:** Deploy the fix, optionally enable EXIT_PRESSURE and/or lower v2 threshold, run last-5-trades and effectiveness reports, and follow EXIT_IMPROVEMENT_PLAN for grid and board review.
