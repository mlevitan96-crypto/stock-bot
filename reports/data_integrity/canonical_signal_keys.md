# Canonical Signal Key List

**Source:** `uw_composite_v2._compute_composite_score_core` (single composite scoring path).  
**Contract:** All signal components and group_sums must use these keys end-to-end. No renaming, no silent drops.

---

## 1. Component keys (weighted_contributions / components)

Used in composite scoring and written as `weighted_contributions` (snapshot, blocked_trades) and `components` (composite_meta).

| Key | Group | Notes |
|-----|-------|--------|
| flow | uw | Options flow conviction × weight |
| dark_pool | uw | Dark pool component |
| insider | uw | Insider sentiment component |
| iv_skew | other_components | IV term skew |
| smile | other_components | Smile slope |
| whale | uw | Whale persistence |
| event | uw | Event alignment |
| motif_bonus | regime_macro | Temporal motif bonus |
| toxicity_penalty | other_components | Toxicity penalty |
| regime | regime_macro | Regime modifier |
| congress | other_components | Congress/politician |
| shorts_squeeze | other_components | Short interest / squeeze |
| institutional | other_components | Institutional |
| market_tide | regime_macro | Options market sentiment |
| calendar | regime_macro | Calendar catalyst |
| greeks_gamma | other_components | Gamma exposure |
| ftd_pressure | other_components | FTD pressure |
| iv_rank | other_components | IV rank |
| oi_change | other_components | OI change |
| etf_flow | other_components | ETF flow |
| squeeze_score | other_components | Squeeze score |
| freshness_factor | (excluded from group_sums) | Meta, not summed |

**Canonical component set (22 keys):**  
`flow`, `dark_pool`, `insider`, `iv_skew`, `smile`, `whale`, `event`, `motif_bonus`, `toxicity_penalty`, `regime`, `congress`, `shorts_squeeze`, `institutional`, `market_tide`, `calendar`, `greeks_gamma`, `ftd_pressure`, `iv_rank`, `oi_change`, `etf_flow`, `squeeze_score`, `freshness_factor`

---

## 2. Group-sum keys (group_sums)

Aggregations emitted by the composite and consumed by the pipeline for signal-group expectancy.

| Key | Definition |
|-----|------------|
| uw | Sum of: flow, dark_pool, insider, whale, event |
| regime_macro | Sum of: regime, market_tide, calendar, motif_bonus |
| other_components | Sum of all remaining components except freshness_factor |

**Canonical group_sums set (3 keys):**  
`uw`, `regime_macro`, `other_components`

---

## 3. Mapping (component → group)

- **uw:** flow, dark_pool, insider, whale, event  
- **regime_macro:** regime, market_tide, calendar, motif_bonus  
- **other_components:** congress, shorts_squeeze, institutional, iv_skew, smile, toxicity_penalty, greeks_gamma, ftd_pressure, iv_rank, oi_change, etf_flow, squeeze_score
