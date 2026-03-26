# ALPACA — Signal granularity & adjustability audit (Phase 3)

**Timestamp:** 20260314

---

## Per-trade signal telemetry (exit_attribution.jsonl)

Confirmed from codebase (`src/exit/exit_attribution.py`, `exit_score_v2.py`, `exit_quality_metrics.py`) and droplet sample (TRADE_DATA_COLLECTION_SUMMARY / collect_trade_data_inventory).

| Field | Present | Description |
|-------|---------|-------------|
| **v2_exit_score** | YES | Total exit pressure [0..1] per trade |
| **v2_exit_components** | YES | Per-component numeric values (see matrix below) |
| **attribution_components** | YES | List of `{signal_id, contribution_to_score}` per trade |
| **regime / strategy / mode** | YES | `entry_regime`, `exit_regime`, `regime_label`, `strategy`, `mode` (enrichment) |
| **exit_reason** | YES | Winner mechanism (e.g. profit, replacement, stop, intel_deterioration) |
| **exit_reason_code** | YES | Normalized code (same as exit_reason when set) |
| **exit_quality_metrics** | YES (optional) | MFE/MAE, time_in_trade, profit_giveback when bars or high_water available |

---

## master_trade_log.jsonl

| Field | Present | Description |
|-------|---------|-------------|
| **v2_score** / **entry_v2_score** | YES | Entry and exit composite scores |
| **signals** / **feature_snapshot** / **regime_snapshot** | YES | Snapshots at close (structure varies) |
| **exit_reason** | YES | Why closed |

Exit pressure components are not duplicated in master_trade_log; primary per-signal exit telemetry is in exit_attribution.jsonl.

---

## Signal × available_fields × adjustable matrix

Exit components (from `exit_score_v2.compute_exit_score_v2`). All are **logged per trade** in `v2_exit_components` and in `attribution_components` (with `exit_` prefix for signal_id). Weights are in code; **adjustable = YES** means the lever is configurable via code/config (no runtime UI).

| signal_name | available_fields | numeric_per_trade | schema_versioning | separable (not collapsed) | adjustable |
|-------------|------------------|-------------------|-------------------|--------------------------|------------|
| exit_flow_deterioration | v2_exit_components, attribution_components | YES | composite_version / attribution_schema_version | YES | YES (weight in code) |
| exit_darkpool_deterioration | v2_exit_components, attribution_components | YES | YES | YES | YES |
| exit_sentiment_deterioration | v2_exit_components, attribution_components | YES | YES | YES | YES |
| exit_score_deterioration | v2_exit_components, attribution_components, score_deterioration | YES | YES | YES | YES |
| exit_regime_shift | v2_exit_components, attribution_components | YES | YES | YES | YES |
| exit_sector_shift | v2_exit_components, attribution_components | YES | YES | YES | YES |
| exit_vol_expansion | v2_exit_components, attribution_components | YES | YES | YES | YES |
| exit_thesis_invalidated | v2_exit_components, attribution_components | YES | YES | YES | YES |
| exit_earnings_risk | v2_exit_components, attribution_components | YES | YES | YES | YES |
| exit_overnight_flow_risk | v2_exit_components, attribution_components | YES | YES | YES | YES |

**exit_quality_metrics** (optional):

| signal_name | available_fields | numeric_per_trade | adjustable |
|-------------|------------------|-------------------|------------|
| mfe_pct / mfe | exit_quality_metrics | YES (when bars/high_water) | Observational only |
| mae_pct / mae | exit_quality_metrics | YES | Observational only |
| hold_minutes / time_in_trade_sec | exit_quality_metrics, time_in_trade_minutes | YES | Observational only |

---

## Schema versioning

- **composite_version:** `"v2"` in exit_attribution records.
- **attribution_schema_version:** Set in writer (e.g. ATTRIBUTION_SCHEMA_VERSION).
- **docs:** `docs/ALPACA_ATTRIBUTION_SCHEMA.md` (canonical exit schema).

---

## Verdict

- **Fine-grained signal telemetry exists per trade:** v2_exit_score, v2_exit_components, attribution_components, regime/strategy/mode, exit_reason, exit_reason_code, and optional exit_quality_metrics (MFE/MAE).
- **Components are separable:** Each component is a distinct key in v2_exit_components and a distinct entry in attribution_components; not collapsed into a single value.
- **Adjustability:** Weights and thresholds are in code (`exit_score_v2.py` weights, exit pressure thresholds); changes require code/config deployment. No runtime API for tuning without deploy.
- **Governance:** Signal granularity is sufficient for board-level attribution and for governed, fine-grained tuning (with code/config change process).
