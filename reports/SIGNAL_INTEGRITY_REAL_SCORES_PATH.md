# Signal Integrity: Real Scores Path (Multi-Model Adversarial)

**Goal:** Actionable, real scores for profitable trades. No fake placeholders or hardcoded numbers. Signals must be collected somewhere and tied into the trading pipeline; if not working, fix them.

**Date:** 2026-02-23

---

## 1. Prosecutor (Adversarial)

**Claim:** Signals are broken in ways that prevent real scores and profitable trades.

**Evidence:**
- **Placeholders:** Conviction defaults to **0.5** when missing (`uw_composite_v2.py`); greeks component defaults to **0.2** when data missing. These inflate or distort scores when upstream data is absent.
- **Missing data sources:** Congress, shorts_squeeze, institutional, market_tide, calendar, whale, motif_bonus get **0** when expanded_intel/cache lack them. On droplet, six signals are 100% zero (per DROPLET_RUN_DATA_AND_ANSWERS.md) because no producer writes those keys into the cache for many symbols.
- **No single “signal health” store:** We cannot answer “which signals are working?” from one place. Score telemetry and snapshot exist but do not expose per-component “has_data” in a way the pipeline or ops can act on.
- **Enricher uses same cache:** iv_term_skew, smile_slope, event_alignment, toxicity are **derived** from conviction/sentiment/dark_pool (not from real options IV/smile). When cache is empty or stale, those derived values are still computed from defaults (e.g. conviction 0.5 in enricher) — so we get numbers that look real but are not from live data.

**Verdict:** Do not assume scores are actionable until (1) placeholders are removed, (2) every component either has a real data source or is explicitly zero when missing, and (3) signal health is collected and visible so we can fix missing data.

---

## 2. Defender (Pushback)

**Claim:** The pipeline is wired correctly; the issue is data availability and placeholder policy, not “signals not tied in.”

**Evidence:**
- **Daemon collects real data:** `uw_flow_daemon.py` polls UW API for flow (sentiment/conviction), dark_pool_levels, insider, calendar, greeks, oi_change, etf_flow, iv_rank, ftd_pressure, congress, institutional and writes per-ticker into `data/uw_flow_cache.json`. When the daemon runs and API returns data, those signals **are** real.
- **Enricher uses cache:** iv_term_skew, smile_slope, event_alignment, toxicity, freshness, motifs are computed from the same cache. So they are “real” in the sense of being derived from collected data; the problem is cache empty/stale or daemon not running, not “untied” signals.
- **build_expanded_intel** merges premarket + postmarket + cache; congress/insider/etc. come from cache (daemon) when present. So expanded_intel is not a separate source — it’s a merge. Fix is: ensure daemon and intel producers run and populate cache, not add more placeholders.

**Falsification:** If we remove the 0.5 conviction default and the 0.2 greeks default, scores may drop further when data is missing. That is **correct**: we should not trade on fake numbers. The fix is to ensure conviction and greeks are **collected** (daemon + health checks), not to keep placeholders.

**Verdict:** Accept removal of placeholders; invest in data collection and signal health visibility so we fix upstream instead of faking.

---

## 3. SRE / Operations

**Data contracts and collection:**

| Signal / component       | Data source                          | Collected by              | When missing |
|--------------------------|--------------------------------------|---------------------------|--------------|
| conviction, sentiment   | UW flow API                          | uw_flow_daemon            | Use 0 / NEUTRAL; log and telemetry |
| dark_pool                | UW dark_pool_levels                  | uw_flow_daemon            | Component 0; no constant |
| insider                  | UW insider API                       | uw_flow_daemon            | Component 0 |
| congress                 | UW congress_recent_trades (aggregate)| uw_flow_daemon            | Component 0 |
| institutional            | UW institutional endpoint            | uw_flow_daemon            | Component 0 |
| calendar                 | UW calendar                          | uw_flow_daemon            | Component 0 |
| greeks, oi_change, etf_flow, iv_rank, ftd_pressure | UW daemon pollers | uw_flow_daemon            | Component 0; no 0.2 default |
| iv_term_skew, smile_slope, event_alignment, toxicity, freshness | Enricher from cache | uw_enrichment_v2 (enrich_signal) | From cache only; no fake defaults in composite |
| whale, motif_*            | TemporalMotifDetector (history)      | uw_enrichment_v2          | 0 when not detected |
| market_tide              | UW market_tide                       | uw_flow_daemon            | Component 0 |

**Checklist (droplet):**
1. **uw_flow_daemon** running and writing `data/uw_flow_cache.json`; file present and mtime &lt; 15 min.
2. **Intel producers** (run_intel_producers_on_droplet.sh): build_daily_universe → run_premarket_intel → run_postmarket_intel → build_expanded_intel so expanded_intel is merged from cache.
3. **No placeholders:** Conviction missing → 0.0 in composite and log/telemetry; greeks missing → 0.0 (remove 0.2 neutral default).
4. **Signal health:** One place (e.g. `state/signal_health.json` or `logs/signal_health.jsonl`) records per-symbol per-component `has_data` (and optionally contribution) so we can see which signals are working.

---

## 4. Board (Agreed Path Forward)

**Decisions:**
1. **No fake placeholders.**  
   - Conviction: when missing/None, use **0.0** in composite (not 0.5). Log/telemetry when conviction is missing so we fix upstream.  
   - Greeks: when greeks_data is missing, use **0.0** (remove 0.2 neutral default).  
   - No other hardcoded “neutral” numbers that inflate score when data is absent.

2. **Collect signal health in one place.**  
   - Record per-symbol, per-component whether the component had real data (e.g. from `component_sources` / composite_meta).  
   - Write to `logs/signal_health.jsonl` (append) or update `state/signal_health.json` so dashboard/scripts can answer “which signals are working?”  
   - Tie this into the same path that already has composite result (e.g. where we call append_score_snapshot / score telemetry).

3. **Ensure data is collected.**  
   - Daemon must run on droplet; cache must be populated and fresh.  
   - Intel producers (premarket, postmarket, build_expanded_intel) must run so expanded_intel reflects cache.  
   - Add or use existing health check: fail or alert if `uw_flow_cache.json` is missing or stale for key symbols.

4. **Plugins / tooling.**  
   - Use config/tuning and attribution schema (e.g. compound-engineering-context or repo docs) when adding telemetry or new signal fields so naming stays consistent.  
   - Multi-model runner and reports can consume signal_health (and score telemetry) for evidence-based verdicts.

5. **Trade integrity preserved.**  
   - We are **not** lowering gates or letting all trades through. We are ensuring scores are **real** (from collected data or explicitly 0 when missing). Profitable trades come from actionable scores; actionable scores require real signals.

---

## 5. Implementation Summary

| Item | Action |
|------|--------|
| Conviction when missing | `uw_composite_v2`: use 0.0 (not 0.5); optional: log or pass to telemetry “conviction_missing”. |
| Greeks when missing | `uw_composite_v2`: use 0.0 (remove 0.2 neutral default). |
| Signal health | Add `append_signal_health(symbol, component_sources, components)` writing to `logs/signal_health.jsonl`; call from main where composite_meta is available. |
| Daemon / cache | Document in runbook; verify droplet runs daemon + intel producers; health check cache presence/freshness. |
| Enricher defaults | Keep enrich_signal passing through cache only; composite already gets enriched_data — no extra placeholders in composite beyond the two removals above. |

---

## 6. References

- MEMORY_BANK.md §7 (Scoring Pipeline Contract)
- SIGNAL_SCORE_PIPELINE_AUDIT.md
- reports/investigation/DROPLET_RUN_DATA_AND_ANSWERS.md
- reports/signal_review/SCORING_PIPELINE_AUDIT_SUMMARY.md
- reports/ACTIONABLE_NEXT_STEPS_AND_PLUGINS.md (plugins for schema/docs)
