# UW_GRANULARITY_SMOKE_PROOF

## Existing sinks (droplet counts)

Command: `wc -l /root/stock-bot/logs/score_snapshot.jsonl /root/stock-bot/logs/signal_context.jsonl`

| File | Lines |
|------|------:|
| `logs/score_snapshot.jsonl` | **2000** |
| `logs/signal_context.jsonl` | **0** |

## `verify_uw_signal_context_nonempty.py`

- **Not added:** no new `uw_signal_context` file path in repo.
- **Canonical UW-adjacent proof:** non-zero **`score_snapshot.jsonl`** line count above.

## Sample (schema only, no secrets)

- **`_PROFIT_V2_DROPLET_RAW.json`** (`phase1.score_snap_wc`) contains first `score_snapshot` row keys: `signal_group_scores.components` includes `flow`, `dark_pool`, `whale`, etc.
