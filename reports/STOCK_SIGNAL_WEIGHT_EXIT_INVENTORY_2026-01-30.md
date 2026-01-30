# Stock Signal / Weight / Exit Inventory

**Date:** 2026-01-30
**Generated:** 2026-01-30T22:27:47.567823+00:00

## Memory Bank (cited)

- **Golden Workflow:** User→Cursor→GitHub→Droplet→GitHub→Cursor→User (MEMORY_BANK §0.1)
- **Data Source Rule:** Reports use droplet production data; ReportDataFetcher / droplet as source of truth (§3.2)
- **Signal Integrity:** No "unknown" unless truly unknown; preserve signal_type, metadata (§4)
- **Composite v2 + weight tuning:** config/registry.py COMPOSITE_WEIGHTS_V2; adaptive state/signal_weights.json (§7.5, §7.7)
- **Attribution invariants:** Append-only logs (attribution, exit_attribution, master_trade_log) (§5.5, §7.9)

---

## 1. Static inventory (code + config)

### COMPOSITE_WEIGHTS_V2 (config/registry.py)
- **Version:** 2026-01-20_wt1
- **Numeric/param keys:** ['vol_center', 'vol_scale', 'vol_bonus_max', 'low_vol_penalty_center', 'low_vol_penalty_max', 'beta_center', 'beta_scale', 'beta_bonus_max', 'uw_center', 'uw_scale', 'uw_bonus_max', 'premarket_align_bonus', 'premarket_misalign_penalty', 'regime_align_bonus', 'regime_misalign_penalty', 'posture_conf_strong', 'high_vol_multiplier', 'mid_vol_multiplier', 'low_vol_multiplier', 'misalign_dampen']...

### Where weights are applied

- uw_composite_v2.py: get_weight(component, regime), get_multiplier(component)
- uw_composite_v2.py: _compute_composite_score_core() uses COMPOSITE_WEIGHTS_V2 and adaptive multipliers
- config/registry.py: COMPOSITE_WEIGHTS_V2 (single source of truth per Memory Bank §7.7)

### Adaptive multiplier sources

- state/signal_weights.json (runtime adaptive multipliers 0.25x–2.5x)
- adaptive_signal_optimizer.py: get_optimizer(), get_weights_for_composite(regime), get_multipliers_only(); persists to state/signal_weights.json

### Signals feeding entry (composite formula §7.2)

| Component | Base weight (approx) |
|-----------|----------------------|
| options_flow | 2.4 |
| dp_strength | 1.3 |
| insider | 0.5 |
| iv_skew | 0.6 |
| smile_slope | 0.35 |
| whale | 0.7 |
| event_align | 0.4 |
| motif | 0.6 |
| toxicity | -0.9 |
| regime | 0.3 |
| congress | 0.9 |
| shorts_squeeze | 0.7 |
| institutional | 0.5 |
| market_tide | 0.4 |
| calendar | 0.45 |
| ... (+6 more) | — |

---

## 2. Exit usage inventory

| Question | Determination |
|----------|---------------|
| Exits use composite_score? | **YES** |
| Exits use component breakdown? | **YES** |
| Exits use UW intel features? | **YES** |
| Exits use regime/posture? | **YES** |
| **Exits use weights / adaptive multipliers?** | **YES** |

**File/symbol references:**

- main.py: current_composite_score from compute_composite_score_v2(); score_deterioration, now_v2_score, decay_ratio; log_exit_attribution(..., v2_exit_score, v2_exit_components)
- src/exit/exit_attribution.py: build_exit_attribution_record(..., score_deterioration, relative_strength_deterioration, v2_exit_score, v2_exit_components)

---

## 3. Runtime evidence (droplet-state if present)

- **state/signal_weights.json:** active multipliers snapshot (keys_present, weight_bands components, version).
  - keys: ['entry_weights', 'exit_model', 'learner', 'saved_at', 'saved_dt', 'weight_bands']
- **state/score_telemetry.json:** component zero% and missing intel counts present.
  - keys: ['scores', 'components', 'missing_intel', 'defaulted_conviction', 'decay_factors', 'neutral_defaults', 'core_features_missing', 'last_update']
- **logs/system_events.jsonl (composite_version_used):** no recent event found.

---

## 4. Gaps and next safe actions

- **Gaps:** Unknown exit paths (if any) should be audited; signal_decay variants documented in §7.1; veto traceability via gate_event rules (§4.3).
- **Next safe actions (observability only):** Run this inventory on droplet after EOD; include manifest pass/fail in daily review; no strategy or safety logic changes.

---
