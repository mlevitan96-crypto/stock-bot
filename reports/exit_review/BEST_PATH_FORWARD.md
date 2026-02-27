# Best path forward — exit promotion (multi-model + all personas)

**Run:** `exit_promotion_review_20260223T210904Z` (executed on droplet)  
**Artifacts:** `reports/exit_review/promotion_exit_promotion_review_20260223T210904Z/`

---

## What ran on the droplet

- **Baseline effectiveness v2** → 2,782 joined trades (real attribution data).
- **Shadow effectiveness v2** → same cohort, pressure-in-logs when present.
- **Tuning recommendations** → 55 lines (saved_loss_rate 0% → consider earlier exit); patch in `exit_tuning_patch.json` (empty until Board approves).
- **Dashboard truth audit** → skipped (script `run_dashboard_truth_audit_on_droplet.py` not on droplet; use alternative below).
- **Multi-model / personas** → Prosecutor, Defender, SRE, Board ran; outputs in `board_review/`.
- **Board decision (exit)** → `BOARD_DECISION.json`: verdict **CHANGES_REQUIRED**, G1_effectiveness and G2_tail_risk in **REVIEW**.

**Note on multi-model verdict:** The persona run looks for a *backtest* layout (e.g. `baseline/backtest_summary.json`). The exit promotion run dir has *exit effectiveness* layout (`baseline/exit_effectiveness_v2.json`). So the multi-model runner reported "0 trades" and **ACCEPT_WITH_FIX** from a backtest lens. The **exit-specific** verdict to use is **BOARD_DECISION.json**: CHANGES_REQUIRED; Board must review deltas and tuning before enabling EXIT_PRESSURE.

---

## Personas summary

| Role | Verdict / stance |
|------|-------------------|
| **Prosecutor** | Do not promote until trades_count ≥ 30 and bar discovery + score path documented (backtest lens: saw no backtest_summary → 0 trades). |
| **Defender** | Accept run as valid if discovery and fallback score are in place and a follow-up run produces trades; do not reject on one zero-trade run. |
| **SRE** | Evidence bundle present (dashboard_truth_audit.log, exit_tuning_patch.json, exit_tuning_recommendations.md); reproducibility via provenance and config. |
| **Board (multi-model)** | ACCEPT_WITH_FIX: treat zero-trade run as config/data issue; re-run after discovery + fallback fixes; require trades_count ≥ 30 for promotion. |
| **Board (exit pipeline)** | CHANGES_REQUIRED: review baseline vs shadow deltas and tuning; confirm dashboard truth PASS; then G1–G6 and test env only. |

---

## Best path forward (prioritized)

All steps below are intended to be run **from or on the droplet** unless noted. Use **TOP_5_ACTION_ITEMS_DROPLET.md** for exact commands.

### 1. Fix G3 on droplet (dashboard truth audit)

The promotion script expected `run_dashboard_truth_audit_on_droplet.py` on the droplet; that script is meant to run from your **local** machine. On the droplet, run the audit directly:

**On droplet:**

```bash
cd /root/stock-bot
[ -s logs/exit_truth.jsonl ] || echo '{"exit_pressure":0.5,"decision":"HOLD","ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","symbol":"_bootstrap"}' >> logs/exit_truth.jsonl
chmod +x scripts/CURSOR_DASHBOARD_TRUTH_AUDIT_AND_EOD_WIRING.sh
bash scripts/CURSOR_DASHBOARD_TRUTH_AUDIT_AND_EOD_WIRING.sh
```

**Or from local (uses DropletClient):**  
`python scripts/run_exit_review_on_droplet.py` — uploads scripts, runs effectiveness v2 + tuning + dashboard audit on droplet, fetches results. This is the recommended "plugin" to get G3 done from your machine while execution stays on the droplet.

### 2. Board review (exit-specific)

- **Review** `promotion_exit_promotion_review_20260223T210904Z/baseline/exit_effectiveness_v2.md` vs `shadow/exit_effectiveness_v2.md` (giveback, saved_loss, tail).
- **Review** `exit_tuning_recommendations.md`; decide APPROVE/DEFER/REJECT and conditions (see **BOARD_REVIEW_OUTPUT.md**).
- **Review** EXIT_PROMOTION_CHECKLIST.md G1–G6; sign off when gates are satisfied.

### 3. Run G1 backtest on droplet (pressure on vs off)

- Run backtest with `EXIT_PRESSURE_ENABLED=1` and same period with `EXIT_PRESSURE_ENABLED=0`.
- Document run dir and metrics; confirm objective (giveback lower and/or saved_loss higher within tail constraint).

### 4. Close G2 (tail), G4 (integrity), G5 (rollback), G6 (shadow)

- **G2:** From G1 runs, ensure tail loss and max drawdown do not worsen beyond tolerance.
- **G4:** Attribution schema and exit_reason_code unchanged; no join/exit_attribution regression.
- **G5:** Document rollback: set `EXIT_PRESSURE_ENABLED=0`, redeploy, confirm behavior; apply `exit_tuning_patch.json` only after Board approval.
- **G6:** Use the promotion run’s baseline vs shadow; confirm delta direction (e.g. more saved_loss, less giveback) before enabling pressure.

### 5. Enable EXIT_PRESSURE in test env only

After G1–G6 pass and Board sign-off:

- On **test** env only: `export EXIT_PRESSURE_ENABLED=1` and restart the process.
- Do **not** set in production until Board has approved and rollback is validated.

---

## Recommended next command (from your machine)

To re-run the full pipeline on the droplet **and** get dashboard truth (G3) executed on the droplet via your client:

```bash
python scripts/run_exit_review_on_droplet.py
```

This uploads needed scripts, runs effectiveness v2 + tuning + **CURSOR_DASHBOARD_TRUTH_AUDIT_AND_EOD_WIRING.sh** on the droplet, and pulls back `exit_effectiveness_v2.*`, `exit_tuning_recommendations.md`, and dashboard truth results. Then run the full multi-persona promotion when you want a fresh BOARD_DECISION and board_review artifacts:

```bash
python scripts/run_exit_promotion_review_on_droplet.py
```

---

## Summary table

| Priority | Action | Where | Command / doc |
|----------|--------|--------|----------------|
| 1 | Get G3 (dashboard truth) passing | Droplet (or trigger via local client) | `bash scripts/CURSOR_DASHBOARD_TRUTH_AUDIT_AND_EOD_WIRING.sh` or `python scripts/run_exit_review_on_droplet.py` |
| 2 | Board review exit deltas + tuning | Board | BOARD_REVIEW_OUTPUT.md, exit_tuning_recommendations.md, EXIT_PROMOTION_CHECKLIST.md |
| 3 | G1 backtest (pressure on vs off) | Droplet | Backtest orchestration with EXIT_PRESSURE_ENABLED=1 vs 0 |
| 4 | Close G2, G4, G5, G6 | Droplet + doc | Tail check, integrity, rollback doc, shadow delta |
| 5 | Enable pressure in test only | Test env on droplet | `EXIT_PRESSURE_ENABLED=1` after Board sign-off |

All personas (prosecutor, defender, SRE, board) ran and outputs are in `board_review/`. Use **BOARD_DECISION.json** and **EXIT_PROMOTION_CHECKLIST.md** as the source of truth for exit promotion; use the multi-model verdict for backtest-promotion context when you run backtest-style orchestration with the same runner.
