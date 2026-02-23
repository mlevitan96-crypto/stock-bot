# Board review — exit tuning & pressure promotion

**Generated:** 2026-02-23  
**Artifacts:** exit_tuning_recommendations.md, exit_effectiveness_v2, EXIT_PROMOTION_CHECKLIST.md

---

## Links to all board-reviewed documents (GitHub)

| Document | Path | GitHub link |
|----------|------|-------------|
| **Board review (this file)** | `reports/exit_review/BOARD_REVIEW_OUTPUT.md` | [BOARD_REVIEW_OUTPUT.md](https://github.com/mlevitan96-crypto/stock-bot/blob/main/reports/exit_review/BOARD_REVIEW_OUTPUT.md) |
| Exit tuning recommendations | `reports/exit_review/exit_tuning_recommendations.md` | [exit_tuning_recommendations.md](https://github.com/mlevitan96-crypto/stock-bot/blob/main/reports/exit_review/exit_tuning_recommendations.md) |
| Exit promotion checklist | `reports/exit_review/EXIT_PROMOTION_CHECKLIST.md` | [EXIT_PROMOTION_CHECKLIST.md](https://github.com/mlevitan96-crypto/stock-bot/blob/main/reports/exit_review/EXIT_PROMOTION_CHECKLIST.md) |
| Exit effectiveness v2 (summary) | `reports/exit_review/exit_effectiveness_v2.md` | [exit_effectiveness_v2.md](https://github.com/mlevitan96-crypto/stock-bot/blob/main/reports/exit_review/exit_effectiveness_v2.md) |
| Exit redesign contract | `reports/exit_review/EXIT_REDESIGN_CONTRACT.md` | [EXIT_REDESIGN_CONTRACT.md](https://github.com/mlevitan96-crypto/stock-bot/blob/main/reports/exit_review/EXIT_REDESIGN_CONTRACT.md) |
| Cursor final summary | `reports/exit_review/CURSOR_FINAL_SUMMARY.txt` | [CURSOR_FINAL_SUMMARY.txt](https://github.com/mlevitan96-crypto/stock-bot/blob/main/reports/exit_review/CURSOR_FINAL_SUMMARY.txt) |
| Droplet run summary | `reports/exit_review/DROPLET_RUN_SUMMARY.md` | [DROPLET_RUN_SUMMARY.md](https://github.com/mlevitan96-crypto/stock-bot/blob/main/reports/exit_review/DROPLET_RUN_SUMMARY.md) |
| EOD exit enforcement | `reports/exit_review/EOD_EXIT_ENFORCEMENT.md` | [EOD_EXIT_ENFORCEMENT.md](https://github.com/mlevitan96-crypto/stock-bot/blob/main/reports/exit_review/EOD_EXIT_ENFORCEMENT.md) |

*Replace `main` in the URL with your branch name if different.*

---

## 1. Exit tuning recommendations

Recommendations are in `exit_tuning_recommendations.md`. No patch is applied until Board approves.

| Field | Value |
|-------|--------|
| **Review date** | |
| **Decision** | ☐ APPROVE patch / ☐ DEFER / ☐ REJECT |
| **Conditions** | *(e.g. paper only; shadow 7d; limit to threshold change)* |
| **Approved by** | |
| **Notes** | |

---

## 2. Exit pressure promotion (EXIT_PRESSURE_ENABLED)

Gates in `EXIT_PROMOTION_CHECKLIST.md` (G1–G6). Promotion = allow EXIT_PRESSURE_ENABLED=1 in production.

| Field | Value |
|-------|--------|
| **Review date** | |
| **Promotion decision** | ☐ Approved / ☐ Not yet (gates incomplete) / ☐ Rejected |
| **Conditions** | *(e.g. backtest delta; tail cap; rollback verified)* |
| **Board sign-off** | |

---

## 3. Copy/paste summary (for Board)

**Exit effectiveness v2 (droplet, real data):** 2,671 joined trades; overall avg_pnl -0.11; wins 798, losses 1,685. Top exit reasons: signal_decay (various ratios), signal_decay+flow_reversal, other, trail_stop, stale_alpha_cutoff. Giveback/saved_loss/left_money not yet in join; structure ready.

**Tuning:** 55 recommendation lines (saved_loss_rate 0% → consider earlier exit). Patch: `exit_tuning_patch.json` (empty until Board approves changes).

**Dashboard truth:** All 6 panels ran; Exit Truth PASS (bootstrapped). Live Trades, UW Cache PASS; Expectancy Gate, Signal Health, Score Telemetry WARN (stale).

**Board action:** (1) Review tuning recommendations → APPROVE/DEFER/REJECT and conditions. (2) Review promotion checklist → approve or defer EXIT_PRESSURE_ENABLED promotion. Sign off above.
