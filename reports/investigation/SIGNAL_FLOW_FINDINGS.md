# Signal flow findings (from droplet)

**Fix (2026-02-20):** No hardcoded numbers—signals adjust only from imported data and push long/short. When data is missing for congress, shorts_squeeze, institutional, market_tide, calendar, whale, or motif_bonus, the component returns **0.0** (no additive constant), so scoring is data-driven only. Reverted previous neutral-default change so that only real data moves the composite toward long or short.

**Source:** Droplet's `data/uw_flow_cache.json` was fetched via SSH; `scripts/signal_audit_diagnostic.py` was run **locally** with that cache. Enrichment path: enrich_signal → compute_composite_score_v2 (same as main.py). So the numbers below are from **droplet's actual cache data**.

## All signals available (22 components, all wired into trade engine)

All 22 components are defined in `uw_composite_v2.py` and used in `compute_composite_score_v2` → `_compute_composite_score_core`. The trade engine (main.py) gets composite from this path: `enriched = uw_enrich.enrich_signal(symbol, uw_cache, regime)` then `composite = uw_v2.compute_composite_score_v2(symbol, enriched, regime)`. So every signal is wired in; the issue is **which ones receive 0 or missing data**.

| Component | Wired | Typical source |
|-----------|-------|-----------------|
| flow, dark_pool, insider, iv_skew, smile, whale, event, motif_bonus, toxicity_penalty, regime | Yes | enriched_data / uw_flow_cache |
| congress, shorts_squeeze, institutional, market_tide, calendar | Yes | expanded_intel / symbol_intel / enriched_data |
| greeks_gamma, ftd_pressure, iv_rank, oi_change, etf_flow, squeeze_score, freshness_factor | Yes | enriched_data |

## Summary

- **Sample size:** 50 symbols
- **Error:** None
- **Composite distribution:** {'min': 0.169, 'max': 1.09, 'mean': 0.937, 'count': 50, 'pct_below_2': 100.0, 'pct_below_3': 100.0}

## Signals not working / passing 0 / not wired

| signal_name | failure_mode | suspected_root_cause | confidence |
|-------------|--------------|----------------------|------------|
| whale | zeroed | All values zero or constant zero | high |
| motif_bonus | zeroed | All values zero or constant zero | high |
| congress | zeroed | All values zero or constant zero | high |
| shorts_squeeze | zeroed | All values zero or constant zero | high |
| institutional | zeroed | All values zero or constant zero | high |
| calendar | zeroed | All values zero or constant zero | high |
| freshness_factor | unweighted | Effective weight near zero | high |

## Value audit (per-signal across samples)

- **event:** mean=0.3192, pct_zero=0.0%, constant=False
- **dark_pool:** mean=0.26, pct_zero=0.0%, constant=True
- **freshness_factor:** mean=0.2334, pct_zero=0.0%, constant=False
- **insider:** mean=0.125, pct_zero=0.0%, constant=True
- **squeeze_score:** mean=0.0952, pct_zero=0.0%, constant=False
- **greeks_gamma:** mean=0.08, pct_zero=0.0%, constant=True
- **oi_change:** mean=0.07, pct_zero=0.0%, constant=True
- **ftd_pressure:** mean=0.06, pct_zero=0.0%, constant=True
- **etf_flow:** mean=0.06, pct_zero=0.0%, constant=True
- **iv_rank:** mean=0.03, pct_zero=0.0%, constant=True
- **regime:** mean=0.012, pct_zero=0.0%, constant=True
- **toxicity_penalty:** mean=-0.2502, pct_zero=0.0%, constant=False
- **market_tide:** mean=0.3044, pct_zero=6.0%, constant=False
- **flow:** mean=2.208, pct_zero=8.0%, constant=False
- **iv_skew:** mean=0.1076, pct_zero=8.0%, constant=False
- **smile:** mean=0.0064, pct_zero=8.0%, constant=False
- **whale:** mean=0.0, pct_zero=100.0%, constant=True
- **motif_bonus:** mean=0.0, pct_zero=100.0%, constant=True
- **congress:** mean=0.0, pct_zero=100.0%, constant=True
- **shorts_squeeze:** mean=0.0, pct_zero=100.0%, constant=True
- **institutional:** mean=0.0, pct_zero=100.0%, constant=True
- **calendar:** mean=0.0, pct_zero=100.0%, constant=True

## Per-symbol breakdown (SPY, QQQ, COIN, NVDA, TSLA)

### SPY: score=1.038, missing=['dark_pool', 'whale', 'motif_bonus']
- Zero or missing: dark_pool, whale, motif_bonus, congress, shorts_squeeze, institutional, calendar

### QQQ: score=1.055, missing=['dark_pool', 'whale', 'motif_bonus']
- Zero or missing: dark_pool, whale, motif_bonus, congress, shorts_squeeze, institutional, calendar

### COIN: score=1.087, missing=['dark_pool', 'whale', 'motif_bonus']
- Zero or missing: dark_pool, whale, motif_bonus, congress, shorts_squeeze, institutional, calendar

### NVDA: score=1.048, missing=['dark_pool', 'whale', 'motif_bonus']
- Zero or missing: dark_pool, whale, motif_bonus, congress, shorts_squeeze, institutional, calendar

### TSLA: score=1.049, missing=['dark_pool', 'whale', 'motif_bonus']
- Zero or missing: dark_pool, whale, motif_bonus, congress, shorts_squeeze, institutional, calendar

## Root cause (why low scores)

Composite mean score is **0.937** (below MIN_EXEC_SCORE 2.5). 
**7** signals are dead or muted (zeroed, unweighted, or no contribution). 
**Root cause:** (1) **Six signals are 100% zero** on droplet's cache: whale, motif_bonus, congress, shorts_squeeze, institutional, calendar. They are wired in but **never get real data**—either expanded_intel/symbol_intel has no data for these symbols, or UW cache has no whale/motif/congress/shorts/institutional/calendar keys. (2) **Dark pool** is marked "missing" for SPY/QQQ/COIN/NVDA/TSLA (0 notional or NEUTRAL), so it contributes only the 0.2 baseline. (3) **Freshness_factor** is treated as unweighted in the diagnostic (it multiplies composite_raw; effective weight near zero in the audit). (4) Flow and event are the largest contributors (mean 2.2 and 0.32), but **composite mean is 0.937** because the six zeroed signals plus low dark_pool and modest flow/event keep the sum below 2.5.

**Fix (no strategy tuning):** (1) Populate **expanded_intel** (data/uw_expanded_intel.json) with congress, shorts, institutional, market_tide, calendar per symbol so those components stop being 0. (2) Ensure **whale** and **motif_bonus** get data when motif_whale/motif_staircase/motif_burst are present in enriched_data. (3) Verify UW daemon or intel pipeline writes these keys into uw_flow_cache or expanded_intel. (4) Optionally increase freshness or ensure cache is refreshed so freshness_factor does not crush scores.
