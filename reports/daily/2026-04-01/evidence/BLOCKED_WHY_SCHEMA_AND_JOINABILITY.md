# BLOCKED_WHY_SCHEMA_AND_JOINABILITY

## blocked_has_decision_ts

- **Answer:** `YES`
- **Proof (first n=8669 rows):** `has_timestamp` count = **8669**
- **Field:** `timestamp` (ISO string) on `log_blocked_trade` record.

## blocked_has_direction

- **Answer:** `YES`
- **Proof (first n=8669 rows):** rows with `side` OR `direction` non-empty = **8669**

## Join keys

- **Primary:** `symbol` + `timestamp` (blocked) aligned to minute bars.
- **Secondary:** `canonical_trade_id` when present on blocked row (`get_symbol_attribution_keys`).
- **Executed:** `canonical_trade_id`, `entry_ts` / `entry_timestamp`, `exit_ts` / `timestamp`.

## Sample key sets

```json
{
  "blocked_top_keys": [
    [
      "timestamp",
      50
    ],
    [
      "symbol",
      50
    ],
    [
      "reason",
      50
    ],
    [
      "block_reason",
      50
    ],
    [
      "score",
      50
    ],
    [
      "candidate_score",
      50
    ],
    [
      "candidate_rank",
      50
    ],
    [
      "expected_value_usd",
      50
    ],
    [
      "would_have_entered_price",
      50
    ],
    [
      "side",
      50
    ],
    [
      "signals",
      50
    ],
    [
      "direction",
      50
    ],
    [
      "decision_price",
      50
    ],
    [
      "components",
      50
    ],
    [
      "outcome_tracked",
      50
    ],
    [
      "composite_meta",
      50
    ],
    [
      "first_signal_ts_utc",
      50
    ],
    [
      "uw_signal_quality_score",
      50
    ],
    [
      "uw_edge_suppression_rate",
      50
    ],
    [
      "survivorship_adjustment",
      50
    ],
    [
      "variant_id",
      50
    ],
    [
      "trend_signal",
      50
    ],
    [
      "momentum_signal",
      50
    ],
    [
      "volatility_signal",
      50
    ],
    [
      "regime_signal",
      50
    ]
  ],
  "exit_top_keys": [
    [
      "symbol",
      50
    ],
    [
      "timestamp",
      50
    ],
    [
      "entry_timestamp",
      50
    ],
    [
      "exit_reason",
      50
    ],
    [
      "pnl",
      50
    ],
    [
      "pnl_pct",
      50
    ],
    [
      "entry_price",
      50
    ],
    [
      "exit_price",
      50
    ],
    [
      "qty",
      50
    ],
    [
      "time_in_trade_minutes",
      50
    ],
    [
      "entry_uw",
      50
    ],
    [
      "exit_uw",
      50
    ],
    [
      "entry_regime",
      50
    ],
    [
      "exit_regime",
      50
    ],
    [
      "entry_sector_profile",
      50
    ],
    [
      "exit_sector_profile",
      50
    ],
    [
      "score_deterioration",
      50
    ],
    [
      "relative_strength_deterioration",
      50
    ],
    [
      "v2_exit_score",
      50
    ],
    [
      "v2_exit_components",
      50
    ],
    [
      "replacement_candidate",
      50
    ],
    [
      "replacement_reasoning",
      50
    ],
    [
      "composite_version",
      50
    ],
    [
      "variant_id",
      50
    ],
    [
      "exit_regime_decision",
      50
    ]
  ]
}
```
