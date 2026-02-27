# Multi-Model Signal Attribution Plan

## MODEL A (Primary Investigator)

**What per-signal fields must be logged to understand edge?**
- Per-component **weighted contributions** (weight × raw_value) for each composite component (flow, dark_pool, insider, iv_skew, whale, regime, congress, etc.).
- **Group sums**: uw (options_flow + dark_pool + insider + whale_persistence + event_alignment), regime_macro (regime_modifier + market_tide + calendar_catalyst + temporal_motif), other_components (remaining).
- **Pre-normalization composite** (sum of components × freshness + whale_boost, before clamp).
- **Post-normalization composite** (final clamped score used by gates).
- Optional: **raw signal values** (conviction, dp_strength, etc.) for sanity checks.

**Failure modes that could hide signal-level edge?**
- Components logged under different key names than used in composite (schema drift).
- Stale cache causing same components for many symbols (no variance → no correlation with pnl).
- Score snapshot only at expectancy gate (missing score_below_min candidates) if not also emitted at score gate.
- blocked_trades storing a different component schema (e.g. attribution keys) than composite components.

**Tests to confirm signal integrity?**
- After logging: join replay_results with snapshot/blocked_trades; assert group_sums and components exist and sum ≈ composite_pre_norm.
- Spot-check: for N symbols, recompute composite from components and compare to logged composite_score.

---

## MODEL B (Adversarial Reviewer)

**What per-signal fields must be logged?**
- Same as A, plus: **timestamp**, **symbol**, **block_reason**, and **which gate** (score_gate vs expectancy_gate) so we can filter and avoid double-counting.

**Failure modes that could hide edge?**
- **Survivorship**: only blocked trades are logged; executed trades may have different signal distribution → correlation on blocked set may not generalize.
- **Lookahead**: if “raw” values are post-adjustment (e.g. after survivorship or quality), we’re not measuring the composite’s true inputs.
- **Missing data**: defaulted/missing components written as 0; winners vs losers may differ in “missing” rate, not in value → spurious correlation.
- **Single snapshot per symbol per cycle**: if multiple blocks for same symbol, only one snapshot may be stored.

**Tests?**
- Assert no duplicate (symbol, ts) in snapshot when same symbol blocked twice in one cycle.
- Check fraction of “missing” or “default” per component for winners vs losers in replay.

---

## MODEL C (Forensic Auditor)

**What per-signal fields must be logged?**
- **weighted_contributions** (must match composite formula: same keys as WEIGHTS_V3 / composite result).
- **group_sums** (derived from same component set; backward compatible if we add new components later).
- **composite_pre_norm**, **composite_post_norm** (for audit: pre = before clamp, post = final).
- **Schema version** or **attribution_schema_version** for backward compatibility.

**Failure modes?**
- Stale caches (uw_flow_cache, expanded_intel) making components identical across symbols.
- Clock skew: snapshot ts vs blocked_trades timestamp mismatch → join fails.
- File path differences (logs/ vs state/) so that local vs droplet paths differ.

**Tests?**
- Checksum: sum(weighted_contributions) + whale_boost ≈ composite_pre_norm (within float tolerance).
- Load oldest and newest snapshot; confirm schema keys unchanged.

---

## MODEL D (Synthesis)

**Reconciled list of per-signal fields to log:**
1. **weighted_contributions** (components dict from composite).
2. **group_sums** (uw, regime_macro, other_components).
3. **composite_pre_norm** (before clamp), **composite_post_norm** (final score).
4. **symbol**, **ts**, **block_reason** (and gate type if available).
5. Optional: **raw_signal_values** where easily available without extra I/O.

**Failure-mode summary:** Schema drift, stale cache, survivorship bias, missing/default masking, path/ts mismatch.

**Test summary:** (1) Sum of components ≈ composite_pre_norm. (2) Join replay with attribution by symbol/ts. (3) No duplicate (symbol, ts) in snapshot. (4) Backward compatibility: new fields optional so old readers still work.
