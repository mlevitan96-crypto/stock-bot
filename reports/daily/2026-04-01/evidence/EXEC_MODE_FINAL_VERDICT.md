# EXEC_MODE_FINAL_VERDICT

- **Best policy (test-day mean PnL heuristic):** `P2_PASSIVE_THEN_CROSS|ttl=3`
- **P0 baseline mean / p05:** -0.217971 / -3.3
- **Profit delta / day (approx):** `4.169022` USD vs P0 × test-day trade count n=143 (heuristic; policies may differ in fill_rate)
- **Tail-risk note:** p05 delta (best - P0): 0.06

## ONE paper-only action contract

**Action:** Enable **PASSIVE_THEN_CROSS** with **TTL=3** in the **paper** router **only** for symbols in `EXEC_MODE_UNIVERSE_TOP20_LAST3D.json` — **offline replay first**; no live executor change until board sign-off.

**Kill criteria:** Test-day mean_pnl below P0 by >X USD/trade over two subsequent ET weeks **or** fill_rate < 0.85 in paper replay (adjust X with governance).

**Rollback:** Remove policy flag; revert to marketable proxy; archive this evidence bundle.
