# UW polling + caching + shadow tracking policy

**Goal:** Stay close to UW quota limits *without* wasting calls, while ensuring we have the data we need during market hours and can measure the impact of slower intel via shadow logging.

## Data flow (current)

- **Only component that should call UW:** `uw_flow_daemon.py`
- **Primary cache:** `data/uw_flow_cache.json`
- **Quota audit log (every UW call):** `data/uw_api_quota.jsonl` (`CacheFiles.UW_API_QUOTA`)
- **Trading engine consumption:** `main.py` reads the cache; composite scoring uses cache + enrichment.
- **Shadow tracking (rejected signals):** `self_healing/shadow_trade_logger.py` logs rejected signals (with components), and `shadow_tracker.py` tracks virtual positions for some blocked signals.

## Verified endpoints (no guessing)

These are listed as ✅ working in `UW_API_ENDPOINTS_OFFICIAL.md` and/or `UW_API_ENDPOINT_VERIFICATION.md`:

- `/api/option-trades/flow-alerts` (params: `symbol`, `limit`)
- `/api/darkpool/{ticker}`
- `/api/stock/{ticker}/greeks`
- `/api/stock/{ticker}/greek-exposure`
- `/api/stock/{ticker}/max-pain`
- `/api/stock/{ticker}/oi-change`
- `/api/stock/{ticker}/iv-rank`
- `/api/shorts/{ticker}/ftds`
- `/api/etfs/{ticker}/in-outflow` (may return empty for non-ETF tickers)
- `/api/insider/{ticker}`
- `/api/calendar/{ticker}`
- `/api/market/top-net-impact`
- `/api/market/market-tide`

## 404 endpoints (fixed by discovery + correct endpoints)

Per repo docs, these **do not exist per-ticker** and return 404:

- `/api/congress/{ticker}` (❌ 404)
- `/api/institutional/{ticker}` (❌ 404)

**Policy:** we do **not** keep calling known-404 paths. Instead, the daemon now supports **endpoint discovery**:
- It reads candidate endpoint paths from env vars:
  - `UW_CONGRESS_ENDPOINT_CANDIDATES`
  - `UW_INSTITUTIONAL_ENDPOINT_CANDIDATES`
- It probes candidates with your real UW key and **only uses endpoints that return HTTP 200**.
- The last-known-good endpoints are persisted to `state/uw_endpoint_discovery.json`.

This is the only safe way to “fix” 404s without hallucinating endpoints, because UW may expose congress/institutional under different paths (often market-wide or a different parameterization).

## OpenAPI source (“save it and use it”)

UW’s docs page at `https://api.unusualwhales.com/docs#/` loads the official OpenAPI YAML from:

- `https://api.unusualwhales.com/api/openapi`

This repo now fetches and caches a compact catalog of endpoints to:

- `state/uw_openapi_catalog.json`

The daemon uses that catalog to select the correct congress and institutional endpoints.

## Polling cadence rules (market hours)

### High-frequency (market alpha)
- **Option flow**: every 150s
- **Dark pool**: every 600s
- **Top net impact / market tide**: every 300s
- **Greeks / Greek exposure**: every 1800s
- **OI change / max pain**: every 900s
- **IV rank / ETF flow / FTDs**: unchanged from daemon defaults unless tuned

### Slow-moving intel (quota optimized)

#### Calendar
- **Baseline**: weekly (7 days)
- **Accelerate near events** (best-effort from cached calendar payload):
  - within 30 days: daily
  - within 7 days: every 6 hours
  - within 2 days: hourly

#### Insider
- **Daily** (24 hours)

#### Congress (market-wide)
- **Daily**: poll `/api/congress/recent-trades` once and distribute summaries into each ticker’s cache entry.

#### Institutional ownership
- **Daily per ticker**: poll `/api/institution/{ticker}/ownership` and store concentration summaries.

### Off-hours behavior
Outside market hours the daemon normally polls **3× less frequently** to conserve quota.

**Exception:** daily/weekly endpoints keep their cadence even off-hours:
- `calendar`
- `insider`

## Shadow tracking policy (new)

When signals are blocked by gates (score gate / expectancy gate), the shadow logger now receives:

- **Composite component scores** (existing)
- **Component sources + expanded intel flags** (from `composite_meta`)
- **Compact UW cache snapshot** (no raw `flow_trades` array):
  - sentiment/conviction/trade_count/flow_trades_n
  - dark_pool, insider, calendar, market_tide
  - greeks, oi_change, iv_rank, etf_flow, ftd_pressure
  - congress/institutional placeholders (currently `{}`)

This lets us quantify “what would have happened” if slow intel were weighted differently, without immediately promoting it to trade signals.

## How to measure real UW usage

Run:

```bash
python3 analyze_uw_usage.py --hours 24 --daily-limit 15000
```

This reads `data/uw_api_quota.jsonl` and summarizes:
- total calls
- calls/day (ET) utilization
- top endpoints and tickers
- peak calls/minute

