# Exit objective function (explicit)

**Purpose:** Single composite objective for exit tuning. Used by effectiveness reports and tuning recommendations.

---

## Minimize

- **Giveback:** profit_giveback (fraction of MFE given back by exit). Lower = less “left on table.”
- **Left money:** fraction of exits where exit_efficiency.left_money is true. Lower = fewer “exited too early” cases that then ran further.
- **Tail loss:** 5th percentile (or similar) of realized P&L. Avoid increasing tail loss when improving giveback.

---

## Maximize

- **Realized P&L:** average (and optionally median) realized P&L per trade.
- **Saved loss rate:** fraction of exits where exit_efficiency.saved_loss is true (exited before loss grew).
- **Win rate:** secondary; prefer improving giveback/saved_loss without sacrificing win rate.

---

## Constrain

- **Turnover:** do not exceed target turnover (exits per day / per symbol) unless risk override.
- **Slippage proxy:** if available, limit exit urgency that would cause market orders in illiquid names.
- **Risk exposure:** hard stops and compliance overrides always win; no relaxation of risk controls.

---

## Composite (for tuning comparison)

For a single scalar “exit quality” (e.g. for backtest vs baseline):

- `exit_quality = w1 * (1 - avg_giveback) + w2 * saved_loss_rate + w3 * avg_pnl_normalized - w4 * tail_loss_penalty`
- Weights and normalization are configurable; default emphasis: reduce giveback and increase saved_loss without increasing tail loss beyond tolerance.

---

## Regime conditioning

Objective can be evaluated **per regime** (e.g. BULL, BEAR, MIXED, high_vol_neg_gamma). Tuning may recommend different thresholds or weights per regime; promotion gates apply to each regime slice as well as overall.
