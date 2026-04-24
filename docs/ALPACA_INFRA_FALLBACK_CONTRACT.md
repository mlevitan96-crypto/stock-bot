# Alpaca Infra Fallback Contract

**Authority:** `docs/ALPACA_GOVERNANCE_CONTEXT.md` Section A1 (Truth Contracts).  
**Scope:** Alpaca-only. Expected behavior for market data outages, order submission failures, and rate limits. No cross-venue logic.

This document states the **expected behavior** of the Alpaca bot when infrastructure degrades. Code paths that implement these behaviors are referenced; no new automated tests are added unless clearly justified (per governance execution plan).

---

## 1. Market data outages

### 1.1 Alpaca historical bars (1Min / 5Min / 15Min)

**Expectation:**

- If 1Min bars are missing or empty for a symbol/date, the system SHOULD try **5Min** then **15Min** as fallback before treating the symbol as having no bars.
- On fallback use: log a **WARN** (e.g. bars_loader using 5m/15m fallback) so operators can see degradation.
- If no bars are available for a symbol/date after fallback, downstream (replay, EOD, attribution) MAY skip that symbol or record a missing-data indicator; the **data feed health contract** SHOULD reflect NO_BARS rate.

**Code references:**

- `data/bars_loader.py`: 1Min fetch; on failure or empty, tries `5Min`, then `15Min`; logs fallback and writes fallback cache. See `_fetch_bars_alpaca`, fallback loop with `_warn(... "trying 5m/15m fallback")`.
- `scripts/data_feed_health_contract.py`: Checks bars presence and freshness for today/yesterday; NO_BARS rate over last 24h from `reports/uw_health/uw_failure_events.jsonl`; FAIL if rate above threshold. Writes `reports/data_integrity/DATA_FEED_HEALTH_CONTRACT.md` and `.json`.

### 1.2 Unusual Whales (UW) / external signal data

**Expectation:**

- On UW API failure or timeout: do **not** block the trading loop. Defer or suppress UW contribution for that cycle; log the failure (e.g. `uw_error.jsonl`, `uw_rate_limit_block`).
- Cached UW data MAY be used when fresh enough; staleness MUST be indicated in attribution (e.g. quality_flags) per attribution truth contract.

**Code references:**

- `src/uw/uw_client.py`: Rate limiting, daily budget, logging; `event_type="uw_rate_limit_block"`, `event_type="uw_call"`; non-200 and errors logged.
- `main.py`: UW calls wrapped; failures do not halt scoring/execution; `jsonl_write("uw_error", ...)` on errors.

### 1.3 Alpaca live feed (websocket)

**Expectation:**

- If the websocket disconnects or has no message for a configured window during market hours, the system SHOULD log the condition and the **data feed health contract** SHOULD report FAIL for websocket during market hours so operators can restart the collector.
- Trading MAY continue using last-known quotes or REST fallbacks where implemented; behavior SHOULD be documented (e.g. “use cached quote” or “skip order if no quote”).

**Code references:**

- `scripts/data_feed_health_contract.py`: `_websocket_status()` checks `reports/data_integrity/alpaca_ws_health.jsonl`; during US market hours, FAIL if disconnected or last message older than `WS_LAST_MSG_MAX_AGE_SECONDS` (e.g. 300s).
- `scripts/alpaca_ws_collector.py`: Writes to the health JSONL; start/restart via script or service.

---

## 2. Order submission failures

**Expectation:**

- On order **reject** (e.g. invalid symbol, insufficient buying power, not shortable): log the rejection with reason; **do not** retry the same order in the same cycle. Optionally retry in a later cycle only if the condition can change (e.g. buying power).
- On **transient** failure (e.g. network timeout, 5xx): a bounded retry (e.g. 1–2 retries with backoff) is acceptable; then log and do not retry same order indefinitely.
- On **fill failure** or partial fill: reconcile positions and ledger; log and do not assume fill until broker confirms.

**Code references:**

- `main.py`: Order submission path with `submit_entry`, limit then market fallback; `log_event("submit_entry", ...)`, `log_order(...)`; reject handling does not retry same order in loop. See `submit_entry` and surrounding error handling.
- Order reconciliation: `reconcile` events and position restore logic in `main.py`; `log_event("reconcile", "retry_after_failure", ...)`, `"all_retries_failed"`, `"position_restored"`, `"complete"`.

---

## 3. Rate limits

### 3.1 Alpaca API (orders, positions, account, bars)

**Expectation:**

- On **429 (rate limit)**: back off (e.g. exponential or fixed delay); do not hammer the API. If in a “panic” or critical path, queue or defer the request and log (e.g. `api_resilience`, `signal_queued_on_429`).
- After backoff, retry the request a bounded number of times; then treat as failure and log.

**Code references:**

- `main.py`: 429 handling in the signal/API path; `log_event("api_resilience", "signal_queued_on_429", ...)` when rate limited; queue or skip and continue.
- Alpaca SDK/docs: Standard rate limits apply; no custom retry logic is mandated beyond “back off and retry once or twice.”

### 3.2 UW / external APIs

**Expectation:**

- UW client SHOULD enforce a daily budget and per-minute/call rate limits so the bot does not exceed provider limits. On rate limit: log (`uw_rate_limit_block`) and skip or defer the call for that cycle.

**Code references:**

- `src/uw/uw_client.py`: Rate limit and daily budget; logging of `event_type="uw_rate_limit_block"` and `event_type="uw_call"`; calls fail gracefully without crashing the loop.

---

## 4. Summary table

| Scenario | Expected behavior | Primary code reference |
|----------|-------------------|-------------------------|
| Bars 1Min missing | Try 5Min then 15Min; WARN; record NO_BARS if still missing | `data/bars_loader.py` |
| Bars stale / no data today | Data feed health contract FAIL; repair guidance in report | `scripts/data_feed_health_contract.py` |
| UW failure / timeout | Log; defer/suppress UW for cycle; do not block loop | `src/uw/uw_client.py`, `main.py` |
| Websocket down (market hours) | Data feed health contract FAIL; log; restart collector | `scripts/data_feed_health_contract.py`, `scripts/alpaca_ws_collector.py` |
| Order reject | Log; do not retry same order in same cycle | `main.py` submit_entry / order path |
| Order transient failure | Bounded retry with backoff; then log and stop retry | `main.py` reconcile / retry logic |
| Alpaca 429 | Back off; queue or skip; log | `main.py` (api_resilience, signal_queued_on_429) |
| UW rate limit | Log; skip/defer call for cycle | `src/uw/uw_client.py` |

---

## 5. Verification

- **Data feed health:** Run `python scripts/data_feed_health_contract.py`; inspect `reports/data_integrity/DATA_FEED_HEALTH_CONTRACT.md` and `.json` for PASS/FAIL and repair recommendations.
- **No automated test** is added for this contract per execution plan (documentation and existing scripts suffice unless a specific need is approved).
