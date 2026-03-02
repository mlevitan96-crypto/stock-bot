# Signal Ingestion Audit

**Date:** 2026-03-02  
**Purpose:** Confirm every signal we ingest provides a number (or documented default); no artificial inflation when data is missing.

## Design principle

- **Conviction:** `0` when there is no conviction/data; positive magnitude when flow supports it; direction from sentiment (BULLISH/BEARISH). We do not inflate with a neutral constant (e.g. 0.5) when the value is missing.
- **All numeric fields:** Source (daemon or enrichment) must set a value or we explicitly default to `0` / empty; composite uses `_to_num(..., 0.0)` so missing/None become 0.

---

## 1. Options flow (primary)

| Field        | Source                    | Provides number? | Notes |
|-------------|----------------------------|------------------|--------|
| `sentiment` | UW daemon / enrichment      | Yes (string)     | BULLISH / BEARISH / NEUTRAL. Daemon sets from flow; enrichment derives from `_derive_conviction_from_flow_trades` when missing. |
| `conviction`| UW daemon / enrichment      | Yes (float)      | Daemon: always set in `_normalize_flow_data` (0.05–1.0) or 0.0 when no flow. Enrichment: from cache or derived from `flow_trades` via `_derive_conviction_from_flow_trades`; **0 when no flow and not in cache**. Composite: `flow_conv = _to_num(conv_raw) if conv_raw is not None else 0.0`. |
| `trade_count` | UW daemon / enrichment   | Yes (int)        | From cache or `len(flow_trades)`; default 0. |
| `total_premium`, `call_premium`, `put_premium`, `net_premium` | Daemon | Yes | Set in `_normalize_flow_data`; 0.0 when no flow. |

**Fixes applied:**  
- Enrichment: no 0.5 default; use cache value, else derive from `flow_trades`, else 0.  
- Composite: missing conviction → 0.0 (not 0.5).  
- Daemon: when preserving existing `flow_trades`, always derive and write `conviction`/`sentiment` from `_normalize_flow_data`.

---

## 2. Dark pool

| Field                 | Source   | Provides number? | Notes |
|-----------------------|----------|------------------|--------|
| `sentiment`           | Daemon   | Yes (string)     | BULLISH/BEARISH/NEUTRAL; empty → "NEUTRAL". |
| `total_notional`      | Daemon   | Yes              | `_normalize_dark_pool`; empty fallback has `total_notional`: 0.0. |
| `total_notional_1h`   | Daemon   | Yes              | In normalized payload; empty fallback now includes `total_notional_1h`: 0.0. |
| `total_premium`       | Daemon   | Yes              | Same as total_notional in daemon; fallback 0.0. |

**Fixes applied:**  
- Daemon empty dark_pool fallback now includes `total_notional` and `total_notional_1h`: 0.0 so composite always gets a number.

---

## 3. Insider

| Field                 | Source | Provides number? | Notes |
|-----------------------|--------|------------------|--------|
| `sentiment`           | Cache  | Yes (string)     | Default "NEUTRAL". |
| `net_buys`, `net_sells` | Cache | Yes (int)      | Composite uses as-is; daemon stores API response. |
| `total_usd`           | Cache  | Yes              | `_to_num(..., 0)`. |
| `conviction_modifier` | Cache  | Yes              | `_to_num(ins.get("conviction_modifier", 0.0))`. |

---

## 4. Congress / institutional

| Field             | Source | Provides number? | Notes |
|-------------------|--------|------------------|--------|
| `recent_count`, `buys`, `sells` | Cache | Yes (int) | Default 0 in composite. |
| `conviction_boost`| Cache  | Yes              | `_to_num(..., 0.0)`. |
| Institutional (top_holder_pct, etc.) | Cache | Yes | `_to_num` with 0.0. |

---

## 5. Shorts / FTD

| Field          | Source | Provides number? | Notes |
|----------------|--------|------------------|--------|
| `ftd_count`    | Cache  | Yes              | `_to_num(..., 0)`; daemon normalizes via `_normalize_ftd_for_composite`. |
| `squeeze_risk` | Cache | Yes (bool)       | Default False. |
| `interest_pct`, `days_to_cover` | Cache | Yes | `_to_num` with 0. |

---

## 6. Market tide

| Field              | Source | Provides number? | Notes |
|--------------------|--------|------------------|--------|
| `call_premium`, `put_premium`, `net_call_premium`, `net_put_premium` | Cache | Yes | `_to_num(..., 0)` in composite. |

---

## 7. Calendar

| Field               | Source | Provides number? | Notes |
|---------------------|--------|------------------|--------|
| `has_earnings`, `days_to_earnings`, `has_fda`, `economic_events` | Cache | Yes / list | Composite uses .get with safe defaults. |

---

## 8. Enrichment-computed (from cache + formulas)

| Field              | Source     | Provides number? | Notes |
|--------------------|------------|------------------|--------|
| `iv_term_skew`     | Enricher   | Yes (float)      | Uses `data.get("conviction", 0.0)` (no 0.5). |
| `smile_slope`      | Enricher   | Yes (float)      | From sentiment only; no conviction default. |
| `put_call_skew`    | Enricher   | Yes (float)      | Uses `data.get("conviction", 0.0)`. |
| `toxicity`         | Enricher   | Yes (float)      | Uses `data.get("conviction", 0.0)`. |
| `event_alignment`  | Enricher   | Yes (float)      | Uses `data.get("conviction", 0.0)`. |
| `freshness`        | Enricher   | Yes (float)      | From `_last_update`/`last_update`; clamped 0–1. |
| `trade_count`      | Enrichment | Yes (int)        | From cache or `len(flow_trades)`. |

**Fixes applied:**  
- All enricher methods that used `data.get("conviction", 0.5)` now use `float(data.get("conviction", 0.0) or 0.0)` so no inflation when conviction is missing.

---

## 9. Greeks / IV / OI / ETF / Squeeze

| Field / block | Source | Provides number? | Notes |
|----------------|--------|------------------|--------|
| `greeks` (gamma_exposure, call_gamma, put_gamma, max_pain) | Daemon / cache | Yes | `_to_num(..., 0)` in composite. |
| `iv_rank`     | Cache  | Yes              | `_to_num(..., 50)` or 0 where used. |
| `oi_change`   | Cache  | Yes              | net_oi_change, curr_oi, volume via `_to_num`. |
| `etf_flow`    | Cache  | Yes (sentiment string + flags) | overall_sentiment default "NEUTRAL". |
| `squeeze_score` | Cache / enrichment | Yes | signals: `_to_num(..., 0)`; synthetic when missing. |

---

## 10. Composite numeric safety

- **`_to_num(x, default=0.0)`:** Returns `float(x)` or `default` on any exception; used for all numeric reads from enriched_data and nested dicts.
- **Conviction:** Explicitly `0.0` when missing (no 0.5 fallback).
- **Sentiment:** String; missing → `"NEUTRAL"`.

---

## Summary of code changes (this audit)

1. **uw_enrichment_v2.py**
   - Added `_derive_conviction_from_flow_trades(flow_trades)` (same formula as daemon) to derive conviction/sentiment when cache has flow_trades but no conviction.
   - Enrichment: conviction from cache if present and valid; else derived from flow_trades; else **0** (no 0.5).
   - Enricher: `compute_iv_term_skew`, `compute_put_call_skew`, `compute_toxicity`, `compute_event_alignment` use `data.get("conviction", 0.0)` (or equivalent) so no 0.5 inflation.

2. **uw_composite_v2.py**
   - `flow_conv = _to_num(conv_raw) if conv_raw is not None else 0.0` (was 0.5 when missing).

3. **uw_flow_daemon.py**
   - When preserving existing `flow_trades`, always set `sentiment` and `conviction` from `_normalize_flow_data(existing_flow_trades, ticker)` so cache always has a number.
   - Empty dark_pool fallback now includes `total_notional` and `total_notional_1h`: 0.0.

Result: every signal either comes from a source that provides a number, or is derived from flow_trades (conviction/sentiment), or defaults to 0 (or documented value) without artificial inflation.
