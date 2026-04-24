# BOARD_QUANT — Displacement deep dive

**Source JSON:** `DISPLACEMENT_GOOD_VS_BAD_SEPARATION.json`, `DISPLACEMENT_EXIT_EMULATOR_RESULTS.json`.

## Stability across splits

- **Baseline:** `n_rows` 5705, `baseline_bad_rate` 0.5707 (BAD = `pnl_60m` variant A > 0).
- **Top univariate rule** (`dist_thr`, threshold 2.3856): **time split** train accuracy **0.4869**, test **0.6075** — both are **not** clearly aligned and **do not** form a stable monotone story versus baseline majority-class behavior without a full calibration curve.
- **Symbol split:** train **0.5029**, test **0.5467** — modest; **generalization of a single threshold rule is unproven** for production-like symbol mix.
- **Impurity reduction** for the best split is **~0.0065** — statistically suggestive at this **n** but **economically small**; conclusion **A** in the script is a **weak separator** flag (`impurity_reduction > 0.001`), not a strong classifier.

## Tail risk under exit emulator

- **Positive mean cells** (11/18) coexist with **deep negative p05** (e.g. **~−0.43 to −1.17 USD** per row notional proxy in grid, see `DISPLACEMENT_EXIT_EMULATOR_RESULTS.json`). Tail risk **remains material**; mean-positive grid does **not** imply acceptable CVaR without further analysis.

## Do separation rules generalize?

**Not established.** Univariate rules + weak stability metrics imply rules are **explanatory**, not **deployable predictors**. Any live use would need walk-forward validation, multiple regimes, and explicit FDR control on rule mining.
