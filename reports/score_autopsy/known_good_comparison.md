# Known-good comparison: blocked vs executed

## Blocked candidates (current window, from ledger)
- count=3037, score_final min=0.170, max=1.039, mean=0.211

## Historically executed trades (logs/attribution.jsonl entry_score)
- count=1110, above MIN_EXEC_SCORE (2.5): 1110, below: 0
- Executed score min=3.019, max=8.800, mean=5.084
- **Verdict: Executed trades historically above MIN_EXEC_SCORE → threshold scale is correct; current block is due to low post-adjustment scores.**