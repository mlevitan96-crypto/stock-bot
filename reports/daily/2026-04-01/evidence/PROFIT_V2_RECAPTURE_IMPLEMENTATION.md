# PROFIT_V2_RECAPTURE_IMPLEMENTATION

Constraint recap: **additive**, **read-only** research paths; **no** strategy, liquidation, tuning, or order-logic changes.

## Bars (required)

| Item | Detail |
|------|--------|
| Script | `scripts/audit/fetch_alpaca_bars_for_counterfactuals.py` |
| Input | `logs/exit_attribution*.jsonl` → union of symbols + min/max entry/exit times |
| Output | `artifacts/market_data/alpaca_bars.jsonl` (one JSON line per symbol, `{"data":{"bars":{SYM:[...]}}}`) |
| Auth | `ALPACA_API_KEY` + `ALPACA_SECRET_KEY` (or `ALPACA_KEY` / `ALPACA_SECRET`) from sourced `.env` |
| Data host | `ALPACA_DATA_URL` if set, else **`https://data.alpaca.markets`** (paper `ALPACA_BASE_URL` alone does **not** force sandbox data host; see `PROFIT_V2_RUNTIME_FLAG_ANALYSIS.md`) |
| Caching | None in-script (optional future: reuse `data/bars_cache` layout) |

## Exit horizon counterfactuals

| Item | Detail |
|------|--------|
| Script | `scripts/audit/replay_exit_timing_counterfactuals.py` |
| Output | `PROFIT_V2_EXIT_TIMING_COUNTERFACTUALS.json` + `.md` (written under `--evidence-dir`) |

## UW uplift + blocked tallies

| Item | Detail |
|------|--------|
| Script | `scripts/audit/compute_profit_v2_uplift_and_blocked.py` |
| Blocked path | **`state/blocked_trades.jsonl`** primary; `logs/blocked_trades.jsonl` fallback |
| Output | `PROFIT_V2_SIGNAL_UW_UPLIFT.*`, `PROFIT_V2_BLOCKED_MISSED_CAUSAL.*` |

## Canonical `signal_context` sink (optional / not applied to running engine)

| Item | Detail |
|------|--------|
| Existing writer | `telemetry/signal_context_logger.py` → `logs/signal_context.jsonl` |
| Smoke | `scripts/audit/verify_signal_context_nonempty.py` |
| Status | **Not** fixed by restarting or patching `main.py` in this mission; **recovery** uses `score_snapshot` instead (see `PROFIT_V2_RECOVERY_DECISION.md`). |

## Deploy

- Scripts uploaded to droplet via **SFTP** (`DropletClient.put_file`).
- **No** `systemctl restart stock-bot`.
