# Dashboard Panel Wiring

**Generated:** 2026-01-28T16:08:19.715054+00:00

## Data source

- **Cache path:** `config.registry.CacheFiles.UW_FLOW_CACHE` → `/root/stock-bot/data/uw_flow_cache.json`
- **Dashboard:** reads cache via `read_json(cache_file)` in `api_positions` / score logic.
- **UW endpoint panels:** data from `sre_monitoring.get_sre_health()` → `uw_api_endpoints`.

## SRE health (uw_api_endpoints)

- **Source:** `sre_monitoring.check_uw_api_health()` checks **single** cache file `data/uw_flow_cache.json`.
- **Per-endpoint status:** same cache file; if cache missing or stale, all endpoints show unhealthy.
- **Message when cache missing:** `Cache file does not exist - UW daemon may not have started`.

## Expected behavior

- Panel wired to correct path: yes (single cache for all).
- Panel reads expected fields: yes (cache dict keyed by symbol).
- Missing cache handling: SRE returns status `no_cache` / `stale`; dashboard shows error in panel.
- Error rate: from uw_error.jsonl per endpoint URL (if present).
