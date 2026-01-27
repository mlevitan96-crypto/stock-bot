# Alpha Discovery Ready — 2026-01-26

**Generated:** 2026-01-27

---

## Live Changes

1. **Thesis + feature snapshot (mandatory)**
   - **`telemetry/thesis_tags.py`:** `derive_thesis_tags(snapshot)` — flow/dark pool/premarket/earnings/congress/insider/regime/vol tags. Missing => `None`.
   - **`telemetry/feature_snapshot.py`:** `build_feature_snapshot(enriched_signal, market_context, regime_state)` — canonical per-trade feature vector.
   - **`logs/run.jsonl`:** Every live entry emits `event_type=trade_intent` with `feature_snapshot`, `thesis_tags`, `displacement_context` (when applicable). Every live exit emits `event_type=exit_intent` with `feature_snapshot_at_exit`, `thesis_tags_at_exit`, `thesis_break_reason`. Additive only.

2. **Directional alignment gate (HIGH_VOL)**
   - For **top-quartile `realized_vol_20d`** symbols only: longs require at least one of `thesis_flow_continuation`, `thesis_dark_pool_accumulation`, `thesis_regime_alignment_score >= 0.6`; shorts require at least one of `thesis_flow_reversal`, `thesis_dark_pool_distribution`, `thesis_regime_alignment_score <= 0.4`.
   - If not met → block entry, log `subsystem=directional_gate`, `event_type=blocked_high_vol_no_alignment` with snapshot + thesis_tags. Does **not** reduce vol exposure.

3. **Shadow experiment matrix**
   - **Config:** `SHADOW_EXPERIMENTS_ENABLED`, `SHADOW_EXPERIMENTS`, `SHADOW_MAX_VARIANTS_PER_CYCLE` (4).
   - **`telemetry/shadow_experiments.py`:** `run_shadow_variants(live_context, candidates, positions)` — runs up to 4 variants per cycle, writes **only** to `logs/shadow.jsonl`. **No** live orders.
   - **Events:** `shadow_variant_decision` (per symbol/variant), `shadow_variant_summary` (per variant/cycle).

4. **EOD alpha diagnostic**
   - **`reports/_daily_review_tools/generate_eod_alpha_diagnostic.py`:** Produces `reports/EOD_ALPHA_DIAGNOSTIC_<DATE>.md` with Headline, Displacement, **Winners vs Losers**, **Telemetry** (trade/exit intent, directional gate), **Shadow experiment scoreboard**, Data availability.

---

## Experiments Running

- **exp_flow_8**, **exp_darkpool_8**, **exp_regime_8**, **exp_vol_8** — weight overrides.
- **exp_no_disp**, **exp_fast_disp**, **exp_strict_disp** — displacement variants.
- **exp_shorts_aggr** — shorts when regime != bull.
- Up to **4 variants per cycle**; rotate via `SHADOW_MAX_VARIANTS_PER_CYCLE`.

---

## What the Data Will Now Answer

- **WHY winners vs losers:** Feature snapshots + thesis tags at entry/exit → effect sizes (mean winners vs mean losers) and **what to turn up / turn down**.
- **High-vol alpha:** Directional gate blocks + HIGH_VOL cohort in EOD → whether we’re directionally justified in volatile names.
- **Shadow comparative:** Per-variant `would_enter` / `would_exit` / blocked → which variants would have traded more or less vs live.
- **Displacement effectiveness:** EOD displacement table + blocked-by-reason → churn vs survival and what-if.

---

## Verification

```bash
python scripts/verify_alpha_upgrade.py
```

**Checks:** Displacement policy, displacement logging, shorts sanity, feature snapshot, **trade_intent** (snapshot+tags), **exit_intent** (thesis_break), **directional_gate**, shadow experiments, EOD report. **FAIL hard** if any missing.

---

## EOD Report

```bash
python reports/_daily_review_tools/generate_eod_alpha_diagnostic.py --date YYYY-MM-DD
```

Output: `reports/EOD_ALPHA_DIAGNOSTIC_<DATE>.md`. Use **Winners vs Losers**, **Telemetry**, **Shadow scoreboard**, and **Data availability** to decide **what to turn up** and **what to turn down**.
