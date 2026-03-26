# ALPACA Max Profit Edge Analysis — `20260325_0205`

- **TRADING_ROOT:** `/root/stock-bot`
- **Generated (UTC):** 2026-03-25T00:09:27.957519+00:00

## Personas

- **Quant:** univariate lifts on exit attribution components vs `pnl_pct`; coverage tables; regime/time notes.
- **SRE:** read-only JSONL; deterministic keys assumed where present; reproducibility command below.
- **CSA:** sample gates; leakage warnings; promotion readiness forced NO.

## Phase 0 — Dataset counts (read-only)

| Source | Rows scanned (tail) |
|--------|---------------------|
| `logs/run.jsonl` | 2040 |
| `logs/orders.jsonl` | 16442 |
| `logs/signal_context.jsonl` | 1 |
| `state/blocked_trades.jsonl` | 15000 |
| `logs/exit_attribution.jsonl` | 2860 |

- **trade_intent entered:** 64
- **trade_intent blocked:** 1168
- **exit_intent:** 56
- **orders (filled-like proxy):** 8637
- **orders (close_*):** 1919
- **exit_attribution rows with numeric pnl_pct:** 2858
- **trade_intent entered joined to exit PnL via canonical_trade_id:** 0

## Economics status (honest)

- **Included:** `pnl_pct` / `pnl` from `exit_attribution` when present; `exit_quality_metrics` MFE/MAE when present.
- **Excluded / explicit policy:** per-fill fees often `fee_excluded_reason` on paper (`telemetry/attribution_emit_keys`); slippage uses `decision_slippage_ref_mid` when set — many historical rows predate schema; **do not treat missing slippage as zero**.

## Methods executed

- Univariate: bottom vs top quartile of each numeric feature vs mean `pnl_pct` (min n=40 pairs, quartiles min 5 each).
- **Not run at full depth (scope):** pairwise grid on all features; full walk-forward per-feature regression; blocked-trade counterfactual outcomes (pending definitional join).

Walk-forward: exit_attribution with pnl split half n1=1429 n2=1429; compare top-feature quartile effects separately (manual spot-check recommended).

## Top 10 candidate edges (offline; ranked by |Q75-Q25 mean pnl delta|)

| rank | feature | n | delta_mean_pnl_pct | mean_low | mean_high | source |
|------|---------|---|-------------------|----------|-----------|--------|
| 1 | `v2_exit.vol_expansion` | 2857 | -0.0941612 | -0.0639025 | -0.158064 | exit_attribution_components |
| 2 | `v2_exit.score_deterioration` | 2857 | -0.0182795 | -0.0976458 | -0.115925 | exit_attribution_components |
| 3 | `v2_exit.regime_shift` | 2857 | -0.010156 | -0.0838896 | -0.0940456 | exit_attribution_components |
| 4 | `v2_exit.sentiment_deterioration` | 2857 | -0.00886449 | -0.0851811 | -0.0940456 | exit_attribution_components |
| 5 | `v2_exit.sector_shift` | 2857 | -0.0069974 | -0.0870482 | -0.0940456 | exit_attribution_components |
| 6 | `v2_exit.darkpool_deterioration` | 2857 | 0 | -0.0940456 | -0.0940456 | exit_attribution_components |
| 7 | `v2_exit.earnings_risk` | 2857 | 0 | -0.0940456 | -0.0940456 | exit_attribution_components |
| 8 | `v2_exit.flow_deterioration` | 2857 | 0 | -0.0940456 | -0.0940456 | exit_attribution_components |
| 9 | `v2_exit.overnight_flow_risk` | 2857 | 0 | -0.0940456 | -0.0940456 | exit_attribution_components |
| 10 | `v2_exit.thesis_invalidated` | 2857 | 0 | -0.0940456 | -0.0940456 | exit_attribution_components |

## Promotion readiness

**ALL candidates: `OFFLINE CANDIDATE ONLY`.** `PROMOTION READINESS`: **NO** — post-deploy exits, economics completeness, and larger N must be proven before live promotion.

## CSA adversarial review

### Top 5 edges worth live confirmation later (hypothesis only)
1. `v2_exit.vol_expansion` — effect -0.09416 on n=2857 (confirm causality + stability; watch overfit).
2. `v2_exit.score_deterioration` — effect -0.01828 on n=2857 (confirm causality + stability; watch overfit).
3. `v2_exit.regime_shift` — effect -0.01016 on n=2857 (confirm causality + stability; watch overfit).
4. `v2_exit.sentiment_deterioration` — effect -0.008864 on n=2857 (confirm causality + stability; watch overfit).
5. `v2_exit.sector_shift` — effect -0.006997 on n=2857 (confirm causality + stability; watch overfit).

### Top 5 mirages to ignore

1. Any edge with n < 100 and single-split ranking.
2. Features perfectly collinear with exit reason (leakage).
3. PnL drivers that ignore explicit fee/slippage exclusions.
4. Joins by symbol-only same-day proximity (not used here; do not adopt without `canonical_trade_id`).
5. Overnight/session effects without session bucket controls.

## SRE integrity review

- **Joins in this build:** outcome features taken **only** from within each `exit_attribution` row (no cross-file heuristic join).
- **Files written:** `MEMORY_BANK.md`, `reports/ALPACA_MEMORY_BANK_CANONICAL_UPDATE_*.md`, `reports/ALPACA_MAX_EDGE_ANALYSIS_*.md`, and this script if uploaded.
- **Reproducibility:**

```bash
cd /root/stock-bot && TRADING_BOT_ROOT=/root/stock-bot ./venv/bin/python3 scripts/alpaca_canonical_memory_bank_and_edge_mission.py
```

## CSA verdict — offline edge discovery legitimacy

**PASS** — sufficient exit PnL rows and lift signals for **hypothesis generation** only.
