# Alpaca dashboard fix implementation log (SRE)

**Artifact ID:** `ALPACA_DASHBOARD_FIX_IMPLEMENTATION_20260326_1900Z`  
**CSA:** Dashboard-only changes; no trading logic.

---

## Implemented (this branch)

1. **`DASHBOARD_HTML`**
   - Inserted `#direction-banner` with classes `direction-banner __BANNER_SEV__` and inner `__BANNER_HTML__`.
   - Inserted `#situation-strip` with `__SITUATION_HTML__`.
   - Added CSS for banner severities (`info`, `warning`, `error`, `success`), situation strip, promo badges.

2. **Boot + refresh**
   - Initial `setTimeout`: also calls `loadDirectionBanner()` and `loadSituationStrip()`.
   - Replaced no-op 60s `setInterval` with banner + situation refresh.

3. **`/api/telemetry/latest/computed`**
   - Missing bundle / unknown name / missing file → **HTTP 200** with `ok: false`, `error`, `data: null`, `as_of_ts`.
   - Successful read → `ok: true` plus prior fields.

4. **Telemetry tab JS**
   - **STALE / INCOMPLETE TELEMETRY** banner when `live_vs_shadow_pnl`, `signal_performance`, or `signal_weight_recommendations` returns `ok: false`.

5. **Signal review empty state**
   - Expanded copy to cite endpoint and typical log path.

6. **Self-heal ledger `fetch`**
   - `credentials: 'same-origin'` and explicit non-OK rejection → catch shows error row.

7. **`scripts/dashboard_verify_all_tabs.py`**
   - Expanded `TAB_ENDPOINTS` to match tab/strip coverage.

8. **`scripts/alpaca_dashboard_truth_probe.py`** (new)
   - Emits `reports/ALPACA_DASHBOARD_DATA_SANITY_20260326_1900Z.json`.

---

## Evidence

- JSON: `reports/ALPACA_DASHBOARD_DATA_SANITY_20260326_1900Z.json` — **22/22** endpoints HTTP 200 (local probe).

---

## Not implemented here

- Droplet deploy / systemd restart (operator).
- Top-strip explicit STALE on swallowed fetch failures.
- Removal or relabeling of Kraken row in System Health (product decision).
