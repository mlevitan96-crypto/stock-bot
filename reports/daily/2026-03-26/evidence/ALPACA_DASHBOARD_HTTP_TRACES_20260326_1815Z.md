# Alpaca dashboard — HTTP trace proof

**Timestamp:** 20260326_1815Z  
**Base:** `http://127.0.0.1:5000` on droplet

## Commands

```bash
# Operational activity (Basic auth — required on this instance for this path)
curl -sS -u "$DASHBOARD_USER:$DASHBOARD_PASS" \
  "http://127.0.0.1:5000/api/alpaca_operational_activity?hours=72"

curl -sS -u "$DASHBOARD_USER:$DASHBOARD_PASS" \
  "http://127.0.0.1:5000/api/telemetry/latest/computed?name=data_integrity"
```

## Results

| Request | HTTP | Notes |
|--------|------|--------|
| `GET /api/alpaca_operational_activity?hours=72` | **200** | `disclaimer` contains exact CSA line; `generated_at_utc` freshness |
| `GET /api/telemetry/latest/computed?name=data_integrity` | **200** | `ok`: **false**, `error`: `unknown computed artifact: data_integrity` — **PARTIAL** (expected for missing bundle artifact); `as_of_ts` present |

Full JSON bodies: `reports/ALPACA_DASHBOARD_HTTP_TRACES_20260326_1815Z.json`.
