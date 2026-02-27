# Exit review — full droplet run output

**Date:** 2026-02-23  
**MEMORY_BANK:** All execution on droplet; results pulled to local.  
**Run 1:** Exit promotion (multi-model, all personas)  
**Run 2:** Exit review + dashboard truth audit  

---

## 1. Exit promotion pipeline (on droplet)

**Run tag:** `exit_promotion_review_20260223T211129Z`  
**RUN_DIR (on droplet):** `/root/stock-bot/reports/exit_review/promotion_exit_promotion_review_20260223T211129Z`

### Console output (droplet)

```
[2026-02-23T21:11:29Z] === START EXIT PROMOTION REVIEW exit_promotion_review_20260223T211129Z ===
[2026-02-23T21:11:29Z] Running BASELINE exit effectiveness v2
Wrote .../baseline/exit_effectiveness_v2.json and .md
[2026-02-23T21:11:29Z] Running SHADOW exit effectiveness v2 (writes to shadow/; pressure-at-exit when present in logs)
Wrote .../shadow/exit_effectiveness_v2.json and .md
[2026-02-23T21:11:29Z] Generating tuning recommendations from SHADOW
Wrote exit_tuning_recommendations.md and exit_tuning_patch.json to reports/exit_review/
[2026-02-23T21:11:29Z] Running dashboard truth audit
python3: can't open file '.../run_dashboard_truth_audit_on_droplet.py': [Errno 2] No such file or directory
[2026-02-23T21:11:29Z] Running multi-persona board review (if backtest layout present)
Multi-model -> .../board_review (prosecutor_output.md, defender_output.md, sre_output.md, board_verdict.json, board_verdict.md)
[2026-02-23T21:11:29Z] Synthesizing board decision
Wrote .../BOARD_DECISION.json
RUN_DIR: /root/stock-bot/reports/exit_review/promotion_exit_promotion_review_20260223T211129Z
DECISION: BOARD_REVIEW_COMPLETE
PR_BRANCH: NONE
[2026-02-23T21:11:29Z] === COMPLETE EXIT PROMOTION REVIEW ===
```

### BOARD_DECISION.json (exit pipeline)

```json
{
  "verdict": "CHANGES_REQUIRED",
  "rationale": [
    "Baseline vs shadow effectiveness computed; board review required."
  ],
  "gates": {
    "G1_effectiveness": "REVIEW",
    "G2_tail_risk": "REVIEW"
  },
  "next_actions": [
    "Review exit_effectiveness_v2 baseline vs shadow deltas (giveback, saved_loss, tail).",
    "Review tuning recommendations; decide config-only patch.",
    "Confirm dashboard truth audit PASS for Exit Truth panel.",
    "If all G1–G6 pass, enable EXIT_PRESSURE_ENABLED=1 in test env."
  ]
}
```

### Effectiveness v2 (baseline) — headline

- **Joined trades:** 2,782  
- **Top exit_reason_code:** other (782), signal_decay(0.96) (245), signal_decay(0.90) (107), signal_decay(0.88) (105), …  
- **Giveback / saved_loss / left_money:** None / 0% in current join; structure ready.

### Multi-model board verdict (personas)

- **Prosecutor:** Do not promote until trades_count ≥ 30 and bar discovery + score path documented. (Note: multi-model run looked for backtest layout; exit run has 2,782 joined trades.)
- **Defender:** Accept run as valid if discovery and fallback score in place and follow-up produces trades.
- **Board (multi-model):** ACCEPT_WITH_FIX — treat zero-trade (backtest) as config issue; re-run after discovery + fallback; require trades_count ≥ 30 for promotion.
- **SRE:** Evidence bundle present (dashboard_truth_audit.log, exit_tuning_patch.json, exit_tuning_recommendations.md); reproducibility via provenance and config.

---

## 2. Exit review + dashboard truth audit (on droplet)

**Run tag:** `dashboard_truth_20260223T211158Z`  
**RUN_DIR (on droplet):** `/root/stock-bot/reports/signal_review/dashboard_truth_dashboard_truth_20260223T211158Z`

### Console output (droplet)

```
Wrote .../reports/exit_review/exit_effectiveness_v2.json and .md
Wrote exit_tuning_recommendations.md and exit_tuning_patch.json to reports/exit_review/
[2026-02-23T21:11:58Z] === START dashboard truth audit dashboard_truth_20260223T211158Z ===
[2026-02-23T21:11:58Z] Dashboard contract written to /tmp/dashboard_contract.json for EOD
[2026-02-23T21:11:58Z] Running dashboard truth audit
[2026-02-23T21:11:58Z] Wiring dashboard truth audit into EOD
[2026-02-23T21:11:58Z] EOD script already includes dashboard truth audit
RUN_DIR: /root/stock-bot/reports/signal_review/dashboard_truth_dashboard_truth_20260223T211158Z
DECISION: DASHBOARD_TRUTH_LOCKED
PR_BRANCH: NONE
[2026-02-23T21:11:58Z] === COMPLETE dashboard truth audit ===
```

### Dashboard truth (droplet) — panel status

| Panel            | Source                        | Status | Reason                    |
|------------------|-------------------------------|--------|---------------------------|
| Live Trades      | journalctl:stock-bot.service  | FAIL   | no recent evidence in logs |
| Expectancy Gate  | logs/gate_truth.jsonl         | WARN   | stale (5365s)             |
| Signal Health    | logs/signal_health.jsonl      | WARN   | stale (5365s)             |
| Score Telemetry | state/score_telemetry.json    | WARN   | stale (5312s)             |
| UW Cache         | data/uw_flow_cache.json       | PASS   |                           |
| Exit Truth       | logs/exit_truth.jsonl         | WARN   | stale (2688s)             |

---

## 3. Artifacts pulled locally

All from droplet into this repo:

| Artifact | Local path |
|---------|------------|
| Promotion run | `reports/exit_review/promotion_exit_promotion_review_20260223T211129Z/` |
| BOARD_DECISION.json | `.../BOARD_DECISION.json` |
| CURSOR_FINAL_SUMMARY.txt | `.../CURSOR_FINAL_SUMMARY.txt` |
| Baseline effectiveness | `.../baseline/exit_effectiveness_v2.{json,md}` |
| Shadow effectiveness | `.../shadow/exit_effectiveness_v2.{json,md}` |
| Tuning | `.../exit_tuning_recommendations.md`, `.../exit_tuning_patch.json` |
| Board review (personas) | `.../board_review/prosecutor_output.md`, `defender_output.md`, `sre_output.md`, `board_verdict.md`, `board_verdict.json` |
| Exit effectiveness (exit_review run) | `reports/exit_review/exit_effectiveness_v2.{json,md}` |
| Exit tuning (exit_review run) | `reports/exit_review/exit_tuning_recommendations.md` |
| Dashboard truth | `reports/exit_review/dashboard_truth_droplet.json` |

---

## 4. Summary

- **Exit promotion:** Ran on droplet (baseline + shadow effectiveness v2, tuning, multi-model personas, BOARD_DECISION). **2,782** joined trades. Verdict: **CHANGES_REQUIRED**; G1/G2 in REVIEW.
- **Exit review + dashboard truth:** Ran on droplet (effectiveness v2, tuning, CURSOR_DASHBOARD_TRUTH_AUDIT). **DECISION: DASHBOARD_TRUTH_LOCKED.** UW Cache PASS; Exit Truth / Live Trades / others WARN or FAIL (stale or no recent evidence).
- **Next:** Board review deltas and tuning; get Exit Truth and Live Trades to PASS (fresh logs); then G1–G6 and EXIT_PRESSURE_ENABLED=1 in test env only.

**Output is here:** this file + the paths in §3.
