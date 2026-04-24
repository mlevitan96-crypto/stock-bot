# ALPACA METADATA IMPACT (Stage 2)

- UTC `20260330_181537Z`

## Count of positions where pathway is weakened/disabled

```json
{
  "decay_ratio_exit": 32,
  "v2_entry_snapshot_for_exit_intel": 32,
  "entry_reason_attribution": 32,
  "entry_components": 32
}
```

## Per symbol

| symbol | pathways_disabled_count | disabled |
| --- | --- | --- |
| AAPL | 4 | decay_ratio_exit, v2_entry_snapshot_for_exit_intel, entry_reason_attribution, entry_components |
| AMD | 4 | decay_ratio_exit, v2_entry_snapshot_for_exit_intel, entry_reason_attribution, entry_components |
| C | 4 | decay_ratio_exit, v2_entry_snapshot_for_exit_intel, entry_reason_attribution, entry_components |
| COIN | 4 | decay_ratio_exit, v2_entry_snapshot_for_exit_intel, entry_reason_attribution, entry_components |
| COP | 4 | decay_ratio_exit, v2_entry_snapshot_for_exit_intel, entry_reason_attribution, entry_components |
| F | 4 | decay_ratio_exit, v2_entry_snapshot_for_exit_intel, entry_reason_attribution, entry_components |
| GM | 4 | decay_ratio_exit, v2_entry_snapshot_for_exit_intel, entry_reason_attribution, entry_components |
| GOOGL | 4 | decay_ratio_exit, v2_entry_snapshot_for_exit_intel, entry_reason_attribution, entry_components |
| HD | 4 | decay_ratio_exit, v2_entry_snapshot_for_exit_intel, entry_reason_attribution, entry_components |
| HOOD | 4 | decay_ratio_exit, v2_entry_snapshot_for_exit_intel, entry_reason_attribution, entry_components |
| INTC | 4 | decay_ratio_exit, v2_entry_snapshot_for_exit_intel, entry_reason_attribution, entry_components |
| JPM | 4 | decay_ratio_exit, v2_entry_snapshot_for_exit_intel, entry_reason_attribution, entry_components |
| LCID | 4 | decay_ratio_exit, v2_entry_snapshot_for_exit_intel, entry_reason_attribution, entry_components |
| MA | 4 | decay_ratio_exit, v2_entry_snapshot_for_exit_intel, entry_reason_attribution, entry_components |
| MRNA | 4 | decay_ratio_exit, v2_entry_snapshot_for_exit_intel, entry_reason_attribution, entry_components |
| MS | 4 | decay_ratio_exit, v2_entry_snapshot_for_exit_intel, entry_reason_attribution, entry_components |
| MSFT | 4 | decay_ratio_exit, v2_entry_snapshot_for_exit_intel, entry_reason_attribution, entry_components |
| NIO | 4 | decay_ratio_exit, v2_entry_snapshot_for_exit_intel, entry_reason_attribution, entry_components |
| NVDA | 4 | decay_ratio_exit, v2_entry_snapshot_for_exit_intel, entry_reason_attribution, entry_components |
| PFE | 4 | decay_ratio_exit, v2_entry_snapshot_for_exit_intel, entry_reason_attribution, entry_components |
| PLTR | 4 | decay_ratio_exit, v2_entry_snapshot_for_exit_intel, entry_reason_attribution, entry_components |
| RIVN | 4 | decay_ratio_exit, v2_entry_snapshot_for_exit_intel, entry_reason_attribution, entry_components |
| SLB | 4 | decay_ratio_exit, v2_entry_snapshot_for_exit_intel, entry_reason_attribution, entry_components |
| SOFI | 4 | decay_ratio_exit, v2_entry_snapshot_for_exit_intel, entry_reason_attribution, entry_components |
| TGT | 4 | decay_ratio_exit, v2_entry_snapshot_for_exit_intel, entry_reason_attribution, entry_components |
| TSLA | 4 | decay_ratio_exit, v2_entry_snapshot_for_exit_intel, entry_reason_attribution, entry_components |
| UNH | 4 | decay_ratio_exit, v2_entry_snapshot_for_exit_intel, entry_reason_attribution, entry_components |
| WFC | 4 | decay_ratio_exit, v2_entry_snapshot_for_exit_intel, entry_reason_attribution, entry_components |
| XLI | 4 | decay_ratio_exit, v2_entry_snapshot_for_exit_intel, entry_reason_attribution, entry_components |
| XLK | 4 | decay_ratio_exit, v2_entry_snapshot_for_exit_intel, entry_reason_attribution, entry_components |
| XLP | 4 | decay_ratio_exit, v2_entry_snapshot_for_exit_intel, entry_reason_attribution, entry_components |
| XLV | 4 | decay_ratio_exit, v2_entry_snapshot_for_exit_intel, entry_reason_attribution, entry_components |

## Summary

- **`entry_score==0`** disables the standard **decay_ratio** exit arm in `evaluate_exits` (requires `entry_score>0`).
- **Missing `v2` block** forces empty `entry_uw_inputs` / regime profile at entry for v2 exit score — deterioration vs entry intel is muted.
