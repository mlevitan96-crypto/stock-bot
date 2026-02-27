# Signal contribution nuclear audit — Plan review (multi-model BEFORE)

**Date:** 2026-02-18  
**Goal:** Prove all scoring signals execute, produce values, contribute non-zero weight, and materially affect composite. Assume scoring is broken until proven otherwise.

---

## Audit plan summary

1. **Signal inventory:** Enumerate signals (from uw_composite_v2 WEIGHTS_V3 + components dict), source file, weight, expected range.
2. **Execution proof:** Run composite scoring for a sample of symbols; verify each component key present in every result.
3. **Value audit:** Per signal: min, max, mean, % zeros, % NaN; flag all-zero, all-NaN, constant.
4. **Weight audit:** Effective weights (get_weight / get_all_current_weights); flag zero or near-zero; match config.
5. **Composite contribution:** Per signal contribution = value × weight (components are already weighted); contribution distribution; flag ~0 contribution.
6. **Distribution sanity:** Composite score distribution; flag compression near floor.
7. **Dead/muted list:** signal_name, failure_mode, suspected root cause, confidence.

**Verdict:** FAIL if any high-impact signal dead/muted, composite unnaturally compressed, or >X% of signals contribute ~0. PASS only if all execute, all contribute non-zero, distribution sane.

---

## Multi-model oversight

### Adversarial: How could scoring lie silently?

| Risk | Mitigation |
|------|------------|
| Components dict is populated with defaults (0.2) so "all present" but not real signal | We use component_sources (real/default/missing) from the scorer; value audit reports % zero and constant; we flag neutral_default-heavy signals. |
| Weights are overwritten by adaptive optimizer to 0 | Weight audit reads effective weight per component; we flag zero or near-zero. |
| Composite is clamped or overwritten after sum | We read score and components from the same run; distribution check detects compression. |
| Sample is too small or unrepresentative | We use up to 50 symbols from live cache; report sample size and symbol list. |

### Quant: Are distributions sane?

| Check | Action |
|-------|--------|
| Composite scores | Histogram/summary (min, max, mean, percentiles); flag if >80% of scores in [0, 1] or all near floor. |
| Per-component values | Min/max/mean; flag constant or all-zero. |
| Contribution share | No single component should be 0% across samples unless weight is 0; we flag ~0 contribution. |

### Product: Are outputs interpretable?

| Check | Action |
|-------|--------|
| Report bundle | Numbered 00–08; summary, inventory, execution, values, weights, contribution, distribution, dead/muted, verdict. |
| Dead/muted table | signal_name, failure_mode, root_cause, confidence so product can prioritize fixes. |

---

## Go

Proceed with script creation and droplet run. No tuning, no strategy changes.
