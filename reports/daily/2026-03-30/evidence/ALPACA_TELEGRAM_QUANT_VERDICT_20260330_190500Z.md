# ALPACA_TELEGRAM_QUANT_VERDICT_20260330_190500Z

**Verdict: OK — semantics aligned with documented baselines**

## Trade counting

- Uses **`build_trade_key(symbol, side, entry_ts)`** consistent with strict join documentation.
- Filters by **exit timestamp ≥ session open** (economic close window), not promotion watermark — matches mission spec (“from today’s market open”).

## Integrity vs DATA_READY

- Coverage thresholds compare parsed markdown from truth warehouse artifacts — aligns with MEMORY_BANK section 1.2 narrative.
- **`DATA_READY`** in milestone message is **best-effort** from latest coverage file; may be `unknown` if no artifact yet.
- **Strict `LEARNING_STATUS`**: **ARMED** = pass-shaped; **BLOCKED** = fail-shaped; regression alert only on **ARMED → BLOCKED** transition to limit noise.

## Spurious alerts

- Cooldowns reduce repeat pages; stale coverage uses `warehouse_coverage_file_max_age_hours`.
- Pager-derived reasons may fire when post-close unit is **failed** on host — actionable, not spurious.

## SPI pointer

- Best-effort glob; absence does not block milestone.
