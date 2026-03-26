# Alpaca Telemetry Repair — Executive Summary (Phase 7)

## What was broken

1. **Entry attribution never emitted** on the live path: `main.py` required `entry_status == "FILLED"` but the executor returns **`"filled"`** — condition always false.  
2. **Unified stream empty** — `emit_entry_attribution` appends to `alpaca_unified_events.jsonl`; it never ran.  
3. **`alpaca_entry_attribution.jsonl` missing** — same cause.  
4. **Trade ID alignment** — even a naive case-fix would have used wrong timestamps vs `position_metadata.json`; repair emits **after** `mark_open` using persisted `entry_ts`.

## Why it broke

Case mismatch (`FILLED` vs `filled`) + emit placed before canonical `entry_ts` existed in metadata.

## What was fixed (code)

- Case-insensitive filled check for XAI block.  
- **`emit_entry_attribution`** immediately **after** `mark_open`, using metadata **`entry_ts`** for `trade_id` / `trade_key`.  
- Failure → **`telemetry` / `emit_entry_attribution_failed`** log (warning only).  
- Scripts: **epoch writer**, **forward proof**, **droplet inventory**.

## What is provably true **today**

- **Exit** telemetry on droplet is real and append-only.  
- **Entry/unified** files are still **absent** on droplet until **deploy + new fills** after repair.

## What analysis is allowed

| Cohort | Allowed |
|--------|---------|
| Pre-repair history | Exit-only / aggregate metrics; **not** entry-causality at promotion grade |
| Post-repair, pre-proof | **Forbidden** for causal entry claims |
| Post-repair, after forward proof **PASS** | **DATA_READY** for forward window only |

## Next actions (operator)

1. Deploy; restart bot.  
2. `python3 scripts/write_alpaca_telemetry_repair_epoch.py`  
3. Wait ≥50 exits; run `python3 scripts/alpaca_telemetry_forward_proof.py`  
4. Refresh **CSA_SRE_ALPACA_TELEMETRY_CERTIFICATION.md** when PASS.
