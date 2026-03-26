# CSA Review — Alpaca Trade Notifications

---

## Threshold alignment

| Threshold | Diagnostic intent | Alignment |
|-----------|-------------------|-----------|
| **100 trades** | Confirm promotion + telemetry operational | **Aligned** — early validation that exit attribution is writing and diagnostic is active |
| **500 trades** | Diagnostic review window complete | **Aligned** — sufficient N for Quant + CSA evaluation per `ALPACA_DIAGNOSTIC_PROMOTION_EVAL_CRITERIA.md` (48–72h window typically yields 200–400 trades; 500 is conservative) |

---

## Message governance

| Message | Governance grade | Notes |
|---------|------------------|-------|
| 100-trade | **Yes** — clear, factual, no claims | States operational confirmation only |
| 500-trade | **Yes** — signals readiness for review | Does not claim success; signals evaluation window |

---

## Spam / duplication risk

| Risk | Mitigation | Status |
|------|------------|--------|
| **Duplicate messages** | `notified_*` flags in state file | **Mitigated** |
| **Repeated runs** | Idempotent counting + flag checks | **Mitigated** |
| **Cron overlap** | 10-minute interval; script completes in <10s | **Low risk** |

---

## CSA approval

| Field | Value |
|-------|--------|
| **ALPACA_TRADE_NOTIFICATION_APPROVED** | **YES** |
| **Rationale** | Thresholds align with diagnostic intent; messages are governance-grade; duplication risk mitigated via state flags |

---

## Conditions

- **Telegram credentials** must be set in Alpaca venv (per SRE scheduling doc).
- **State file** must persist across restarts (atomic writes confirmed).
- **Dry run** must pass before production cron install.

---

*CSA — trade notifications approved for production after dry run verification.*
