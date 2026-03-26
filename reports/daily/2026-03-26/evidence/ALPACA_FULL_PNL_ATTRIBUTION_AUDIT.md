# Alpaca Full PnL + Attribution Audit (Scoped)

**DATA_READY_FOR_AUDIT:** YES (scoped — see `CSA_REVIEW_ALPACA_DATA_READINESS.md`)  
**SAFE MODE:** Active — **no live/paper parameter changes** from this document.  
**Droplet commit:** `28abc2a33e365caa58736b99a175ae360f9d1447` · **UTC:** 2026-03-20T00:08Z  
**Primary ledger:** `logs/exit_attribution.jsonl` (2,209 lines; **2,204** unique canonical keys)

---

## 1. Signal contribution (exit-side)

From exit reason and v2 exit machinery (counts on full set):

| Signal / driver | Proxy (exit_reason_code) | Count | Share |
|-----------------|---------------------------|-------|-------|
| Default / hold pressure | `hold` | 2,068 | ~93.8% |
| Intel deterioration | `intel_deterioration` | 135 | ~6.1% |
| Other | `other` / `unknown` | 2 | ~0.1% |

**Attribution components** (`attribution_components`, `v2_exit_components`) are present on records per sample keys — detailed per-component ranking requires a dedicated effectiveness script run on the droplet (e.g. `scripts/analysis/run_effectiveness_reports.py`) **not executed** in this gate run to preserve SAFE MODE scope.

---

## 2. Entry vs exit loss attribution (summary)

| Bucket | Count |
|--------|-------|
| Wins | 892 |
| Losses | 1,283 |
| Breakeven / unknown | 29 |

**Win rate (trade-level):** ~40.4% (892 / 2,204). **Loss-heavy** regime on this window — consistent with **Quant** review of sufficiency (large-N; not edge discovery).

---

## 3. Regime slicing

**Per-symbol coverage:** Top symbols carry **43–68** trades each (see sufficiency report) — enough for coarse per-symbol buckets. **Explicit regime labels** (`entry_regime`, `exit_regime`, `regime_label`) are present on exit records; full regime×PnL matrix is a **follow-on SQL/CSV extract**, not recomputed here.

---

## 4. “Would-have” exit analysis

**Status:** **Not executed** in this audit pass. Requires frozen bar set + replay harness (see `scripts/alpaca_edge_2000_pipeline.py` pattern). **Recommendation:** run `scripts/run_alpaca_edge_2000_on_droplet.py` or replay tooling when SAFE MODE allows batch jobs.

---

## 5. Indicator / rule ranking

**Status:** **Deferred.** SAFE MODE prohibits selecting and promoting a live rule. **No** “best indicator” computed from fresh droplet sweeps in this run.

**Historical reference:** Prior board packets under `reports/alpaca_edge_2000_*` / `ALPACA_EDGE_PROMOTION_SHORTLIST_*.md` may be cited for **hypothesis only**, not as live promotion.

---

## 6. Session coverage (“including TODAY”)

Latest exit **calendar day** in sample: **2026-03-19** (US session dates in `trades_per_day`). Audit timestamp **2026-03-20** UTC — confirm **2026-03-19** US close is included in exit file; for **2026-03-20** session, re-run scan after close if required.

---

*Read-only audit summary from droplet scans — no config or strategy mutation.*
