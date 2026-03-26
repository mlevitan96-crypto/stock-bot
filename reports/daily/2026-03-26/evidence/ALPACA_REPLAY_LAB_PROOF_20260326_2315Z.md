# Alpaca replay lab proof (deterministic strict gate)

**TS:** `20260326_2315Z`

## Objective

Provide a **code-complete**, **rerunnable** path to evaluate the Alpaca strict gate against an **additive** workspace (no destructive edits to primary `logs/`).

## Script

`scripts/audit/alpaca_replay_lab_strict_gate.py`

## Command executed (this run)

```text
PYTHONPATH=. python scripts/audit/alpaca_replay_lab_strict_gate.py ^
  --workspace artifacts/alpaca_replay_lab_smoke ^
  --init-snapshot --open-ts-epoch 1774458080 --audit --ts 20260326_2315Z
```

`--init-snapshot` copies listed jsonl files from the repo `logs/` into `artifacts/alpaca_replay_lab_smoke/logs/`.

## Result

- **Bundle:** `reports/ALPACA_REPLAY_LAB_GATE_20260326_2315Z.json`
- **Observed:** `trades_seen: 0` for `OPEN_TS_UTC_EPOCH=1774458080` — copied historical closes have position **open** times **before** the strict era floor, so the **entry-era filter** excludes them from the learning cohort.

## Interpretation (honest)

- The lab **infrastructure is valid** (deterministic gate invocation on an isolated tree).
- This run **does not** prove `incomplete==0` on a non-empty cohort; it proves **cohort segmentation** excludes local snapshot data at the configured epoch.
- **CODE_COMPLETE_CERTIFIED** for join quality would require a replay slice with closes whose **open** time is ≥ floor (or a dedicated lab epoch documented by CSA).

## Adversarial note

Using a looser `--open-ts-epoch` in the lab without CSA labeling would **inflate** green results — excluded by contract §F (replay must be documented).
