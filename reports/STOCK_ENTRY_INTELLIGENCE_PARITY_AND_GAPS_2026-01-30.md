# Stock Entry Intelligence Population & Parity Audit

**Date:** 2026-01-30
**Generated:** 2026-01-30T22:56:30.535228+00:00

## Memory Bank (cited)

- **§4 Signal Integrity:** preserve signal_type, metadata; no "unknown" unless truly unknown.
- **§7.2 Composite v2 scoring:** flow, dp, insider, iv_skew, smile, whale, event, motif, toxicity, regime, congress, shorts, inst, tide, calendar, greeks, ftd, iv_rank, oi, etf, squeeze.
- **§7.5–§7.7 Adaptive weights & telemetry:** state/signal_weights.json; state/score_telemetry.json.
- **§7.8 UW Intelligence Layer:** UW client, premarket/postmarket intel, expanded endpoints.
- **§7.9 Attribution invariants:** append-only logs.
- **Observability-only:** NO tuning, NO gating changes.

---

## Why 0% coverage (from prior audit)

The signal contribution audit showed 0% coverage for all components in exit_attribution v2_exit_components.
This indicates either: (1) v2_exit_components uses different keys than the audit expected, or (2) components
are not being written to exit records. At entry, components are computed from enriched_data (uw_flow_cache
+ uw_enrichment_v2 + expanded_intel). If uw_flow_cache is empty or UW daemon is not running, all flow-based
components default. Expanded intel (congress, shorts, greeks, etc.) requires UW expanded endpoints to be
polled and written to cache or uw_expanded_intel.json.

---

## Phase 1: Entry intelligence presence check

| Component | Status | Expected inputs | Source |
|-----------|--------|-----------------|--------|
| calendar | DEFAULTED | calendar | uw_flow_cache or expanded_intel |
| congress | DEFAULTED | congress | uw_flow_cache or data/uw_expanded_intel.json |
| dark_pool | MISSING | dark_pool | uw_flow_cache (UW ingestion) |
| etf_flow | DEFAULTED | etf_flow | uw_flow_cache (UW etf endpoint) |
| event | DEFAULTED | event_alignment | uw_enrichment_v2 (computed from cache) |
| flow | PRESENT | sentiment, conviction, trade_count | uw_flow_cache (UW ingestion) |
| freshness_factor | PRESENT | _last_update, last_update | uw_flow_cache _last_update |
| ftd_pressure | DEFAULTED | ftd, shorts | uw_flow_cache (UW shorts/FTD) |
| greeks_gamma | PRESENT | greeks | uw_flow_cache (UW greeks endpoint) |
| insider | PRESENT | insider | uw_flow_cache (UW ingestion) |
| institutional | DEFAULTED | institutional | uw_flow_cache or expanded_intel |
| iv_rank | MISSING | iv, iv_rank | uw_flow_cache (UW iv endpoint) |
| iv_skew | PRESENT | iv_term_skew | uw_enrichment_v2 (computed from cache) |
| market_tide | DEFAULTED | market_tide | uw_flow_cache or expanded_intel |
| motif_bonus | MISSING | motif_staircase, motif_burst | uw_enrichment_v2 motif_staircase/burst (from cache |
| oi_change | DEFAULTED | oi_change, oi | uw_flow_cache (UW oi endpoint) |
| regime | MISSING | regime | state/regime_state.json, regime_detector |
| shorts_squeeze | DEFAULTED | shorts, ftd | uw_flow_cache or expanded_intel |
| smile | PRESENT | smile_slope | uw_enrichment_v2 (computed from cache) |
| squeeze_score | DEFAULTED | squeeze_score | uw_flow_cache or computed |
| toxicity_penalty | MISSING | toxicity | uw_enrichment_v2 (computed from cache) |
| whale | MISSING | motif_whale | uw_enrichment_v2 motif_whale (from cache history) |

---

## Phase 2: Source trace (MISSING/DEFAULTED)

- **calendar**: expanded_intel not populated
- **congress**: expanded_intel not populated
- **dark_pool**: wiring incomplete or intentionally disabled
- **etf_flow**: UW expanded endpoints may not be polled or wired to cache
- **event**: enrichment computed from cache; cache may lack upstream fields
- **ftd_pressure**: UW expanded endpoints may not be polled or wired to cache
- **institutional**: expanded_intel not populated
- **iv_rank**: UW expanded endpoints may not be polled or wired to cache
- **market_tide**: expanded_intel not populated
- **motif_bonus**: enrichment computed from cache; cache may lack upstream fields
- **oi_change**: UW expanded endpoints may not be polled or wired to cache
- **regime**: wiring incomplete or intentionally disabled
- **shorts_squeeze**: expanded_intel not populated
- **squeeze_score**: wiring incomplete or intentionally disabled
- **toxicity_penalty**: enrichment computed from cache; cache may lack upstream fields
- **whale**: enrichment computed from cache; cache may lack upstream fields

---

## Phase 3: Parity & applicability

| Component | Applicability | Rationale |
|-----------|---------------|-----------|
| calendar | APPLICABLE to stock-bot | Stock-bot equities |
| congress | APPLICABLE (congress trading in equities) | Stock-bot equities |
| dark_pool | APPLICABLE to stock-bot | Stock-bot equities |
| etf_flow | APPLICABLE (options/ETF data for equity names) | Stock-bot equities |
| event | APPLICABLE to stock-bot | Stock-bot equities |
| flow | APPLICABLE (UW options flow for equities) | Stock-bot equities |
| freshness_factor | APPLICABLE to stock-bot | Stock-bot equities |
| ftd_pressure | APPLICABLE (options/ETF data for equity names) | Stock-bot equities |
| greeks_gamma | APPLICABLE (options/ETF data for equity names) | Stock-bot equities |
| insider | APPLICABLE to stock-bot | Stock-bot equities |
| institutional | APPLICABLE to stock-bot | Stock-bot equities |
| iv_rank | APPLICABLE (options/ETF data for equity names) | Stock-bot equities |
| iv_skew | APPLICABLE to stock-bot | Stock-bot equities |
| market_tide | APPLICABLE to stock-bot | Stock-bot equities |
| motif_bonus | APPLICABLE to stock-bot | Stock-bot equities |
| oi_change | APPLICABLE (options/ETF data for equity names) | Stock-bot equities |
| regime | REQUIRES STOCK-SPECIFIC SOURCE (regime_state/regime_detector) | Stock-bot equities |
| shorts_squeeze | APPLICABLE to stock-bot | Stock-bot equities |
| smile | APPLICABLE to stock-bot | Stock-bot equities |
| squeeze_score | APPLICABLE (FTD/SI squeeze in equities) | Stock-bot equities |
| toxicity_penalty | APPLICABLE to stock-bot | Stock-bot equities |
| whale | APPLICABLE to stock-bot | Stock-bot equities |

---

## Phase 4: Recommendations (NO-APPLY)

### 1) Components to ACTIVATE (data already available)

- **flow**: Data present in cache. Evidence: sampled symbols. **STATUS: SHADOW — NOT APPLIED**
- **insider**: Data present in cache. Evidence: sampled symbols. **STATUS: SHADOW — NOT APPLIED**
- **iv_skew**: Data present in cache. Evidence: sampled symbols. **STATUS: SHADOW — NOT APPLIED**
- **smile**: Data present in cache. Evidence: sampled symbols. **STATUS: SHADOW — NOT APPLIED**
- **greeks_gamma**: Data present in cache. Evidence: sampled symbols. **STATUS: SHADOW — NOT APPLIED**
- **freshness_factor**: Data present in cache. Evidence: sampled symbols. **STATUS: SHADOW — NOT APPLIED**

### 2) Components to ADAPT (need stock-specific intel)

- **ftd_pressure**: Defaulting; wire UW expanded endpoints or premarket intel. **STATUS: SHADOW — NOT APPLIED**
- **oi_change**: Defaulting; wire UW expanded endpoints or premarket intel. **STATUS: SHADOW — NOT APPLIED**
- **etf_flow**: Defaulting; wire UW expanded endpoints or premarket intel. **STATUS: SHADOW — NOT APPLIED**

### 3) Components to DEFER (not applicable)

- None (all components are applicable to equities).

### 4) Minimal new intel sources to add first

- Populate data/uw_expanded_intel.json from UW expanded endpoints or premarket/postmarket intel **STATUS: SHADOW — NOT APPLIED**

---

## Data source status

- **uw_flow_cache.json**: present; 18 symbols
- **uw_expanded_intel.json**: missing
- **premarket_intel.json**: present
- **postmarket_intel.json**: present
- **regime_state.json**: present
- **symbol_risk_features.json**: present
- **market_context_v2.json**: present

---

*Generated by scripts/entry_intelligence_parity_audit.py. Observability-only.*
