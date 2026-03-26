# HARD FAILURE — Join coverage below Truth Gate

**Classification:** ENTRY_PATH_JOIN_INSUFFICIENT

- **Frozen exits:** 2000
- **Entry path intel (gate):** 1351 (67.55%)
- **Strict log join:** 898 (44.90%)
- **Required:** >= 80.0%

## Root cause (typical)

- `alpaca_unified_events.jsonl` / `alpaca_entry_attribution.jsonl` missing or empty on droplet.
- `attribution.jsonl` line count << exit window → historical exits never had entry rows.
- Many exits rely on embedded `entry_uw` only; ~32.5% lack both log join and rich embed.

## Required ops (data — not tuning)

1. Ensure entry emitters write unified/entry_attr for all new trades.
2. Do not truncate `logs/attribution.jsonl` / `logs/master_trade_log.jsonl`.
3. Re-run forensics after 7+ sessions of unified events.

**Phases 3–6 exit aggregates remain valid; entry-attribution causality is NOT decision-grade.**
