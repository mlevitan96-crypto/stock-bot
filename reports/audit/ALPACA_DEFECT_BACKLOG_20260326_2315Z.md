# Alpaca defect backlog (ranked)

**TS:** `20260326_2315Z`

| ID | Symptom | Root cause (hypothesis) | Proof needed | Fix plan | Acceptance | Risk |
|----|---------|-------------------------|--------------|----------|------------|------|
| ALP-001 | Forward certification **STILL_BLOCKED** (prior run) | Post-deploy forward cohort vacuous; strict era excludes legacy | Droplet `forward_parity_audit` + strict gate JSON; poll for non-vacuous window | Run `scripts/audit/alpaca_forward_poll_droplet.py` after deploy; collect ≥10 closes | `forward_trades_incomplete==0`, parity, 15 traces | Low — observability only |
| ALP-002 | `LEARNING_STATUS` **BLOCKED** / `NO_POST_DEPLOY_PROOF_YET` on dev workspace | Local `open_ts_epoch` floor yields **trades_seen=0** despite lines in `exit_attribution.jsonl` | Baseline JSON `reports/ALPACA_BASELINE_20260326_2315Z.json` | Use droplet or lower epoch **only** in labeled replay lab, not production gate | Strict cohort non-empty **or** labeled legacy quarantine | Medium if epoch tampered |
| ALP-003 | Legacy cohort incomplete (117+ on droplet prior evidence) | Historical emits before identity repair | Strict gate `legacy_trades_incomplete`; quarantine label | Optional additive backfill mission (CSA-approved only) | Legacy explicitly excluded from forward cert | Backfill risk to raw logs |

**Phase 4 repair loop:** No code defects fixed in this sweep; **telemetry scripts added** (`run_telemetry_learning_baselines.py`, `alpaca_replay_lab_strict_gate.py`, `alpaca_forward_poll_droplet.py`). Per-defect before/after JSON not materialized for ALP-* beyond baseline/replay lab artifacts.
