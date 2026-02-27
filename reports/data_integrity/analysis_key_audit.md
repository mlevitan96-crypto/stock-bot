# Replay & Analysis Key Verification

Confirm that `blocked_expectancy_analysis.py` and `blocked_signal_expectancy_pipeline.py` consume the same keys as the canonical list without renaming or inconsistent fallback.

**Canonical reference:** `reports/data_integrity/canonical_signal_keys.md`

---

## Consumer 1: blocked_expectancy_analysis.py

**Reads:** `state/blocked_trades.jsonl` only.

**Keys consumed from each record:**  
`symbol`, `reason` / `block_reason`, `timestamp` / `ts`, `score` / `candidate_score`, `would_have_entered_price` / `decision_price`, `direction`.

**Signal keys (components, group_sums, weighted_contributions):** **Not consumed.** This script does not read attribution_snapshot, components, or group_sums. It only uses score and price for replay and bucket analysis.

**Conclusion:** **N/A** for signal schema parity. No renaming or key mismatch; script is agnostic to signal keys.

---

## Consumer 2: blocked_signal_expectancy_pipeline.py

**Reads:** `logs/score_snapshot.jsonl`, `state/blocked_trades.jsonl`.

### From score_snapshot.jsonl

| Source field | Usage | Key handling |
|--------------|--------|--------------|
| `weighted_contributions` | Preferred for component dict (`comps`) | Used as-is; keys not renamed. |
| `signal_group_scores` | Fallback when weighted_contributions absent | `signal_group_scores.get("components")` or full dict; keys unchanged. |
| `group_sums` | Preferred for group sums | Used as-is when present. |
| (fallback) | When group_sums absent | `_component_group_sums(comps)` recomputes using UW_KEYS, REGIME_MACRO_KEYS, OTHER_COMPONENT_KEYS. |

**Internal key sets (must match canonical):**

- **UW_KEYS:** flow, dark_pool, insider, whale, event → **MATCH** canonical uw group.
- **REGIME_MACRO_KEYS:** regime, market_tide, calendar, motif_bonus → **MATCH** canonical regime_macro group.
- **OTHER_COMPONENT_KEYS:** congress, shorts_squeeze, institutional, iv_skew, smile, toxicity_penalty, greeks_gamma, ftd_pressure, iv_rank, oi_change, etf_flow, squeeze_score → **MATCH** canonical other_components.

No renaming: pipeline uses the same key names as the composite. Fallback `_component_group_sums(comps)` only recomputes group_sums from components when group_sums is missing (e.g. old data); it does not introduce different keys.

### From blocked_trades.jsonl

| Source field | Usage | Key handling |
|--------------|--------|--------------|
| `attribution_snapshot.weighted_contributions` | Preferred for `components` in bt_by_key | Used as-is. |
| `attribution_snapshot.group_sums` | Stored and merged into candidate | Used as-is. |
| `r.get("components")` | Fallback when attribution_snapshot missing | Same key contract. |

**Conclusion:** **PASS** — Pipeline consumes the same keys as canonical; no renaming; fallbacks preserve key semantics (recompute group_sums from components with same grouping).

---

## Summary

| Script | Consumes signal keys? | Renaming? | Fallback consistent? | Verdict |
|--------|------------------------|-----------|----------------------|---------|
| blocked_expectancy_analysis.py | No | N/A | N/A | N/A (no signal keys) |
| blocked_signal_expectancy_pipeline.py | Yes | No | Yes | **PASS** |
