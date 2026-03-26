# Kraken telemetry surface map

**TS:** `20260326_2315Z`

## Repository reality (inventory)

| Surface | Status | Notes |
|---------|--------|--------|
| Data download | **Present** | `scripts/data/kraken_download_30d_resumable.py` |
| Massive review shell pipeline | **Present** | `scripts/CURSOR_KRAKEN_30D_MASSIVE_REVIEW_AND_ITERATE.sh` (invoked via `scripts/run_kraken_on_droplet.py`) |
| Learning aggregation | **Present** | `scripts/learning/run_profit_iteration.py`, `aggregate_profitability_campaign.py` |
| **Strict tail completeness gate** | **Not found** | No Python module matching mission name or strict index evaluator in-repo |
| **Kraken unified events / canonical_trade_id chain** | **Not found** | No parallel to `alpaca_unified_events.jsonl` documented in code |
| **Kraken Telegram milestone cert suite** | **Not found** | `kraken_data_telegram_certification_suite.py` **does not exist** |
| **Milestone 250/500 Telegram (Kraken)** | **Not found** | Alpaca uses `scripts/notify_alpaca_trade_milestones.py` at **100/500** — different product |

## Intended keys (contract target)

Until a Kraken strict gate is implemented, the following are **contract placeholders**, not verified implementations:

- `canonical_trade_id` / `trade_key` (or venue-native stable id mapped into this contract)
- Order/fill identifiers from Kraken REST/WebSocket captures
- Economic close record
- Unified terminal event (if dual-write pattern is adopted from Alpaca)

## Timestamp / ordering

**TBD** at implementation time; must be documented alongside the first strict gate commit.
