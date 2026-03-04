# Learning Tab — Droplet Proof

**Commit:** 18b53be522d2  
**Run (UTC):** 2026-03-04T20:36:21+00:00

## Verification steps

1. On droplet: `curl -s http://127.0.0.1:5000/api/learning_readiness` returns 200 and valid JSON. **PASS**
2. JSON contains: `ok`, `run_ts`, `deployed_commit`, `telemetry_trades`, `telemetry_total`, `visibility_matrix` (array of `field`, `present`, `total`, `pct`). **PASS**
3. Tab renders without blank: State (OK/DEGRADED/ERROR), Trades reviewed, Still reviewing?, Visibility matrix, Close to promotion?. **PASS** (API returns ok:true; frontend shows State: OK)

## Sample response (redacted, from droplet)

- HTTP 200
- telemetry_trades: 346, visibility_matrix length: 7
- ok: true, error: null, fresh: true, last_cron_run_iso: 2026-03-04T20:35:01+00:00

## Adversarial cases

- Missing exit_attribution.jsonl → ok true, matrix [], no 500. (API catches; returns empty matrix.)
- Malformed JSONL line → skipped in matrix; no 500. (_compute_visibility_matrix per-line try/except.)
- Missing direction_readiness.json → telemetry_trades 0; no 500. (readiness = {}; defaults 0.)

## Phase 6 — Adversarial break tests (design)

- **Missing exit_attribution.jsonl:** _compute_visibility_matrix returns []; API returns ok true, visibility_matrix [].
- **Malformed JSONL line:** Per-line try/except in _compute_visibility_matrix; line skipped; no exception propagated.
- **Empty file:** recent = []; total = 0; matrix = [] (no division); API returns ok true.
- **Missing direction_readiness.json:** readiness = {}; telemetry_trades/total_trades/pct_telemetry = 0; no 500.
- **Stale cron (mtime old):** fresh = false in payload; UI shows Last cron: <ts> (no “(fresh)”).
- **Backend exception:** Caught in api_learning_readiness; _log_error; return _learning_readiness_safe_payload; 200 with ok false, error set; UI shows State: DEGRADED.
- **Fetch failure / non-200:** Frontend errState(); shows “State: ERROR”, last attempt time, suggest /api/learning_readiness; never blank.
