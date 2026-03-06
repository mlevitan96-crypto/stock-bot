# Weekly Decision Packet — 2026-03-06

Owner packet: what we do next. No promotions in this mission.

---

## 1. Week in numbers

| Metric | Value (fill from ledger when run) |
|--------|-----------------------------------|
| Executed (7d) | — |
| Blocked (7d) | — |
| Counter-intel blocked (7d) | — |
| Validation failures (7d) | — |
| Validation failure rate % | — |
| PnL proxy (if available) | — |

*Run `scripts/audit/collect_weekly_droplet_evidence.py` and `scripts/audit/build_weekly_trade_decision_ledger.py` to populate. Ledger summary: reports/audit/WEEKLY_TRADE_DECISION_LEDGER_SUMMARY_2026-03-06.json.*

---

## 2. What changed this week

- Weekly board audit pipeline added: evidence collector, trade decision ledger, CSA weekly review, persona memos, pivot analysis, unturned rocks, cockpit weekly section, this decision packet.
- B2 live paper promotion (if any): see reports/audit/B2_* evidence; no promotion executed in this mission.

---

## 3. What to promote next (and why)

- **No promotions in this mission.** CSA and shadow comparison identify candidates; promote only after enforce_csa_gate and risk/SRE sign-off.
- Next promotable: see CSA_WEEKLY_REVIEW_2026-03-06_BOARD_PACKET.md and shadow nomination in SHADOW_COMPARISON_LAST387.json.

---

## 4. What to kill/disable (and why)

- Nothing to kill this week. If CSA or SRE findings recommend disabling a signal or gate, document in CSA_FINDINGS and run gate enforcement separately.

---

## 5. Top 5 experiments for next week (with success criteria)

| # | Experiment | Success criteria |
|---|------------|------------------|
| 1 | Add 14d and 30d ledger summaries to weekly run | Summary JSONs exist; nomination stability reportable |
| 2 | Instrument blocked opportunity cost (blocked when shadow would profit) | Ledger or summary includes proxy field |
| 3 | Structured validation_failed reason codes | Top_validation_reasons in ledger summary |
| 4 | One do-nothing or buy-hold baseline in board comparison | Baseline return in comparative review |
| 5 | Close one CSA required_next_experiment from latest verdict | Document result; re-run CSA |

---

## 6. Real-money readiness assessment

- **Can we win?** Conditional. Need: positive expectancy in a controlled cohort, execution that does not leak edge, closed missing_data and key experiments.
- **What must be true to trade real money safely?** Risk checklist (max drawdown, position limits); governance and SRE green; at least one full cycle of weekly audit with no blockers; and explicit Owner sign-off.
- **Timeline estimate:** 2–4 weeks (if experiments close and bottleneck is not structural); 1–2 months (if instrumentation and baselines needed); 3+ months (if pivot or major redesign). Tied to evidence from next 2–3 weekly runs.

---

## 7. Pivot recommendation (stocks vs options/wheel)

- **Recommendation:** Stay course (stocks). See reports/board/WEEKLY_REVIEW_2026-03-06_PIVOT_ANALYSIS.md.
- **Staged plan:** 30d — close experiments and add ledger 14d/30d; 60d — shadow/board stability and opportunity-cost proxy; 90d — real-money checklist or explicit defer. Revisit options/wheel only after stock bottleneck is identified and options MVP is designed with success criteria.

---

---

## 8. Verification notes (exit criteria)

- **Droplet evidence:** Run `python scripts/audit/collect_weekly_droplet_evidence.py --date 2026-03-06` from an environment with SSH access to the droplet (droplet_config.json or DROPLET_* env). If critical sources are missing, WEEKLY_EVIDENCE_BLOCKER_2026-03-06.md is written; remediate and re-run.
- **Ledger:** Built locally (0 events when no local logs in window). On droplet or after evidence pull, re-run `build_weekly_trade_decision_ledger.py` with `--base-dir` pointing to repo or weekly_evidence_stage to populate counts.
- **Deploy to droplet:** Commit, push to origin main, then run `python scripts/run_deploy_to_droplet.py`. Verify dashboard Profitability & Learning tab shows **Section 8. Weekly Review (last 7d)** with link to board packet and trades this week.

*Generated for weekly board audit. Update section 1 after running evidence collection and ledger build on droplet.*
