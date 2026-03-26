# Alpaca Data Integrity Results (SRE)

**Droplet:** `/root/stock-bot` · **UTC:** 2026-03-20T00:08Z · **commit:** `28abc2a33e365caa58736b99a175ae360f9d1447`  
**Tooling:** `scripts/audit/alpaca_data_readiness_droplet_scan.py` (also: ad-hoc raw `trade_id` set comparison on droplet)

---

## 1. Raw event vs ingested counts

| Stream | Physical lines | Parsed exit rows | Unique canonical join keys (`live:SYM:entry_ts` @ 1s) |
|--------|----------------|------------------|--------------------------------------------------------|
| `logs/exit_attribution.jsonl` | 2,209 | 2,209 | 2,204 |

**Duplicate keys:** 5 duplicate lines / key collisions (2209 − 2204). **Silent drops:** none detected at ingest (all lines JSON-parseable in scan).

---

## 2. Missing critical fields (`exit_attribution.jsonl`)

| Issue | Count | Notes |
|-------|-------|--------|
| Missing `trade_id` | **2** | Same 2 rows as below |
| Missing `symbol` | **2** | |
| Missing `pnl` / `realized_pnl` | **2** | |
| Missing `entry_ts` / `entry_timestamp` | **2** | |
| Missing `exit_ts` / `timestamp` | **2** | |
| `direction_intel_embed` not a dict | **2** | |
| `intel_snapshot_entry` empty (readiness metric) | (see scan) | TELEMETRY_STANDARD: empty does not count as “telemetry-backed” |

**Example pattern:** 2 lines share the same defect bundle — treat as **repair candidates** or exclude from strict attribution counts until fixed.

---

## 3. Join coverage

### 3.1 Raw `trade_id` overlap (exit vs master closed)

| Set | Unique `trade_id` |
|-----|-------------------|
| `exit_attribution` | 2,205 (incl. empty string on bad rows) |
| `master_trade_log` where `exit_ts` set | **160** |
| **Intersection** | **0** |

**Cause:** `exit_attribution` uses **`open_SYMBOL_…`** (and blanks on bad rows); `master_trade_log` uses **`live:SYMBOL:…`**. No raw string join.

### 3.2 Normalized `live:SYMBOL:entry_ts` (second-precision UTC)

| Metric | Value |
|--------|-------|
| Unique keys in `exit_attribution` | 2,204 |
| Unique keys in `master_trade_log` (closed) | 160 |
| **Intersection** | **1** |
| Exit-only keys | 2,203 |
| Master-only keys | 159 |

**Conclusion:** **Cross-log reconciliation between `exit_attribution` and `master_trade_log` is not viable via automated key match at scale** on current data. This does **not** invalidate row-level PnL in `exit_attribution` (each row is self-contained for a close); it **does** block a naive “single trade_id ledger” story across both files.

### 3.3 `attribution.jsonl` closed vs `exit_attribution`

**~1,112** closed attribution keys (derived from `symbol` + `entry_ts`) **not** present in exit unique-key set — dual-write drift between streams. Use **`exit_attribution`** as the closed-trade authority per MEMORY_BANK for Alpaca PnL.

### 3.4 Orphan semantics (mission language)

| Check | Result |
|-------|--------|
| “Every exit has a matching entry” **within** `exit_attribution` | **PASS** except **2** bad rows (missing entry/exit timestamps) |
| “Every realized PnL maps to a closed trade” **in** `exit_attribution` | **PASS** (each line is a closed trade record); **2** rows lack PnL — **FAIL** subset |
| “Every exit matches a master row” | **FAIL** at scale (intersection 1) — **ID namespace + lineage**, not necessarily data loss in exit file |

---

## 4. Filters / suppression

| Filter | Effect |
|--------|--------|
| `master_trade_log` filter `exit_ts` present | Used only for “closed” subset — **not** applied to exit_attribution ingest |
| Bad JSON lines | **0** in scan (skipped on parse error) |
| Readiness “non-empty `intel_snapshot_entry`” | **Suppresses** counting rows for telemetry-backed readiness — **not** a drop from disk |

---

## 5. SRE verdict (integrity layer)

- **Row-level exit file:** **Mostly complete**; **2** rows **must** be fixed or quarantined for strict audits.  
- **Cross-log master ↔ exit:** **Not integrity-complete** for automated joins; document **exit_attribution-first** PnL audit path.  
- **Unified stream:** `alpaca_unified_events.jsonl` **233** lines vs **2,209** exit lines — **partial** coverage; do not rely on unified alone for full history.

---

*Evidence captured via DropletClient SSH; scanner uploaded to droplet: `scripts/audit/alpaca_data_readiness_droplet_scan.py`.*
