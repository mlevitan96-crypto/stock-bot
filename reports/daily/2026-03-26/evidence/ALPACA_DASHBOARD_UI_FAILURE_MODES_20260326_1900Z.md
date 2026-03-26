# Alpaca dashboard UI failure mode audit (SRE)

**Artifact ID:** `ALPACA_DASHBOARD_UI_FAILURE_MODES_20260326_1900Z`  
**Source:** Static review of `dashboard.py` embedded JS + Flask handlers.

---

## Matrix (tab vs condition)

| Tab / surface | Endpoint 404 / HTTP error | Empty data | Stale / missing artifact |
|---------------|---------------------------|------------|---------------------------|
| Positions | Shows server status + login hint | “No open positions” + source line | N/A (Alpaca snapshot) |
| Closed trades | Red error div | Table with 0 rows + strict snapshot line | Partial via `alpaca_strict_eval_error` |
| System health | Message if `data_integrity` null | Partial panels | Log staleness table; Alpaca strict block |
| Executive | Red error div | Still shows zeros / empty trades | Not labeled STALE (disclaimer: not strict cohort) |
| SRE | Red error on load | Partial cards | Version panels may show mismatch |
| Signal review | Red error div | **Now** explains source + not a loading error | Last signal strip → red if old |
| Telemetry | Was: **silent cascade** if computed 404 in `Promise.all` | Bundle message | **Now:** orange **STALE / INCOMPLETE TELEMETRY** banner when `ok: false` on required computeds |
| Learning | ERROR / DEGRADED cards | “No exits yet” in matrix | `fresh` flag in payload |
| Profitability | Error div | Cockpit empty + runbook text | n/a |
| Fast lane | Error div | “No cycles yet” + run command | `d.error` banner |
| Direction banner | Unavailable text | N/A | SSR + 60s refresh |
| Situation strip | Shows “—” | Same | 60s refresh |
| Self-heal ledger | Row error on fetch failure | “No events” | **Now:** `credentials: 'same-origin'` + HTTP check |

---

## Remaining honesty gaps (not fixed in this pass)

- **Top strip** still shows `—` or zeros if SRE/executive fetch fails without a persistent **STALE** banner (failures are swallowed in `loadTopStrip` with `catch → null`).
- **`/sre` standalone HTML** (separate page) is out of scope for this Alpaca tab audit but shares APIs.
