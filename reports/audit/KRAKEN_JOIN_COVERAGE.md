# Kraken join coverage (Phase 2)

## Objective

Sample **≥1000** recent **Kraken-venue** closed trades; compute entry → execution → exit join; orphan exits; duplicate `trade_id`.

## Result: **HARD FAIL — no sample frame**

| Metric | Value |
|--------|-------|
| Kraken closed trades available on droplet | **0** (no Kraken exit log) |
| Sample size | **0** (< 1000 required) |
| Join coverage | **N/A** |

## MEMORY_BANK threshold

MB does not set a numeric Kraken join threshold. Mission standard: **fail-closed** if join unverifiable. With **zero** Kraken trades, join is **unverifiable** → **FAIL**.

## Alpaca data on same host

`/root/stock-bot/logs/exit_attribution.jsonl` has ~2000 lines (Alpaca lifecycle). **Excluded** from this Kraken audit per mission authority.

## Blocker

**No Kraken live trade stream on audited droplet** — Phase 2 cannot complete until a Kraken runtime emits attributable closed trades under an agreed path.
