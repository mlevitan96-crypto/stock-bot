# Stock-bot Cron + Git + Execution Diagnostic Report

**Date:** 2026-02-01
**Generated:** 2026-02-01T18:43:53.588682+00:00

## 1. Detected Path
- `/root/stock-bot`

## 2. Cron State
```
0 * * * * cd ~/stock-bot && ./report_status_to_git.sh >> /tmp/git_sync.log 2>&1
30 20 * * 1-5 cd /root/stock-bot && venv/bin/python specialist_tier_monitoring_orchestrator.py >> logs/orchestrator.log 2>&1
30 20 * * * cd /root/stock-bot && /root/stock-bot/venv/bin/python3 scripts/run_full_telemetry_extract.py >> logs/telemetry_extract.log 2>&1
32 21 * * 1-5 /root/stock-bot/scripts/droplet_sync_to_github.sh >> /root/stock-bot/cron_sync.log 2>&1
30 21 * * 1-5 cd /root/stock-bot && CLAWDBOT_SESSION_ID="stock_quant_eod_$(date -u +%Y-%m-%d)" /usr/bin/python3 board/eod/run_stock_quant_officer_eod.py >> /root/stock-bot/cron_eod.log 2>&1
31 21 * * 1-5 cd /root/stock-bot && /usr/bin/python3 scripts/run_exit_join_and_blocked_attribution_on_droplet.py --date $(date -u +\%Y-\%m-\%d) >> logs/learning_pipeline.log 2>&1

```

## 3. Script Verification
- board/eod/run_stock_quant_officer_eod.py: not executable (chmod +x board/eod/run_stock_quant_officer_eod.py)
- scripts/run_stock_bot_workflow.py: missing: scripts/run_stock_bot_workflow.py
- scripts/run_wheel_strategy.py: missing: scripts/run_wheel_strategy.py

## 4. Report Generation (EOD --dry-run)
- Exit code: 0
- Stdout: (see below)

```
INFO Calling Clawdbot agent (TODO: model/provider Gemini)...
INFO Dry-run: skipping clawdbot call.
INFO Wrote /root/stock-bot/board/eod/out/stock_quant_officer_eod_2026-02-01.json
INFO Wrote /root/stock-bot/board/eod/out/stock_quant_officer_eod_2026-02-01.md

```

## 5. Git State
- Branch: main

```
On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   clear_freeze.py
	modified:   clear_freeze_and_check.py
	modified:   clear_freeze_and_reset.py
	modified:   comprehensive_daily_trading_analysis.py
	modified:   comprehensive_trading_diagnostic.py
	modified:   dashboard.py
	modified:   fix_blocked_readiness.py
	modified:   inject_fake_signal_test.py
	modified:   trading_readiness_test_harness.py

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	board/eod/out/stock_quant_officer_eod_2026-02-01.json
	board/eod/out/stock_quant_officer_eod_2026-02-01.md
	board/eod/out/stock_quant_officer_eod_raw_2026-01-29.txt
	config/shadow_tuning_profiles.yaml
	data/uw_expanded_intel.json
	data/uw_flow_cache.json
	data/uw_weights.json
	reports/DASHBOARD_ENDPOINT_AUDIT.md
	reports/DASHBOARD_ENDPOINT_CACHE_STATUS.md
	reports/DASHBOARD_ENDPOINT_SCHEMA_CHECK.md
	reports/DASHBOARD_PANEL_INVENTORY.md
	reports/DASHBOARD_PANEL_WIRING.md
	reports/DASHBOARD_PREFLIGHT.md
	reports/DASHBOARD_SYSTEM_EVENTS.md
	reports/DASHBOARD_TELEMETRY_DIAGNOSIS.md
	reports/DASHBOARD_VERDICT.md
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
	reports/LIVE_TRACE_BLOCK_REASONS.md
	reports/LIVE_TRACE_DECISIONS.md
	reports/LIVE_TRACE_GATES.md
	reports/LIVE_TRACE_ORDER_JOIN.md
	reports/LIVE_TRACE_PREFLIGHT.md
	reports/LIVE_TRACE_SENTINEL.md
	reports/LIVE_TRACE_SIGNAL_LAYERS.md
	reports/LIVE_TRACE_VERDICT.md
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
	reports/SHADOW_DAY_SUMMARY_2026-01-01.md
	reports/SHADOW_TUNING_COMPARISON.md
	reports/SHADOW_TUNING_baseline.json
	reports/SHADOW_TUNING_baseline.md
	reports/SHADOW_TUNING_exit_tighten.json
	reports/SHADOW_TUNING_exit_tighten.md
	reports/SHADOW_TUNING_higher_min_exec_score.json
	reports/SHADOW_TUNING_higher_min_exec_score.md
	reports/SHADOW_TUNING_relaxed_displacement.json
	reports/SHADOW_TUNING_relaxed_displacement.md
	reports/UW_CONFIG_AND_EVENTS.md
	reports/UW_DECISION_IMPACT_MATRIX.md
	reports/UW_ENDPOINT_INVENTORY.md
	reports/UW_GATE_INFLUENCE.md
	reports/UW_INGESTION_AUDIT.md
	reports/UW_SCORE_CONTRIBUTION.md
	reports/UW_SIGNAL_ENGINE_MAP.md
	reports/UW_SIGNAL_ENGINE_VERDICT.md
	reports/V2_TUNING_SUGGESTIONS_2026-01-23.md
	reports/daily_report_2026-01-23.json
	reports/daily_report_2026-01-27.json
	reports/daily_report_2026-01-28.json
	reports/daily_report_2026-01-29.json
	reports/daily_report_2026-01-30.json
	reports/dashboard_audits/
	reports/report_2026-01-23.html
	reports/report_2026-01-23.json
	reports/report_2026-01-24.html
	reports/report_2026-01-24.json
	reports/report_2026-01-25.html
	reports/report_2026-01-25.json
	reports/report_2026-01-26.html
	reports/report_2026-01-26.json
	reports/report_2026-01-27.html
	reports/report_2026-01-27.json
	reports/report_2026-01-28.html
	reports/report_2026-01-28.json
	reports/report_2026-01-29.html
	reports/report_2026-01-29.json
	reports/report_2026-01-30.html
	reports/report_2026-01-30.json
	reports/report_2026-01-31.html
	reports/report_2026-01-31.json
	reports/report_2026-02-01.html
	reports/report_2026-02-01.json
	scripts/blocked_counterfactuals_build_today.py
	scripts/build_intelligence_profitability_today.py
	scripts/cleanup_bad_aapl_2026_01_22.py
	scripts/cleanup_bad_aapl_shadow_outliers_2026_01_23.py
	scripts/compare_shadow_profiles.py
	scripts/dashboard_uw_audit.py
	scripts/exit_attribution_build_today.py
	scripts/intel_integrity_audit.py
	scripts/live_trace_verification.py
	scripts/perf_review_summarize_today.py
	scripts/perf_review_today_on_droplet.py
	scripts/perf_tuning_brief_today.py
	scripts/run_postmarket_analysis.py
	scripts/run_shadow_tuning_profile.py
	telemetry/blocked_counterfactuals.py
	telemetry/exit_attribution_enhancer.py
	weights.json

no changes added to commit (use "git add" and/or "git commit -a")

```

## 6. Fixes Applied
Fix SSH/key for root; check known_hosts, remote URL

## 7. Next Steps
- Verify cron fires at scheduled times
- Monitor logs/ directory
