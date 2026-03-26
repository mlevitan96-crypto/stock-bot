# Alpaca Quant Lab — Signal Redundancy (QSA)

**Mission:** Phase 1 — Quantify redundancy and correlation clusters among features/signals.  
**Authority:** QSA.  
**Date:** 2026-03-18.

---

## 1. Correlation Clusters (Conceptual)

Without running a full correlation matrix on frozen trade data, clusters are inferred from signal definitions and data sources:

### 1.1 Flow / Sentiment Cluster

- **options_flow**, **dark_pool**, **market_tide**, **whale_persistence**  
- All derive from UW options/flow data; likely positive correlation.  
- **Redundancy:** Medium; different aspects (conviction, notional, direction, whale flag).

### 1.2 IV / Volatility Cluster

- **iv_term_skew**, **smile_slope**, **iv_rank**, **realized_vol_5d/20d**, **vol_expansion**  
- IV and realized vol can move together.  
- **Redundancy:** Medium–high; consider one IV proxy and one vol proxy in parsimonious models.

### 1.3 Squeeze / Positioning Cluster

- **shorts_squeeze**, **ftd_pressure**, **squeeze_score**, **greeks_gamma**, **oi_change**  
- All relate to short interest, gamma, or positioning.  
- **Redundancy:** High; strong candidate for a single “squeeze/positioning” factor or small subset.

### 1.4 Regime Cluster

- **regime_label**, **regime_modifier**, **entry_regime**, **exit_regime**, **structural_regime**  
- Same underlying state at different layers.  
- **Redundancy:** High; use one regime variable per analysis (e.g. entry_regime).

### 1.5 Calendar / Event Cluster

- **event_alignment**, **calendar_catalyst**, **earnings_days_away**, **thesis_invalidated**, **earnings_risk**  
- Event and calendar awareness.  
- **Redundancy:** Medium; event_alignment vs calendar_catalyst may overlap.

---

## 2. Coverage Redundancy

- **Entry composite score** vs **individual entry components:** Full score is a function of components; for regression/attribution, use components (or a subset) to avoid perfect collinearity with score.
- **Exit score** vs **exit_* components:** Same; use components for “which lever drove exit.”

---

## 3. Recommendation for Phase 4 (Profit Discovery)

- **Deduplicate by behavior:** When ranking strategies, merge strategies that differ only by swapping signals within the same cluster (e.g. iv_term_skew vs iv_rank).
- **Parsimonious subsets:** Test (a) flow cluster representative (e.g. options_flow only), (b) one IV proxy, (c) one squeeze proxy, (d) regime, (e) calendar/event — then expand if needed.
- **Correlation matrix:** For a rigorous redundancy report, run correlation on TRADES_FROZEN + joined attribution (numeric components only) and document actual pairwise correlations; repeat after new freezes.
