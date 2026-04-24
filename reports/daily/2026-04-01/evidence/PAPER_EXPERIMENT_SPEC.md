# PAPER_EXPERIMENT_SPEC

## Single lever (offline, broker-neutral)

- **Lever:** Measure **only** the subset `block_reason == displacement_blocked` for **Variant A** counterfactual **`pnl_60m` > 0** share, using existing `BLOCKED_COUNTERFACTUAL_PNL_FULL.json`.
- **No** `main.py` edits, **no** systemd restart, **no** Alpaca order placement.

## Inputs

- `reports/daily/2026-04-01/evidence/BLOCKED_COUNTERFACTUAL_PNL_FULL.json`
- Script: `scripts/audit/paper_experiment_offline_displacement_stats.py`

## Success metrics (pre-registered)

| Metric | Definition |
|--------|------------|
| `n_covered` | Blocked rows with `coverage==true` and `displacement_blocked` |
| `n_positive_pnl_60m_variant_a` | Subset with `pnl_variant_a_usd.pnl_60m > 0` |
| `share_positive` | Ratio |
| `mean_score` | Mean of `score` where present |

## Duration window

- Single batch run over frozen JSON (2026-04-01 evidence bundle).

## Rollback criteria

- N/A — read-only JSON read; no persistent state change beyond writing `PAPER_EXPERIMENT_RESULTS.json`.

## Paper-only proof

- Command executed on droplet: `python3 scripts/audit/paper_experiment_offline_displacement_stats.py /root/stock-bot` (stdout + results JSON).
