# Telemetry I/O Map

**Purpose:** Every writer and reader of canonical telemetry logs and state.
**Hot path:** execution path (main.py, exit_attribution, direction_intel, master_trade_log). **Offline:** reports, audits, replay, dashboard (read-only).

## Writers (by log)

### attribution.jsonl

- `feature_attribution_v2.py:124 (with ALPHA_ATTRIBUTION_V2.open("a") as f:...)`
- `src\uw\uw_attribution.py:58 (_append_jsonl(UW_ATTRIBUTION_LOG, rec)...)`

### exit_attribution.jsonl

- `main.py:2197 (from src.exit.exit_attribution import build_exit_attribution_record, append_exit...)`
- `main.py:2308 (from src.exit.exit_attribution import append_exit_signal_snapshot, append_exit_e...)`
- `main.py:2424 (append_exit_attribution(rec)...)`
- `scripts\run_regression_checks.py:328 (_run([sys.executable, "-c", "from src.exit.exit_attribution import build_exit_at...)`
- `scripts\run_v2_synthetic_trade_test.py:285 (from src.exit.exit_attribution import build_exit_attribution_record, append_exit...)`
- `scripts\run_v2_synthetic_trade_test.py:366 (append_exit_attribution(ea)...)`
- `scripts\run_v2_synthetic_trade_test.py:494 (from src.exit.exit_attribution import build_exit_attribution_record, append_exit...)`
- `scripts\run_v2_synthetic_trade_test.py:573 (append_exit_attribution(ea)...)`
- `src\exit\exit_attribution.py:44 (def append_exit_attribution(rec: Dict[str, Any]) -> None:...)`
- `scripts\audit\build_telemetry_io_map.py:29 (WRITER_INDICATORS = ["append_exit_attribution", "append_exit_event", "append_mas...)`
- `scripts\governance\check_direction_readiness_and_run.py:10 (- On exit: call this script after append_exit_attribution (e.g. from a small hoo...)`

### master_trade_log.jsonl

- `utils\master_trade_log.py:42 (with MASTER_TRADE_LOG.open("a", encoding="utf-8") as f:...)`
- `main.py:1788 (from utils.master_trade_log import append_master_trade...)`
- `main.py:2146 (from utils.master_trade_log import append_master_trade...)`
- `main.py:2386 (from utils.master_trade_log import append_master_trade...)`
- `scripts\run_v2_synthetic_trade_test.py:284 (from utils.master_trade_log import append_master_trade...)`
- `scripts\run_v2_synthetic_trade_test.py:493 (from utils.master_trade_log import append_master_trade...)`

### exit_event.jsonl

- `src\exit\exit_attribution.py:82 (with EXIT_EVENT_PATH.open("a", encoding="utf-8") as f:...)`
- `main.py:2308 (from src.exit.exit_attribution import append_exit_signal_snapshot, append_exit_e...)`
- `main.py:2383 (append_exit_event(evt)...)`
- `src\exit\exit_attribution.py:78 (def append_exit_event(rec: Dict[str, Any]) -> None:...)`
- `scripts\audit\build_telemetry_io_map.py:29 (WRITER_INDICATORS = ["append_exit_attribution", "append_exit_event", "append_mas...)`

### intel_snapshot_entry.jsonl

- `scripts\audit_direction_intel_wiring.py:62 (# Contract: record is the snapshot itself (append_intel_snapshot_entry writes pa...)`
- `scripts\audit_direction_intel_wiring.py:162 (fix_function = "append_intel_snapshot_entry(): ensure payload contains premarket...)`
- `src\intelligence\direction_intel.py:106 (def append_intel_snapshot_entry(payload: Dict[str, Any], symbol: Optional[str] =...)`
- `src\intelligence\direction_intel.py:306 (append_intel_snapshot_entry(snapshot, symbol)...)`
- `scripts\audit\build_telemetry_io_map.py:29 (WRITER_INDICATORS = ["append_exit_attribution", "append_exit_event", "append_mas...)`
- `src\intelligence\direction_intel.py:114 (with INTEL_SNAPSHOT_ENTRY.open("a", encoding="utf-8") as f:...)`

### intel_snapshot_exit.jsonl

- `src\intelligence\direction_intel.py:120 (def append_intel_snapshot_exit(payload: Dict[str, Any], symbol: Optional[str] = ...)`
- `src\intelligence\direction_intel.py:352 (append_intel_snapshot_exit(exit_snapshot, symbol)...)`
- `scripts\audit\build_telemetry_io_map.py:29 (WRITER_INDICATORS = ["append_exit_attribution", "append_exit_event", "append_mas...)`
- `src\intelligence\direction_intel.py:128 (with INTEL_SNAPSHOT_EXIT.open("a", encoding="utf-8") as f:...)`

### direction_event.jsonl

- `src\intelligence\direction_intel.py:134 (def append_direction_event(...)`
- `src\intelligence\direction_intel.py:307 (append_direction_event(components, "entry", symbol, snapshot.get("timestamp"), {...)`
- `src\intelligence\direction_intel.py:353 (append_direction_event(...)`
- `scripts\audit\build_telemetry_io_map.py:29 (WRITER_INDICATORS = ["append_exit_attribution", "append_exit_event", "append_mas...)`
- `src\intelligence\direction_intel.py:151 (with DIRECTION_EVENT_LOG.open("a", encoding="utf-8") as f:...)`

### position_intel_snapshots.json

- `scripts\audit\build_telemetry_io_map.py:76 (# position_intel_snapshots.json: writer is store_entry_snapshot_for_position in ...)`

## Readers (by log)

### attribution.jsonl

- `scripts\generate_daily_strategy_reports.py:232`
- `scripts\generate_exit_join_health_report.py:52`
- `scripts\generate_snapshot_outcome_attribution_report.py:90`
- `scripts\perf_review_today_on_droplet.py:180`
- `scripts\run_exit_day_summary.py:50`
- `scripts\run_phase9_data_integrity_v5_on_droplet.py:181`
- `scripts\run_regression_checks.py:274`
- `scripts\run_regression_checks.py:313`
- `scripts\run_regression_checks.py:330`
- `scripts\run_v2_synthetic_trade_test.py:269`
- `scripts\run_v2_synthetic_trade_test.py:432`
- `scripts\signal_contribution_and_gaps_audit.py:83`
- `src\exit\exit_attribution.py:26`
- `scripts\exit_research\run_exit_replay_scenario.py:91`
- `scripts\exit_research\run_exit_replay_scenario.py:92`
- `archive\scripts\diagnostic_scripts\check_signals_and_positions.py:101`
- `archive\scripts\diagnostic_scripts\check_workflow_audit.py:291`
- `archive\scripts\diagnostic_scripts\check_workflow_audit.py:330`
- `archive\scripts\diagnostic_scripts\check_workflow_audit.py:338`
- `analyze_today_vs_backtest.py:34`
- `attribution_logging_audit.py:114`
- `backfill_xai_exits.py:54`
- `causal_analysis_engine.py:637`
- `causal_analysis_engine.py:718`
- `comprehensive_daily_trading_analysis.py:110`

### exit_attribution.jsonl

- `scripts\generate_exit_join_health_report.py:52`
- `scripts\generate_snapshot_outcome_attribution_report.py:90`
- `scripts\run_exit_day_summary.py:50`
- `scripts\run_phase9_data_integrity_v5_on_droplet.py:181`
- `scripts\run_regression_checks.py:313`
- `scripts\run_regression_checks.py:330`
- `scripts\run_v2_synthetic_trade_test.py:269`
- `scripts\run_v2_synthetic_trade_test.py:432`
- `scripts\signal_contribution_and_gaps_audit.py:83`
- `src\exit\exit_attribution.py:26`
- `scripts\exit_research\run_exit_replay_scenario.py:92`
- `main.py:1969`
- `main.py:2219`
- `main.py:7279`
- `scripts\owner_validate_artifacts.py:86`
- `scripts\report_last_5_trades.py:116`
- `scripts\run_data_integrity_trace_on_droplet.py:100`
- `scripts\run_full_telemetry_extract.py:662`
- `scripts\run_full_telemetry_extract.py:727`
- `scripts\run_postclose_analysis_pack.py:166`
- `scripts\run_post_revert_fix_droplet.py:305`
- `telemetry\feature_equalizer_builder.py:133`
- `telemetry\feature_family_summary.py:62`
- `telemetry\feature_value_curves.py:130`
- `telemetry\regime_sector_feature_matrix.py:63`

### master_trade_log.jsonl

- `scripts\generate_exit_join_health_report.py:51`
- `scripts\generate_snapshot_outcome_attribution_report.py:89`
- `scripts\run_regression_checks.py:312`
- `scripts\run_v2_synthetic_trade_test.py:268`
- `scripts\run_v2_synthetic_trade_test.py:431`
- `scripts\signal_contribution_and_gaps_audit.py:84`
- `utils\master_trade_log.py:24`
- `scripts\owner_validate_artifacts.py:83`
- `telemetry\exit_join_reconciler.py:113`
- `board\eod\run_stock_quant_officer_eod.py:272`

### exit_event.jsonl

- `scripts\verify_full_exit_telemetry.py:71`
- `fetch_droplet_data_and_generate_report.py:240`
- `first_day_live_analysis.py:260`
- `FULL_TRADING_WORKFLOW_AUDIT.py:352`
- `generate_daily_trading_report.py:306`
- `scripts\verify_full_exit_telemetry.py:113`
- `scripts\verify_intelligence_replay_readiness.py:70`
- `scripts\verify_intelligence_replay_readiness.py:72`
- `scripts\verify_replay_readiness.py:55`
- `archive\investigation_scripts\diagnose_learning_and_exits.py:144`
- `archive\investigation_scripts\verify_learning_and_exits.py:169`
- `archive\investigation_scripts\verify_learning_and_exits.py:187`

### intel_snapshot_entry.jsonl

- `scripts\audit_direction_intel_wiring.py:103`
- `scripts\audit_direction_intel_wiring.py:131`
- `scripts\trade_visibility_review.py:99`
- `src\contracts\telemetry_schemas.py:94`
- `src\governance\direction_readiness.py:56`
- `src\intelligence\direction_intel.py:45`
- `scripts\replay\reconstruct_direction_30d.py:67`
- `src\contracts\telemetry_schemas.py:129`

### intel_snapshot_exit.jsonl

- `src\intelligence\direction_intel.py:46`

### direction_event.jsonl

- `src\intelligence\direction_intel.py:47`

### position_intel_snapshots.json

- `scripts\audit\build_telemetry_io_map.py:77`
- `scripts\audit_direction_intel_wiring.py:170`
- `scripts\audit_direction_intel_wiring.py:174`
- `src\intelligence\direction_intel.py:269`
- `src\intelligence\direction_intel.py:347`
- `scripts\audit\build_telemetry_io_map.py:80`
- `scripts\audit\build_telemetry_io_map.py:81`

## Hot path vs offline

| File | Classification |
|------|-----------------|
| FULL_TRADING_WORKFLOW_AUDIT.py | offline/report |
| analyze_today_vs_backtest.py | offline/report |
| archive\investigation_scripts\VERIFY_LEARNING_PIPELINE.py | offline/report |
| archive\investigation_scripts\analyze_data_availability.py | offline/report |
| archive\investigation_scripts\analyze_historical_data_availability.py | offline/report |
| archive\investigation_scripts\diagnose_learning_and_exits.py | offline/report |
| archive\investigation_scripts\statistical_significance_audit.py | offline/report |
| archive\investigation_scripts\verify_learning_and_exits.py | offline/report |
| archive\scripts\diagnostic_scripts\check_signals_and_positions.py | offline/report |
| archive\scripts\diagnostic_scripts\check_workflow_audit.py | offline/report |
| attribution_logging_audit.py | offline/report |
| backfill_xai_exits.py | offline/report |
| board\eod\run_stock_quant_officer_eod.py | offline/report |
| causal_analysis_engine.py | offline/report |
| comprehensive_daily_trading_analysis.py | offline/report |
| comprehensive_pattern_analysis.py | offline/report |
| counter_intelligence_analysis.py | offline/report |
| daily_alpha_audit.py | offline/report |
| deep_pattern_investigation.py | offline/report |
| deep_trade_analysis.py | offline/report |
| feature_attribution_v2.py | offline/report |
| fetch_droplet_data_and_generate_report.py | offline/report |
| first_day_live_analysis.py | offline/report |
| friday_eow_audit.py | offline/report |
| generate_daily_trading_report.py | offline/report |
| logic_integrity_check.py | offline/report |
| main.py | hot path |
| regime_persistence_audit.py | offline/report |
| reports\_dashboard\intel_dashboard_generator.py | offline/report |
| scripts\adjustment_chain_forensics.py | offline/report |
| scripts\analysis\attribution_loader.py | offline/report |
| scripts\audit\build_telemetry_io_map.py | offline/report |
| scripts\audit_direction_intel_wiring.py | offline/report |
| scripts\exit_research\run_exit_replay_scenario.py | offline/report |
| scripts\generate_daily_strategy_reports.py | offline/report |
| scripts\generate_exit_join_health_report.py | offline/report |
| scripts\generate_snapshot_outcome_attribution_report.py | offline/report |
| scripts\governance\check_direction_readiness_and_run.py | offline/report |
| scripts\owner_validate_artifacts.py | offline/report |
| scripts\perf_review_today_on_droplet.py | offline/report |
| scripts\replay\reconstruct_direction_30d.py | offline/report |
| scripts\report_last_5_trades.py | offline/report |
| scripts\run_data_integrity_trace_on_droplet.py | offline/report |
| scripts\run_exit_day_summary.py | offline/report |
| scripts\run_full_telemetry_extract.py | offline/report |
| scripts\run_phase9_data_integrity_v5_on_droplet.py | offline/report |
| scripts\run_post_revert_fix_droplet.py | offline/report |
| scripts\run_postclose_analysis_pack.py | offline/report |
| scripts\run_regression_checks.py | offline/report |
| scripts\run_v2_synthetic_trade_test.py | offline/report |
| scripts\score_autopsy_from_ledger.py | offline/report |
| scripts\signal_contribution_and_gaps_audit.py | offline/report |
| scripts\trade_visibility_review.py | offline/report |
| scripts\uw_experiment_summary.py | offline/report |
| scripts\verify_full_exit_telemetry.py | offline/report |
| scripts\verify_intelligence_replay_readiness.py | offline/report |
| scripts\verify_replay_readiness.py | offline/report |
| shadow_analysis_blocked_trades.py | offline/report |
| src\contracts\telemetry_schemas.py | offline/report |
| src\exit\exit_attribution.py | offline/report |
| src\governance\direction_readiness.py | offline/report |
| src\intelligence\direction_intel.py | offline/report |
| src\uw\uw_attribution.py | offline/report |
| telemetry\exit_join_reconciler.py | offline/report |
| telemetry\feature_equalizer_builder.py | offline/report |
| telemetry\feature_family_summary.py | offline/report |
| telemetry\feature_value_curves.py | offline/report |
| telemetry\regime_sector_feature_matrix.py | offline/report |
| telemetry\replacement_telemetry_expanded.py | offline/report |
| utils\master_trade_log.py | offline/report |
| validation\scenarios\test_exit_attribution_phase4.py | offline/report |

## Hidden readers (Model B - >=5 confirmed)

| Reader | Log(s) read | Purpose |
|--------|-------------|---------|
| dashboard.py | attribution.jsonl, exit_attribution.jsonl, master_trade_log.jsonl | Dashboard endpoints: trades, exit quality, health |
| src/governance/direction_readiness.py | exit_attribution.jsonl | direction_readiness: count telemetry_trades (direction_intel_embed.intel_snapshot_entry) |
| src/dashboard/direction_banner_state.py | state/direction_readiness.json (derived from exit_attribution) | Banner: X/100 telemetry-backed trades |
| scripts/replay/* (equity_exit_replay, build_canonical_equity_ledger, discover_equity_data_manifest) | attribution.jsonl, exit_attribution.jsonl | Replay loaders and ledger build |
| scripts/build_30d_comprehensive_review.py | attribution.jsonl, exit_attribution.jsonl | EOD/board 30d review |
| scripts/trade_visibility_review.py | exit_attribution, state/direction_readiness.json | Trade visibility and direction readiness report |
| scripts/audit_direction_intel_wiring.py | exit_attribution.jsonl, intel_snapshot_entry.jsonl | Direction intel wiring audit |

*Generated by scripts/audit/build_telemetry_io_map.py*