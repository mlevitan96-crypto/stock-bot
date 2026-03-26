# CSA Review: Alpaca data path integrity & signal granularity

**Mission:** DATA PATH INTEGRITY & SIGNAL GRANULARITY CONFIRMATION  
**Timestamp:** 20260314  
**Authority:** CSA embedded reviewer (veto authority).

---

## 1. Are data paths correct?

**YES.** Canonical sources are declared and consistent:

- **Primary:** `logs/exit_attribution.jsonl` — used by the pipeline (Step 1) to build TRADES_FROZEN.csv. Droplet inventory and pipeline read reconciliation (Phases 0–1) confirm the pipeline reads this file and row counts align (source lines vs CSV data rows).
- **Secondary:** `logs/master_trade_log.jsonl`, `logs/attribution.jsonl` — used for reconciliation and day-PnL; not used as Step 1 input. Paths are correct and append-only.

No evidence of wrong paths, filtering of records by path, or overwrite of primary/secondary logs by the pipeline.

---

## 2. Is signal telemetry sufficient for fine-grained tuning?

**YES.** Phase 3 (signal granularity audit) confirms:

- **Per trade:** `v2_exit_score`, `v2_exit_components` (per-component values), `attribution_components` (signal_id + contribution_to_score), `exit_reason`, `exit_reason_code`, regime/strategy/mode labels, and optional `exit_quality_metrics` (MFE/MAE).
- **Components are separable** (not collapsed): each exit lever (flow_deterioration, score_deterioration, regime_shift, etc.) is logged individually.
- **Schema versioning:** `composite_version` and attribution schema version are present.

Weights and thresholds are in code (`exit_score_v2.py`); changes require code/config deployment. There is no runtime API for tuning without a deploy. For a governed, audit-trail process, this is sufficient for fine-grained adjustment.

---

## 3. Blockers to governed adjustment?

**None** from this mission. Observed limitations (not blockers):

- **Join coverage:** Entry/exit attribution frozen files (`alpaca_entry_attribution.jsonl`, `alpaca_exit_attribution.jsonl`) are empty on the droplet, so join coverage for entry/exit canonical attribution is 0%. TRADES_FROZEN is built from `exit_attribution.jsonl`; trade_key derivation is consistent. Board and tuning do not depend on the empty canonical attribution files for the current pipeline.
- **DATA_READY gates:** Pipeline may emit ALPACA_JOIN_INTEGRITY_BLOCKER or SAMPLE_SIZE blocker when join coverage or sample size is below threshold. These are correct governance behavior; use `--allow-missing-attribution` for diagnostic runs only.

---

## Verdict

- **Data paths:** Correct and consistent.  
- **Signal telemetry:** Sufficient for fine-grained tuning (with code/config change process).  
- **Governed adjustment:** No blockers identified. CSA veto remains in place for any promotion or live change; this audit does not authorize execution changes.
