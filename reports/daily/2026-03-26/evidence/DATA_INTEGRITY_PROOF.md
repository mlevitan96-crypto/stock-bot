# Data Integrity Proof

## Scope

Telemetry and data-integrity wiring only. No change to trading decisions.

---

## Before / After (local)

| Check | Before | After |
|-------|--------|--------|
| Entry capture `entry_ts` | Used `datetime.utcnow()` after mark_open (mismatch with metadata) | Uses same `entry_ts` as metadata (from `mark_open` with `now.isoformat()`) |
| Entry capture location | After `mark_open` in fill path only | Inside `mark_open` on every open |
| `direction_intel_embed` on exit | Set only when truthy | Always set (dict or `{}`) on exit_attribution and exit_event |
| Canonical fields on exit_attribution | Not present | `direction`, `side`, `position_side` added |
| master_trade_log duplicate append | Possible (entry + exit paths) | In-process guard: one append per `trade_id` per process |
| position_intel_snapshots | No pruning | Pruned on exit (entries > 30d removed) |

---

## Tests

- `validation/scenarios/test_telemetry_contracts.py`:
  - `test_validate_master_trade_log`: required fields and types
  - `test_validate_exit_attribution_direction_intel_embed`: embed must be dict; intel_snapshot_entry dict when present
  - `test_master_trade_log_single_append_guard_exists`: guard set exists
- All 3 passed.

---

## Offline audits (must pass)

| Script | Status |
|--------|--------|
| `scripts/ensure_telemetry_paths.py` | Pass (all telemetry paths present) |
| `scripts/audit/telemetry_contract_audit.py` | Pass (no blocking schema failures) |
| `scripts/verify_full_exit_telemetry.py` | Run on droplet / after live run |
| `scripts/verify_replay_readiness.py` | Run on droplet / after live run |
| `scripts/audit_direction_intel_wiring.py` | Run on droplet after 5+ trades |

---

## Sample records (redacted)

After deployment and at least one open + close:

**exit_attribution** (required shape):

```json
{
  "symbol": "T",
  "timestamp": "...",
  "entry_timestamp": "...",
  "exit_reason": "profit",
  "direction_intel_embed": { "intel_snapshot_entry": { ... }, "intel_snapshot_exit": { ... }, "intel_deltas": { ... } },
  "direction": "bullish",
  "side": "buy",
  "position_side": "long"
}
```

**direction_readiness** (state/direction_readiness.json):

- `telemetry_trades`: count of exit_attribution records with non-empty `direction_intel_embed.intel_snapshot_entry`
- `total_trades`: total exit_attribution records
- `ready`: true when telemetry_trades >= 100 and pct_telemetry >= 90

---

## Droplet verification (required for merge)

1. Deploy to droplet.
2. Run a short live window or synthetic lab to generate at least 5 trades (open + close).
3. Confirm:
   - `logs/intel_snapshot_entry.jsonl` exists and has records.
   - `logs/exit_attribution.jsonl` last records contain `direction_intel_embed` with non-empty `intel_snapshot_entry` where entry capture ran.
   - `state/direction_readiness.json`: `telemetry_trades` > 0 after run.
   - Dashboard banner shows progress (e.g. X/100) not 0/100 when trades exist.

---

*Generated as part of data-integrity orchestration. See reports/audit/DATA_INTEGRITY_PLAN.md and docs/DATA_CONTRACT_CHANGELOG.md.*
