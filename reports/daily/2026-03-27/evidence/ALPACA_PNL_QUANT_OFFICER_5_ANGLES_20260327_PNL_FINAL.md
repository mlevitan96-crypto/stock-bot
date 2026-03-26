# Quant Officer — 5 profit angles (20260327_PNL_FINAL)

| # | Hypothesis | Data required | Metric | Decision impact |
|---|------------|---------------|--------|-----------------|
| 1 | Post-fill adverse selection: short-term drift after fill conditional on spread bucket hurts net PnL. | `fill_timestamp, mid_30s_after, spread_bps_at_decision, side` | mean(mid_30s - fill_price) * direction in bps by spread decile | Widen spread gate or switch routing in top drag decile. |
| 2 | Signal half-life: trades entered when UW flow age > X min underperform. | `signal_event_ts, trade_intent_ts, uw_flow_freshness, net_pnl` | PnL expectancy vs age bucket at entry | Tighten freshness veto on entries. |
| 3 | Gate false negatives: blocked trades with shadow-positive EV cluster by veto code. | `block_reason, shadow_pnl_or_path_pnl, symbol, score_at_decision` | Sum opportunity cost by veto × score decile | Relax specific veto when shadow EV positive with bounded notional. |
| 4 | Exit winner interaction: `winner` × `hold_minutes` nonlinear tails drive payoff ratio. | `exit winner, hold_minutes, mfe, mae, net_pnl` | Payoff ratio by (winner, hold quartile) | Retune time-exit vs trail for low-payoff cells. |
| 5 | Infra latency quantile: submit→fill slope changes around deploy markers. | `decision_ts, order_submit_ts, fill_ts, deploy_marker_ts, net_pnl` | PnL vs latency bucket pre/post deploy | Freeze deploys near open; add backoff after restarts. |

## Workspace status

Implementation blocked until truth bundle rows exist (see Phase 1 blockers).
