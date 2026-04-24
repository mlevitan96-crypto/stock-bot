# ALPACA_CANONICAL_TRADE_DEFINITION

## trade_unit
- One **closed trade** = one unique Alpaca **`trade_key`** from `logs/exit_attribution.jsonl`, computed as `build_trade_key(symbol, side, entry_ts)` (see `src/telemetry/alpaca_trade_key.py`).
- Multiple JSONL lines for the same key count once (first qualifying row supplies PnL sum slice for milestone PnL rollups).

## era scope
- **Post-era only:** rows excluded when `utils.era_cut.learning_excluded_for_exit_record(record)` is true (driven by `config/era_cut.json`).

## exclusion / floors
- **Pre-era:** excluded by era cut helper above.
- **Milestone Telegram (100 checkpoint + 250):** additionally require parsed exit timestamp `>=` count floor (`session_open` or `integrity_armed` epoch from `telemetry/alpaca_telegram_integrity/milestone.py`), using the same dedupe + era rules via `compute_canonical_trade_count(root, floor_epoch=...)`.
- **Dashboard cumulative strip:** `compute_canonical_trade_count(root, floor_epoch=None)` — all post-era unique keys with valid exit timestamp (no session floor).
- Rows missing a buildable trade_key are skipped (`skipped_no_trade_key` in count output).

## Ledgers
- **Integrity milestone notifier:** `telemetry/alpaca_telegram_integrity/milestone.py` → `compute_canonical_trade_count`.
- **250-trade / audit alignment:** same `exit_attribution.jsonl` + `trade_key` + era cut; audit missions should call `compute_canonical_trade_count` for eligibility counts.
