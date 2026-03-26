# Alpaca strict gate + cert — droplet result

**Timestamp:** `20260326_STRICT_ZERO_FINAL`

## Commands run (droplet)

1. `scripts/audit/run_alpaca_strict_repair_verify_droplet.py`  
   - `git fetch origin main && git reset --hard origin/main`  
   - Remove prior `strict_backfill_*.jsonl` only  
   - Upload gate/repair/cert sources  
   - `alpaca_strict_six_trade_additive_repair.py --apply --repair-all-incomplete-in-era --open-ts-epoch 1774535335.472568`  
   - `alpaca_strict_repair_forensics.py`  
   - `alpaca_strict_completeness_gate.py --audit --open-ts-epoch 1774535335.472568`  
   - `alpaca_strict_cohort_cert_bundle.py --open-ts-epoch 1774535335.472568 --trace-sample 15`

2. `scripts/audit/run_alpaca_droplet_learning_cert_final.py --ts 20260326_STRICT_ZERO_FINAL --skip-poll`  
   - Replay lab (auto strict epoch)  
   - Same repair script idempotently (`--open-ts-epoch` = replay `strict_epoch_start`)  
   - Strict gate + cert bundle on full `/root/stock-bot` with that epoch  

## Hard criteria (learning-cert mission)

From `reports/ALPACA_DROPLET_CERT_MISSION_20260326_STRICT_ZERO_FINAL.json` parsed fields:

| Criterion | Result |
|-----------|--------|
| A) `trades_incomplete` | **0** |
| B) Parity `strict_cohort_economic_closes` vs unified terminals | **`parity_exact: true`** (119 vs 119 on verify; 53 vs 53 on replay-era mission — both exact) |
| C) Traces | **15** sampled, `trace_all_pass: true`, `cert_ok: true` |
| D) Droplet proof | Mission JSON + this note; verify JSON for additive repair volume |

## Machine-readable bundle

`reports/ALPACA_STRICT_GATE_RESULT_20260326_STRICT_ZERO_FINAL.json` contains `strict_gate_json`, `cert_bundle_json`, replay epoch, and a pointer to the verify capture.

**Stdout/stderr:** Large tails are embedded in `reports/ALPACA_DROPLET_CERT_MISSION_20260326_STRICT_ZERO_FINAL.json` under `steps.*` and in `reports/ALPACA_STRICT_REPAIR_VERIFY_DROPLET.json`.
