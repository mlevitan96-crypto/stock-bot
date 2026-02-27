# Score autopsy summary (droplet-first)

## Dominant cause (one sentence)
Composite score drops by ~3.7 points between cluster (median pre=3.87) and expectancy gate (median post=0.17); droplet logs/signal_quality_adjustments.jsonl, uw_entry_adjustments.jsonl, survivorship_entry_adjustments.jsonl show the adjustment chain. MIN_EXEC_SCORE=2.5 (same scale as score).

## Evidence (droplet paths + stats)
- `/root/stock-bot/reports/decision_ledger/decision_ledger.jsonl`: 3037 events; score_final min=0.170, max=1.039, mean=0.211
- Pre-adjustment (signal_raw.score) median=3.871
- `/root/stock-bot/logs/signal_quality_adjustments.jsonl`: 2000 recent rows
- `/root/stock-bot/logs/uw_entry_adjustments.jsonl`: 2000 recent rows
- `/root/stock-bot/logs/survivorship_entry_adjustments.jsonl`: 2000 recent rows
- MIN_EXEC_SCORE (config): 2.5

## Top 3 alternative hypotheses
1. **Unit/scale mismatch**: Threshold and score are both in same composite units (2.5 vs 0.2–1.0); no evidence of unit mismatch.
2. **Scoring regression**: Pre-adjustment composite (signal_raw.score) is 3.x; post-adjustment (score_final) is 0.2–1.0; the regression is in the adjustment chain, not in uw_composite.
3. **Data alignment bug**: Bars/timestamps would affect raw_signal inputs to signal_quality; adjustment logs on droplet would show if deltas are plausible.

## What changed?
- Bars/timestamps: Not inferred from ledger alone; check logs/signal_quality_adjustments.jsonl for score_before/score_after. Bars sanity: sample 20 blocked symbols on droplet and verify bars timestamps/lookbacks (not yet run).
- Config: MIN_EXEC_SCORE from config/registry or .env.
- Code path: Cluster uses composite_score; decide_and_execute applies signal_quality, uw, survivorship then passes to expectancy gate.

## Which component(s) drove score_final to ~0.2?
Not composite components (flow, dark_pool, etc.) — pre-adjustment composite median is 3.87. The drop to ~0.2 is from the **adjustment chain** (signal_quality_delta + uw_delta + survivorship_delta). Inspect droplet logs/signal_quality_adjustments.jsonl, uw_entry_adjustments.jsonl, survivorship_entry_adjustments.jsonl to attribute the ~3.7 point drop to one or more of these.

## Bars alignment or units corrupted expectancy inputs?
- **Units:** No. Threshold and score are same scale; executed trades had entry_score 3.0–8.8.
- **Bars alignment:** Not yet validated. To check: on droplet, sample 20 blocked events, resolve bars used for those symbols/dates, and verify timestamps/lookbacks.