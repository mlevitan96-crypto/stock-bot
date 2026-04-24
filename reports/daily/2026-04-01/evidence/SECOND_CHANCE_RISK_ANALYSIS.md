# SECOND_CHANCE_RISK_ANALYSIS

## Drawdown

- Paper mechanism does not open positions; **live drawdown is unchanged**.
- Counterfactual mean PnL for **allowed** second-chance rows (joined): **None** USD at 60m vs baseline displacement mean **0.405592** — descriptive only.

## Clustering

- Re-eval timing is **one-shot per block**; no loops. Queue is drained by worker; duplicates prevented via `pending_id` in result log.

## Capacity violations

- Paper **allowed** does not consume capacity. Live capacity unchanged.

## Pathological loops

- None designed: single retry, no feed-back into `main.py` entry path without env flag and separate promotion.
