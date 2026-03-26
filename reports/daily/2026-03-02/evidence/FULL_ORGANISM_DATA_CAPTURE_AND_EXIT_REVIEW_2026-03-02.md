# Full Organism: Data Capture & Exit Review (2026-03-02)

## Goal

Wire the full loop so we have **intelligence → signals → entries → exits → learning → intelligence**, with all data captured for deeper analysis. Confirm **exit review** is in place so we can analyze "exiting very quickly" and improve.

---

## 1. The loop (high level)

```
  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
  │ Intelligence│ ──► │   Signals   │ ──► │   Entries   │ ──► │   Exits     │ ──► │   Learning  │
  │ (UW, regime,│     │ (composite, │     │ (orders,    │     │ (close      │     │ (effectiveness,
  │  universe)  │     │  gates)     │     │  positions) │     │  reason, PnL)│     │  exit review)
  └─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
         ▲                                                                                 │
         └─────────────────────────────────────────────────────────────────────────────────┘
```

- **Intelligence:** UW cache, regime, daily universe, EOD root cause, survivorship.
- **Signals:** Composite score, gates (expectancy, capacity, risk, momentum), trade_intent.
- **Entries:** Filled orders → attribution, master_trade_log, score snapshots, signal history.
- **Exits:** Close reason, PnL, hold time, v2 exit components → exit_attribution, master_trade_log.
- **Learning:** Effectiveness reports, exit effectiveness v2, exit tuning suggestions, EOD board, governance replay.

---

## 2. Entry signal capture (all must be wired)

| Capture point | Where | Output / path | Purpose |
|---------------|--------|----------------|---------|
| **Trade intent** | `_emit_trade_intent()` in main | `logs/run.jsonl` (event_type=trade_intent) | Full feature_snapshot, thesis_tags, gates, decision_outcome (entered/blocked). |
| **Blocked trades** | `log_blocked_trade()` in main | `state/blocked_trades.jsonl` | Reason, score, composite_pre_norm, composite_post_norm, components. |
| **Score snapshot** | `append_score_snapshot()` in main | `logs/score_snapshot.jsonl` or state | Per-candidate score at expectancy gate, block_reason, composite_meta. |
| **Signal history** | `log_signal_to_history()` in main | Signal history storage (dashboard) | Rejected/accepted signals, thresholds, metadata. |
| **Attribution (entry)** | `log_attribution(trade_id=open_*, ...)` in main | `logs/attribution.jsonl` | Entry record: trade_id, symbol, pnl_usd=0, context (entry_score, components, regime). |
| **Master trade log (entry)** | `append_master_trade()` from log_attribution | `logs/master_trade_log.jsonl` | entry_ts, entry_price, entry_v2_score, signals, feature_snapshot. |
| **Signal snapshot (entry)** | `write_snapshot_safe(..., ENTRY_FILL)` in log_attribution | Telemetry/snapshot writer | ENTRY_FILL event for observability. |
| **Expectancy gate truth** | main (when `EXPECTANCY_GATE_TRUTH_LOG=1`) | `logs/expectancy_gate_truth.jsonl` | score_used_by_gate, gate_outcome, fail_reason. |
| **Signal score breakdown** | main (when `SIGNAL_SCORE_BREAKDOWN_LOG=1`) | `logs/signal_score_breakdown.jsonl` | Per-signal contribution, composite_pre/post. |

**Contract:** Every **filled entry** must produce: one `open_*` row in attribution.jsonl, one entry row in master_trade_log.jsonl, and (when enabled) score_snapshot and trade_intent in run.jsonl.

---

## 3. Exit signal capture (all must be wired)

| Capture point | Where | Output / path | Purpose |
|---------------|--------|----------------|---------|
| **Exit attribution (legacy)** | `log_exit_attribution()` in main | `logs/attribution.jsonl` (type=exit) | PnL, close_reason, hold_minutes, context (entry_score, components, time_of_day, flow_magnitude, signal_strength). |
| **Exit attribution (v2)** | `build_exit_attribution_record()` + `append_exit_attribution()` in main | `logs/exit_attribution.jsonl` | exit_reason_code, v2_exit_components, exit_quality_metrics (MFE, MAE, giveback, saved_loss, left_money), time_in_trade. |
| **Master trade log (exit)** | `append_master_trade()` from log_exit_attribution | `logs/master_trade_log.jsonl` | exit_ts, exit_price, realized_pnl_usd, exit_reason, v2_exit_score. |
| **Signal snapshot (exit)** | `write_snapshot_safe(..., EXIT_FILL)` in log_exit_attribution | Telemetry/snapshot writer | EXIT_FILL event, exit reason. |

**Contract:** Every **full close** must produce: one exit row in attribution.jsonl, one append to exit_attribution.jsonl (v2 record), and one master_trade_log update (exit_ts, exit_price, realized_pnl_usd, exit_reason).

**Exit quality:** For "exiting very quickly" analysis, ensure `info["high_water"]` is passed into `log_exit_attribution()` so MFE/giveback can be computed (see reports/phase9_accel_decisions and run_data_integrity_trace_on_droplet.py).

---

## 4. Learning & feedback (intelligence loop)

| Inputs | Script / process | Outputs | Purpose |
|--------|-------------------|---------|---------|
| attribution.jsonl + exit_attribution.jsonl | `scripts/analysis/attribution_loader.py` (join) | Joined closed trades | Join key: trade_id or symbol+entry_ts. |
| Joined trades | `scripts/analysis/run_exit_effectiveness_v2.py` | `reports/exit_review/exit_effectiveness_v2.{json,md}` | By exit_reason_code: avg/median PnL, tail loss, giveback, time_in_trade. |
| Exit effectiveness | `scripts/exit_tuning/suggest_exit_tuning.py` | `reports/exit_review/exit_tuning_recommendations.md`, patch | Tuning suggestions from data. |
| attribution + exit_attribution + blocked | `board/eod/root_cause.py` | exit_causality_matrix.json, uw_root_cause.json, etc. | EOD root cause, exit reasons costing most. |
| EOD bundle | `board/eod/run_stock_quant_officer_eod.py` | board/eod/out/*.json, *.md | Daily memo, parameter recommendations. |
| Governance | Equity governance loop, replay | overlay_config, lock_or_revert_decision | Lever selection from effectiveness/replay. |

---

## 5. Exit review (confirm wired)

- **Run on droplet:** `python scripts/run_exit_review_on_droplet.py`
  - Runs: `run_exit_effectiveness_v2.py` (last 14 days), `suggest_exit_tuning.py`, bootstraps `logs/exit_truth.jsonl`, dashboard truth audit.
  - Fetches: `exit_effectiveness_v2.json`, `exit_effectiveness_v2.md`, `exit_tuning_recommendations.md`, `dashboard_truth_droplet.json` into `reports/exit_review/`.
- **Exit causality:** Built in EOD by `board/eod/root_cause.py` → `board/eod/out/<date>/exit_causality_matrix.json`.
- **Quick check:** After running exit review, open `reports/exit_review/exit_effectiveness_v2.md` and check:
  - **time_in_trade** distribution (are we exiting very quickly?).
  - **by_exit_reason_code** (signal_decay, time_stop, trail, etc.) and which reasons have worst PnL.
  - **exit_tuning_recommendations.md** for suggested parameter changes.

**Recommendation:** Run exit review at least weekly (e.g. after EOD or weekend). Optionally add a cron or manual step: `python scripts/run_exit_review_on_droplet.py` and commit/fetch the reports so "exiting very quickly" is visible and tunable.

---

## 6. Canonical file bundle (EOD / analysis)

From docs/EOD_DATA_PIPELINE.md:

| # | Path | Role in loop |
|---|------|----------------|
| 1 | `logs/attribution.jsonl` | Entry + exit records (P&L, context). |
| 2 | `logs/exit_attribution.jsonl` | One record per exit (reason, P&L, v2 components, exit_quality_metrics). |
| 3 | `logs/master_trade_log.jsonl` | Trade entries/exits (trade_id, entry_ts, exit_ts, entry/exit prices, v2 scores). |
| 4 | `state/blocked_trades.jsonl` | Blocked trade records (reason, score, components). |
| 5 | `state/daily_start_equity.json` | Session baseline. |
| 6 | `state/peak_equity.json` | Peak for drawdown. |
| 7 | `state/signal_weights.json` | Adaptive weights. |
| 8 | `state/daily_universe_v2.json` | Daily universe. |

Plus: `logs/run.jsonl` (trade_intent, complete cycles), `logs/score_snapshot.jsonl` (when written), signal history storage.

---

## 7. Checklist: full organism wired

- [ ] **Entry:** Every filled order triggers `log_attribution(open_*, ...)` and master_trade_log entry row.
- [ ] **Entry:** trade_intent with decision_outcome and feature_snapshot written to run.jsonl for entered (and optionally blocked) candidates.
- [ ] **Entry:** Blocked candidates written to blocked_trades.jsonl with score and composite_pre_norm/post_norm.
- [ ] **Exit:** Every full close triggers `log_exit_attribution()` → attribution.jsonl (exit row), exit_attribution.jsonl (v2 record), master_trade_log update.
- [ ] **Exit:** high_water passed into log_exit_attribution when available so exit_quality_metrics (giveback, MFE, MAE) are computed.
- [ ] **Learning:** Join (attribution + exit_attribution) works; run_exit_effectiveness_v2.py and suggest_exit_tuning.py run on droplet.
- [ ] **Learning:** EOD board reads attribution + exit_attribution; exit_causality_matrix built.
- [ ] **Exit review:** Run `python scripts/run_exit_review_on_droplet.py` periodically; use exit_effectiveness_v2.md and exit_tuning_recommendations.md to tune "exiting very quickly" and other exit behavior.
- [ ] **Verification:** Run `python scripts/verify_data_capture_and_exit_review.py` to confirm exit review script and dependencies exist; capture files are expected after live/droplet runs.

---

## 8. Optional env for deeper analysis

- `EXPECTANCY_GATE_TRUTH_LOG=1` → logs/expectancy_gate_truth.jsonl.
- `SIGNAL_SCORE_BREAKDOWN_LOG=1` → logs/signal_score_breakdown.jsonl.
- `SCORE_SNAPSHOT_DEBUG=1` → verbose score snapshot logging.

Enable on droplet if you need funnel analysis and signal-level breakdown in logs.

---

## 9. Trade designation for replay

To test entry/exit/universe changes in **multiple scenarios** on the same trades, use a **replay cohort** (date range) and **scenario_id** in backtest config and outputs. See **docs/TRADE_DESIGNATION_FOR_REPLAY.md**. The 30-day backtest (`scripts/run_30d_backtest_droplet.py`) already loads by date window; add `replay_cohort` and `scenario_id` to compare e.g. baseline vs exit_hold_longer vs universe_tight.
