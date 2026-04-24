# ALPACA — PnL market day (Phase 4)

**ET date:** `2026-03-27`  
**Evidence JSON:** `ALPACA_PNL_MARKET_DAY_20260327_224500Z.json`  
**Droplet script:** `/tmp/_droplet_pnl_session_bundle.py` (uploaded from this folder)

## Headline (calendar ET day, exit_attribution rows)

| Field | Value |
|--------|------:|
| **Net realized PnL (USD)** | **1.91** (sum of `snapshot.pnl` / `pnl` where present, n=256) |
| **Gross PnL (% points sum)** | **13.14** (sum of `pnl_pct` where present) |
| **Fees** | **Not available** in session — heuristic scan of `orders.jsonl` `type=order` for `commission`/`fee`/`fees` → **0 hits** |
| **Trade count (exits in window)** | **256** |
| **Win rate (% of exits w/ pnl_pct)** | **48.05%** |
| **Avg win / loss (pnl%)** | **0.454 / -0.331** |
| **Worst trade (USD)** | **-8.40** `open_LCID_2026-03-27T13:37:04.806312+00:00` |
| **Worst hour (ET, by sum USD)** | **Hour 15** → **-40.78 USD** |

## Intraday (ET hour, realized USD)

| Hour (ET) | Sum pnl_usd | Count |
|-----------|------------:|------:|
| 10 | 6.66 | 51 |
| 11 | 30.75 | 28 |
| 12 | -9.76 | 55 |
| 13 | 14.18 | 34 |
| 14 | 0.86 | 30 |
| 15 | -40.78 | 58 |

## Top contributors / detractors (USD)

See JSON: `top_contributors_usd`, `worst_detractors_usd` (HOOD +14.38, LCID -15.42 symbol-level net, etc.).

## Integrity gates (no relaxation)

| Gate | Result |
|------|--------|
| **Strict session (open→16:00 ET)** | **ARMED** — 255 seen, 255 complete, 0 incomplete |
| **Dashboard-aligned (STRICT_EPOCH_START)** | **BLOCKED** — 580 seen, 578 complete, **2** incomplete (`no_orders_rows_with_canonical_trade_id`) |
| **Join coverage (session post-close)** | **PASS** — dry-run `join_gate=PASS`, `APPROVED_PLAN=YES` |
| **Fees / economics** | **Gap** — no fee fields located on session orders JSONL |
| **Calendar vs strict count** | **256** exit rows in full ET day vs **255** strict-closed trades to 16:00 ET — one marginal boundary trade |

**Supporting CSV:** none generated; numeric series are in JSON.
