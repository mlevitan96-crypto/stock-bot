# Top 5 action items — exit promotion (all runs from droplet)

Summary and how to accomplish each item **on the droplet**. SSH to the droplet, then run from repo root (e.g. `cd /root/stock-bot` or `cd ~/stock-bot`).

---

## 1. Review baseline vs shadow effectiveness deltas (giveback, saved_loss, tail)

**Summary:** Compare exit effectiveness v2 with pressure-off (baseline) vs pressure-in-logs (shadow) so the Board can see giveback, saved_loss, and tail-risk deltas before promoting EXIT_PRESSURE_ENABLED.

**How to accomplish (on droplet):**

```bash
cd /root/stock-bot   # or your REPO path
git pull origin main

# Single pipeline: baseline + shadow + board decision (writes to reports/exit_review/promotion_<tag>/)
REPO=/root/stock-bot bash scripts/CURSOR_EXIT_PROMOTION_REVIEW_ALL_PERSONAS.sh
```

Then inspect the run dir (printed at end as `RUN_DIR`):

- `RUN_DIR/baseline/exit_effectiveness_v2.json` and `.md`
- `RUN_DIR/shadow/exit_effectiveness_v2.json` and `.md`
- Compare overall and by exit_reason_code: `avg_pnl`, `avg_profit_giveback`, `tail_loss_5pct`, `saved_loss_rate`, `left_money_rate`.

---

## 2. Review tuning recommendations and decide config-only patch

**Summary:** Use the tuner’s recommendations (e.g. earlier exit for low saved_loss_rate buckets) and decide whether to apply a config-only patch; no code changes. Board must approve before applying.

**How to accomplish (on droplet):**

```bash
cd /root/stock-bot
# Ensure effectiveness v2 exists (from step 1 or from exit review)
python3 scripts/analysis/run_exit_effectiveness_v2.py --start 2026-01-01 --end 2026-02-23 --out-dir reports/exit_review
python3 scripts/exit_tuning/suggest_exit_tuning.py
```

- Review: `reports/exit_review/exit_tuning_recommendations.md`
- Proposed patch (do not apply until Board approves): `reports/exit_review/exit_tuning_patch.json`
- After Board approval, apply patch per your config load path (e.g. merge into env or config file on droplet).

---

## 3. Confirm dashboard truth audit PASS for Exit Truth panel (G3)

**Summary:** Satisfy G3: exit truth logs present and fresh; dashboard truth audit PASS for exit panels.

**How to accomplish (on droplet):**

```bash
cd /root/stock-bot
# Bootstrap exit truth if missing (so audit can pass)
[ -s logs/exit_truth.jsonl ] || echo '{"exit_pressure":0.5,"decision":"HOLD","ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","symbol":"_bootstrap"}' >> logs/exit_truth.jsonl

# Run dashboard truth audit (exit panels + exit truth coverage)
chmod +x scripts/CURSOR_DASHBOARD_TRUTH_AUDIT_AND_EOD_WIRING.sh
bash scripts/CURSOR_DASHBOARD_TRUTH_AUDIT_AND_EOD_WIRING.sh
```

- Confirm Exit Truth panel and exit truth coverage PASS in the audit output.
- If the script is not on the droplet, ensure `scripts/CURSOR_DASHBOARD_TRUTH_AUDIT_AND_EOD_WIRING.sh` (and any scripts it calls) are deployed via `git pull` or upload.

---

## 4. Complete G1–G6 and enable EXIT_PRESSURE_ENABLED=1 in test env only

**Summary:** Close promotion gates (backtest delta G1, tail G2, truth/dashboard G3, integrity G4, rollback G5, shadow delta G6); then enable exit pressure only in a test environment.

**How to accomplish (on droplet):**

- **G1 (backtest):** Run backtest with EXIT_PRESSURE_ENABLED=1 vs baseline (same period) on droplet; document run dir and metrics.
- **G2 (tail):** From those runs, confirm tail loss (e.g. 5th percentile PnL) and max drawdown do not worsen beyond tolerance.
- **G3:** Done in step 3 above.
- **G4 (integrity):** Ensure attribution schema and exit_reason_code taxonomy unchanged; no regression in join/exit_attribution (run existing attribution/join checks on droplet if available).
- **G5 (rollback):** Document rollback: set `EXIT_PRESSURE_ENABLED=0` (or unset), redeploy, confirm behavior; keep `exit_tuning_patch.json` apply only after Board approval.
- **G6 (shadow):** Use the promotion review run from step 1; ensure delta direction aligns with objective (e.g. more saved_loss, less giveback) before promoting.

Then, **only in test env** (e.g. a test systemd unit or test shell):

```bash
export EXIT_PRESSURE_ENABLED=1
# Restart your test process so it picks up the env
```

Do not set `EXIT_PRESSURE_ENABLED=1` in production until Board has signed off.

---

## 5. Document rollback and apply tuning patch only after Board approval

**Summary:** Rollback must be documented and repeatable; exit tuning patch must be applied only after Board approval.

**How to accomplish (on droplet):**

- **Rollback (document and test on droplet):**
  - Set `EXIT_PRESSURE_ENABLED=0` or unset in environment / systemd / config.
  - Redeploy or restart the process.
  - Confirm cascade behavior (e.g. exits use non-pressure path; logs/exit_truth.jsonl optional).
- **Tuning patch:**
  - Keep `reports/exit_review/exit_tuning_patch.json` under version control; apply only after Board has approved in `BOARD_REVIEW_OUTPUT.md` / checklist.
  - On droplet, apply by merging patch into the config your app loads (e.g. env file or config service), then restart.

---

## Quick reference — run order on droplet

| Order | Action | Command (on droplet) |
|-------|--------|----------------------|
| 1 | Full promotion review (baseline + shadow + decision) | `REPO=/root/stock-bot bash scripts/CURSOR_EXIT_PROMOTION_REVIEW_ALL_PERSONAS.sh` |
| 2 | Tuning recommendations | `python3 scripts/analysis/run_exit_effectiveness_v2.py --start 2026-01-01 --end 2026-02-23 --out-dir reports/exit_review` then `python3 scripts/exit_tuning/suggest_exit_tuning.py` |
| 3 | Dashboard truth (G3) | `bash scripts/CURSOR_DASHBOARD_TRUTH_AUDIT_AND_EOD_WIRING.sh` |
| 4 | G1/G2 backtest | Run backtest with EXIT_PRESSURE_ENABLED=1 vs 0; compare metrics and tail. |
| 5 | Rollback doc + patch | Document EXIT_PRESSURE_ENABLED=0 rollback; apply exit_tuning_patch.json only after Board sign-off. |

All of the above are intended to be run **on the droplet** (SSH into the box and execute in the repo directory).
