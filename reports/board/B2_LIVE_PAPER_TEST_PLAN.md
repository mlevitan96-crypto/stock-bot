# B2 Live Paper Test Plan

**Scope:** All sessions, all symbols  
**Mode:** Paper-only (no real orders)  
**Feature:** B2 = remove early signal_decay exits (hold < 30 min suppressed when flag ON)

---

## Duration

- **Minimum evaluation window:** 7 calendar days from enable.
- **Minimum sample size:** 50 closed exits (post-enable) for attribution comparison.

---

## Primary success metrics (measurable)

| Metric | Description |
|--------|-------------|
| **Delta in realized PnL attribution** | Compare post-B2 window vs baseline (e.g. last 387 exits or 30d) — expect neutral or improved expectancy. |
| **Delta in drawdown / worst-N tail** | Worst 5% of exits by PnL; do not exceed baseline worst-tail by more than 20% (relative). |
| **Delta in exit reason mix** | Share of exits with reason `signal_decay` should **drop**; share of `stop_loss` / `profit_target` / `trail_stop` may shift. |

---

## Tripwires (auto-rollback triggers)

| Tripwire | Threshold | Action |
|----------|------------|--------|
| **paper_safety_violation** | count > 0 | Immediate rollback (B2 OFF + verify). |
| **Tail-risk breach** | Worst 5% of exits (by PnL) worse than baseline worst 5% by > 20% (relative) | Rollback. |
| **Sustained negative delta** | Realized expectancy (per-exit PnL) below baseline by > 15% for 3+ consecutive days | Rollback. |

---

## Rollback procedure

1. On droplet: set `FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=false` (or unset) in `/root/stock-bot/.env` (or equivalent).
2. Restart: `sudo systemctl restart stock-bot`.
3. Verify: health endpoints 200; confirm flag OFF via env or dashboard/telemetry.

**One command option (droplet):**  
`sed -i 's/FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=true/FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=false/' /root/stock-bot/.env && sudo systemctl restart stock-bot`

---

## References

- B2 changelog: `reports/audit/B2_CHANGELOG.md`
- Enable proof: `reports/audit/B2_LIVE_PAPER_ENABLE_PROOF.md`
- Start snapshot: `reports/board/B2_LIVE_PAPER_START_SNAPSHOT.md` / `.json`
- Rollback drill: `reports/audit/B2_ROLLBACK_DRILL_PROOF.md`
