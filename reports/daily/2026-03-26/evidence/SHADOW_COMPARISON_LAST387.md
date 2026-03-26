# Shadow comparison (last-387)

**Generated (UTC):** 2026-03-05T00:09:01.482951+00:00

## Baseline vs each shadow delta

- **A1_shadow:** would_admit=963, proxy_pnl_delta=-75.4 (proxy)
- **A2_shadow:** would_admit=585, proxy_pnl_delta=-45.8 (proxy)
- **A3_shadow:** would_admit=151, proxy_pnl_delta=-11.82 (proxy)
- **B1_shadow:** would_admit=260, proxy_pnl_delta=21.09 (proxy)
- **B2_shadow:** would_admit=335, proxy_pnl_delta=27.18 (proxy)
- **C2_shadow:** would_admit=1764, proxy_pnl_delta=-138.11 (proxy)

## Ranking by expected improvement

1. B2_shadow
2. B1_shadow
3. A3_shadow
4. A2_shadow
5. A1_shadow
6. C2_shadow

## Risk flags per shadow

- **A1_shadow:** Displacement relaxation increases exposure.
- **A2_shadow:** Max positions increase concentration risk.
- **A3_shadow:** Lower score floor may admit worse entries.
- **B1_shadow:** Min hold extension may increase drawdown in fast reversals.
- **B2_shadow:** Removing early signal_decay may hold losers longer.
- **C2_shadow:** Full C2 requires per-block outcome; proxy only.

## Stability notes

Signal consistency across time windows TBD; last-387 is governing cohort.

## Nomination

- **Advance to live paper test**
- Advance to live paper test candidate: B2_shadow

## Board persona verdicts

### Adversarial

SHADOW_COMPARISON_LAST387 ranks shadows by proxy delta. Recommend advancing B2_shadow only if shadow is least negative and tail-risk acceptable. Others: wait or discard.

### Quant

Ranking by expected improvement (proxy). Advance B2_shadow to live paper test; validate with backtest. Others hold until more data.

### Product Operator

Use comparison to pick ONE shadow for next live paper test: B2_shadow. Others wait for product prioritization.

### Risk

Risk flags per shadow in comparison. Advance only B2_shadow if risk signs off. Others hold or discard.

### Execution Sre

Advance B2_shadow only after SRE confirms rollback procedure. Others: hold.
