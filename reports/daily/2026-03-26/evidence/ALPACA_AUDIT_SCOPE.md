# ALPACA AUDIT SCOPE
Generated: 2026-03-19T17:29:25.881364+00:00
Authority: SRE (data & runtime), QSA (signal correctness), CSA (governance). READ-ONLY.

## Phase 0 — Contracts & baselines

### 1) Loaded
- **ALPACA_QUANT_DATA_CONTRACT.md:** Present
- **ALPACA_EXPANSION_SCOPE.md:** Present
- **MEMORY_BANK.md:** Present

### 2) Entry signals (sources)
Modules that compute composite/entry scores or weights:
- DEPLOY_AND_FIX_TRADING.py
- FIX_ADAPTIVE_WEIGHTS_REDUCTION.py
- FIX_TRADING_NOW.py
- FORENSIC_SIGNAL_INTERROGATION.py
- INTEGRATE_XAI_EXPLAINABLE_LOGGING.py
- adaptive_signal_optimizer.py
- board/eod/live_entry_adjustments.py
- board/eod/root_cause.py
- board/eod/run_stock_quant_officer_eod.py
- check_droplet_trading_now.py
- complete_root_cause_analysis.py
- complete_trade_flow_diagnosis.py
- comprehensive_daily_trading_analysis.py
- comprehensive_learning_orchestrator_v2.py
- comprehensive_no_positions_investigation.py
- comprehensive_score_diagnostic.py
- comprehensive_trading_diagnostic.py
- dashboard.py
- debug_flow_calculation.py
- debug_score_calculation.py
- deep_scoring_investigation.py
- deep_trading_diagnosis.py
- diagnose_score_pipeline.py
- diagnostics/weight_impact_report.py
- direct_droplet_investigation.py
- executive_summary_generator.py
- expand_failure_point_monitor.py
- find_the_blocker.py
- first_day_live_analysis.py
- fix_uw_signal_parser.py
- force_diagnose_and_fix.py
- full_pipeline_verification.py
- get_full_traceback_and_scoring.py
- inject_fake_signal_test.py
- integrate_structural_intelligence.py
- investigate_low_scores.py
- investigate_score_stagnation_on_droplet.py
- investigate_trading_issues.py
- main.py
- mock_signal_injection.py

### 3) Exit signals (sources)
Modules that compute exit score or exit reason:
- INTEGRATE_XAI_EXPLAINABLE_LOGGING.py
- adaptive_signal_optimizer.py
- backfill_xai_exits.py
- board/eod/bundle_writer.py
- board/eod/rolling_windows.py
- board/eod/root_cause.py
- board/eod/run_stock_quant_officer_eod.py
- board/eod/start_live_paper_run.py
- dashboard.py
- deep_pattern_investigation.py
- generate_comprehensive_trading_review.py
- generate_final_comprehensive_report.py
- historical_replay_engine.py
- integrate_structural_intelligence.py
- main.py
- reports/_daily_review_tools/droplet_end_of_day_review_payload.py
- reports/_daily_review_tools/generate_daily_review.py
- reports/_dashboard/intel_dashboard_generator.py
- reports/backtests/alpaca_monday_final_20260222T174120Z/patches/postprocess_trade_fields.py
- schema/attribution_v1.py
- schema/contract_validation.py
- scripts/alpaca_edge_2000_pipeline.py
- scripts/alpaca_fastlane_deep_review.py
- scripts/alpaca_full_audit_on_droplet.py
- scripts/alpaca_loss_forensics_droplet.py
- scripts/analysis/backfill_joined_closed_trades.py
- scripts/analysis/build_30d_truth_dataset.py
- scripts/analysis/exit_param_grid_search.py
- scripts/analysis/normalize_exit_truth_with_provenance.py
- scripts/analysis/replay_exits_with_candidate_signals.py
- scripts/analysis/run_effectiveness_reports.py
- scripts/analysis/run_exit_effectiveness_v2.py
- scripts/audit/build_weekly_trade_decision_ledger.py
- scripts/audit/reconstruct_full_trade_ledger.py
- scripts/audit/run_intraday_forensic_review.py
- scripts/audit/run_learning_visibility_audit_on_droplet.py
- scripts/audit/run_promotion_and_exit_capture_review.py
- scripts/b2/b2_daily_evaluator.py
- scripts/blocked_expectancy_analysis.py
- scripts/blocked_signal_expectancy_pipeline.py

### 4) Gating logic (sources)
Modules that implement gates (score, expectancy, block):
- COMPLETE_FULL_WORKFLOW.py
- COMPLETE_STRUCTURAL_INTELLIGENCE_DEPLOYMENT.py
- COMPREHENSIVE_STAGNATION_DIAGNOSTIC.py
- FORENSIC_SIGNAL_INTERROGATION.py
- INTEGRATE_XAI_EXPLAINABLE_LOGGING.py
- adaptive_signal_optimizer.py
- analyze_code_usage.py
- analyze_trade_workflow.py
- board/eod/bundle_writer.py
- board/eod/live_entry_adjustments.py
- board/eod/rolling_windows.py
- board/eod/run_stock_quant_officer_eod.py
- causal_analysis_engine.py
- check_droplet_trading_now.py
- cleanup_unused_code.py
- complete_root_cause_analysis.py
- complete_trade_flow_diagnosis.py
- complete_workflow_trace.py
- comprehensive_daily_trading_analysis.py
- comprehensive_learning_orchestrator_v2.py
- comprehensive_no_positions_investigation.py
- comprehensive_no_trades_diagnosis.py
- comprehensive_service_fix.py
- comprehensive_system_check.py
- comprehensive_trading_diagnostic.py
- config/registry.py
- counter_intelligence_analysis.py
- counterfactual_analyzer.py
- daily_alpha_audit.py
- dashboard.py

### 5) Telemetry emitters (sources)
Modules that emit attribution/telemetry:
- board/eod/live_entry_adjustments.py
- board/eod/uw_failure_diagnostics.py
- main.py
- scripts/alpaca_full_audit_on_droplet.py
- scripts/alpaca_loss_forensics_droplet.py
- scripts/alpaca_telemetry_forward_proof.py
- scripts/alpaca_telemetry_inventory_droplet.py
- scripts/audit/reconstruct_full_trade_ledger.py
- scripts/audit/run_exit_trace_live_proof_on_droplet.py
- scripts/audit/run_monday_open_smoke_test.py
- scripts/compute_signal_correlation_snapshot.py
- scripts/decision_ledger_writer.py
- scripts/full_system_audit.py
- scripts/intel_integrity_audit.py
- scripts/phase2_dryrun_signal_emit.py
- scripts/phase2_forensic_audit.py
- scripts/phase2_full_workflow.py
- scripts/phase2_shadow_dryrun.py
- scripts/run_decision_ledger_capture.py
- scripts/run_full_telemetry_extract.py
- scripts/run_phase9_data_integrity_v5_on_droplet.py
- scripts/run_post_revert_fix_droplet.py
- scripts/run_shadow_vs_live_deep_dive.py
- scripts/run_truth_audit_on_droplet.py
- scripts/run_uw_intel_on_droplet.py
- scripts/run_v2_synthetic_trade_test.py
- scripts/signal_score_breakdown_summary_on_droplet.py
- scripts/validate_intelligence_trace_dryrun.py

### 6) Canonical log paths (from contract)
- Exit attribution: logs/exit_attribution.jsonl
- Master trade log: logs/master_trade_log.jsonl
- Attribution: logs/attribution.jsonl
- Run: logs/run.jsonl
- Orders: logs/orders.jsonl
- Gate diagnostic: logs/gate_diagnostic.jsonl
- Expectancy gate truth: logs/expectancy_gate_truth.jsonl
