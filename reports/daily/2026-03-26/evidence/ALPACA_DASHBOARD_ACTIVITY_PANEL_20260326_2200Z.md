# Alpaca dashboard — operational activity panel

**Timestamp:** 20260326_2200Z  

## Endpoint

- **`GET /api/alpaca_operational_activity?hours=<1..720>`**  
- **Always HTTP 200** in normal routing: JSON payload or `{ ok: false, state: "DISABLED", reason: ... }` on exception (still 200).  
- **Unauthenticated** on the same GET allowlist pattern as other public dashboard panels (see `dashboard.py` auth allowlist).

## Fields (summary)

| Field | Meaning |
|-------|--------|
| `ok` | `true` for successful snapshot; `false` only with `state: DISABLED` |
| `state` | Panel rollup: `OK`, `PARTIAL`, or with failure `DISABLED` |
| `hours`, `generated_at_utc`, `window_start_utc` | Window metadata |
| `disclaimer` | Exact CSA copy: *“Trades are executing on Alpaca. Data is NOT certified for learning or attribution.”* |
| `trades_observed` | Max of exit / unified exit / entered-intent counts in window |
| `last_exit_timestamp_utc`, `last_entry_timestamp_utc` | From attribution / unified / run logs |
| `orders_rows_in_window`, `fills_seen_heuristic` | From `orders.jsonl` when present |
| `orders_log.state` / `orders_log.reason` | **PARTIAL** when `orders.jsonl` missing/empty |
| `does_not_claim` | Explicit non-claims (certification, attribution completeness, broker reconciliation) |

## UI

- Element: `#alpaca-operational-activity` (`.alpaca-ops-panel`) below learning banner.  
- Loader: `window.loadAlpacaOperationalActivity()` (default window **72h** in fetch URL).  
- Renders disclaimer from API plus per-log explanations when partial.

## Non-goals (per charter)

- No new telemetry schema.  
- No trading logic.  
- No certification gate.
