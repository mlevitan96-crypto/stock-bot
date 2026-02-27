# Conditional Slice Plan (Phase 1)

**Mandate:** Define conditional slices for signal × condition expectancy. No weight changes. Use per-signal attribution already in place. Multi-model proposals.

---

## MODEL A — Primary Investigator

Proposed slices (from available attribution: `group_sums`, `components`, `bucket`):

| Slice dimension | Levels | Definition | Data source |
|-----------------|--------|------------|-------------|
| **Score bucket** | 0.5–1.0, 1.0–1.5, 1.5–2.0, 2.0–2.5, … | Composite score at block time | `bucket` (replay) |
| **UW strength** | low, mid, high | Tertile of `group_sums.uw` | `group_sums.uw` |
| **Regime/macro** | low, mid, high | Tertile of `group_sums.regime_macro` | `group_sums.regime_macro` |
| **Other components** | low, mid, high | Tertile of `group_sums.other_components` | `group_sums.other_components` |
| **Flow present** | absent, present | `components.flow` ≤ 0 vs > 0 (or median split) | `components.flow` |
| **Dark pool** | absent, present | `components.dark_pool` ≤ 0 vs > 0 | `components.dark_pool` |
| **Market tide** | low, high | Tertile or median of `components.market_tide` | `components.market_tide` |
| **Calendar pressure** | off, on | `components.calendar` low vs high (e.g. median split) | `components.calendar` |

**Interactions to test:** uw × regime_macro, flow × market_tide, score_bucket × uw.

---

## MODEL B — Adversarial Reviewer

- **Volatility:** Not in current snapshot/replay. Slice “low vs high vol” requires enriching snapshot with `realized_vol_20d` or vol_regime at write time. **Proposal:** Add as future slice when enrichment exists; omit for now or use proxy (e.g. other_components).
- **Regime (market regime):** “Regime up vs down vs transition” is not a field in replay. **Proposal:** Use `regime_macro` group sum as proxy for “regime/macro context strength,” not literal market regime. Label clearly.
- **Liquidity:** No liquidity field. **Proposal:** Omit or proxy with “other_components” or trade count if ever logged.
- **Flow present vs absent:** Agreed; use `components.flow` threshold (0 or median).
- **Spurious splits:** Avoid slices with n < 10; report n per cell.

---

## MODEL C — Forensic Auditor

- **Schema alignment:** All slice inputs must come from `replay_results.jsonl`: `group_sums`, `components`, `bucket`. No new fields without schema change.
- **Missing components:** If `components` is empty (old data), only `group_sums` and `bucket` slices are valid; signal×condition tables for component-level slices will be empty.
- **Tertile boundaries:** Compute from sample (replay_results) so boundaries are data-driven; document “tertile = sample tertile” to avoid lookahead.

---

## MODEL D — Synthesis

**Approved conditional slices (implementable today):**

1. **score_bucket** — levels: as in pipeline (0.5–1.0, 1.0–1.5, 1.5–2.0, …).
2. **uw** — low / mid / high (tertile of `group_sums.uw`).
3. **regime_macro** — low / mid / high (tertile of `group_sums.regime_macro`).
4. **other_components** — low / mid / high (tertile of `group_sums.other_components`).
5. **flow** — absent (≤0) vs present (>0); or low vs high (median split) for more nuance.
6. **dark_pool** — absent (≤0) vs present (>0).
7. **market_tide** — low vs high (median or tertile of `components.market_tide`).
8. **calendar** — off (low) vs on (high) by median of `components.calendar`.

**Deferred (need schema/enrichment):** volatility, explicit market regime, liquidity.

**Output:** Conditional expectancy by (signal group or component) × slice; then adversarial review and edge map.
