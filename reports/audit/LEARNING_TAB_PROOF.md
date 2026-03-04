# Learning Tab — Droplet Proof

**Commit:** (fill after deploy)  
**Run (UTC):** (fill after verification)

## Verification steps

1. On droplet: `curl -s http://127.0.0.1:5000/api/learning_readiness` returns 200 and valid JSON.
2. JSON contains: `ok`, `run_ts`, `deployed_commit`, `telemetry_trades`, `telemetry_total`, `visibility_matrix` (array of `field`, `present`, `total`, `pct`).
3. Tab renders without blank: State (OK/DEGRADED/ERROR), Trades reviewed, Still reviewing?, Visibility matrix, Close to promotion?.

## Sample response (redacted)

```json
{
  "ok": true,
  "run_ts": "...",
  "deployed_commit": "...",
  "telemetry_trades": 0,
  "telemetry_total": 0,
  "visibility_matrix": [],
  "error": null
}
```

## Adversarial cases

- Missing exit_attribution.jsonl → ok true, matrix [], no 500.
- Malformed JSONL line → skipped in matrix; no 500.
- Missing direction_readiness.json → telemetry_trades 0; no 500.
