# Scoring pipeline audit – summary (why no Alpaca trades)

**Date:** 2026-02-23  
**Source:** Droplet run via `run_scoring_pipeline_audit_via_droplet.py` (real data: decision_ledger, funnel, traces).

---

## Bottom line

- **Trades are not occurring** because **100% of candidates are blocked at the expectancy gate** (composite score below MIN_EXEC_SCORE 2.5).
- **Not a gate bug:** the gate is doing what it should. **Scores are too low.**
- **Best scores in window:** 0.172, 0.316, or 1.055 (e.g. SPY, QQQ, CAT) — all below 2.5.

---

## Pipeline path (all signals tied to trade engine)

1. **UW cache** → `data/uw_flow_cache.json`
2. **Enrichment** → `uw_enrichment_v2.enrich_signal(symbol, cache, regime)`
3. **Composite score** → `uw_composite_v2.compute_composite_score_v2(symbol, enriched, regime)` → 22 components (flow, dark_pool, insider, iv_skew, smile, whale, event, motif_bonus, toxicity_penalty, regime, congress, shorts_squeeze, institutional, market_tide, calendar, greeks_gamma, ftd_pressure, iv_rank, oi_change, etf_flow, squeeze_score, freshness_factor)
4. **Gate** → `should_enter_v2(composite, ticker)` (threshold 2.7, freshness ≥ 0.30, toxicity < 0.90) → clusters with `source=composite_v3`
5. **Engine** → `decide_and_execute()` → adjustments (signal_quality, UW, survivorship) → **expectancy gate** (composite_exec_score ≥ MIN_EXEC_SCORE 2.5) → capacity/theme/cooldown/trade_guard → `submit_entry()` → Alpaca

Every signal is wired; the break is **score level** (scores 0.17–1.05 never reach 2.5).

---

## What’s broken (score level)

From MEMORY_BANK §7 and SIGNAL_SCORE_PIPELINE_AUDIT:

1. **Missing/zero flow conviction** → flow component (weight 2.4) contributes 0.
2. **Missing core features** → iv_term_skew, smile_slope, event_alignment default to 0 → ~1.35 points lost.
3. **Missing expanded intel** → 11 V3 components (congress, shorts, institutional, tide, calendar, greeks, ftd, iv_rank, oi_change, etf_flow, squeeze_score) contribute 0 when data missing.
4. **Freshness decay** → composite_raw × freshness; stale data cuts score.
5. **Adjustment chain** → signal_quality, UW, survivorship can reduce score further before the expectancy gate.

So many components are 0 or small → total composite stays in 0.17–1.05 → expectancy gate blocks every candidate.

---

## Evidence (droplet)

| Metric | Value |
|--------|--------|
| Candidates (7d) | 2922 |
| Blocked at expectancy_gate:score_floor_breach | 2922 (100%) |
| Post-adjust score p50 | 0.172 |
| Post-adjust score p90 | 0.316 |
| % above MIN_EXEC_SCORE (2.5) | 0% |
| Example “best” scores | SPY/QQQ/CAT 1.055 (still &lt; 2.5) |

Decision ledger traces show **Score components (sample): {}** — no component breakdown in ledger; run `signal_audit_diagnostic.py` on droplet with `data/uw_flow_cache.json` for per-signal contribution.

---

## What to do next

1. **Confirm UW cache and enrichment on droplet:**  
   - `data/uw_flow_cache.json` present and populated (conviction, sentiment, dark_pool, insider).  
   - Run `python3 scripts/signal_audit_diagnostic.py` on droplet; inspect `signal_audit_diagnostic_droplet.json` for dead/muted signals and value_audit.

2. **Apply MEMORY_BANK §7 fixes (if not already):**  
   - Default flow_conv to 0.5 when missing (uw_composite_v2).  
   - Ensure iv_term_skew, smile_slope, event_alignment always computed or defaulted (main.py / enricher).  
   - Neutral defaults for missing expanded_intel components.  
   - DECAY_MINUTES = 180 in enrichment (slower freshness decay).

3. **Optional:** Enable `SIGNAL_SCORE_BREAKDOWN_LOG=1`, run until `logs/signal_score_breakdown.jsonl` has 100+ lines, then run `signal_score_breakdown_summary_on_droplet.py` and `signal_pipeline_deep_dive_on_droplet.py` for per-candidate signal tables.

4. **Re-run audit:**  
   `python scripts/run_scoring_pipeline_audit_via_droplet.py`  
   Check `reports/signal_review/SCORING_PIPELINE_TRADE_BLOCKER_AUDIT.md` for updated choke point and “Can we make trades?”.

---

## Artifacts

- **Full audit:** `reports/signal_review/SCORING_PIPELINE_TRADE_BLOCKER_AUDIT.md`
- **Funnel:** `reports/signal_review/signal_funnel.md` / `signal_funnel.json`
- **Traces:** `reports/signal_review/top_50_end_to_end_traces.md`
- **Adversarial:** `reports/signal_review/multi_model_adversarial_review.md`
