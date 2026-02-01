# Stock-bot Cron + Git + Execution Diagnostic Report

**Date:** 2026-02-01
**Generated:** 2026-02-01T18:30:08.464337+00:00

## 1. Detected Path
- `C:\Dev\stock-bot`

## 2. Cron State
```
crontab not found (Windows?)
```

## 3. Script Verification
- board/eod/run_stock_quant_officer_eod.py: ok: board/eod/run_stock_quant_officer_eod.py
- scripts/run_stock_bot_workflow.py: missing: scripts/run_stock_bot_workflow.py
- scripts/run_wheel_strategy.py: missing: scripts/run_wheel_strategy.py

## 4. Report Generation (EOD --dry-run)
- Exit code: 0
- Stdout: (see below)

```
## EOD bundle summary

### Attribution (logs/attribution.jsonl)
- Trades: 2022, Wins: 1315, Losses: 696, Total P&L USD: -33.22
- Exit reasons: {'reconciled_from_daily_report': 2022}
- Sample trades (last 5):
  - SOFI pnl_usd=-0.01 ts=2025-12-30T16:00:00
  - SOFI pnl_usd=-0.01 ts=2025-12-30T16:00:00
  - SOFI pnl_usd=-0.01 ts=2025-12-30T16:00:00
  - SOFI pnl_usd=-0.01 ts=2025-12-30T16:00:00
  - SOFI pnl_usd=-0.01 ts=2025-12-30T16:00:00

### Exit attribution (logs/exit_attribution.jsonl)
- Exits: 35, Total P&L: 63000.00
- Exit reasons: {'profit': 35}
- Sample (last 5):
  - AAPL pnl=None reason=profit
  - AAPL pnl=4500.0 reason=profit
  - AAPL pnl=None reason=profit
  - AAPL pnl=4500.0 reason=profit
  - AAPL pnl=None reason=profit

### Master trade log (logs/master_trade_log.jsonl)
- Records: 10, entries-without-exit: 5, with-exit: 5

### Blocked trades: **MISSING**

### Daily start equity (state/daily_start_equity.json)
- **MISSING**

### Peak equity (state/peak_equity.json)
- **MISSING**

### Signal weights (state/signal_weights.json)
- Top-level keys (up to 20): ['weight_bands']

### Daily universe v2 (state/daily_universe_v2.json)
- Symbol count: 14, sample: [{'breakdown': {'regime_alignment': 0.0125, 'sector_alignment': 0.0125, 'volatility': 0.0}, 'context': {'regime_label': 'NEUTRAL', 'sector': 'TECH'}, 'score': 0.025, 'symbol': 'AAPL'}, {'breakdown': {'regime_alignment': 0.0125, 'sector_alignment': 0.0125, 'volatility': 0.0}, 'context': {'regime_label': 'NEUTRAL', 'sector': 'TECH'}, 'score': 0.025, 'symbol': 'AMD'}, {'breakdown': {'regime_alignment': 0.0125, 'sector_alignment': 0.0125, 'volatility': 0.0}, 'context': {'regime_label': 'NEUTRAL', 'sector': 'TECH'}, 'score': 0.025, 'symbol': 'AMZN'}, {'breakdown': {'regime_alignment': 0.0125, 'sector_alignment': 0.0125, 'volatility': 0.0}, 'context': {'regime_label': 'NEUTRAL', 'sector': 'TECH'}, 'score': 0.025, 'symbol': 'COIN'}, {'breakdown': {'regime_alignment': 0.0125, 'sector_alignment': 0.0125, 'volatility': 0.0}, 'context': {'regime_label': 'NEUTRAL', 'sector': 'TECH'}, 'score': 0.025, 'symbol': 'META'}, {'breakdown': {'regime_alignment': 0.0125, 'sector_alignment': 0.0125, 'volatility': 0.0}, 'context': {'regime_label': 'NEUTRAL', 'sector': 'TECH'}, 'score': 0.025, 'symbol': 'MSFT'}, {'breakdown': {'regime_alignment': 0.0125, 'sector_alignment': 0.0125, 'volatility': 0.0}, 'context': {'regime_label': 'NEUTRAL', 'sector': 'TECH'}, 'score': 0.025, 'symbol': 'NVDA'}, {'breakdown': {'regime_alignment': 0.0125, 'sector_alignment': 0.0125, 'volatility': 0.0}, 'context': {'regime_label': 'NEUTRAL', 'sector': 'TECH'}, 'score': 0.025, 'symbol': 'PLTR'}, {'breakdown': {'regime_alignment': 0.0125, 'sector_alignment': 0.0125, 'volatility': 0.0}, 'context': {'regime_label': 'NEUTRAL', 'sector': 'TECH'}, 'score': 0.025, 'symbol': 'QQQ'}, {'breakdown': {'regime_alignment': 0.0125, 'sector_alignment': 0.0125, 'volatility': 0.0}, 'context': {'regime_label': 'NEUTRAL', 'sector': 'UNKNOWN'}, 'score': 0.025, 'symbol': 'SPY'}, {'breakdown': {'regime_alignment': 0.0125, 'sector_alignment': 0.0125, 'volatility': 0.0}, 'context': {'regime_label': 'NEUTRAL', 'sector': 'TECH'}, 'score': 0.025, 'symbol': 'TSLA'}, {'breakdown': {'regime_alignment': 0.0125, 'sector_alignment': 0.0125, 'volatility': 0.0}, 'context': {'regime_label': 'NEUTRAL', 'sector': 'ENERGY'}, 'score': 0.025, 'symbol': 'XLE'}, {'breakdown': {'regime_alignment': 0.0125, 'sector_alignment': 0.0125, 'volatility': 0.0}, 'context': {'regime_label': 'NEUTRAL', 'sector': 'FINANCIALS'}, 'score': 0.025, 'symbol': 'XLF'}, {'breakdown': {'regime_alignment': 0.0125, 'sector_alignment': 0.0125, 'volatility': 0.0}, 'context': {'regime_label': 'NEUTRAL', 'sector': 'TECH'}, 'score': 0.025, 'symbol': 'XLK'}]

### Missing files
state/blocked_trades.jsonl, state/daily_start_equity.json, state/peak_equity.json

### Symbol risk intelligence (state/symbol_risk_snapshot.json)
- Date: 2026-01-30, universe_size: 14
- Top loss contributors:
  - MSOS: pnl_usd=-68.6
  - MJ: pnl_usd=-54.24
  - APP: pnl_usd=-35.36
  - TSLA: pnl_usd=-31.14
  - COST: pnl_usd=-23.56
- Notes: state/blocked_trades.jsonl missing.; Mode not available in logs; totals only.; Price returns not available; LARGE_MOVE flags not computed.

### Signal profitability insights: **not_loaded** (logs/signal_context.jsonl optional)

### Signal edge diagnostics (summary)

- Data missing. Run `python scripts/analyze_signal_profitability.py --edge --date 2026-02-01` for reports/SIGNAL_EDGE_ANALYSIS_<DATE>.md.

### Equity strategy report (reports/2026-02-01_stock-bot_equity.json)
- strategy_id: equity | date: 2026-02-01
- realized_pnl: 0 | unrealized_pnl: -1130.0
- positions_by_symbol: {'AUDIT-SPY': {'qty': 1, 'market_value': 0.0, 'cost_basis': 450.0}, 'AUDIT-QQQ': {'qty': 1, 'market_value': 0.0, 'cost_basis': 380.0}, 'AUDIT-STOP': {'qty': 1, 'market_value': 0.0, 'cost_basis': 100.0}, 'AUDIT-TP': {'qty': 1, 'market_value': 0.0, 'cost_basis': 100.0}, 'AUDIT-TIME': {'qty': 1, 'market_value': 0.0, 'cost_basis': 100.0}}

### Wheel strategy report (reports/2026-02-01_stock-bot_wheel.json)
- strategy_id: wheel | date: 2026-02-01
- realized_pnl: 0 | unrealized_pnl: 0.0
- premium_collected: 0 | capital_at_risk: 0.0
- assignment_count: 0 | call_away_count: 0 | yield_per_period: None
- positions_by_symbol: {}

### Combined account report (reports/2026-02-01_stock-bot_combined.json)
- date: 2026-02-01
- total_realized_pnl: 0 | total_unrealized_pnl: -1130.0
- equity_strategy_pnl: -1130.0 | wheel_strategy_pnl: 0
- capital_allocation: {'equity': 0, 'wheel': 0}
- account_equity: 0.0 | buying_power: 0.0

---

## Wheel Strategy Review

Answer the following using the wheel and combined reports above:

### 1) Universe & Regime
- Are we running the wheel on liquid, high-quality underlyings with tight spreads?
- Are any tickers showing persistent slippage, wide spreads, or poor fills?
- Is implied volatility high enough to justify selling premium (relative to min_iv_rank or IV proxy)?
- Are we avoiding major earnings or event risk for our underlyings?

### 2) Entries (CSP & CC)
- Are CSPs consistently within the configured delta and DTE bands?
- Are we receiving sufficient premium relative to capital at risk (e.g., weekly or per-cycle yield)?
- Are CCs being sold at strikes that respect cost basis and desired upside, or are we capping gains too aggressively?

### 3) Risk & Capital
- Is wheel staying within its max_capital_fraction and per_position_capital_fraction?
- Is capital overly concentrated in any single ticker or sector?
- What is the worst drawdown from wheel over the last week, and is it acceptable relative to income generated?

### 4) Assignment & Outcomes
- How often are CSPs being assigned vs expiring worthless? Is this in line with expectations?
- How often are CCs being called away vs expiring worthless?
- Are there underlyings that repeatedly lead to poor outcomes and should be removed from the wheel universe?

### 5) Performance & Improvement
- What is the realized yield (premium collected / capital at risk) over the last week and month?
- Is the wheel strategy meaningfully improving the account's risk-adjusted return vs the equity strategy alone?
- Based on recent performance, should we adjust delta bands, DTE ranges, capital allocation, or pause wheel in certain regimes (e.g., very low IV or high event risk)?

---

## WHEEL UNIVERSE REVIEW

(No wheel universe metadata in telemetry for this date.)

Answer when data is available:

- Are the selected tickers appropriate given liquidity, spreads, IV, and sector balance?
- Are we avoiding overexposure to technology?
- Are there better non-tech ETFs or mega-cap stocks that should be promoted?
- Should any current tickers be demoted due to poor assignment outcomes or low premium?
- Is the universe sufficiently diversified across sectors?
- Are we capturing enough premium relative to risk in the chosen universe?

---

## STRATEGY PROMOTION REVIEW

### Strategy comparison (from combined report)
- equity_realized_pnl: 0.0 | wheel_realized_pnl: 0.0
- equity_drawdown: None | wheel_drawdown: None
- equity_sharpe_proxy: None | wheel_sharpe_proxy: None
- wheel_yield_per_period: None
- capital_efficiency_equity: 0.0 | capital_efficiency_wheel: 0.0
- promotion_readiness_score: 45 | recommendation: WAIT

Answer using the comparison data above:

- Compare equity vs wheel performance today and this week.
- Which strategy has better realized PnL stability?
- Which strategy has lower drawdowns?
- Which strategy has better capital efficiency?
- Is wheel generating consistent premium relative to risk?
- Is wheel's assignment behavior healthy or dangerous?
- Based on the promotion_readiness_score, should wheel be promoted to real capital?
- If not, what specific improvements are needed?

ERROR Bundle file missing: C:\Dev\stock-bot\state\blocked_trades.jsonl
ERROR Bundle file missing: C:\Dev\stock-bot\state\daily_start_equity.json
ERROR Bundle file missing: C:\Dev\stock-bot\state\peak_equity.json
WARNING Missing bundle files: ['state/blocked_trades.jsonl', 'state/daily_start_equity.json', 'state/peak_equity.json']; continuing with partial analysis.
INFO Calling Clawdbot agent (TODO: model/provider Gemini)...
INFO Dry-run: skipping clawdbot call.
INFO Wrote C:\Dev\stock-bot\board\eod\out\quant_officer_eod_2026-02-01.json
INFO Wrote C:\Dev\stock-bot\board\eod\out\quant_officer_eod_2026-02-01.md
INFO Wrote C:\Dev\stock-bot\board\eod\out\symbol_risk_snapshot_2026-02-01.json
INFO Wrote C:\Dev\stock-bot\board\eod\out\symbol_risk_snapshot_2026-02-01.md

```

## 5. Git State
- Branch: main

```
On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   MEMORY_BANK.md
	modified:   board/eod/install_eod_cron_on_droplet.py
	modified:   board/eod/run_eod_on_droplet.py
	modified:   board/eod/run_stock_quant_officer_eod.py
	modified:   board/stock_quant_officer_contract.md
	modified:   main.py
	modified:   reports/SNAPSHOT_HARNESS_VERIFICATION_2026-01-30.md
	modified:   reports/eod_manifests/.gitkeep
	modified:   scripts/droplet_sync_to_github.sh
	modified:   scripts/local_sync_from_droplet.sh
	modified:   scripts/run_stock_eod_integrity_on_droplet.sh

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	EOD--OUT/
	PAPER_MODE_DEPLOY_VERIFY.md
	board/eod/_check_paths_droplet.py
	board/eod/_find_bundle_droplet.py
	board/eod/_run_eod_fresh_session.py
	board/eod/_run_eod_on_droplet_check.py
	board/eod/audit_eod_pipeline.py
	board/eod/out/.gitkeep
	board/eod/out/2026-01-30_raw_response.txt
	board/eod/out/quant_officer_eod_2026-01-30.json
	board/eod/out/quant_officer_eod_2026-01-30.md
	board/eod/out/quant_officer_eod_2026-01-31.json
	board/eod/out/quant_officer_eod_2026-01-31.md
	board/eod/out/quant_officer_eod_2026-02-01.json
	board/eod/out/quant_officer_eod_2026-02-01.md
	board/eod/out/stock_quant_officer_eod_raw_2026-01-29.txt
	board/eod/out/symbol_risk_snapshot_2026-01-30.json
	board/eod/out/symbol_risk_snapshot_2026-01-30.md
	board/eod/out/symbol_risk_snapshot_2026-01-31.json
	board/eod/out/symbol_risk_snapshot_2026-01-31.md
	board/eod/out/symbol_risk_snapshot_2026-02-01.json
	board/eod/out/symbol_risk_snapshot_2026-02-01.md
	board/quant_officer_contract.md
	config/config_loader.py
	config/health_escalation.py
	config/live/
	config/moltbot/
	config/paper/
	config/paper_mode_config.py
	config/paper_mode_overrides.json
	config/paper_mode_overrides.yaml
	config/shadow/
	config/shadow_tuning_profiles.yaml
	config/strategies.yaml
	config/universe_wheel.yaml
	config/universe_wheel_expanded.yaml
	data/__init__.py
	data/composite_cache.json
	data/composite_cache.json.bak_stress4
	data/health_status.json
	data/self_heal_escalations.json
	deploy/stock-bot-health.service
	deploy/stock-bot-health.timer
	docs/CRON_STRATEGIC_REVIEW.md
	docs/stock-bot_governance.md
	docs/stock-bot_overview.md
	docs/stock-bot_wheel_strategy.md
	health/
	reports/2026-01-31_stock-bot_combined.json
	reports/2026-01-31_stock-bot_equity.json
	reports/2026-01-31_stock-bot_wheel.json
	reports/2026-01-31_weekly_promotion_report.json
	reports/2026-02-01_stock-bot_combined.json
	reports/2026-02-01_stock-bot_equity.json
	reports/2026-02-01_stock-bot_wheel.json
	reports/AI_GOVERNANCE_BOARD.md
	reports/DASHBOARD_DEBUG_AUDIT.md
	reports/DASHBOARD_ENDPOINT_AUDIT.md
	reports/DASHBOARD_ENDPOINT_AUDIT_FINAL.md
	reports/DASHBOARD_ENDPOINT_CACHE_STATUS.md
	reports/DASHBOARD_ENDPOINT_FIX_PLAN.md
	reports/DASHBOARD_ENDPOINT_SCHEMA_CHECK.md
	reports/DASHBOARD_PANEL_INVENTORY.md
	reports/DASHBOARD_PANEL_WIRING.md
	reports/DASHBOARD_PREFLIGHT.md
	reports/DASHBOARD_SYSTEM_EVENTS.md
	reports/DASHBOARD_TELEMETRY_DIAGNOSIS.md
	reports/DASHBOARD_VERDICT.md
	reports/DROPLET_INTEL_AUDIT_AND_FIXES.md
	reports/EOD_CANONICALIZATION_NOTICE.md
	reports/EOD_PIPELINE_DIAGNOSTIC_REPORT.md
	reports/EOD_RUN_VERIFICATION_2026-01-30.md
	reports/EOD_TARGETED_REPAIR_SUMMARY.md
	reports/FALLBACK_USAGE.md
	reports/FULL_DEPLOYMENT_AND_DATA_HEALTH_REPORT.md
	reports/GIT_SYNC_VERIFICATION_2026-01-30.md
	reports/GOVERNANCE_INTROSPECTION_AUDIT.md
	reports/HEALTH_ACTIONS.md
	reports/HEALTH_CHECKS.md
	reports/HEALTH_IMPLEMENTATION_SUMMARY.md
	reports/HEALTH_SELF_HEAL_VERIFICATION.md
	reports/HEALTH_VERDICT.md
	reports/INTELLIGENCE_TRACE_DEPLOYMENT_PROOF.md
	reports/INTELLIGENCE_TRACE_DROPLET_DEPLOYMENT_PROOF.md
	reports/INTEL_ARTIFACT_HEALTH.md
	reports/INTEL_DATA_PRESENCE.md
	reports/INTEL_DECISION_TRACE.md
	reports/INTEL_EXPECTED_INVENTORY.md
	reports/INTEL_GATES.md
	reports/INTEL_SCORE_COMPONENTS.md
	reports/INTEL_SIGNAL_FEATURES.md
	reports/INTEL_SILENT_FAILURES.md
	reports/INTEL_SYSTEM_VERDICT.md
	reports/LIVE_CONFIRMATION_DECISIONS.md
	reports/LIVE_CONFIRMATION_ORDERS.md
	reports/LIVE_CONFIRMATION_POSITIONS.md
	reports/LIVE_CONFIRMATION_PREFLIGHT.md
	reports/LIVE_CONFIRMATION_SHADOW.md
	reports/LIVE_CONFIRMATION_VERDICT.md
	reports/LIVE_MARKET_AUDIT_REPORT.md
	reports/LIVE_TRACE_BLOCK_REASONS.md
	reports/LIVE_TRACE_DECISIONS.md
	reports/LIVE_TRACE_GATES.md
	reports/LIVE_TRACE_ORDER_JOIN.md
	reports/LIVE_TRACE_PREFLIGHT.md
	reports/LIVE_TRACE_SENTINEL.md
	reports/LIVE_TRACE_SIGNAL_LAYERS.md
	reports/LIVE_TRACE_VERDICT.md
	reports/MEMORY_FIRST_EOD_DISCOVERY_REPORT.md
	reports/PERF_TODAY_GATES.json
	reports/PERF_TODAY_RAW_STATS.json
	reports/PERF_TODAY_REGIME.json
	reports/PERF_TODAY_SIGNALS.json
	reports/PERF_TODAY_SUMMARY.md
	reports/PERF_TODAY_TRADES.json
	reports/PERF_TUNING_BRIEF_TODAY.md
	reports/POSTMARKET_EXECUTION.md
	reports/POSTMARKET_GATES_AND_DISPLACEMENT.md
	reports/POSTMARKET_POSITIONS_AND_EXITS.md
	reports/POSTMARKET_PREFLIGHT.md
	reports/POSTMARKET_SHADOW_ANALYSIS.md
	reports/POSTMARKET_SIGNALS.md
	reports/POSTMARKET_VERDICT_2026-01-27.md
	reports/SELF_HEAL_OBSERVABILITY_SUMMARY.md
	reports/SELF_HEAL_PATTERNS.md
	reports/SELF_HEAL_STRESS_TEST.md
	reports/SHADOW_TUNING_COMPARISON.md
	reports/SHADOW_TUNING_baseline.json
	reports/SHADOW_TUNING_baseline.md
	reports/SHADOW_TUNING_exit_tighten.json
	reports/SHADOW_TUNING_exit_tighten.md
	reports/SHADOW_TUNING_higher_min_exec_score.json
	reports/SHADOW_TUNING_higher_min_exec_score.md
	reports/SHADOW_TUNING_relaxed_displacement.json
	reports/SHADOW_TUNING_relaxed_displacement.md
	reports/SIGNAL_CONTEXT_CAPTURE_VERIFICATION_2026-01-30.md
	reports/SIGNAL_EDGE_ANALYSIS_2026-01-30.md
	reports/SIGNAL_EDGE_CAPTURE_VERIFICATION_2026-01-30.md
	reports/SIGNAL_INTELLIGENCE_AUDIT_2026-01-30.md
	reports/SIGNAL_PROFIT_ATTRIBUTION_2026-01-30.md
	reports/STOCKS_SYSTEMS_CARTOGRAPHER_EOD_BUNDLE.md
	reports/SYMBOL_RISK_INTELLIGENCE_IMPLEMENTATION.md
	reports/SYMBOL_RISK_INTELLIGENCE_VERIFICATION_2026-01-30.md
	reports/UW_CONFIG_AND_EVENTS.md
	reports/UW_DECISION_IMPACT_MATRIX.md
	reports/UW_ENDPOINT_INVENTORY.md
	reports/UW_GATE_INFLUENCE.md
	reports/UW_INGESTION_AUDIT.md
	reports/UW_SCORE_CONTRIBUTION.md
	reports/UW_SIGNAL_ENGINE_MAP.md
	reports/UW_SIGNAL_ENGINE_VERDICT.md
	scripts/analyze_signal_profitability.py
	scripts/audit_stock_bot_readiness.py
	scripts/blocked_counterfactuals_build_today.py
	scripts/build_intelligence_profitability_today.py
	scripts/clear_health_safe_mode.py
	scripts/compare_shadow_profiles.py
	scripts/dashboard_uw_audit.py
	scripts/deploy_dashboard_pull_and_restart.py
	scripts/deploy_intelligence_trace_to_droplet.py
	scripts/diagnose_cron_and_git.py
	scripts/discover_alpaca_credentials_on_droplet.py
	scripts/exit_attribution_build_today.py
	scripts/fetch_eod_to_local.py
	scripts/generate_daily_strategy_reports.py
	scripts/generate_symbol_risk_snapshot.py
	scripts/generate_weekly_promotion_report.py
	scripts/generate_wheel_universe_health.py
	scripts/governance_cleanup_and_ai_board_activation.sh
	scripts/health_run.py
	scripts/install_dashboard_on_droplet.py
	scripts/install_stock_bot_cron.py
	scripts/intel_integrity_audit.py
	scripts/live_trace_verification.py
	scripts/perf_review_summarize_today.py
	scripts/perf_review_today_on_droplet.py
	scripts/perf_tuning_brief_today.py
	scripts/run_dashboard_uw_audit_on_droplet.py
	scripts/run_full_deploy_and_verification_on_droplet.py
	scripts/run_full_tuning_cycle_today_on_droplet.py
	scripts/run_intel_integrity_audit_on_droplet.py
	scripts/run_live_confirmation_on_droplet.py
	scripts/run_live_market_audit_on_droplet.py
	scripts/run_live_trace_verification_on_droplet.py
	scripts/run_perf_review_today_on_droplet.py
	scripts/run_postmarket_analysis.py
	scripts/run_postmarket_analysis_on_droplet.py
	scripts/run_shadow_tuning_profile.py
	scripts/run_uw_deploy_and_audit_on_droplet.py
	scripts/run_uw_signal_engine_audit_on_droplet.py
	scripts/self_heal_pattern_report.py
	scripts/stress_test_self_heal.py
	scripts/verify_dashboard_contracts.py
	scripts/verify_health_and_self_heal.py
	strategies/
	telemetry/blocked_counterfactuals.py
	telemetry/exit_attribution_enhancer.py
	telemetry/paper_mode_intel_state.json
	telemetry/signal_context_logger.py

no changes added to commit (use "git add" and/or "git commit -a")

```

## 6. Fixes Applied
None

## 7. Next Steps
- Verify cron fires at scheduled times
- Monitor logs/ directory
