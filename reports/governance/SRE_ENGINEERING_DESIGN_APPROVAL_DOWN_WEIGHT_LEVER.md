# SRE/Engineering design approval: down-weight worst signal entry lever

**Date:** 2026-02-27  
**Status:** Approved (Execution/SRE persona)  
**Scope:** Board consensus change #1 — add "down-weight worst signal" as an entry-lever option; scoring changes fed into engine and tracked; no new infra; one lever at a time.

---

## Design summary

1. **Single new lever type:** When the governance loop chooses **entry** and recommendation provides a worst signal (from `top5_harmful`), the loop may apply an **entry overlay that down-weights that signal** (e.g. multiplier delta −0.05) instead of raising MIN_EXEC_SCORE. One cycle at a time; 100-trade gate; LOCK/REVERT unchanged.

2. **Data flow (all within organism):**
   - **Recommendation:** `generate_recommendation.py` already produces `top5_harmful` from `signal_effectiveness`. Add `entry_lever_type` (`"min_exec_score"` | `"down_weight_signal"`), `worst_signal_id`, `down_weight_delta` (−0.05) when weak_entry and top5_harmful present.
   - **Overlay config:** Autopilot A3 builds `overlay_config.json` with `change.signal_weight_delta: { "<component>": -0.05 }` when `entry_lever_type == "down_weight_signal"`; else current behavior (min_exec_score).
   - **Apply:** `apply_paper_overlay.py` writes `state/path_to_profitability_overlay.json` with `signal_weight_delta` (and existing entry audit fields). For entry+down_weight we do **not** bump MIN_EXEC_SCORE (stay at 2.5) so the only change is weight.
   - **Engine:** `uw_composite_v2.get_weight(component)` already uses adaptive optimizer. Add: read `state/path_to_profitability_overlay.json`; if `lever == "entry"` and `signal_weight_delta` and component in it: `weight *= (1 + delta)`, clamped to [0.25, 2.5]. No new services; no new config files beyond existing state overlay.
   - **Activation:** For entry (min_exec or down_weight), systemd drop-in sets MIN_EXEC_SCORE (for down_weight we keep 2.5). Restart stock-bot; engine reads overlay at score time.
   - **REVERT:** Autopilot A6 already removes systemd drop-in and restarts. **Addition:** Clear `state/path_to_profitability_overlay.json` (and `state/paper_overlay.env`) on REVERT so the engine does not keep applying the old delta.

3. **Component name safety:** `worst_signal_id` comes from `signal_effectiveness` (entry_attribution_components → signal_id/name). These match composite component names (e.g. options_flow, dark_pool). We only apply overlay when `worst_signal_id` is in `SIGNAL_COMPONENTS` (adaptive_signal_optimizer); otherwise fall back to min_exec_score lever.

4. **Tracking:** Overlay is recorded in `state/path_to_profitability_overlay.json` (lever, overlay_start_date, signal_weight_delta, run_tag). Effectiveness and compare use existing joined trades; attribution already includes component contributions. No new telemetry; existing loop state and board review capture the lever used.

5. **No breakage:**
   - If recommendation has no top5_harmful or entry_lever_type is min_exec_score: behavior identical to today (min_exec_score bump only).
   - If optimizer unavailable: get_weight() fallback unchanged; overlay applied on top of static weights when present.
   - REVERT clears overlay state so next cycle starts clean.

---

## Execution/SRE approval

- **No new infrastructure:** Overlay is a state file; engine reads it at weight resolution time.
- **One lever at a time:** Down-weight is an alternative entry lever, not additive to min_exec in the same cycle.
- **Stopping checks unchanged:** Same 100-trade gate, same compare, same LOCK/REVERT.
- **Rollback:** REVERT clears overlay file and drop-in; restart restores baseline.
- **Scoring in the loop:** All scoring changes go through state overlay → get_weight() → composite → gate; fully tracked and reversible.

**Approved for implementation and deployment to droplet.**
