# Telemetry Standard — Memory Bank

**Authority:** This document is the canonical contract for telemetry truth roots, required fields, and governance. All writers, readers, and audits MUST align to it. Schema enforcement lives in `src/contracts/telemetry_schemas.py`.

**Version:** 1.0.0  
**Last updated:** 2026-03-03

---

## Droplet Data Authority (Non-Negotiable)

**NO DATA REVIEW WITHOUT DROPLET EXECUTION.**

The **droplet** is the **SINGLE source of truth** for:

- trade data  
- telemetry  
- attribution  
- backtests  
- replays  
- governance decisions  

**Local analysis is invalid for conclusions.**

- Any analysis, replay, or backtest run **locally** is **INVALID** for conclusions.  
- Local runs are **ALLOWED only** for schema validation or dry-run debugging (and must be explicitly labeled non-authoritative).  
- Any report, board review, or recommendation **MUST**:  
  - reference a **droplet run**  
  - include **deployed_commit** and **run_ts**  
- If droplet execution did **not** occur, the task is **FAILED**, not "pending".

---

## 1. Canonical truth roots (exact paths)

All paths are relative to repo root unless noted. Override via `config.registry` (LogFiles, Directories) or env (e.g. `EXIT_ATTRIBUTION_LOG_PATH`, `MASTER_TRADE_LOG_PATH`).

| Root | Path | Purpose |
|------|------|---------|
| Trade lifecycle | `logs/master_trade_log.jsonl` | One record per trade at full close; append once per trade_id. |
| | `logs/attribution.jsonl` | Entry-side attribution (open_* and closed records). |
| | `logs/exit_attribution.jsonl` | Exit-side attribution; MUST include `direction_intel_embed` (dict). |
| | `logs/exit_event.jsonl` | Unified replay record; MUST include `direction_intel_embed` when present. |
| Direction / intel | `logs/intel_snapshot_entry.jsonl` | One row per entry capture. |
| | `logs/intel_snapshot_exit.jsonl` | One row per exit capture. |
| | `logs/direction_event.jsonl` | Direction events (entry/exit). |
| Join state | `state/position_intel_snapshots.json` | Temporary join state (key: symbol:entry_ts[:19]); prune by age (e.g. 30d) and closed trades. |

---

## 2. Canonical required fields

### 2.1 Attribution (`logs/attribution.jsonl`)

- **Required:** `type` = "attribution", `ts` or `timestamp`
- **Canonical (prefer top-level):** `direction`, `side`, `position_side`, `regime_at_entry` (if available)

### 2.2 Exit attribution (`logs/exit_attribution.jsonl`)

- **Required:** `symbol`, `timestamp`, `entry_timestamp`, `exit_reason`
- **Canonical (required for replay/readiness):** `trade_id` (or join key), `symbol`, `entry_ts` (or entry_timestamp), `exit_ts` (or timestamp), `entry_price`, `exit_price`, `realized_pnl` (or pnl), `direction`, `side`, `position_side`, `regime_at_entry` (if available)
- **Required at exit:** `direction_intel_embed` MUST be present as a dict (may be empty `{}`). Once capture is live, readiness/audits require `direction_intel_embed.intel_snapshot_entry` to be a **non-empty** dict for telemetry-backed counting.

### 2.3 Exit event (`logs/exit_event.jsonl`)

- **Required:** `trade_id`, `symbol`, `entry_ts`, `exit_ts`, `exit_reason_code`
- **Required when present:** `direction_intel_embed` must be a dict; same non-empty contract for readiness as exit_attribution.

### 2.4 Master trade log (`logs/master_trade_log.jsonl`)

- **Required:** `trade_id`, `symbol`, `entry_ts`, `exit_ts`, `source`

---

## 3. Non-empty contract rules

- **direction_intel_embed** may exist as an empty dict `{}` (e.g. when entry capture failed or no snapshot). Schema validators accept empty dict.
- **Readiness and audits:** For "telemetry-backed" counting (e.g. direction_readiness X/100), a record counts ONLY when `direction_intel_embed.intel_snapshot_entry` is a **non-empty** dict. Field-exists-but-empty MUST NOT count toward readiness.
- **Dashboard / reports:** MUST distinguish "has key" vs "has non-empty intel_snapshot_entry" for coverage metrics.

---

## 4. Versioning and backward compatibility

- **Additive fields preferred.** New fields MUST be added without removing existing ones.
- **Deprecations:** Require (1) entry in `memory_bank/TELEMETRY_CHANGELOG.md`, (2) dual-read period during which both old and new fields are written/read, (3) update of all readers before removing old field.
- **Schema authority:** `src/contracts/telemetry_schemas.py` is the single source of truth for validators. Any new log type or required field MUST be added there and reflected in this standard.

---

## 5. References

- **IO map:** `scripts/audit/build_telemetry_io_map.py` → `reports/audit/TELEMETRY_IO_MAP.md`
- **Contract audit:** `scripts/audit/telemetry_contract_audit.py` → `reports/audit/TELEMETRY_CONTRACT_AUDIT.md`
- **Integrity gate:** `scripts/audit/telemetry_integrity_gate.py` (CI/local)
- **Adding telemetry:** `memory_bank/TELEMETRY_ADDING_CHECKLIST.md`
