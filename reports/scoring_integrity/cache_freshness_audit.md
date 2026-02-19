# Cache & Data Freshness Audit

## Key caches

| Cache | Path | Updated by | Used by |
|-------|------|------------|---------|
| uw_flow_cache | data/uw_flow_cache.json | uw_flow_daemon | main.py, enrichment, composite |
| score_snapshot | state/score_snapshot.jsonl or logs/ | main.py (append_score_snapshot) | Truth audit |
| signal_weights | state/signal_weights.json | Adaptive/learning | composite optional |
| regime_detector_state | state/regime_detector_state.json | Regime detector | structural_intelligence |

## Freshness and timestamps

- **uw_flow_cache:** No in-file timestamp in standard schema; daemon writes periodically. Staleness inferred by mtime or last log from daemon.
- **Enrichment:** freshness computed inside enrich_signal from cache/context; applied in composite as multiplier.
- **Missing keys:** enrich_signal and composite use defaults (e.g. conviction 0.5, NEUTRAL); missing symbol in expanded_intel → zeros for congress/shorts/inst/tide/calendar.

## Empty caches

- If uw_flow_cache.json missing or {}: no clusters or zero scores from UW path.
- Directories resolved from CWD (config/registry Paths); if process CWD differs, paths can point to wrong dir (see score_snapshot path fix in snapshot_fix).

## Verification

- On droplet: `ls -la data/uw_flow_cache.json`, `python3 -c "import json; d=json.load(open('data/uw_flow_cache.json')); print(len(d))"`.
- Check score_snapshot_writer uses CWD-independent path (STATE / "score_snapshot.jsonl" or similar).
