# PROFIT_V2_RECAPTURE_SMOKE_PROOF

## Bars artifact

| Check | Command / result |
|-------|------------------|
| File exists | `/root/stock-bot/artifacts/market_data/alpaca_bars.jsonl` |
| Line count | **49** (`wc -l`) |
| Size | **8242141** bytes (`ls -la` on droplet) |
| Fetch exit code | **0** after data-host fix |
| Symbol coverage | 49 equity/ETF symbols listed in fetch stdout (e.g. SPY, QQQ, NVDA, …) |

## Exit replay

| Check | Result |
|-------|--------|
| Script | `scripts/audit/replay_exit_timing_counterfactuals.py` |
| Exit code | **0** |
| Summary | `exit_rows_total` **432**, `rows_with_full_horizons` **432**, `skipped` **{}** (`PROFIT_V2_EXIT_TIMING_COUNTERFACTUALS.json` → `summary`) |

## `signal_context` smoke (explicit failure)

| Check | Result |
|-------|--------|
| Script | `scripts/audit/verify_signal_context_nonempty.py --root /root/stock-bot` |
| Exit code | **2** |
| Message | `FAIL: zero valid JSONL rows in /root/stock-bot/logs/signal_context.jsonl` |

**Interpretation:** bars re-capture **passed**. Canonical `signal_context` sink remains **empty**; UW granularity is **recovered elsewhere** (`score_snapshot`, UW caches) — not a “bars blocker.”

## `PROFIT_V2_RECAPTURE_BLOCKER.md`

**Not written:** bars sink is **non-empty** and replay **fully joined** all exit rows to minute bars.
