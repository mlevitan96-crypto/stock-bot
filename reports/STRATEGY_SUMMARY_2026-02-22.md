# Stock-Bot Strategy Summary (Live Droplet Config)
*Generated on droplet: 2026-02-22T17:30:03.738957+00:00*
## Entry
- **Score gate:** Trades are taken only when the composite **exec score** meets or exceeds **MIN_EXEC_SCORE** (live value: **2.5**). Direction: score ≥ 3.0 → long; otherwise short. Hierarchical thresholds (base/canary/champion) from uw_composite_v2 ENTRY_THRESHOLDS: base 2.7, canary 2.9, champion 3.2. Composite uses **config/registry COMPOSITE_WEIGHTS_V2** (version: 2026-01-20_wt1). **Entry signal components** (uw_composite_v2 WEIGHTS_V3): options_flow, dark_pool, insider, iv_term_skew, smile_slope, whale_persistence, event_alignment, toxicity_penalty, temporal_motif, regime_modifier; congress, shorts_squeeze, institutional, market_tide, calendar_catalyst, etf_flow; greeks_gamma, ftd_pressure, iv_rank, oi_change, squeeze_score. Structural layer (COMPOSITE_WEIGHTS_V2): vol/beta reward, UW strength proxy, premarket alignment, regime/posture alignment, with optional shaping. Max concurrent positions: 16; position size and spread/watchdog limits apply.
## Exit
**Exit urgency** (adaptive_signal_optimizer): urgency = sum of weighted components; **urgency ≥ 6.0 → EXIT**, **≥ 3.0 → REDUCE**, else **HOLD**. **Exit signal components** (and default weights): entry_decay (1.0), adverse_flow (1.2), drawdown_velocity (1.5), time_decay (0.8), momentum_reversal (1.3), volume_exhaustion (0.9), support_break (1.4). Entry decay: when current_score/entry_score < 0.7. Adverse flow: flow reversal vs position direction. Loss limit: +2.0 urgency if current_pnl_pct < -5%. **Hard/rule-based exits:** Trailing stop at **TRAILING_STOP_PCT** (live: **0.015**); time exit at **TIME_EXIT_MINUTES** (live: **240**); stale position: age ≥ **TIME_EXIT_DAYS_STALE** (12 days) and PnL < **TIME_EXIT_STALE_PNL_THRESH_PCT** (0.03). Profit acceleration: after 30 min in profit, trailing stop can tighten to 0.5%; in MIXED regime default trail 1.0%. Displacement and regime-protection exits also apply.
## Adjustments in the Last 72 Hours
```
d412d4f Add generate_strategy_summary_on_droplet.py for full strategy + last 72h adjustments (live config)
b7e86f1 Monday prep: relax baseline validation to direction+attribution_components (exit_reason optional for legacy); check 200 trades
f1659a4 Monday prep: contract-aligned required list, configs/backtest_config.json, optional score_vs_profitability, customer advocate fallback (generate_customer_advocate | customer_advocate_report | inline)
0cd102e Score-vs-profitability: wire into orchestration, deploy and fetch on droplet
a51919f reports: reduce backtest output to 3 files (run_overview.md, multi_model_review.md, baseline_data.json); all data preserved in sections
b652d3b reports: push backtest alpaca_backtest_20260221T225347Z (FINAL_VERDICT OK) + governance + ACTIONABLE_BACKTEST_FRAMEWORK_AND_IDEAS for review (profitability)
6788a2c Full diagnostic orchestration: droplet script, simulation direction/attribution/diverse exits, per-signal attribution, ablation, exec sensitivity, blocked-trade analysis, via-droplet runner
0994119 orchestration: plugin evidence bundle, --evidence for multi-model SRE, step 8/9 contract
4646f32 reports: add backtest details (trades.csv, backtest_trades.jsonl, backtest_exits.jsonl, backtest_details.json) - no gz
7ce971d reports: push backtest run alpaca_backtest_20260221T165416Z (FINAL_VERDICT OK) for download
c65e669 reports: add droplet backtest run alpaca_backtest_20260220T231217Z and zero-trades finding for review
7689ac0 30-day backtest after intelligence overhaul — Fri Feb 20 22:24:09 UTC 2026
31da74d Data-driven scoring only (0 when missing); today backtest summary script for droplet + fetch
20f1ec0 fix: neutral defaults for 6 zeroed signals so composite not crushed when expanded_intel missing
2afeca1 Daily Alpha Audit 2026-02-20 - MEMORY_BANK.md Specialist Tier Monitoring | Friday EOW Audit 2026-02-20 - MEMORY_BANK.md Specialist Tier Monitoring | Regime Persistence Audit 2026-02-20 - MEMORY_BANK.md Specialist Tier Monitoring
a5cfcba Investigation: baseline, gate truth, breakdown, closed loops, order reconciliation, runbook
48f448f Truth run: minimal replay from blocked_trades when no bars; Unicode-safe print
57a36e0 Daily Alpha Audit 2026-02-19 - MEMORY_BANK.md Specialist Tier Monitoring
f37a3d5 Truth run: fallback candidates from blocked_trades + enrich replay with attribution for real A/B/C output (no live trade code)
2448c93 Add droplet truth run + research dataset pipeline (precheck, replay, conditional, build table, audit, baselines, verdict)
e835325 Config: adjust signal weights based on blocked-trade win/loss profile

(Recent file changes: see git log --stat on droplet.)
```
