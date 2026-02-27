# Conditional Edge Map (Phase 4) — Where Edge Actually Exists

**Mandate:** Synthesize which signals are predictive, under which conditions, with what confidence. No weight changes.

---

## 1. Which signals are predictive?

- **From conditional slice plan:** Signals available for conditioning are **group_sums** (uw, regime_macro, other_components) and **components** (flow, dark_pool, market_tide, calendar, regime, whale, event, etc.).
- **From conditional expectancy (when data exists):** Positive expectancy in a signal×condition cell means “when this condition holds, mean_pnl for blocked trades in that slice is positive.” That is predictive of “blocked trade would have been profitable in that slice.”

---

## 2. Under which conditions?

Approved slice dimensions (from conditional_slice_plan.md):

| Dimension | Levels | Use |
|-----------|--------|-----|
| score_bucket | 0.5–1.0, 1.0–1.5, 1.5–2.0, … | Context: score strength at block. |
| uw | low / mid / high | UW flow strength. |
| regime_macro | low / mid / high | Regime/macro context strength. |
| other_components | low / mid / high | Other signal strength. |
| flow | absent / present | Flow component present. |
| dark_pool | absent / present | Dark pool present. |
| market_tide | low / high | Market-tide component. |
| calendar | off / on | Calendar pressure. |

**Interactions:** uw × regime_macro (and optionally flow × market_tide) to capture alignment/divergence.

---

## 3. With what confidence?

- **High:** Same signal×condition shows positive mean_pnl with n ≥ 20 in this window and (if available) same sign in a holdout window.
- **Medium:** Positive mean_pnl with n ≥ 10; no holdout check yet.
- **Low / hypothesis:** n < 10 or sign flip across adjacent slices; treat as hypothesis only.

---

## 4. Top signal × condition pairs (template)

*When conditional_expectancy.md is populated from droplet data, fill from that report. Until then, no data → no pairs.*

- **Top 3 signal × condition with positive expectancy:** (from conditional_expectancy.md)
- **Conditions under which NO signals work:** (from conditional_expectancy.md: slices where all cells have mean_pnl ≤ 0 or n too small)

---

## 5. Recommendation

- **If** at least one signal×condition cell has positive mean_pnl with n ≥ 10 and is not flagged as fragile in adversarial review → **“EDGE IS CONDITIONAL — PROCEED TO CONDITIONAL SCORING.”**
- **If** no such cell exists, or only fragile/small-n cells → **“NO EDGE FOUND — SIGNAL SET INSUFFICIENT”** (or “collect more data and re-run”).

*Current state:* No replay data in this run → no conditional cells computed → **“NO EDGE FOUND — SIGNAL SET INSUFFICIENT”** (or “run on droplet with attribution data to populate conditional_expectancy.md and re-evaluate”).
