# Truth Audit Fix — Results Review (multi-model)

**Date:** 2026-02-18  
**Bundle:** reports/truth_audit_fix/20260218/

## Adversarial: what still might be wrong?

- **Dashboard JSON:** Root cause is either (1) NaN/Inf in signal dicts (fix: sanitize on write and read), or (2) malformed line in JSONL (fix: skip with counters). Trace script and hardened signal_history_storage address both. If error persists, trace artifact will show exact position and snippet.
- **Score snapshot:** Emitted only for candidates that reach the expectancy gate. If no candidates pass composite gate, snapshot may still be empty until gate thresholds or universe change. Audit PASS requires snapshot_size >= 50 after wait window.
- **Gate alignment:** Unchanged; truth audit Axis 4 still greps main.py. Runtime proof requires that paper run actually evaluates candidates (score_snapshot > 0).

## Quant

- **Distribution from snapshot:** Axis 3 uses composite_score from score_snapshot when diagnostic is unavailable. Same sanity rules (mean >= 1.0, not >80% below 2).
- **Validator:** Only checks JSONL line-by-line parse; does not validate schema of score_snapshot or signal_history fields.

## Product

- **Reversibility:** Score snapshot can be disabled by removing the append_score_snapshot call; signal history sanitization and atomic trim are backward compatible.
- **Verdict rule:** PASS only if deploy OK, validator OK, snapshot_count >= 50, and truth audit Axes 1–6 PASS.

## Files written

- reports/truth_audit_fix/20260218_plan_review.md
- reports/truth_audit_fix/20260218_dashboard_json_error_trace.md (by trace script on droplet)
- reports/truth_audit_fix/20260218_results_review.md (this file)
- reports/truth_audit_fix/20260218/00_deploy_proof.md
- reports/truth_audit_fix/20260218/01_dashboard_json_fix_proof.md
- reports/truth_audit_fix/20260218/02_score_snapshot_proof.md
- reports/truth_audit_fix/20260218/03_truth_audit_postfix.md
- reports/truth_audit_fix/20260218/04_verdict.md

## After run (required output in chat)

- Root cause of dashboard JSON error (file + why)
- Whether score_snapshot is emitting (sample_size, first/last ts)
- Truth audit axis results (1–6)
- PASS/FAIL
- Files written (paths)
