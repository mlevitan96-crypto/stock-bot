# Alpaca Phase 4 — Promotion Gate — Implementation Plan

**Status:** Plan only. No code until CSA + SRE approve.  
**Scope:** Compute promotion gate status from convergence state, Tier 1/2/3 packets, shadow comparison, and SRE. Output state only; **no auto-promotion**; human approval required for any promotion.  
**Context:** Alpaca design §8 (Promotion gate); Phase 3 convergence state. Alpaca-only scope.

---

## 1. Gate Conditions (design)

Gate status is **advisory**. A "gate_ready" or "blocked" outcome does not execute promotion; it informs human review.

- **Tier3 OK:** Tier 3 packet (or last387 review) present; Tier 3 summary has total_pnl_attribution_usd (or equivalent). No sign requirement for "OK" — presence and readability only.
- **Tier2 OK:** Tier 2 packet (or 7d/30d/last100 review) present; at least one scope has total_pnl_attribution_usd.
- **Convergence:** No **severe** divergence. Read `state/alpaca_convergence_state.json`; if `divergence_class` is "severe" → gate blocked for promotion path until human review.
- **Shadow comparison:** `reports/board/SHADOW_COMPARISON_LAST387.json` (or equivalent) exists and has `nomination` (Advance/Hold/Discard). Missing or empty → gate blocks promotion path (design: "Produce shadow comparison before any promotion").
- **SRE:** No anomaly. Read `reports/audit/SRE_STATUS.json`; if anomaly (same definition as Phase 3) → gate blocked for promotion path.

**Gate ready (promotion path):** Tier3 OK + Tier2 OK + convergence not severe + shadow comparison present with nomination + SRE no anomaly. **Human must still approve;** script only writes state.

**Blocked:** Any of: severe divergence, missing shadow comparison, SRE anomaly, or missing Tier2/Tier3 data. State records reason(s).

---

## 2. Required Artifacts (inputs)

| Artifact | Path | Used for |
|----------|------|----------|
| Convergence state | state/alpaca_convergence_state.json | divergence_class, convergence_status |
| Tier 3 packet or review | state/alpaca_board_review_state.json → last_packet_dir / BOARD_REVIEW.json; or reports/board/last387_comprehensive_review.json | Tier3 OK |
| Tier 2 packet or review | state → tier2_last_packet_dir / TIER2_REVIEW.json; or reports/board/7d\|30d\|last100 | Tier2 OK |
| Shadow comparison | reports/board/SHADOW_COMPARISON_LAST387.json | nomination present |
| SRE status | reports/audit/SRE_STATUS.json | anomaly flag |

All read-only. No writes to logs, trading, or enforcement scripts.

---

## 3. Output File

**Path:** `state/alpaca_promotion_gate_state.json`

**Schema (design):**
- `last_run_ts`: ISO8601
- `gate_ready`: bool — true only when all conditions above pass (advisory; human approval still required)
- `blockers`: list of str — e.g. ["severe_divergence"], ["missing_shadow_comparison"], ["sre_anomaly"], ["tier2_missing"], ["tier3_missing"]
- `convergence_divergence_class`: str (from convergence state)
- `shadow_nomination`: str | null (Advance/Hold/Discard or null if missing)
- `sre_anomaly`: bool
- `tier2_ok`: bool
- `tier3_ok`: bool
- `one_liner`: str (human-readable summary)

Overwrite each run. No other files created.

---

## 4. Script

**Path:** `scripts/run_alpaca_promotion_gate.py`

**Behavior:**
- Args: `--base-dir`, `--force`, `--dry-run`.
- Load convergence state; load Tier 2/3 from state packet dirs or board fallbacks; load shadow comparison; load SRE status.
- Compute tier2_ok, tier3_ok, convergence not severe, shadow present with nomination, SRE no anomaly.
- Set gate_ready = (all true). Populate blockers list when not gate_ready.
- Write state/alpaca_promotion_gate_state.json. On write failure exit 1.
- **No auto-promotion.** No changes to enforce_csa_gate.py or any execution path. Human approval required for any promotion.

**Idempotency:** Each run overwrites gate state. Safe to run multiple times.

---

## 5. Testing Plan

1. **Dry-run:** `--dry-run` → exit 0; print gate_ready and blockers; no file write.
2. **Full run:** Run script → state/alpaca_promotion_gate_state.json updated; exit 0.
3. **CSA review:** Review gate state and script; ACCEPT or REVISE.
4. **SRE review:** Validate read-only inputs and single state write; OK or FIX REQUIRED.

---

## 6. Architecture Fit (for CSA/SRE)

- Consumes Phase 3 convergence state and existing Tier 2/3 packets and board artifacts. No new cron; no change to Tier 1/2/3 or convergence scripts. Single new script and single new state file.
- Alpaca-only. Advisory only; no execution impact. Design §8: "No automatic promotion. Gate is human-in-the-loop."

---

STOP for CSA + SRE review.
