# BOARD_QUANT_PROFIT_VERDICT

## Evidence anchors

- **n=432** exits — marginal for multi-way regime × signal interaction estimates.
- **Regime label** collapsed effectively to **`mixed`** for all rows in directional table — **no regime conditioning power** in this extract.
- Signal ranking **n=63** matched — **underpowered** for false-positive control on ~15+ components.

## Statistical validity

- Subgroups (regime × direction) often **small n**; wide confidence intervals implied.
- **Adversarial:** Median-split t-style comparison without SE — treat ranking as **hypothesis generation only**.

## Sample size

- Directional stats: LONG n=280, SHORT n=152.
- Snapshot-matched exits: **63**.

## Overfitting

- Ranking signals on same tail used for exploration inflates apparent edge; **holdout** or **walk-forward** required.
- **Correlation matrix** truncated to 15 keys and 3000 rows — may omit rare but important components.

