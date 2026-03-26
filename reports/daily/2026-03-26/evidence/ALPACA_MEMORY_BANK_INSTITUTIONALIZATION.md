# ALPACA MEMORY BANK INSTITUTIONALIZATION (Phase 6)

**Mission:** ALPACA MEMORY BANK DISCOVERY, RECONCILIATION, AND INSTITUTIONALIZATION  
**Phase:** 6 — Enforce MEMORY_BANK.md as law for Alpaca going forward.  
**Authority:** Cursor executor; CSA/SRE veto.

---

## 1. Sole source of truth

- **MEMORY_BANK.md** is the canonical governing contract for the stock-bot system, including all Alpaca operations.
- Every Alpaca-related action (reports, board reviews, data readiness, experiments, Telegram, E2E audit) MUST reference MEMORY_BANK.md and comply with its sections (Golden Workflow §0.1, Data Source §3.2, Truth Gate §3.4, EOD §5.5, Deployment §6, Exit Intelligence §7.12, Alpaca governance subsections under §5).

---

## 2. Truth Gate Declaration

- Every Alpaca action that produces a conclusion or report MUST satisfy a **Truth Gate Declaration**:
  - Data used came from droplet execution and canonical paths (or explicitly labeled non-authoritative for local-only validation).
  - Required data (e.g. exit_attribution, master_trade_log) was present; if missing, the task is FAILED, not "pending".
  - Join coverage and readiness thresholds, when asserted, were met or the failure was explicit (HARD FAILURE).

---

## 3. Failure modes (HARD FAILURE)

- **Missing data** = HARD FAILURE. Do not proceed to conclusions; do not report success.
- **Join coverage below threshold** (e.g. direction_readiness, exit-join health) when asserted as readiness = HARD FAILURE.
- **Schema mismatch or unversioned required fields** = HARD FAILURE.
- **Only frozen artifacts** (EOD bundle, frozen trade sets, e.g. alpaca_edge_2000 TRADES_FROZEN) may be used for learning or tuning; ad-hoc unfrozen data MUST NOT be used for promotion or tuning decisions.

---

## 4. Operational procedures

- **Droplet first:** All production data and reports come from droplet runs; local analysis is invalid for conclusions unless explicitly labeled non-authoritative.
- **Paths:** Use config.registry.LogFiles and paths in MEMORY_BANK §5.5; override only via env for regression/isolation.
- **Retention:** Never truncate or rotate retention-protected paths (MEMORY_BANK §5.5, docs/DATA_RETENTION_POLICY.md, deploy_supervisor.RETENTION_PROTECTED).
- **CSA/SRE:** Governance outputs are review-only; MEMORY_BANK updates require CSA and SRE approval; veto blocks update and must be documented.

---

## 5. References

- MEMORY_BANK.md §0, §3.4, §5.5, §6, §7.12, Alpaca subsections.
- reports/audit/ALPACA_MEMORY_BANK_LOADED.md, ALPACA_MEMORY_BANK_UPDATED.md.
- reports/audit/CSA_REVIEW_ALPACA_MEMORY_BANK_UPDATE.md, SRE_REVIEW_ALPACA_MEMORY_BANK_UPDATE.md.

---

*Alpaca is now governed by MEMORY_BANK.md under this institutionalization. Cursor and operators MUST follow the Truth Gate and HARD FAILURE rules.*
