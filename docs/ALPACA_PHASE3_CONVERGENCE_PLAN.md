# Alpaca Phase 3 — Convergence Logic — Implementation Plan

**Status:** Plan only. No code until CSA + SRE approve.  
**Scope:** Convergence check across Tier 1, Tier 2, Tier 3. Advisory only; no auto-block, no promotion logic.  
**Context:** Alpaca design §6 (Convergence Model); existing Tier 1/2/3 scripts and state. Alpaca-only scope.

---

## 1. Convergence Definition (Tier1 vs Tier2 vs Tier3)

- **Tier1 5d sign:** From Tier 1 packet or state: 5d rolling PnL sign (positive / negative / zero). Source: `tier1_summary.rolling_5d_last_point.pnl` or Tier 1 JSON; or last line of `reports/state/rolling_pnl_5d.jsonl`.
- **Tier2 sign:** From Tier 2 packet or latest 7d/30d/last100 review: primary scope total PnL sign. Source: Tier 2 JSON `tier2_summary.7d` or `30d` or `last100` → `total_pnl_attribution_usd`; or read `reports/board/7d_comprehensive_review.json` (or 30d/last100) if packet not present.
- **Tier3 sign:** From Tier 3 packet or last387 review: total PnL sign. Source: Tier 3 JSON `tier3_summary.total_pnl_attribution_usd`; or `reports/board/last387_comprehensive_review.json`.
- **SRE status:** From `reports/audit/SRE_STATUS.json` → `overall_status`. Anomaly = not "HEALTHY" or "OK" (exact values TBD from existing SRE schema).
- **Shadow nomination:** From Tier 3 or `reports/board/SHADOW_COMPARISON_LAST387.json` → `nomination`. Informational only for convergence.

**Convergence:** Tier1_5d_sign, Tier2_sign, Tier3_sign consistent (same sign or at least one zero/missing); SRE no anomaly. Divergence = different signs (e.g. Tier1 5d negative, Tier3 positive) or SRE anomaly.

---

## 2. Divergence Classification

- **Mild:** Missing data (e.g. Tier 1 packet absent, or 5d state absent). One-line: "Missing Tier1/2/3 data; cannot assess convergence."
- **Moderate:** Tier1 5d sign ≠ Tier2 or Tier3 sign (e.g. 5d negative, last387 positive). One-line: "Short-term (5d) underperforming vs cohort (Tier2/Tier3)."
- **Severe:** Tier1 5d sign ≠ Tier2/Tier3 sign **and** SRE anomaly. One-line: "Divergence plus SRE anomaly; human review required."

No automatic blocking: classification is advisory. Output includes `convergence_status` (green / yellow / red) and `divergence_class` (none | mild | moderate | severe).

---

## 3. Required Surfaces

| Surface | Source | Used for |
|---------|--------|----------|
| PnL Tier1 5d | Tier 1 packet JSON or `reports/state/rolling_pnl_5d.jsonl` (last line) | Tier1_5d_sign |
| PnL Tier2 | Tier 2 packet JSON or reports/board/7d|30d|last100_comprehensive_review.json | Tier2_sign |
| PnL Tier3 | Tier 3 packet JSON or reports/board/last387_comprehensive_review.json | Tier3_sign |
| Attribution | Already embedded in Tier 1/2/3 packets (no separate read) | — |
| Shadow | Tier 3 packet or SHADOW_COMPARISON_LAST387.json | nomination (informational) |
| Blocked | In Tier 2/3 comprehensive review (no separate read) | — |
| SRE | reports/audit/SRE_STATUS.json | anomaly flag |

All paths under repo root (--base-dir). Read-only.

---

## 4. Output File

**Path:** `state/alpaca_convergence_state.json`

**Schema (design):**
- `last_run_ts`: ISO8601
- `tier1_5d_sign`: "positive" | "negative" | "zero" | "missing"
- `tier2_sign`: same
- `tier3_sign`: same
- `sre_anomaly`: bool
- `convergence_status`: "green" | "yellow" | "red"
- `divergence_class`: "none" | "mild" | "moderate" | "severe"
- `one_liner`: str (human-readable summary)
- `sources_used`: { "tier1_packet" | "rolling_5d", "tier2_packet" | "board_7d|30d|last100", "tier3_packet" | "board_last387", "sre_status" }

Overwrite on each run (no append). No other files created.

---

## 5. Script

**Path:** `scripts/run_alpaca_convergence_check.py`

**Behavior:**
- Args: `--base-dir`, `--force`, `--dry-run`.
- Resolve base; read state/alpaca_board_review_state.json for last packet dirs (tier1, tier2, last_packet_dir for Tier3). Load latest Tier 1/2/3 packet JSON from those dirs if present; else fallback to rolling_5d.jsonl, board 7d/30d/last100, board last387.
- Compute Tier1_5d_sign, Tier2_sign, Tier3_sign (from PnL values).
- Read SRE_STATUS.json; set sre_anomaly = (overall_status not in ("HEALTHY", "OK") or anomalies_detected true if present).
- Classify divergence (mild/moderate/severe) and convergence_status (green/yellow/red).
- Write state/alpaca_convergence_state.json. On write failure exit 1.
- No promotion logic, no cron, no Telegram in this phase.

**Idempotency:** Each run overwrites convergence state. Safe to run multiple times.

---

## 6. Testing Plan

1. **Dry-run:** `python scripts/run_alpaca_convergence_check.py --force --dry-run` → exit 0; print one_liner and convergence_status; no file write.
2. **Full run:** `python scripts/run_alpaca_convergence_check.py --force` → state/alpaca_convergence_state.json updated; exit 0.
3. **CSA review:** Review convergence state and script behavior; ACCEPT or REVISE.
4. **SRE review:** Validate paths, no writes to trading/logs; OK or FIX REQUIRED.

---

## 7. Architecture Fit (for CSA/SRE)

- **Fits current architecture:** Uses existing Tier 1/2/3 packet dirs from state; uses existing board review and SRE artifacts. No new cron; no change to Tier 1/2/3 scripts. Single new script and single new state file.
- **Venue:** All paths and logic Alpaca US equities only.
- **Advisory only:** Convergence status does not gate promotion or trading; design §6: "No auto-block; CSA may lower confidence or add finding."

---

STOP for CSA + SRE review.
