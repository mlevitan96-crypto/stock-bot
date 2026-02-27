# Memory bank — Droplet run (authoritative execution)

**One-page reference for running the profitability acceleration on the droplet.**  
Local runs were preparatory only; **all authoritative results come from the droplet** (real logs + live paper run).

---

## 1. Context (fixed)

- **We are losing money daily.** Speed matters; discipline matters more.
- **Backtests do NOT measure exit-weight overlays** → do **not** run baseline vs proposed backtest for exit levers. **Logs-based effectiveness + paper runs are the source of truth.**
- **Current live experiment:** Paper run with overlay `config/tuning/overlays/exit_score_weight_tune.json` (score_deterioration 0.25 → 0.28). Paper is **ACTIVE** on the droplet. State: `state/live_paper_run_state.json` (governed_tuning_config).
- **Policy:** Trade-count gates (30 early REVERT, 50 LOCK/REVERT). One blame baseline before any new cycle. No stacking overlays. Multi-model oversight before each decision.

---

## 2. Paths (droplet repo root: `/root/stock-bot` or `/root/stock-bot-current`)

| What | Path |
|------|------|
| Repo root | `/root/stock-bot` (or stock-bot-current) |
| Logs (attribution / exits) | `logs/attribution.jsonl`, `logs/exit_attribution.jsonl` |
| Paper run state | `state/live_paper_run_state.json` |
| Baseline effectiveness (authoritative) | `reports/effectiveness_baseline_blame/` |
| Paper-period effectiveness (rolling) | `reports/effectiveness_paper_score028_current/` |
| Paper gate 50 run | `reports/effectiveness_paper_score028_gate50/` |
| Decision memos | `reports/phase9_accel_decisions/` |
| Paper run doc | `reports/PROFITABILITY_PAPER_RUN_2026-02-18.md` |
| Next cycle stub | `reports/change_proposals/next_cycle_entry_or_exit_20260218.md` |

---

## 3. Commands (run from repo root on droplet)

**Step 1 — Sync + state**
```bash
cd /root/stock-bot
git status
# If drift: git stash push -m 'pre-accel' OR commit to branch
git pull origin main
# Record commit hash + status in reports/phase9_accel_decisions/<date>_droplet_state.md
```

**Step 2 — Authoritative baseline blame**
```bash
python3 scripts/analysis/run_effectiveness_reports.py \
  --start 2026-02-01 --end $(date +%F) \
  --out-dir reports/effectiveness_baseline_blame

python3 scripts/governance/generate_recommendation.py \
  --effectiveness-dir reports/effectiveness_baseline_blame
```
- Goal: `entry_vs_exit_blame.json` exists, joined_count ≥ 20, losing_trades ≥ 5. If not, iterate date window.
- Write memo: `reports/phase9_accel_decisions/<date>_baseline_blame.md` (weak_entry_pct vs exit_timing_pct; top harmful signals/exits; conclusion: EXIT justified vs ENTRY dominates).

**Step 3 — Paper window + rolling effectiveness**
```bash
PAPER_START=2026-02-18   # or from state/live_paper_run_state.json
PAPER_END=$(date +%F)

python3 scripts/analysis/run_effectiveness_reports.py \
  --start $PAPER_START --end $PAPER_END \
  --out-dir reports/effectiveness_paper_score028_current
```
- From output / EFFECTIVENESS_SUMMARY: joined_count, losers, win_rate, avg_profit_giveback. Update `reports/PROFITABILITY_PAPER_RUN_2026-02-18.md` “Current checkpoint”.

**Step 4 — 30-trade gate (if joined_count ≥ 30)**
- Compare paper vs baseline_blame. Early REVERT if: **win_rate < baseline - 3%** OR **giveback > baseline + 0.05**.
- Write `reports/phase9_accel_decisions/<date>_paper_gate_30.md` (multi-model: adversarial / quant / product; why conclusion could be wrong; proceed or abort).
- If REVERT: stop paper, restart without overlay, document, **end run**.
  ```bash
  python3 board/eod/start_live_paper_run.py --date $(date +%F)
  ```
  (no `--overlay`)

**Step 5 — 50-trade gate (when joined_count ≥ 50)**
```bash
python3 scripts/analysis/run_effectiveness_reports.py \
  --start $PAPER_START --end $PAPER_END \
  --out-dir reports/effectiveness_paper_score028_gate50
```
- Write `reports/phase9_accel_decisions/<date>_paper_gate_50_comparison.md` (win_rate delta, giveback delta, blame mix). LOCK requires: win_rate ≥ -2%, giveback ≤ +0.05.
- Write `reports/phase9_accel_decisions/<date>_paper_gate_50_models.md` (multi-model review). Decision: LOCK or REVERT. Update `reports/PROFITABILITY_PAPER_RUN_2026-02-18.md` with final decision + evidence.

**Step 6 — Next cycle (stub only; do not execute)**
- From baseline_blame: if weak_entry_pct > exit_timing_pct → next cycle = **ENTRY** (one lever, down-weight worst signal). Else **EXIT** only, one lever, no stacking. Ensure stub exists: `reports/change_proposals/next_cycle_entry_or_exit_<date>.md`.

---

## 4. Gates (numbers)

| Gate | Condition | Action |
|------|-----------|--------|
| Baseline | joined ≥ 20, losers ≥ 5 | Authoritative baseline; write baseline_blame memo. |
| 30-trade | joined_count (paper) ≥ 30 | Early REVERT if win_rate < baseline - 3% or giveback > baseline + 0.05. Multi-model memo. |
| 50-trade | joined_count (paper) ≥ 50 | Compare; LOCK if win_rate Δ ≥ -2%, giveback Δ ≤ +0.05; else REVERT. Written comparison + multi-model memo. |

---

## 5. Decision memos (multi-model)

Before **each** decision (baseline blame, 30-trade, 50-trade):

- **Adversarial / Quant / Product:** each states why the conclusion could be wrong, what risk remains, proceed or abort.
- Write to `reports/phase9_accel_decisions/<YYYYMMDD>_<topic>.md`.

---

## 6. Rules (non-negotiable)

- Droplet execution only for authoritative results.
- Logs-based effectiveness is authoritative for exit levers (no backtest compare for exit).
- Trade-count gates; no LOCK/REVERT on &lt;30 trades for this overlay.
- No stacking overlays (exit_flow + exit_score not together).
- No LOCK without written comparison + multi-model review.
- If evidence is inconclusive, REVERT is **success**.

---

## 7. Key docs (reference)

- **Paper run + checkpoint:** `reports/PROFITABILITY_PAPER_RUN_2026-02-18.md`
- **Acceleration policy:** `reports/PROFITABILITY_ACCELERATION_REVIEW_2026-02-18.md`
- **Strategic context:** `reports/STRATEGIC_RESET_MULTI_MODEL_REVIEW_2026-02-18.md`
- **Path to profitability:** `docs/PATH_TO_PROFITABILITY.md`
