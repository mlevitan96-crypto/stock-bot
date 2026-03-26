# Alpaca Telemetry Backfill Assessment (Phase 5)

## Verdict: **Historical entry attribution NOT reliably reconstructable**

### Raw sources available

| Source | Usable for entry composite at open? |
|--------|-------------------------------------|
| `logs/attribution.jsonl` | **Partial** — ~1 line per window vs ~2000 exits; `trade_id` / timestamp alignment incomplete. |
| `logs/exit_attribution.jsonl` | **Partial** — embeds `entry_uw`, `entry_regime`, `composite_at_entry`; not full contribution vector at entry decision. |
| `logs/master_trade_log.jsonl` | **Partial** — feature snapshots; not guaranteed 1:1 with every exit. |
| `signal_snapshots` / ENTRY_DECISION | **Theoretical** — join by surrogate key; fragile, not audited for 100% coverage. |

### Deterministic reconstruction?

**No guarantee.** Entry-time `trade_id` for old trades was never written to `alpaca_entry_attribution.jsonl`. Rebuilding `open_{SYMBOL}_{entry_ts}` from exit rows matches metadata only if `entry_ts` strings match exactly; legacy `log_attribution` used `now_iso()` at log time, not `mark_open` ts — **systematic skew**.

### Join guarantee for history?

**Cannot assert 100%** for pre-repair cohort.

## Declaration

- **Pre-repair history:** **NOT DATA_READY** for entry-causality analysis at promotion grade.  
- **Forward-only:** From **`repair_iso_utc`** (epoch file), after forward proof **PASS**, entry+exit causality **allowed** for that cohort only.
