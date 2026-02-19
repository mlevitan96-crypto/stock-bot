# Scoring Pipeline Integrity — Multi-Model Adversarial Plan

## Ways scoring could silently break

- **Composite vs min gate score mismatch:** Min-score gate uses adjusted `score` (after signal_quality, UW, survivorship, regime/macro); expectancy gate uses `c.get("composite_score", score)` (raw cluster composite). If cluster has `composite_score` set, expectancy sees raw value; min gate sees adjusted value → candidate can pass min gate then fail expectancy on score_floor_breach.
- **Freshness decay:** Composite applies `composite_raw * freshness`; stale cache → low freshness → scores suppressed; diagnostic using different freshness or no decay can diverge from live.
- **Default/fallback values:** `getattr(Config, "MIN_EXEC_SCORE", 3.0)` in main vs `Config.MIN_EXEC_SCORE` from env 2.5 → wrong floor if Config not loaded.
- **NaN/Inf in components:** Any component producing NaN/Inf can poison sum or clamp; need defensive checks in composite and gate.
- **Weight application:** Missing or zero weights, wrong key names (e.g. flow vs options_flow) can zero out components.
- **Cluster source vs score path:** Clusters with `source` not in ("composite", "composite_v3") skip structural_intelligence block; score may stay raw while expectancy still uses c["composite_score"].
- **Self-healing threshold:** Raises min_score above MIN_EXEC_SCORE; min gate uses adjusted threshold, expectancy_floor stays MIN_EXEC_SCORE → possible inconsistency.
- **Score snapshot / diagnostic path:** Different code path (e.g. dashboard v3 vs main v2) can yield different scores for same symbol/cache.

## Ways systemd could be running stale or dead workers

- **Single unit, subprocess model:** One systemd unit (trading-bot or stockbot) runs deploy_supervisor.py; no separate predictive_engine, ensemble_predictor, signal_resolver, feature_builder units. Stale = supervisor not restarted after deploy; dead = one of dashboard, uw-daemon, trading-bot crashed and restart loop or not restarted.
- **WorkingDirectory / path:** If service uses wrong WorkingDirectory, cache paths (e.g. data/uw_flow_cache.json) can be wrong or missing.
- **Import errors on start:** Any missing module or env causes exit before main loop; journalctl would show traceback.
- **uw_flow_daemon not writing cache:** If daemon crashes or rate-limited, uw_flow_cache.json stale or empty → no clusters or zero scores.

## Ways signals could be missing, zero, NaN, or stale

- **UW cache empty or old:** uw_flow_daemon.py writes data/uw_flow_cache.json; if daemon down or API failure, cache not updated.
- **Enrichment defaults:** enrich_signal returning None or missing keys; conviction/sentiment defaulting to 0 or NEUTRAL.
- **Expanded intel missing:** _load_expanded_intel() missing symbol → symbol_intel = {} → congress/shorts/inst/tide/calendar components zero.
- **Feature builders not run:** If any signal provider is optional and fails silently, component stays 0.

## Ways composite scores could be mis-constructed

- **Component name mismatch:** COMPONENT_TRACKING_VERIFICATION.md notes flow vs options_flow, iv_skew vs iv_term_skew etc.; wrong keys → wrong or zero components.
- **Sum order / clamp:** composite_raw sum then * freshness then clamp 0–8; any component omitted from sum or double-counted.
- **Regime/adaptive weights:** get_adaptive_weights(regime) returning None or wrong regime → wrong weights.
- **Whale boost applied after clamp:** whale_conviction_boost applied after clamp; if logic order wrong, score can be inconsistent.

## Ways caches could be stale or empty

- **uw_flow_cache.json:** Only updated by uw_flow_daemon; timestamp or file mtime not checked before scoring.
- **State files:** signal_weights.json, regime_detector_state.json, etc.; if not written or wrong path, defaults used.
- **Directories.STATE/DATA:** Resolved from CWD; if process starts from different CWD, paths wrong → empty caches.

## Ways diagnostics could diverge from live scoring

- **Different entry point:** Diagnostic scripts call compute_composite_score_v3 or v2 with local cache; main.py uses same module but cache loaded by supervisor/main process.
- **Different regime:** Live uses market_regime from loop; diagnostic may use fixed "mixed" or "NEUTRAL".
- **Score used for gate:** Live uses `score` (adjusted) for min gate and c["composite_score"] for expectancy; diagnostic may only compare raw composite to threshold.

---

*This plan informs Phases 2–7. Root cause chosen in Phase 7.*
