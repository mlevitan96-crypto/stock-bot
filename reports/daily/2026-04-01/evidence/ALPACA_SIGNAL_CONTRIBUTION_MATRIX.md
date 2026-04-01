# ALPACA_SIGNAL_CONTRIBUTION_MATRIX

- **UW / Unusual Whales sub-signals in this pipeline:** `flow`, `dark_pool`, and other keys appear as **`weighted_contributions` component names** in `score_snapshot.jsonl` (not nested `UW.flow` paths). When `logs/signal_context.jsonl` is empty, **full per-decision UW cache subfields are not available** for this run — see inventory.

- Exits with pnl matched to `score_snapshot` within 600s before entry, same symbol: **63**

## Interpretation

- **High vs low** = median split on component value at nearest pre-entry snapshot.
- **delta_mean_pnl** = naive association with realized PnL; **not** causal uplift.

## Top 25 by proxy score (delta × n)

| signal | n | delta_mean_pnl | mean_pnl high | mean_pnl low |
|--------|---|----------------|---------------|--------------|
| `greeks_gamma` | 63 | 0.451958 | -0.220455 | -0.672412 |
| `market_tide` | 63 | 0.363296 | -0.177995 | -0.54129 |
| `toxicity_penalty` | 63 | 0.363296 | -0.177995 | -0.54129 |
| `event` | 63 | 0.084583 | -0.355417 | -0.44 |
| `flow` | 63 | -0.316817 | -0.366817 | -0.05 |
| `calendar` | 63 | -0.356759 | -0.356759 | 0.0 |
| `congress` | 63 | -0.356759 | -0.356759 | 0.0 |
| `dark_pool` | 63 | -0.356759 | -0.356759 | 0.0 |
| `etf_flow` | 63 | -0.356759 | -0.356759 | 0.0 |
| `ftd_pressure` | 63 | -0.356759 | -0.356759 | 0.0 |
| `insider` | 63 | -0.356759 | -0.356759 | 0.0 |
| `institutional` | 63 | -0.356759 | -0.356759 | 0.0 |
| `motif_bonus` | 63 | -0.356759 | -0.356759 | 0.0 |
| `oi_change` | 63 | -0.356759 | -0.356759 | 0.0 |
| `regime` | 63 | -0.356759 | -0.356759 | 0.0 |
| `shorts_squeeze` | 63 | -0.356759 | -0.356759 | 0.0 |
| `smile` | 63 | -0.356759 | -0.356759 | 0.0 |
| `squeeze_score` | 63 | -0.356759 | -0.356759 | 0.0 |
| `whale` | 63 | -0.356759 | -0.356759 | 0.0 |
| `iv_rank` | 63 | -0.505437 | -0.525238 | -0.019802 |
| `freshness_factor` | 63 | -0.593432 | -0.648766 | -0.055333 |
| `iv_skew` | 63 | -1.136585 | -0.807785 | 0.3288 |

## Full JSON

- `ALPACA_SIGNAL_RANKING.json`

