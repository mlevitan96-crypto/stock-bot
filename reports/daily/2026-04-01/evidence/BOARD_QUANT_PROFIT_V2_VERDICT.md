# BOARD_QUANT_PROFIT_V2_VERDICT

## Statistical validity

- **n=432** exits with full minute horizons — adequate for **descriptive** moments; **insufficient** for high-dimensional causal claims.  
- **n=63** exit↔snapshot matches for component uplift — **narrow**; bootstrap CIs on mean differences are **wide** (see JSON).

## Overfitting / multiple testing

- Many components tested (`flow`, `dark_pool`, `whale`, …) without FDR control — **exploration only**.  
- Ranking signals on the same tail used for splits (`ALPACA_SIGNAL_RANKING.json`) inflates apparent separation.

## Generalization

- Single-host, single-regime mix (`mixed` dominant in directional memo).  
- Bars are **Alpaca vendor** minute aggregates — may differ from live fills.

## Verdict

**HOLD:** use artifacts to **prioritize shadow experiments**, not to set thresholds. Require **walk-forward** or **holdout** before any production change.
