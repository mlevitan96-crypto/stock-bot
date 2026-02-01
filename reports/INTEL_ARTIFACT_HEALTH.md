# Post-Trade & Shadow Artifact Health

**Generated:** 2026-01-28T17:19:45.026989+00:00 (UTC)

---

## Artifact presence, freshness, size
- **entry_parity_details.json:** exists=False, size=0, mtime=None, status=MISSING
- **live_vs_shadow_pnl.json:** exists=False, size=0, mtime=None, status=MISSING
- **shadow_vs_live_parity.json:** exists=False, size=0, mtime=None, status=MISSING
- **feature_family_summary.json:** exists=False, size=0, mtime=None, status=MISSING
- **exit_intel_completeness.json:** exists=True, size=2783, mtime=2026-01-27 20:30:08.240229+00:00, status=OK
- **score_distribution_curves.json:** exists=True, size=161782, mtime=2026-01-27 20:30:08.292230+00:00, status=OK
- **signal_performance.json:** exists=True, size=70, mtime=2026-01-27 20:30:08.308230+00:00, status=OK
- **signal_weight_recommendations.json:** exists=True, size=78, mtime=2026-01-27 20:30:08.308230+00:00, status=OK
- **feature_equalizer_builder.json:** exists=True, size=774, mtime=2026-01-27 20:30:08.237229+00:00, status=OK
- **feature_value_curves.json:** exists=True, size=3732, mtime=2026-01-27 20:30:08.243229+00:00, status=OK
- **long_short_analysis.json:** exists=True, size=777, mtime=2026-01-27 20:30:08.237229+00:00, status=OK
- **regime_sector_feature_matrix.json:** exists=True, size=138, mtime=2026-01-27 20:30:08.246229+00:00, status=OK
- **regime_timeline.json:** exists=True, size=12260, mtime=2026-01-27 20:30:08.297230+00:00, status=OK
- **replacement_telemetry_expanded.json:** exists=True, size=629, mtime=2026-01-27 20:30:08.299230+00:00, status=OK
- **pnl_windows.json:** exists=True, size=19504, mtime=2026-01-27 20:30:08.304230+00:00, status=OK

## Generation logic (code references)
- entry_parity_details, feature_family_summary, live_vs_shadow_pnl, shadow_vs_live_parity: `generate_missing_shadow_artifacts.py`
- exit_intel_completeness, score_distribution_curves, signal_performance, signal_weight_recommendations: `scripts/run_full_telemetry_extract.py` + telemetry/*.py