# PHASE 9 — DROPLET EXECUTION & FIRST GOVERNED CYCLE
## (CANONICAL RUNBOOK — EXECUTION AUTHORIZED)

**Strategic review:** `reports/phase9_strategic_review_and_go_nogo.md`  
**Verdict:** GO — First governed tuning cycle authorized.

**Conditions (non-negotiable):**
- Baseline must exist and be recorded before any proposed run.
- One lever only (exit_flow_weight_phase9), small delta only (+0.02).
- Follow this runbook exactly. No new tuning ideas mid-run. No bypassing guards.
- Every step must produce a proof artifact.

**Hypothesis this cycle:** exit_weights.flow_deterioration +0.02 | Overlay: `config/tuning/overlays/exit_flow_weight_phase9.json`

---

## STEP 1 — DEPLOY (IF NEEDED) + CAPTURE PROOF

```bash
# On droplet
cd /root/stock-bot   # or stock-bot-current
bash board/eod/deploy_on_droplet.sh
```

**Verify**

- Open `/api/ping`
- Open `/api/version`
- Dashboard loads → Attribution & Effectiveness tab
- Trade ID lookup: use ONE known live trade_id

**Proof artifact →** `reports/phase8_deploy_proof.md`  
Fill: commit hash deployed, restart output snippet, health endpoint responses, timestamp.

---

## STEP 2 — ESTABLISH BASELINE (BEFORE)

**Preferred: fresh 30d backtest on droplet**

```bash
cd /root/stock-bot   # or stock-bot-current
OUT_DIR_PREFIX=30d_baseline bash board/eod/run_30d_backtest_on_droplet.sh
```

**Confirm**

- `state/latest_backtest_dir.json` updated to new backtest dir (e.g. `backtests/30d_baseline_YYYYMMDD_HHMMSS`)
- `backtests/30d_baseline_*/effectiveness/*` exists

**If a suitable existing backtest already has `effectiveness/*`:** record that dir as baseline instead; do not re-run.

**Proof artifacts →**

- `reports/phase8_first_cycle_result.md` — baseline backtest dir path, baseline effectiveness dir path, mtime evidence
- `reports/change_proposals/exit_flow_weight_phase9.md` — Section 2: baseline path, cited metrics (from baseline effectiveness JSONs)

---

## STEP 3 — PROPOSED RUN (WITH OVERLAY)

```bash
cd /root/stock-bot   # or stock-bot-current
export GOVERNED_TUNING_CONFIG=config/tuning/overlays/exit_flow_weight_phase9.json
OUT_DIR_PREFIX=30d_proposed bash board/eod/run_30d_backtest_on_droplet.sh
```

**Note:** Result dir will be `backtests/30d_proposed_YYYYMMDD_HHMMSS` — use this and the baseline dir from Step 2 in Step 4.

---

## STEP 4 — COMPARE + GUARDS

**Compare**

```bash
# Replace <baseline_ts> and <proposed_ts> with actual dir timestamps from Step 2 and Step 3
python3 scripts/governance/compare_backtest_runs.py \
  --baseline backtests/30d_baseline_<baseline_ts> \
  --proposed backtests/30d_proposed_<proposed_ts> \
  --out reports/governance_comparison/exit_flow_weight_phase9
```

**Guards**

```bash
python3 scripts/governance/regression_guards.py
```

**Proof artifacts →**

- `reports/governance_comparison/exit_flow_weight_phase9/comparison.md` and `comparison.json` (created by compare script)
- `reports/phase8_first_cycle_result.md` — record PASS/FAIL for guards, key deltas from comparison

---

## STEP 5 — DECISION (LOCK OR REVERT)

Based on comparison + guards and falsification criteria in the change proposal:

- **LOCK** if: PnL or giveback improves (or neutral), win rate does not drop >2%, guards PASS.
- **REVERT** if: win rate drops >2%, giveback increases >0.05, or guards FAIL.  
  Treat REVERT as process success if the loop ran and artifacts are complete.

**Proof artifacts →**

- `reports/phase8_first_cycle_result.md` — Decision: LOCK or REVERT; rationale; baseline/proposed dirs; comparison deltas (PnL, win rate, giveback, blame mix); guard result
- `reports/change_proposals/exit_flow_weight_phase9.md` — Update cited metrics (Section 2) and status

---

## STEP 6 — DASHBOARD TRUTH CHECK

- Confirm dashboard shows **“From latest backtest”**, correct source path, and source_mtime.
- Trade ID lookup on 2–3 **live** trades: one winner, one loser, one high-giveback (if available).

**Proof artifact →** Screenshots per `reports/phase7_proof/README.md` (add to `reports/phase7_proof/`).

---

## STEP 7 — FINAL CHECKLIST

Complete `reports/phase9_deliverables_checklist.md`.

**Minimum DONE:** phase8_deploy_proof.md filled | baseline + proposed run | governance comparison artifacts exist | guards run and recorded | phase8_first_cycle_result.md filled (LOCK/REVERT) | dashboard screenshots captured.

**After LOCK:** Plan a short paper period as post-LOCK validation (per strategic review).

---

**END — PHASE 9 RUNBOOK**
