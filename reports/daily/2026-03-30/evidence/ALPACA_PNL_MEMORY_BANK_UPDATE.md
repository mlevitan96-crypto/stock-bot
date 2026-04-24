# ALPACA PNL MEMORY BANK UPDATE (evidence)

## Inserted governance (see MEMORY_BANK.md for full file)

- Canonical docs: `docs/pnl_audit/REQUIRED_FIELDS.md`, `LINEAGE_MATRIX.md`, `LINEAGE_MATRIX.json`, `FIELD_ADDITION_PLAYBOOK.md`, `ADVERSARIAL_FINDINGS.md`.
- **LINEAGE_MATRIX.json** is the machine contract; any telemetry change must update it.
- **Broker vs local** sources are explicit per matrix row (`source_of_truth`, `persistence_location`).
- Map check: `python3 scripts/audit/alpaca_pnl_lineage_map_check.py --write-evidence`
- Full evidence bundle: `python3 scripts/audit/alpaca_pnl_lineage_evidence_bundle.py`

## Prior MEMORY_BANK excerpt (first `## 1.` block, truncated)

```markdown
## 1.1 Alpaca strict learning era (CSA)

- **STRICT_EPOCH_START (UTC epoch seconds):** `1774458080` (`2026-03-25T17:01:20Z`). Canonical: `telemetry/alpaca_strict_completeness_gate.py` (`STRICT_EPOCH_START`).
- **Strict cohort (entry-based):** When `evaluate_completeness` is called with `open_ts_epoch` set, terminal closes are kept only if exit time `>= open_ts_epoch`. Among those, a trade is in the strict cohort only if the open instant parsed from `trade_id` (`open_<SYM>_<ISO8601>`) is also `>= open_ts_epoch`. Earlier opens are excluded (`PREERA_OPEN`) and do not count as `trades_seen` or incomplete.

## 1.2 Alpaca truth warehouse — DATA_READY baseline (do not drift)

**Purpose:** Before profitability narratives, board packets, or learning promotion, the repo defines a **single scripted path** that proves telemetry + broker data are **joinable** for PnL attribution (fees, slippage, signal snapshots, UW/blocked context). This section is the **contract**; detail and commands live in **`docs/DATA_READY_RUNBOOK.md`**.

### Canonical artifacts (code + docs)

| Item | Role |
|------|------|
| `scripts/alpaca_full_truth_warehouse_and_pnl_audit_mission.py` | **Only** authoritative runner 
```
