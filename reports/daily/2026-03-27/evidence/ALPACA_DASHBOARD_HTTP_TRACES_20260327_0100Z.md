# Alpaca dashboard — HTTP trace proof (Phase 4)

**Timestamp:** `20260327_0100Z`  
**Environment:** Cursor agent workspace; **not** Alpaca droplet.

## Verdict

**NOT EXECUTED — BLOCKED**

## Required on droplet (minimum)

After auth (Basic) or session as your stack requires:

| Endpoint | Purpose |
|----------|---------|
| `GET /api/alpaca_operational_activity?hours=72` | Operational activity panel + disclaimer |
| `GET /api/telemetry/latest/index` | Telemetry tab freshness (`as_of_ts` if present) |
| `GET /api/telemetry/latest/computed?name=live_vs_shadow_pnl` | Telemetry partial/OK behavior |
| `GET /api/dashboard/data_integrity` | System Health (`generated_at_utc`) |
| `GET /api/stockbot/fast_lane_ledger` | Fast Lane tab |
| `GET /api/sre/health` | SRE tab |
| `GET /api/executive_summary` | Executive tab |

Capture status line + JSON body (truncate large bodies in markdown; keep full JSON in companion file).

## Local workspace trace (control only)

```text
$ curl.exe -m 3 -sS -w "\nhttp_code=%{http_code}\n" http://127.0.0.1:5000/api/ping
curl: (7) Failed to connect to 127.0.0.1 port 5000 ...
http_code=000
```

This confirms **no** dashboard was listening on the agent’s loopback; it is **not** droplet evidence.
