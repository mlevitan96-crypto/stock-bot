# Dashboard Telemetry Health — Proof

**Purpose:** Confirm dashboard Telemetry Health panel and /api/telemetry_health reflect canonical log status and direction coverage after deploy and trades.

---

## Verification steps (post-deploy, after verification PASS)

1. Open the dashboard (e.g. http://localhost:5000 or your droplet URL). Log in if required.
2. Open **More → Telemetry Health**.
3. Confirm:
   - **Canonical logs:** Each of master_trade_log, attribution, exit_attribution, exit_event, intel_snapshot_entry, intel_snapshot_exit, direction_event shows **Exists: Yes** with a recent **last_write** (after deploy_ts).
   - **Coverage:** Direction telemetry-backed shows **X/100** with **X > 0**.
   - **Direction ready:** Yes when telemetry_trades >= 100 and pct_telemetry >= 90%.
   - **Contract audit (last run):** PASS (or run `make telemetry_gate_legacy` / `make telemetry_gate` to refresh).
4. **Direction banner** (top of dashboard): Shows "Directional intelligence accumulating" with **Telemetry-backed trades: X/100** (not 0/100 once capture is live).

---

## Sample /api/telemetry_health payload (after PASS)

Run locally or on droplet (with dashboard running):

```bash
curl -s http://localhost:5000/api/telemetry_health
```

Expected shape (example; fill after deploy):

```json
{
  "log_status": [
    {"log": "master_trade_log", "exists": true, "last_write": "2026-03-03T..."},
    {"log": "attribution", "exists": true, "last_write": "..."},
    {"log": "exit_attribution", "exists": true, "last_write": "..."},
    {"log": "exit_event", "exists": true, "last_write": "..."},
    {"log": "intel_snapshot_entry", "exists": true, "last_write": "..."},
    {"log": "intel_snapshot_exit", "exists": true, "last_write": "..."},
    {"log": "direction_event", "exists": true, "last_write": "..."}
  ],
  "direction_telemetry_trades": 5,
  "direction_total_trades": 5,
  "direction_ready": false,
  "direction_coverage": "5/100",
  "gate_status": "PASS"
}
```

---

## Status

**Current:** Verification has not yet passed (see DATA_INTEGRITY_BLOCKERS.md). Dashboard Telemetry Health will show X/100 > 0 and canonical logs existing only after deploy + real trades and re-run of verification.

**After blockers resolved:** Capture the JSON from `/api/telemetry_health` and paste or attach to this file (or add "Captured at <ts>: ..." with redacted payload).

---

*Ref: memory_bank/TELEMETRY_STANDARD.md, reports/audit/DATA_INTEGRITY_DROPLET_VERIFICATION.md.*
