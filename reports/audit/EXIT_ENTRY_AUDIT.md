# Phase 3 — Exit/Entry Logic and Attribution Audit (incl. v2 Exit Fix)

**Audit date:** 2026-02-27  
**Scope:** v2 exit fix in code and logs, entry MIN_EXEC_SCORE, effectiveness reports, exit vs entry blame.

---

## 1. v2 Exit Fix — Code Verification

### 1.1 `src/exit/exit_score_v2.compute_exit_score_v2` return value

**Contract (docstring):** Returns `(exit_score [0..1], components, recommended_reason, attribution_components, reason_code)` — **5 values**.

**Code (exit_score_v2.py):**
- Line 44: signature returns `Tuple[float, Dict[str, Any], str, list, str]`.
- Line 137: `return float(score), components, reason, attribution_components, reason_code`.

**Verdict:** **VERIFIED** — 5-value return implemented.

### 1.2 main.py unpack and usage

**Location:** main.py ~6431–6514 (v2 exit block).

- Line 6455: `v2_exit_score, v2_exit_components, v2_exit_reason, v2_exit_attribution_components, v2_exit_reason_code = compute_exit_score_v2(...)`  
**Verdict:** **VERIFIED** — Correct 5-value unpack; no 4-value bug.

- Lines 6495–6501: `exit_intel_by_symbol[symbol]` is populated with:
  - `v2_exit_score`, `v2_exit_components`, `v2_exit_reason`, `v2_exit_attribution_components`, `v2_exit_reason_code`.
- Later (e.g. 6570–6579): exit_reasons[symbol] uses `v2_exit_reason`; log_event "v2_exit_triggered" includes v2_exit_score, v2_exit_reason.
- Exit attribution write (e.g. 2197–2277, 2249–2277): `exit_reason_code=v2_exit_reason_code`, `v2_exit_components`, `v2_exit_score`, `attribution_components`.

**Verdict:** v2 exit bug (4 vs 5 value) is **fully resolved in code**. All downstream consumers use the 5-value unpack and write reason_code and components.

---

## 2. Exit reason codes (v2)

**From exit_score_v2.py:** reason_code is one of: `hold`, `intel_deterioration`, `stop`, `replacement`, `profit` (plus thesis/earnings/vol conditions). Multi-factor (flow_deterioration, score_deterioration, regime_shift, sector_shift, vol_expansion, thesis_invalidated, etc.) feed the score; the recommended reason is derived from thresholds.

**Adversarial check:** If in production all exits show `signal_decay` only, that would indicate an alternate path (e.g. time/signal_decay exit) dominating and v2 not being the primary. Code shows v2 is used when v2_exit_score >= 0.80 (line 6570) and exit_reasons use build_composite_close_reason(exit_signals) which can include "v2_exit(reason)". So both v2 and legacy (signal_decay, trail_stop, etc.) can appear; healthy state = mix of exit_reason_codes including intel_deterioration, replacement, profit, stop, not only signal_decay.

---

## 3. `report_last_5_trades.py`

**Script:** Reads `logs/attribution.jsonl` and `logs/exit_attribution.jsonl`, joins via `load_joined_closed_trades`, prints last N with:
- Entry: entry_score, entry_attribution_components, entry_regime.
- Exit: v2_exit_score, v2_exit_components, exit_reason_code, attribution_components, exit_quality_metrics.

**Local:** No `logs/attribution.jsonl` or `logs/exit_attribution.jsonl` in repo (expected; logs live on droplet).

**DROPLET_REQUIRED:**
```bash
cd /root/stock-bot && python3 scripts/report_last_5_trades.py --base-dir . --n 5
```
**Confirm:** (1) v2_exit_score present, (2) v2_exit_components present, (3) exit_reason_code present and varied (not only signal_decay).

---

## 4. `logs/exit_attribution.jsonl`

**Expected fields (from main.py write path):** symbol, entry_timestamp, timestamp, v2_exit_score, v2_exit_components, v2_exit_reason_code, attribution_components (v2_exit_attribution_components), exit_quality_metrics, etc.

**DROPLET_REQUIRED:**
```bash
tail -5 /root/stock-bot/logs/exit_attribution.jsonl | python3 -c "import sys,json; [print(json.dumps({k:json.loads(L).get(k) for k in ['v2_exit_score','v2_exit_components','exit_reason_code']})) for L in sys.stdin if L.strip()]"
```

---

## 5. Entry logic

- **MIN_EXEC_SCORE:** Applied via env (e.g. paper-overlay.conf or GOVERNANCE_ENTRY_THRESHOLD). Overlays: `apply_paper_overlay_and_restart_stockbot_on_droplet.py`, CURSOR_DROPLET_EQUITY_GOVERNANCE_AUTOPILOT.sh write drop-in under `stock-bot.service.d`.
- **Entry score and signal contributions:** Logged in attribution (context.attribution_components, entry_score). Effectiveness uses joined rows; signal_effectiveness requires entry_attribution_components in attribution — board docs note this is sometimes missing (fix entry attribution so signal_effectiveness populates).

**Verification:** No code change in this audit; confirm on droplet that MIN_EXEC_SCORE in service env matches intended lever (e.g. 2.7 for paper).

---

## 6. Effectiveness reports

**Script:** `scripts/analysis/run_effectiveness_reports.py`  
**Outputs:** entry_vs_exit_blame.json, exit_effectiveness.json, signal_effectiveness.json, effectiveness_aggregates.json, counterfactual_exit.json, EFFECTIVENESS_SUMMARY.md.

**effectiveness_aggregates:** total_pnl, expectancy_per_trade, win_rate, joined_count, avg_profit_giveback (can be null if exit_quality_metrics.profit_giveback not populated).

**DROPLET_REQUIRED:**
```bash
python3 scripts/analysis/run_effectiveness_reports.py --start 2026-02-01 --end 2026-02-27 --out-dir reports/audit/effectiveness_sample
```
**Confirm:** entry_vs_exit_blame has realistic weak_entry_pct / exit_timing_pct / unclassified_pct; exit_effectiveness shows per exit_reason_code stats; effectiveness_aggregates includes total_pnl, expectancy_per_trade, avg_profit_giveback.

---

## 7. Summary and next steps

| Item | Status | Note |
|------|--------|------|
| v2 exit 5-value return | VERIFIED | exit_score_v2.py and main.py correct. |
| v2 unpack in main | VERIFIED | No 4-value bug. |
| exit_reason_code / components written | VERIFIED | Log and exit_attribution paths write them. |
| report_last_5_trades output | DROPLET | Run on droplet; confirm v2 fields and reason variety. |
| exit_attribution.jsonl content | DROPLET | tail and spot-check v2 fields. |
| Effectiveness reports | DROPLET | Run run_effectiveness_reports; confirm aggregates and blame. |
| Entry attribution → signal_effectiveness | YELLOW | Board: ensure attribution.jsonl has context.attribution_components so signal_effectiveness populates. |

**Recommendations:**
1. On droplet run `report_last_5_trades.py` and capture output; confirm no exit row missing v2_exit_score / exit_reason_code.
2. Run effectiveness report; if avg_profit_giveback is null, trace exit_quality_metrics.profit_giveback in exit_attribution and join logic.
3. Add regression test: call `compute_exit_score_v2` and assert return length 5 and reason_code in allowed set.
4. Continue exit/entry review: if one signal dominates exit_reason_code, consider weight or threshold tweaks in a future (non-audit) change.
