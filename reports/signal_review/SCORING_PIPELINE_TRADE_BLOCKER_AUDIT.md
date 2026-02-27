# Scoring pipeline trade-blocker audit

**Generated (droplet):** 2026-02-23T17:01:44.803373+00:00
**Window:** last 7 days. **MIN_EXEC_SCORE (config):** 2.5

---

## 1. Executive summary

- **Dominant choke point:** 5_expectancy_gate — expectancy_gate:score_floor_breach (2922 / 2922 = 100.0%).
- **Score distribution (post-adjust):** median = 0.172; % above MIN_EXEC_SCORE = 0.0%.

**Verdict:** Trades are **not** occurring because **every candidate fails the expectancy gate** (composite score below MIN_EXEC_SCORE). The pipeline is blocking correctly; the issue is **scores are too low**, not a gate bug.

---

## 2. All signals in the pipeline (tied to trade engine)

Every signal below is **wired** into the trade engine:
- **Path:** `main.py` → load `data/uw_flow_cache.json` → `uw_enrichment_v2.enrich_signal()` → `uw_composite_v2.compute_composite_score_v2()` → clusters with `source=composite_v3` → `decide_and_execute()` → expectancy gate (composite_exec_score vs MIN_EXEC_SCORE) → `submit_entry()`.
- **Composite formula:** sum of component contributions × freshness; clamp 0–8. Entry requires score ≥ MIN_EXEC_SCORE and passing `should_enter_v2` (threshold, freshness ≥ 0.30, toxicity < 0.90).

(Signal audit diagnostic did not run or produced no JSON. Check `data/uw_flow_cache.json` and script.)

---

## 3. Per-trade flow: signals firing and reaching execution

For each candidate that reaches `decide_and_execute`:
1. **Cluster** has `composite_score` and `source=composite_v3`.
2. **Adjustments** (signal_quality, UW, survivorship) may reduce score → `composite_exec_score`.
3. **Expectancy gate** compares `composite_exec_score` to MIN_EXEC_SCORE; if below → block (score_floor_breach).
4. **Later gates:** regime, concentration, theme, momentum, cooldown, position exists, trade_guard.
5. **submit_entry** → Alpaca only if all pass.

If **no trades**: the dominant blocker in section 1 is where the pipeline stops (almost always expectancy_gate:score_floor_breach when scores are low).

---

## 4. Can we make trades?

**No (current run).** In this window, composite scores are below MIN_EXEC_SCORE for **all** candidates, so the expectancy gate blocks every one. No new orders would reach Alpaca from the current scoring pipeline.

(Any fills in the window are from earlier runs; the current signal/score state does not allow new trades.)

**Root cause (score level):** Likely combination of: (1) missing or zero flow/conviction/dark_pool/insider in UW cache, (2) many components defaulting to 0 or neutral when data missing, (3) freshness decay, (4) adjustment chain reducing score. Fix: ensure UW cache is populated and fresh; verify conviction/sentiment present; run intel producers and keep uw_flow_daemon running (see docs/SIGNAL_DATA_SOURCES_AND_CHECKLIST.md).

---

## 5. Droplet commands (re-run audit)

```bash
cd /root/stock-bot
python3 scripts/run_scoring_pipeline_audit_on_droplet.py --days 7
```

To enable per-candidate signal breakdown (optional):
```bash
export SIGNAL_SCORE_BREAKDOWN_LOG=1
# run main.py / paper until logs/signal_score_breakdown.jsonl has 100+ lines
python3 scripts/signal_score_breakdown_summary_on_droplet.py
python3 scripts/signal_pipeline_deep_dive_on_droplet.py
```
