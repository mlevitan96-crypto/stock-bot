# Scenario Experiment Registry — Alpaca

**Purpose:** Track parallel, analysis-only scenario experiments (#2–N). These are NOT truth experiments; they do not gate execution or write to the Experiment #1 ledger. They generate ranked hypotheses for future experiment selection.

**Canonical truth:** Experiment #1 (ALPACA_BASELINE_VALIDATION_AND_METRICS_TRUTH) remains the single canonical truth source. Scenario outputs must NOT be written to `state/governance_experiment_1_hypothesis_ledger_alpaca.json`.

---

## Registry format

For each scenario experiment:

| Field | Description |
|-------|-------------|
| **scenario_id** | Unique identifier (e.g. `scenario_002`, `scenario_exit_tight`) |
| **description** | Short description of what is varied |
| **parameters_varied** | Entry thresholds, exit timing, sizing curves, session filters, etc. |
| **data_source** | Historical / shadow logs (e.g. `logs/exit_attribution.jsonl`, `logs/attribution.jsonl`) |
| **output_artifact_path** | `reports/scenario_lab/<scenario_id>_<DATE>.json` |
| **status** | RUNNING \| COMPLETE |

---

## Registered scenarios

| scenario_id | description | parameters_varied | data_source | output_artifact_path | status |
|-------------|-------------|-------------------|-------------|----------------------|--------|
| scenario_002 | Stricter entry threshold (score floor +0.5) | entry_min_score | logs/exit_attribution.jsonl, logs/attribution.jsonl | reports/scenario_lab/scenario_002_&lt;DATE&gt;.json | RUNNING |
| scenario_003 | Longer min-hold (exit timing) | exit_min_hold_minutes | logs/exit_attribution.jsonl | reports/scenario_lab/scenario_003_&lt;DATE&gt;.json | RUNNING |
| scenario_004 | Session filter (first 2h only) | session_start_minutes, session_end_minutes | logs/exit_attribution.jsonl | reports/scenario_lab/scenario_004_&lt;DATE&gt;.json | RUNNING |

*Add rows as new scenarios are defined. Run with `scripts/scenario_lab/run_scenario_batch.py --scenario <id>` or batch with `--workers N`.*

---

## Runner

- **Script:** `scripts/scenario_lab/run_scenario_batch.py`
- **Outputs:** Write only to `reports/scenario_lab/`. No broker writes; no ledger writes; no execution hooks.
- **Summary:** After a batch run, generate `reports/scenario_lab/SCENARIO_SUMMARY_<DATE>.md` with ranking, CSA_REVIEW, and SRE_REVIEW.
