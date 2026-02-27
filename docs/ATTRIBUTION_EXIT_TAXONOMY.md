# Exit Reason Taxonomy & Component Mapping (Phase 4)

**Schema version:** 1.0.0  
**Purpose:** Stable exit_reason_code and mapping to attribution components for blame separation and tuning.

---

## 1. Exit reason taxonomy (stable codes)

| exit_reason_code     | Description |
|----------------------|-------------|
| **hold**             | Do not exit; exit score below threshold. |
| **intel_deterioration** | Thesis invalidated or score deterioration ≥ 0.35. |
| **stop**             | Volatility expansion (vol_exp ≥ 0.8 and score ≥ 0.6) or earnings_risk and score ≥ 0.5. |
| **replacement**      | Exit score ≥ 0.75 (rotate to better idea). |
| **profit**           | Exit score ≥ 0.55 (take profit). |
| **time_exit**        | Time-based exit (e.g. TIME_EXIT_MINUTES, STALE_TRADE_EXIT_MINUTES). |
| **trail_stop**       | Trailing stop hit. |
| **stop_loss**        | Hard stop loss (e.g. P&L ≤ -1%). |
| **displacement**     | Displaced by stronger signal. |
| **other**            | Fallback when reason does not match above. |

---

## 2. Mapping: exit reason → components

| exit_reason_code     | Primary components (high contribution) |
|----------------------|----------------------------------------|
| **intel_deterioration** | exit.score_deterioration, exit.thesis_invalidated |
| **stop**             | exit.vol_expansion, exit.thesis_invalidated (earnings_risk), exit.score_deterioration |
| **replacement**      | Aggregate of flow_det, score_det, regime_shift, etc. (exit score ≥ 0.75) |
| **profit**           | Same components; exit score 0.55–0.75 |
| **time_exit**        | Not in exit score; structural trigger (time). |
| **trail_stop**       | Not in exit score; structural trigger (price). |
| **stop_loss**        | Not in exit score; structural trigger (P&L). |
| **displacement**     | exit.score_deterioration, replacement_candidate. |

**Note:** time_exit, trail_stop, stop_loss, displacement are set by the main exit loop (build_composite_close_reason or similar), not by `compute_exit_score_v2`. When we persist the exit snapshot we use the same exit_reason_code taxonomy; the code that sets the reason (e.g. "time_exit_150") is normalized to "time_exit" via _normalize_exit_reason.

---

## 3. Exit attribution components (Phase 1 shape)

Every exit snapshot includes **attribution_components** with:

| signal_id | source | description |
|-----------|--------|-------------|
| exit.flow_deterioration | exit | entry_flow − now_flow (clamped 0–1) |
| exit.darkpool_deterioration | exit | \|entry_dp\| − \|now_dp\| (clamped) |
| exit.sentiment_deterioration | exit | 1 if sentiment flipped to NEUTRAL or changed |
| exit.score_deterioration | exit | (entry_v2_score − now_v2_score) / 8 |
| exit.regime_shift | exit | 1 if regime changed |
| exit.sector_shift | exit | 1 if sector changed |
| exit.vol_expansion | exit | (realized_vol_20d − 0.35) / 0.25 (clamped) |
| exit.thesis_invalidated | exit | 1 if thesis_flags.thesis_invalidated |
| exit.earnings_risk | exit | 1 if thesis_flags.earnings_risk (0 weight in score) |
| exit.overnight_flow_risk | exit | 1 if thesis_flags.overnight_flow_risk (0 weight) |

**Invariant:** exit_score == sum(contribution_to_score) over attribution_components (after scaling).

---

## 4. Known coarse areas (to refine later)

- **earnings_risk / overnight_flow_risk:** In components for transparency but currently 0 weight in the weighted sum. If we add weight later, attribution will already be present.
- **Time / trail / stop_loss:** Not decomposed into exit score components; they are structural triggers. For "which component led to this exit" we still have exit_reason_code; sub-coding (e.g. time_exit_150) can be stored in exit_reason (free text) alongside exit_reason_code.
- **Replacement candidate:** replacement_candidate and replacement_reasoning are in the exit record but not as attribution components; could add exit.replacement_signal_strength later.
- **Post-exit excursion:** exit_quality_metrics.post_exit_excursion is not yet computed (requires bars after exit_ts).

---

## 5. Entry vs exit blame separation

- **Entry snapshot:** ENTRY_DECISION / ENTRY_FILL with attribution_components (entry composite).
- **Exit snapshot:** EXIT_DECISION / EXIT_FILL with attribution_components (exit components), exit_reason_code, decision_id.
- **Exit quality metrics:** mfe, mae, time_in_trade_sec, profit_giveback, exit_efficiency (saved_loss, left_money).

Same trade_id links entry snapshot, exit snapshot, and exit_quality_metrics so we can ask: bad entry (low entry score, bad components) vs good entry exited badly (high giveback, left_money).
