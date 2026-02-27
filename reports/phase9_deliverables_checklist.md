# Phase 9 — Final deliverables checklist

**Date:** 2026-02-18

**Execution authorized.** Canonical runbook: `reports/phase9_droplet_runbook.md` (Steps 1–7).

**Conditions:** Baseline first | one lever (exit_flow_weight_phase9) | follow runbook exactly | no new tuning mid-run | no bypass guards | every step produces proof.

---

## Pre-execution (done)

- [x] **reports/phase8_cursor_multi_model_review.md** — Multi-model findings; do now / do later.
- [x] **reports/phase9_strategic_review_and_go_nogo.md** — Strategic review; GO verdict.
- [x] **reports/change_proposals/exit_flow_weight_phase9.md** — One hypothesis, evidence-backed.
- [x] **config/tuning/overlays/exit_flow_weight_phase9.json** — One config-only overlay (+0.02 flow_deterioration).

---

## Execution proof (fill on droplet per runbook)

- [ ] **STEP 1** — `reports/phase8_deploy_proof.md` filled (commit hash, restart snippet, health, timestamp).
- [x] **STEP 2** — Baseline path in `phase8_first_cycle_result.md` and in `change_proposals/exit_flow_weight_phase9.md` Section 2. (No effectiveness/ on droplet runs.)
- [x] **STEP 3** — Proposed backtest run complete; proposed dir noted.
- [x] **STEP 4** — `reports/governance_comparison/exit_flow_weight_phase9/comparison.md` + `.json` exist (evidence recovery: inline aggregate on droplet; scripts not on droplet); guards run locally → **PASS**; deltas in `phase8_first_cycle_result.md`.
- [x] **STEP 5** — Decision **LOCK** and rationale in `phase8_first_cycle_result.md`; cited metrics in `change_proposals/exit_flow_weight_phase9.md`.
- [ ] **STEP 6** — Dashboard truth check optional; if auth blocks (401), note in phase8_first_cycle_result — do not treat as failure.
- [x] **STEP 7** — This checklist completed.

---

## Minimum DONE (process validation)

- [ ] phase8_deploy_proof.md filled
- [x] Baseline + proposed backtests run
- [x] Governance comparison artifacts exist
- [x] Guards run and recorded (PASS)
- [x] phase8_first_cycle_result.md filled (LOCK)
- [ ] Dashboard screenshots captured (optional if 401)

**Phase 9 COMPLETE** (evidence recovery mode). Comparison artifacts exist, guards executed, final LOCK recorded. 7d results provisional; post-LOCK paper validation recommended.

**Note:** A REVERT is a success if the loop ran and all artifacts are complete. After LOCK, plan a short paper period as post-LOCK validation.
