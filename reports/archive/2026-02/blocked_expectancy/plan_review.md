# Blocked-Trade Expectancy Analysis — Plan Review (Multi-Model)

## Objective

Use score_snapshot.jsonl (when available) and state/blocked_trades.jsonl + price data to:
1. Analyze blocked trades (score_below_min, expectancy_blocked:score_floor_breach).
2. Replay counterfactual performance with existing exit logic.
3. Compute expectancy by score bucket.
4. Identify profitable score floor.
5. Recommend minimal, reversible threshold or scaling (config-only).
6. Preserve full auditability.

---

## 1. Score bucketing (all models)

- **Proposal A (wide):** [1.0, 1.5), [1.5, 2.0), [2.0, 2.5), [2.5, 3.0), [3.0, 4.0), 4.0+.
- **Proposal B (narrow):** 0.5-width from 1.0 to 4.0 (1.0–1.5, 1.5–2.0, …).
- **Chosen:** 0.5-width buckets from 1.0 to 4.0; bucket key = floor(score * 2) / 2.0 so 1.25 → 1.0–1.5. Ensures enough bins to find profitable floor without tiny samples.

---

## 2. Replay methodology (no lookahead)

- **Entry:** Simulate entry at `would_have_entered_price` (blocked_trades) or snapshot price at snapshot `ts`. Use first bar at or after decision time when price missing.
- **Bars:** Load 1m (or 5m) bars for symbol/date via existing infra (data/bars_loader or Alpaca). No use of future bars.
- **Exit rule:** Apply same logic as live: trailing stop (e.g. TRAILING_STOP_PCT 1.5%), time exit (e.g. TIME_EXIT_MINUTES 240), or end-of-session. For replay: at each bar, check (1) trailing stop hit, (2) time exit reached, (3) session end; exit at first.
- **MFE/MAE:** From entry to exit bar series: MFE = max(unrealized_pnl_pct) before exit, MAE = min(unrealized_pnl_pct). No lookahead.

---

## 3. Metrics per trade and per bucket

- **Per trade:** pnl_pct, pnl_usd (notional-based), mfe_pct, mae_pct, hold_bars, exit_reason (trailing_stop / time_exit / session_end).
- **Per bucket:** mean_expectancy (mean of pnl_pct), win_rate (% with pnl_pct > 0), median_pnl_pct, sample_size, sum(pnl_usd). Expectancy here = realized pnl_pct (counterfactual).

---

## 4. Bias and lookahead avoidance

- Use only bars at or before exit time for exit decision and for MFE/MAE.
- Do not use score_snapshot or gate data from future cycles.
- Filter blocked_trades by reason in (`score_below_min`, `expectancy_blocked:score_floor_breach`) so we analyze the gates that are currently blocking.
- If score_snapshot.jsonl is empty, use state/blocked_trades.jsonl only (score, timestamp, would_have_entered_price from there).

---

## 5. Data sources

| Source | Use |
|--------|-----|
| state/blocked_trades.jsonl | symbol, score, reason, timestamp, would_have_entered_price (decision_price) |
| logs/score_snapshot.jsonl | Optional: composite_score, ts_iso; link by symbol+time when available |
| logs/gate.jsonl | Optional: cycle_summary gate_counts for validation |
| data/bars (or Alpaca) | OHLCV for replay and MFE/MAE |

---

## 6. Outputs (auditability)

- extracted_candidates.jsonl — one record per blocked candidate (symbol, score, reason, ts, entry_price).
- replay_results.jsonl — one record per replayed trade (symbol, score, bucket, pnl_pct, mfe_pct, mae_pct, exit_reason, hold_bars).
- bucket_analysis.md — table of buckets with mean_expectancy, win_rate, median_pnl_pct, n.
- decision.md — Case A/B/C and recommended threshold or scaling.
- Config change (registry or overlay) + proof.md after deploy.
