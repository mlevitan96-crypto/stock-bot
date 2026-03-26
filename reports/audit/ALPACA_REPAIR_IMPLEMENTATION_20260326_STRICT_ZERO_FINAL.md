# Alpaca strict repair — additive implementation summary

**Timestamp:** `20260326_STRICT_ZERO_FINAL`

## Principles

- **Additive only:** No mutation of primary logs (`run.jsonl`, `orders.jsonl`, `alpaca_unified_events.jsonl`, `exit_attribution.jsonl`, etc.).
- **Deterministic sidecars:** Append-only JSONL under `logs/strict_backfill_run.jsonl`, `logs/strict_backfill_orders.jsonl`, `logs/strict_backfill_alpaca_unified_events.jsonl`.
- **Gate merge:** `telemetry/alpaca_strict_completeness_gate.py` merges primary + `strict_backfill_*` for evaluation.

## Scripts

| Component | Path |
|-----------|------|
| Iterative repair (era incomplete → rounds) | `scripts/audit/alpaca_strict_six_trade_additive_repair.py` |
| Target six + `--repair-all-incomplete-in-era --open-ts-epoch <epoch>` | same |
| Read-only forensics | `scripts/audit/alpaca_strict_repair_forensics.py` |
| Strict gate | `telemetry/alpaca_strict_completeness_gate.py` |
| Parity + trace sample | `scripts/audit/alpaca_strict_cohort_cert_bundle.py` |
| Droplet repair + gate capture | `scripts/audit/run_alpaca_strict_repair_verify_droplet.py` |
| Learning cert (git sync, replay era, repair, gate, cert) | `scripts/audit/run_alpaca_droplet_learning_cert_final.py` |

## Repairs emitted per eligible trade

When both `exit_attribution` and a **terminal** unified `alpaca_exit_attribution` exist for `trade_id`, the repair emits:

1. **Entered / unified entry backfill:** `trade_intent` (`decision_outcome=entered`) and `alpaca_entry_attribution` with `canonical_trade_id`, `trade_key` aligned to the unified exit row, `strict_backfilled: true`, `strict_backfill_trade_id`, timestamp at entry (ISO from open id).
2. **Canonical order linkage:** Synthetic `orders` row in the sidecar with `id=strict_backfill_order:<trade_id>`, `canonical_trade_id` set to the **trade_key** from the unified exit (so the orders leg joins the same key family the gate seeds from the exit).
3. **Exit intent:** `exit_intent` with `timestamp` strictly **before** econ/terminal close (entry + 30s clamped below exit − 2s when exit time known), `strict_backfilled: true`.

Trades **without** both econ exit + unified terminal cannot be repaired by this script (fail closed for that class).

## Fail-closed guard (runtime observability)

- `src/telemetry/strict_chain_guard.py` + hooks from `src/exit/exit_attribution.py`: optional env `ALPACA_STRICT_CHAIN_GUARD` enables append-only `logs/alpaca_strict_chain_guard.jsonl` for **detection** of closes without entered + exit_intent. **Does not block** production closes (fail-open by design) so trading is not halted; operations use the log for prevention workflows.

## Droplet repair batch (verify run)

From `reports/ALPACA_STRICT_REPAIR_VERIFY_DROPLET.json`: iterative repair completed in **4** rounds with **54** run lines, **27** orders lines, **27** unified sidecar lines (covers all incompletes in that strict window, not only the six-symbol target list).
