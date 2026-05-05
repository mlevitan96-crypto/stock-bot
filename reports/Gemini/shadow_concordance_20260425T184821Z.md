# Shadow–Primary Concordance Report

> **Tape empty:** `shadow_executions.jsonl` had no qualifying rows — nothing to grade yet.

- **Generated (UTC):** `20260425T184821Z`
- **Root:** `C:\Dev\stock-bot`
- **Shadow log:** `C:\Dev\stock-bot\logs\shadow_executions.jsonl` (missing)
- **Run log:** `C:\Dev\stock-bot\logs\run.jsonl` (present)
- **Join window:** ±45s (shadow `ts` ↔ `trade_intent.ts`)
- **Pricing:** API disabled or keys missing · no local `research_bars.db`

## Summary

| Metric | Value |
|--------|-------|
| Shadow rows ingested | **0** |
| Joined to `trade_intent` (blocked + `challenger_ai_approved`) | **0** |
| Rows with forward 1d or 5d return | **0** |
| Win rate (1d, signed return > 0) | **n/a** (0/0) |
| Win rate (5d) | **n/a** (0/0) |
| Expectancy (mean signed 1d return) | **n/a** |
| Expectancy (mean signed 5d return) | **n/a** |
| **Missed profit** (Primary blocked & 1d right) — count | **0** |
| **Missed profit** — sum signed 1d returns (fraction of entry) | **0.000000** |

## Definitions

- **Join:** Closest `trade_intent` with `decision_outcome=blocked`, `challenger_ai_approved=true`, same `symbol` and side bucket (`buy`/`long` vs `sell`/`short`), within join window.
- **Signed forward return:** Long: `(close_fwd - entry) / entry`. Short: `(entry - close_fwd) / entry`.
- **1d / 5d:** Next 1 / 5 **available** daily bars after the last daily bar with `bar_time <= shadow_ts` (UTC ordering; aligns with `research_bars` / Alpaca `1Day` timestamps).
- **Missed profit (opportunity cost):** Primary blocked the live trade while Challenger-approved shadow would have gained on **1d** signed return (`> 0`).

## Artifacts

- CSV: `C:\Dev\stock-bot\reports\Gemini\shadow_concordance_20260425T184821Z.csv`
