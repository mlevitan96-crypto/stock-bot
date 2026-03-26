# Non-vacuous certification mechanisms — implementation

**TS:** `20260327_0200Z`

## MECHANISM 1 — Live forward poll

**File:** `scripts/audit/alpaca_forward_poll_droplet.py`

- `--max-wait-seconds` (default **21600**)
- `--poll-interval-seconds` (default **300**)
- Stop when `(econ>=10 AND entered>=10)` OR `(runtime>=3600 AND econ>0 AND entered>0)` OR `--success-on-non-vacuous-only`
- Per-iteration artifacts: `<json_out_stem>_iter_<n>.json` and `.md`
- Final aggregate: `--json-out`

## MECHANISM 2 — Replay strict gate (code-complete)

**File:** `scripts/audit/alpaca_replay_lab_strict_gate.py`

- `--strict-epoch-start` **or** `--slice-hours` (with optional `--replay-era-auto`)
- `--init-snapshot` copies jsonl into isolated `--workspace`
- `--json-out` full bundle path
- Output includes `era_selection_meta` and `cert_label`

## Strict cohort cert bundle

**File:** `scripts/audit/alpaca_strict_cohort_cert_bundle.py`

- `--open-ts-epoch` + `--trace-sample 15` + `--json-out`
- Parity on **strict cohort** trade_ids; traces sampled from `complete_trade_ids`
- `non_vacuous`: economic closes in era + entered signal (cohort symbol / epoch / or `trades_complete>0`)

## Gate extensions (telemetry)

**File:** `telemetry/alpaca_strict_completeness_gate.py`

- `collect_complete_trade_ids`, `collect_strict_cohort_trade_ids` for certification tooling

## Droplet orchestration

**File:** `scripts/audit/run_alpaca_droplet_learning_cert_final.py`

- Git sync, service discovery, upload scripts, replay lab, strict gate stdout, cert bundle
