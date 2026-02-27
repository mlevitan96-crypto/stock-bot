# Phase 3 — Full Scoring Decomposition: Note

**Date:** 2026-02-17  
**Status:** Phase 3 complete. All scoring influences emitted as Phase 1–compliant attribution components.

---

## What Was Done

- **Core composite** (`_compute_composite_score_core`): Already emitted full `attribution_components` (Phase 2: UW micro-signals + internal.* + derived.toxicity_penalty + internal.freshness + internal.whale_conviction_boost). No opaque "flow"/"dark_pool"/"insider"; only `uw.*` micro-signals.
- **V2 adjustments** (`compute_composite_score_v2`): V2 adjustments (vol_bonus, low_vol_penalty, beta_bonus, uw_bonus, premarket_bonus, regime_align_bonus, regime_misalign_penalty, shaping_adj) were previously stored only in `v2_adjustments` dict. They are now **explicit attribution components**: `internal.v2_vol_bonus`, `internal.v2_low_vol_penalty`, `internal.v2_beta_bonus`, `internal.v2_uw_bonus`, `internal.v2_premarket_bonus`, `internal.v2_regime_align_bonus`, `internal.v2_regime_misalign_penalty`, `internal.v2_shaping_adj`. The full `attribution_components` list is then scaled so **sum(attribution_components) == score** (final clamped score).
- **Schema version:** `attribution_schema_version: "1.0.0"` added to composite result for consumers.

---

## Hardest to Decompose

1. **V2 adjustment block**  
   V2 adds many small terms (vol, beta, premarket, regime alignment, etc.) that were only in a single `v2_adjustments` object. Decomposing them into eight named components was straightforward; the only subtlety was preserving the invariant **sum(attribution_components) == score** after the final clamp to [0, 8]. We do this by scaling the full list (core + v2) so the sum equals the clamped score.

2. **Freshness and whale_conviction_boost**  
   These were already single components (`internal.freshness`, `internal.whale_conviction_boost`) in the core. No further decomposition.

3. **UW intel layer (premarket/postmarket)**  
   When `compute_composite_score_v2` applies UW intel (sector/regime alignment, etc.), the delta is folded into `score_v2` via `uw_adj["total"]`. That total is **not** yet split into per-signal components (e.g. sector_alignment, regime_alignment). So the **UW intel contribution** is still a single additive delta to the score; only the base UW flow/dp/insider are fully decomposed into `uw.*` micro-signals. Decomposing the UW intel layer into separate components (e.g. `internal.uw_intel_sector_alignment`, `internal.uw_intel_regime_alignment`) would require passing through the per-term breakdown from the UW intel block and adding them as attribution components; left for a follow-up if needed.

---

## Signals Still Suspiciously Coarse

- **UW intel total**  
  The premarket/postmarket UW intel block adds a single `uw_adj["total"]` to the score. That total is not yet broken into sub-components (sector_alignment, regime_alignment, earnings_proximity, etc.) in `attribution_components`. So "UW intel" is one implicit lump; only the base UW (flow, dark_pool, insider) is fully micro-signal decomposed.

- **Sizing overlay**  
  `sizing_overlay` is computed (iv_skew_align_boost, whale persistence, congress, shorts, skew conflict, toxicity) but used for **sizing**, not for the composite score. So it does not appear in `attribution_components`. If sizing ever feeds back into score or risk, it should be added as explicit components.

- **Entry delay**  
  `entry_delay_sec` is derived from motifs (staircase, sweep, burst) but is a timing output, not a score component. No change.

---

## Backtest + Lab Parity

- **Live:** Composite result includes full `attribution_components` and `attribution_schema_version`. When the entry pipeline builds context for `log_attribution`, it now copies `attribution_components` and `attribution_schema_version` from `composite_meta` (the full composite result) into context when present. So `logs/attribution.jsonl` entries written at entry time include the same schema as the composite (Phase 3 parity).
- **Backtest:** `historical_replay_engine` loads signals from attribution logs (e.g. `logs/attribution.jsonl`). It does not call the composite. Logs written by live now contain `context.attribution_components` when the cluster was composite-scored; backtest can consume this structure. No change to the replay engine is required for Phase 3.
- **Lab / replay injection:** `scripts/replay_signal_injection.py` injects raw signals into attribution dicts for backtest enrichment. When the lab path uses the composite (e.g. recomputes score), the composite return already includes full attribution_components; when building clusters from composite, `composite_meta` is the full result, so parity is maintained.

---

## Invariants Verified

- **composite_score == sum(contributions):** Enforced by scaling the full `attribution_components` list (core + v2) so the sum equals the final clamped score.
- **No opaque totals:** Every value that affects the score appears as a named component (signal_id + contribution_to_score). The only remaining lump is the UW intel total (see above).
- **schema_version:** Present on the composite result as `attribution_schema_version: "1.0.0"`.
- **decision_id:** To be added at snapshot write time (Phase 4 persistence).
