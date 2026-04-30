"""
Shadow Vanguard V2/V3 (XGBoost) — canonical implementation: ``telemetry.vanguard_ml_runtime``.

``telemetry.shadow_evaluator`` builds the ML row and calls ``enrich_shadow_v2_v3_fields`` there.
This module exists as a stable anchor path for audits and docs; do not duplicate model loading here.
"""
