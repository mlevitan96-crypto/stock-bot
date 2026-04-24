# Alpaca entry intent completeness (Kraken field mapping)

**Evidence host:** local_workspace  
**ET report date:** 2026-03-27  
**Generated (UTC):** 20260328_032555Z

## Kraken → Alpaca mapping

| Kraken (mission) | Alpaca |
|------------------|--------|
| signal_trace | intelligence_trace (trade_intent, joined) OR raw_signals (alpaca_entry_attribution) |
| entry_score_total | composite_score (alpaca_entry_attribution) |
| entry_score_components | contributions or raw_signals (alpaca_entry_attribution) |

## Strict cohort context

- `trades_seen` (strict window): 0
- `trades_complete`: 0

## Sample

- Sample size: **0** (target ≥20 strict-complete trades; full set if smaller)
- signal_trace pass: **False** (0/0 OK)
- entry_score_total pass: **False** (0/0 OK)
- entry_score_components pass: **False** (0/0 OK)

## Violations (capped)

```json
[
  {
    "trade_id": "*",
    "reason": "NO_SAMPLE"
  }
]
```

## Full machine JSON

```json
{
  "strict_completeness_trades_seen": 0,
  "strict_completeness_complete": 0,
  "sample_trade_ids": [],
  "sample_size": 0,
  "kraken_field_mapping": {
    "signal_trace": "intelligence_trace (trade_intent, joined) OR raw_signals (alpaca_entry_attribution)",
    "entry_score_total": "composite_score (alpaca_entry_attribution)",
    "entry_score_components": "contributions or raw_signals (alpaca_entry_attribution)"
  },
  "pass_signal_trace": false,
  "pass_entry_score_total": false,
  "pass_entry_score_components": false,
  "pass_all": false,
  "no_sample_reason": "zero strict-complete trades in evaluate_completeness(collect_complete_trade_ids=True)",
  "violations": [
    {
      "trade_id": "*",
      "reason": "NO_SAMPLE"
    }
  ],
  "counts": {
    "signal_trace_ok": 0,
    "entry_score_total_ok": 0,
    "entry_score_components_ok": 0
  }
}
```
