# Phase 2 — Synthesis Approval (Multi-Model Review)

**Date:** 2026-02-18  
**Scope:** Per-signal attribution added to `score_snapshot.jsonl` and `blocked_trades.jsonl`.

## Model A (Correctness)
- `uw_composite_v2` returns `group_sums` (uw, regime_macro, other_components) and `composite_pre_clamp`.
- `score_snapshot_writer` accepts optional `weighted_contributions`, `group_sums`, `composite_pre_norm`, `composite_post_norm`; written when provided.
- `main.py` passes `composite_meta` (components, group_sums, composite_pre_clamp) into both expectancy-gate and score-below-min snapshot/blocked_trade logging.
- `log_blocked_trade` stores `attribution_snapshot` (weighted_contributions, group_sums, composite_pre_norm, composite_post_norm) in each record.

## Model B (Adversarial)
- Backward compatible: all new fields optional; old readers unchanged.
- Possible gap: raw (unweighted) signal values not logged; only weighted contributions. Acceptable for edge discovery (weight × value is what drives score).

## Model C (Schema + Backward Compatibility)
- Snapshot: new keys are additive; existing `composite_score` / `components` unchanged.
- Blocked trades: `attribution_snapshot` is a single JSON object; no schema version bump required.
- Pipeline: `blocked_signal_expectancy_pipeline.py` prefers `weighted_contributions` / `group_sums` from record when present, falls back to `signal_group_scores` / `_component_group_sums(comps)` for old data. Component key sets aligned with composite (flow, dark_pool, insider, whale, event, regime, market_tide, calendar, motif_bonus, etc.).

## Model D (Synthesis)
- **Approved.** All models contributed; schema consistent; backward compatible; attribution present on both snapshot and blocked_trades. Safe to commit.

**Commit message (suggested):**  
`Attribution: per-signal group_sums and composite pre/post norm in snapshot and blocked_trades (multi-model Phase 2)`
