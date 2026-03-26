# Alpaca strict repair — forensic deep dive (target cohort)

**Timestamp:** `20260326_STRICT_ZERO_FINAL`  
**Machine-readable:** `reports/ALPACA_REPAIR_FORENSICS_20260326_STRICT_ZERO_FINAL.json`  
**Source:** Droplet forensics after additive repair (`scripts/audit/alpaca_strict_repair_forensics.py`), captured in `reports/ALPACA_STRICT_REPAIR_VERIFY_DROPLET.json`.

Streams merged: primary `run.jsonl` / `orders.jsonl` / `alpaca_unified_events.jsonl` plus `strict_backfill_*` sidecars (see `telemetry/alpaca_strict_completeness_gate.py`).

## Per-trade diagnosis (post-repair)

| trade_id | Symbol | Exit econ | Unified terminal exit | Missing legs (strict gate) |
|----------|--------|-----------|------------------------|----------------------------|
| open_PFE_2026-03-26T14:29:25.977370+00:00 | PFE | yes | yes | none |
| open_QQQ_2026-03-26T15:10:28.882493+00:00 | QQQ | yes | yes | none |
| open_WMT_2026-03-26T15:10:28.883737+00:00 | WMT | yes | yes | none |
| open_HOOD_2026-03-26T15:51:38.174449+00:00 | HOOD | yes | yes | none |
| open_LCID_2026-03-26T15:51:38.396698+00:00 | LCID | yes | yes | none |
| open_CAT_2026-03-26T16:34:40.245664+00:00 | CAT | yes | yes | none |

## Engineering interpretation (pre-repair root causes)

For this cohort, incompletes were driven by **joinability**, not missing economic closes:

- **Entered / unified entry:** `trade_intent` with `decision_outcome=entered` and/or `alpaca_entry_attribution` were absent or not keyed so they joined under the authoritative `trade_key` from the unified terminal exit.
- **Orders linkage:** `orders.jsonl` rows did not carry a `canonical_trade_id` (or alias) that the strict gate could connect to the exit’s key family.
- **Exit intent:** `exit_intent` rows were missing or not keyed, while `exit_attribution.jsonl` and unified terminal exits existed (econ close without a strict-chain exit-intent leg).

Repair synthesized **additive** rows only in `logs/strict_backfill_run.jsonl`, `logs/strict_backfill_orders.jsonl`, and `logs/strict_backfill_alpaca_unified_events.jsonl`, keyed with `strict_backfill_trade_id`, `strict_backfilled: true`, and timestamps bounded before terminal close (see implementation note).

Detailed join flags (`entered_trade_intent_joinable`, `exit_intent_joinable`, `unified_entry_present`, `orders_row_with_canonical_in_aliases`, `order_ids_matching_symbol`) are in the JSON file per trade.
