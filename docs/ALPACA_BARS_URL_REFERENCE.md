# Alpaca Market Data — Bars URL reference

For **regular (non-broker) accounts**. Source: [Historical bars](https://docs.alpaca.markets/reference/stockbars), [Getting Started](https://docs.alpaca.markets/docs/getting-started-with-alpaca-market-data), [Market Data FAQ](https://docs.alpaca.markets/docs/market-data-faq).

## URL for historical stock bars

| Environment | Historical bars base URL |
|-------------|---------------------------|
| **Production (live/paid)** | `https://data.alpaca.markets` |
| **Sandbox (paper)** | `https://data.sandbox.alpaca.markets` |

**Endpoint:** `GET /v2/stocks/bars`  
**Full URL example:** `https://data.alpaca.markets/v2/stocks/bars`

Never call this endpoint on trading hosts (`api.alpaca.markets` / `paper-api.alpaca.markets`); market data is only on the `data.*` hosts.

## Authentication (regular users)

Use HTTP headers (not Basic auth):

- `APCA-API-KEY-ID`: your API key
- `APCA-API-SECRET-KEY`: your API secret

Same credentials as for the Trading API; use the key/secret from your Alpaca dashboard (API Keys).

## Query parameters

| Parameter | Description |
|-----------|-------------|
| `symbols` | Comma-separated symbols, e.g. `SPY` or `SPY,AAPL` |
| `timeframe` | e.g. `1Min`, `1Day` |
| `start` | Start of range (RFC-3339 or `YYYY-MM-DD`) |
| `end` | End of range (RFC-3339 or `YYYY-MM-DD`) |
| `limit` | Max 10000 per request |
| `page_token` | For pagination (from previous response `next_page_token`) |
| `feed` | Optional: `iex` (free, no subscription) or `sip` (all US exchanges; subscription may be required). Default is best available for your subscription. |

## Paid account (production)

For a **paid/live** account:

1. Use **production** data host: `ALPACA_DATA_URL=https://data.alpaca.markets` (or leave unset and ensure `ALPACA_BASE_URL` does not contain "paper" or "sandbox" so the app defaults to production data).
2. Ensure `ALPACA_KEY` and `ALPACA_SECRET` in `instance_a/.env` are your **production** API key/secret from the dashboard.
3. If you get **403 Forbidden**: check [Market Data FAQ](https://docs.alpaca.markets/docs/market-data-faq) — wrong host, wrong credentials, or insufficient permissions. For historical bars with `feed=iex`, no subscription is needed; for SIP or recent data, a subscription may be required.

## Verification curl (production)

```bash
source instance_a/.env
curl -s -o /dev/null -w "%{http_code}\n" \
  -H "APCA-API-KEY-ID: $ALPACA_KEY" \
  -H "APCA-API-SECRET-KEY: $ALPACA_SECRET" \
  "https://data.alpaca.markets/v2/stocks/bars?symbols=SPY&timeframe=1Day&limit=5"
```

Expect `200` if credentials and host are correct.

## 30-day bar coverage: fill gaps only (no full re-fetch)

We use **existing** Alpaca bars from previous runs. For 30d coverage we **fill in only missing (symbol, date)** from Alpaca; we do **not** re-fetch 30 days from scratch.

- **Bars cache:** `data/bars/` (and `data/bars/YYYY-MM-DD/SYMBOL_1Min.json`).
- **Find gaps:** `scripts/analysis/find_exits_missing_bars.py` — compares exits (from normalized exit truth or exit_attribution) to cached bars; outputs `missing_bars.json`.
- **Fetch only missing:** `scripts/analysis/fetch_missing_bars_from_alpaca.py` — fetches from Alpaca only the (symbol, date) in `missing_bars.json` and writes into `data/bars`.

**Scripts:**

| Goal | Script |
|------|--------|
| Fill gaps for last 30d using `logs/exit_attribution.jsonl` | `python scripts/fill_alpaca_bars_30d.py --days 30` |
| Fill gaps using existing normalized exit truth + grid rerun | `bash scripts/CURSOR_FETCH_MISSING_BARS_AND_RERUN_GRID.sh` (set `HIST_RUN_DIR` to a run that has `normalized_exit_truth.json`) |

Run on the droplet so `ALPACA_KEY`/`ALPACA_SECRET` and `logs/exit_attribution.jsonl` are available.
