# ALPACA MEMORY BANK — UPDATED (Phase 5)

**Mission:** ALPACA MEMORY BANK DISCOVERY, RECONCILIATION, AND INSTITUTIONALIZATION  
**Phase:** 5 — Apply approved MEMORY_BANK.md updates (CSA and SRE both approved).  
**Authority:** Cursor executor. Governed update only.

---

## 1. Pre-update (frozen)

| Field | Value |
|-------|--------|
| **File path** | `MEMORY_BANK.md` (repo root) |
| **Last modified (UTC)** | 2026-03-17T17:31:42.1090863Z |
| **Content hash (SHA256)** | `91CA4408AF99F0E62F58D23E5FA7E7B80726F0E1A0BD0F7850F01EAC8608D795` |

---

## 2. Post-update

| Field | Value |
|-------|--------|
| **File path** | `MEMORY_BANK.md` (repo root) |
| **Last modified (UTC)** | 2026-03-17T18:26:28.0814500Z |
| **Content hash (SHA256)** | `29D568EF8B232805A2D5CAB2D34B0E7B0E4113B5FBE60AEF4BBC21B9A05C2A70` |

---

## 3. Summary of Alpaca-related changes

All six proposed diffs were applied (CSA and SRE approved):

1. **Header version** — Appended "; Alpaca governance current 2026-03-17" to version line.
2. **§5.5 Log path env overrides** — Documented EXIT_ATTRIBUTION_LOG_PATH and MASTER_TRADE_LOG_PATH for regression/isolation; default = canonical.
3. **§3.4 Truth Gate** — New subsection: droplet execution and canonical data as Truth Gate; HARD FAILURE for missing data, join coverage below threshold, schema mismatch; only frozen artifacts for learning/tuning.
4. **§6.3 Project dir** — Canonical project dir set to `/root/stock-bot` (or `/root/stock-bot-current` as alternate); removed promotion of `trading-bot-current` for stock-bot.
5. **§7.12 Schema version** — Added line: Schema version ATTRIBUTION_SCHEMA_VERSION in exit_attribution.py (e.g. 1.0.0).
6. **§5 Join key / trade_id** — Added: For Alpaca, trade_id is built via src/telemetry/alpaca_trade_key.build_trade_key(symbol, side, entry_ts).

---

## 4. Approval record

- **CSA:** reports/audit/CSA_REVIEW_ALPACA_MEMORY_BANK_UPDATE.md — APPROVE (no veto).
- **SRE:** reports/audit/SRE_REVIEW_ALPACA_MEMORY_BANK_UPDATE.md — OK (no veto).

---

## 5. Commit

This update SHOULD be committed as a governed Memory Bank update (e.g. message: "MEMORY_BANK: Alpaca Truth Gate and reconciliation diffs (CSA/SRE approved)").

---

*Phase 5 complete. MEMORY_BANK.md updated; Phase 6–8 follow.*
