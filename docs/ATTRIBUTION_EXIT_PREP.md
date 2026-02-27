# Exit-Side Prep (Phase 3) — For Phase 4

**Purpose:** Identify components reused in exit logic, implicit exit penalties, and where exit reasons map to score deterioration. **Do not modify exit behavior yet.**

---

## 1. Exit Logic Location (Phase 0 Map)

- **Exit evaluation:** `main.py::AlpacaExecutor.evaluate_exits()`
- **Exit score (v2):** `src/exit/exit_score_v2.py::compute_exit_score_v2()`
- **Exit attribution:** `src/exit/exit_attribution.py` (`build_exit_attribution_record`, `append_exit_attribution`)
- **Composite close reason:** `main.py::build_composite_close_reason()`

---

## 2. Components Reused or Mirrored in Exit Logic

| Entry / scoring component | Exit-side usage |
|---------------------------|-----------------|
| **UW flow / dark pool / sentiment** | `compute_exit_score_v2` uses `entry_uw_inputs` vs `now_uw_inputs`: flow_strength, darkpool_bias, sentiment. So **entry** and **now** UW are compared; deterioration (flow_det, dp_det, sent_det) drives exit score. These are **reused conceptually** but exit uses aggregated UW inputs (flow_strength, darkpool_bias), not the full UW micro-signal tree. |
| **Composite score (entry vs now)** | `score_deterioration = (entry_v2_score - now_v2_score) / 8` — single scalar. Entry and “now” scores are composite totals; the exit pipeline does **not** consume `attribution_components` (entry vs now component trees). So exit does **not** yet see which micro-signals deteriorated. |
| **Regime / sector** | `compute_exit_score_v2` uses entry_regime vs now_regime, entry_sector vs now_sector (r_shift, s_shift). Same conceptual regime/sector as entry; not yet broken into attribution components at exit. |

So: **exit reuses UW aggregates (flow_strength, darkpool_bias, sentiment) and composite score level (entry vs now), plus regime/sector.** It does **not** yet consume the full entry/exit attribution component trees. Phase 4 persistence can store exit-time attribution snapshots (same schema as entry) so that later we can analyze “which components deteriorated before this exit.”

---

## 3. Exit Penalties Currently Implicit

- **Weights in exit score:** `compute_exit_score_v2` uses fixed weights (0.20 flow_det, 0.10 dp_det, 0.10 sent_det, 0.25 score_det, 0.10 r_shift, 0.05 s_shift, 0.10 vol_exp, 0.10 thesis_bad). These are **implicit** in the formula; the function returns a single exit score and a `components` dict of raw terms (flow_deterioration, darkpool_deterioration, …), but **no signed contribution_to_score per component** in Phase 1 attribution shape. So exit “components” are raw inputs to the exit score, not yet attribution components with signal_id and contribution_to_score.
- **Recommended reason:** Exit reason (hold, intel_deterioration, stop, replacement, profit) is derived from thresholds on the exit score and sub-terms; it is **not** yet an explicit “which component triggered exit” mapping. Phase 4 can add exit attribution snapshots with the same schema (components with contribution_to_score) so that exit_reason_code can be tied to which exit components were high.

---

## 4. Where Exit Reasons Map to Score Deterioration

- **intel_deterioration:** Triggered when thesis_bad >= 1.0 or score_det >= 0.35. So “score deterioration” (entry vs now composite) and “thesis invalidated” drive this reason.
- **stop:** Triggered when vol_exp >= 0.8 and score >= 0.6, or earnings_risk >= 1.0 and score >= 0.5. So volatility expansion and earnings_risk (from thesis_flags) drive this.
- **replacement / profit:** Triggered by exit score level (>= 0.75, >= 0.55). So aggregate exit score drives these; the breakdown (flow_det, score_det, etc.) is in the `components` dict but not yet in Phase 1 attribution form.

To support “which components preceded this exit reason,” Phase 4 should store at exit decision time an **exit attribution snapshot** (same schema as entry): list of components with signal_id and contribution_to_score for the **exit** score (e.g. exit.flow_deterioration, exit.score_deterioration, …). Then we can segment by exit_reason_code and by component pattern.

---

## 5. Summary for Phase 4

- **Entry:** Already have full attribution_components in composite result; Phase 4 persists them at ENTRY_DECISION / ENTRY_FILL with decision_id and schema_version.
- **Exit:** Today exit has a `components` dict (flow_deterioration, score_deterioration, …) but not Phase 1–shaped attribution (signal_id, contribution_to_score, quality_flags). Phase 4 should:
  - Build an **exit attribution snapshot** (same schema as entry snapshot) from `compute_exit_score_v2` output: each exit term as a component with signal_id (e.g. exit.flow_deterioration, exit.score_deterioration) and contribution_to_score (signed), so exit_score == sum(contributions).
  - Persist exit snapshot at EXIT_DECISION / EXIT_FILL with exit_reason_code and link to trade_id.
- **No change to exit logic in Phase 3:** Only observation and this prep doc.
