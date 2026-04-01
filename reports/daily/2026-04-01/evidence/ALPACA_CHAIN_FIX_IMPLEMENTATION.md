# Chain fix implementation (summary)

## Commits

1. **`1d80fd43`** — Strict runlog telemetry override, startup banner, historical backfill, smoke script.  
   - Files: `main.py`, `scripts/audit/strict_chain_historical_backfill.py`, `scripts/audit/chain_emit_config_smoke.py`, plus pre-existing evidence files on `main` from prior work.

2. **Follow-up on `main`** — `main.py`: skip non-dict `info` in `evaluate_exits` loop to avoid corrupt `self.opens` entries breaking exit evaluation (defensive; no strategy / threshold change). Chain mission evidence under `reports/daily/2026-04-01/evidence/` (same commit as this bundle).

## Why minimal

- **Forward behavior:** Does not change entry/exit thresholds; only ensures strict runlog events append when configured and documents effective flags at startup.
- **Historical behavior:** Backfill is **additive** JSONL under `logs/strict_backfill_*`; strict gate already merges these streams (`_stream_jsonl_primary_then_backfill`).
- **No strict bypass:** `evaluate_completeness` semantics unchanged.

## Smoke scripts

- `scripts/audit/chain_emit_config_smoke.py` — prints effective env-driven flags.
- `scripts/audit/strict_chain_historical_backfill.py` — idempotent repair from `exit_attribution.jsonl`.

## Droplet evidence

- Backfill: `chain_fix_mission/backfill_stdout.txt` → `backfill_count 341 applied`.
