# INTRADAY PROFITABILITY FORENSIC

**Date:** 2026-03-09 (UTC day boundary)  
**Source:** Droplet (production logs/state). Run: `scripts/audit/run_intraday_forensic_on_droplet.py --date 2026-03-09`  
**Generated:** 2026-03-09 (droplet)

---

## PHASE 0 — DATA INTEGRITY (SRE) **[Run on droplet — PASS]**

- exit_decision_trace present: **True** (size 2,546,186 bytes)
- exit_attribution present: **True** (174 exits for 2026-03-09)
- exit_decision_trace today samples: **3,980**
- blocked_trades present: **True** (2,000 records for 2026-03-09)
- **FAIL CLOSED: False** — All decision-affecting telemetry present; no gaps.

---

## PHASE 1 — INTRADAY PnL SHAPE (CSA + Quant)

- Trades (with symbol): 98
- **Realized PnL (USD):** -124.19
- Unrealized peak proxy (sum MFE): 13.71 USD
- Winners: 23 | Losers: 73 | Win rate: 23.47%

### Time windows where unrealized was positive
- Reconstructed from MFE: trades with MFE > 0 had positive unrealized at some point. Count: 27

---

## PHASE 2 — EXIT WINDOW FORENSICS

Trades with MFE > 0 that ended in loss (green-then-red):

- **JPM** PnL=-0.05 USD, MFE=0.03 USD, exit_reason=signal_decay(0.77)
- **SLB** PnL=-0.06 USD, MFE=0.015 USD, exit_reason=signal_decay(0.94)
- **LCID** PnL=-0.11 USD, MFE=0.01 USD, exit_reason=signal_decay(0.70)
- **TGT** PnL=-0.08 USD, MFE=0.005 USD, exit_reason=signal_decay(0.79)+flow_reversal

**Could we have exited profitably?** For the 4 green-then-red trades above, MFE was small (0.005–0.03 USD). Earlier exit at peak would have captured minimal profit; exit logic did not fire at peak (signal_decay threshold not met at peak).

---

## PHASE 3 — BLOCKED & COUNTER-INTEL

- Blocked trades today (from state/blocked_trades.jsonl on droplet): **2,000** (predominantly displacement_blocked; scores 4.5–5.6).
- Counterfactual PnL for blocked: requires post-block price movement; not computed in this run.

---

## PHASE 4 — WHY TODAY LOST MONEY (CSA VERDICT)

See INTRADAY_BOARD_VERDICT for causal verdict.

---

## PHASE 5 — WHAT WOULD HAVE MADE TODAY PROFITABLE

See INTRADAY_BOARD_VERDICT.
