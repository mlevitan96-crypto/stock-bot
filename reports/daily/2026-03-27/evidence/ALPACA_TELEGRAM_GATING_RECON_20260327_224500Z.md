# ALPACA — Telegram gating reconciliation (Phase 2)

**ET session day:** `2026-03-27`  
**Canonical market-day bounds (logs / post-close):** ET calendar day `[00:00, 24:00)` America/New_York → UTC half-open window (see `scripts/alpaca_postclose_deepdive._session_bounds_utc`).  
**Strict “today session” gate (decision-grade subset):** `market_open_epoch_today_et()` → `exit_ts_max` = **regular cash close 16:00 ET** (`1774641600.0` UTC epoch on droplet helper run).

## Count provenance

| Metric | Value | Provenance |
|--------|------:|------------|
| **dashboard_count** (`trades_seen`) | **580** | Same evaluator as dashboard health: `telemetry.alpaca_strict_completeness_gate.evaluate_completeness(root, open_ts_epoch=STRICT_EPOCH_START)` — see `dashboard.py` (~3218). |
| **strict_complete_count** (today’s session window to 16:00 ET) | **255** | `evaluate_completeness` with `open_ts_epoch=market_open_epoch_today_et()`, `exit_ts_max_epoch=1774641600.0`. |
| **strict_complete_count** (dashboard / forward-era cohort) | **578** | Same as above but `open_ts_epoch=STRICT_EPOCH_START` (`1774458080.0`). |
| **Exit rows (calendar ET day, post-close style)** | **256** | `exit_attribution.jsonl` rows with timestamp in ET calendar day window (bundle script). |

## incomplete_tail (dashboard-aligned strict)

- **trades_incomplete:** **2**
- **LEARNING_STATUS:** **BLOCKED**
- **Top reason:** `no_orders_rows_with_canonical_trade_id` (count **2** in histogram)
- **Example trade_id:** `open_MSFT_2026-03-26T19:11:17.704367+00:00` (duplicate example rows in audit output — likely paired exit rows; same underlying key `MSFT|LONG|1774552277`)

## Expected vs actual Telegram state

| Field | Value |
|--------|--------|
| **expected_state** | **SEND** — weekday timer fired; post-close is not gated on strict completeness for HTTP send (it embeds learning status in body). Join block does **not** suppress send. |
| **actual_state** | **SEND_FAILED (pre-send)** — service ran, **exit code 4**, `STOP — Memory Bank: canonical markers missing` (`scripts/alpaca_postclose_deepdive.main`). No `2026-03-27` live Telegram audit line. |
| **root_cause** | **MEMORY_BANK.md missing Alpaca attribution contract markers** required by `_verify_memory_bank()` — scheduler and secrets were healthy. |

## Reconciliation table (mission)

| dashboard_count | strict_complete_count | incomplete_tail + top reasons | expected_state | actual_state | root_cause |
|-----------------|----------------------|---------------------------------|----------------|--------------|------------|
| 580 (STRICT_EPOCH_START open) | 255 (today open→16:00 ET exit cap) | 2 incomplete; `no_orders_rows_with_canonical_trade_id` | SEND | Aborted before send (exit 4) | Missing MEMORY_BANK canonical markers |

**Note:** “GATED” in the sense of **CSA join_block** did **not** apply today’s run — the job failed earlier. Session-scoped strict completeness was **ARMED** (255/255); dashboard-era strict is **BLOCKED** (578/580).
