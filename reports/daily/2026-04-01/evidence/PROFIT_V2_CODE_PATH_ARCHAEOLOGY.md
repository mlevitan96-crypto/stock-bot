# PROFIT_V2_CODE_PATH_ARCHAEOLOGY

Repo root: `/root/stock-bot` (droplet). Method: static search in workspace `main.py`, `telemetry/`, `scripts/`, `src/` for emitters and sinks.

## `signal_context` (canonical JSONL)

| Piece | Location | Role |
|-------|----------|------|
| Writer | `telemetry/signal_context_logger.py` | `log_signal_context(...)` appends one JSON object per call; **never raises**; gated by env |
| Call sites | `main.py` | **Blocked:** `log_blocked_trade` path (~1253) with `decision="blocked"`, `uw_components` in `signals` |
| | `main.py` | **Exit:** exit attribution path (~2809) `decision="exit"`, V2 exit components / regime fields |
| | `main.py` | **Enter:** post-fill path (~10847) `decision="enter"` |
| Sink path | `config.registry.LogFiles` → default `logs/signal_context.jsonl` | Droplet file **empty** despite code paths (see runtime memo) |

## UW / flow / options signal composition

| Piece | Location | Role |
|-------|----------|------|
| Scoring / components | `main.py` (large) | Unusual Whales–driven multi-factor scoring; component names align with `score_snapshot` (`flow`, `dark_pool`, …) |
| Snapshot log | Emitted wherever score snapshots are written to `logs/score_snapshot.jsonl` (writers in bot pipeline — see grep `score_snapshot` in repo) | **Droplet:** 2000 lines with full `components` |
| SPI analytics | `src/analytics/alpaca_signal_path_intelligence.py` | SPI / orthogonality style analysis (batch/report oriented) |

## Bars for counterfactuals

| Piece | Location | Role |
|-------|----------|------|
| Replay (scenario hold floors) | `scripts/replay_exit_timing_counterfactuals.py` | Consumes `artifacts/market_data/alpaca_bars.jsonl` |
| Replay (horizon MTM) | `scripts/audit/replay_exit_timing_counterfactuals.py` | **V2:** +1m/+5m/+15m/+30m/+60m from **entry** |
| Fetch (V2) | `scripts/audit/fetch_alpaca_bars_for_counterfactuals.py` | Read-only HTTP to Alpaca Data API v2; writes jsonl lines |
| Older droplet layout | — | **No** `src/data/` on droplet at capture time → fetch script is **self-contained** (no `src.data` import) |

## Blocked trades

| Piece | Location | Role |
|-------|----------|------|
| Primary path | `state/blocked_trades.jsonl` | Used by `run_alpaca_profit_discovery_campaign.py` and `compute_profit_v2_uplift_and_blocked.py` |
| Legacy fallback | `logs/blocked_trades.jsonl` | Checked if state path missing |

## Why the campaign “missed” bars / signal_context

- **Bars:** No job had populated `artifacts/market_data/alpaca_bars.jsonl` on this host; other bars tooling targets `data/bars`, parquet, or caches — **different path contract** than replay scripts.
- **signal_context:** Emitter exists, but droplet file is **empty** — see `PROFIT_V2_RUNTIME_FLAG_ANALYSIS.md` (silent no-op vs. no calls vs. `.env`).
