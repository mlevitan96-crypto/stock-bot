# Alpaca Fast-Lane 25-Trade Deep Review — Board Packet

**Generated:** 20260317_1525
**Cycles:** 10 | **Total trades:** 250 | **Cumulative PnL:** $-49.91

---
## Executive summary

This packet aggregates all 10 completed 25-trade cycles. Total trades analyzed: 250; cumulative PnL: $-49.91. Baseline mean PnL per trade: $-0.1996.

---
## What is working

- **Promotion-grade factors:** time_of_day=afternoon (mean PnL $-0.04, n=84)
- **Paper-only candidates:** entry_regime=MIXED; exit_regime=MIXED

---
## What is noise

- High-sample factors with no edge (DISCARD): TECH, UNKNOWN, short, low, close, NEUTRAL, NEUTRAL

---
## What is dangerous

- No automatic promotion is applied; all recommendations are advisory. Overfitting risk: factors with low trade count or high variance are RESEARCH-ONLY or DISCARD.

---
## Promotion verdict

**PROMOTABLE:** time_of_day:afternoon

---
## Factor stability (top 15 by |mean PnL|)

- **exit_reason:stale_alpha_cutoff(1059min,-0.03%)** — trades=1, mean_pnl=$-13.17, win_rate=0.00
- **exit_reason:signal_decay(0.47)** — trades=2, mean_pnl=$-4.65, win_rate=0.00
- **symbol:INTC** — trades=6, mean_pnl=$-4.06, win_rate=0.00
- **exit_reason:signal_decay(0.54)+flow_reversal** — trades=1, mean_pnl=$3.69, win_rate=1.00
- **exit_reason:signal_decay(0.46)+stale_alpha_cutoff(3996min,-0.01%)** — trades=1, mean_pnl=$-3.27, win_rate=0.00
- **exit_reason:stale_alpha_cutoff(1061min,0.01%)** — trades=1, mean_pnl=$3.11, win_rate=1.00
- **exit_reason:signal_decay(0.73)+flow_reversal** — trades=1, mean_pnl=$-2.34, win_rate=0.00
- **exit_reason:signal_decay(0.51)+flow_reversal** — trades=1, mean_pnl=$2.25, win_rate=1.00
- **exit_reason:signal_decay(0.70)+flow_reversal+stale_alpha_cutoff(4002min,0.01%)** — trades=1, mean_pnl=$2.10, win_rate=1.00
- **exit_reason:stale_alpha_cutoff(1062min,0.00%)** — trades=1, mean_pnl=$1.89, win_rate=1.00
- **exit_reason:signal_decay(0.34)+flow_reversal** — trades=1, mean_pnl=$1.87, win_rate=1.00
- **exit_reason:signal_decay(0.69)+flow_reversal** — trades=2, mean_pnl=$1.86, win_rate=0.50
- **exit_reason:stale_alpha_cutoff(1061min,-0.00%)** — trades=2, mean_pnl=$1.82, win_rate=1.00
- **symbol:MRNA** — trades=8, mean_pnl=$-1.74, win_rate=0.38
- **sector:BIOTECH** — trades=8, mean_pnl=$-1.74, win_rate=0.38

---
## Exit-reason decomposition (sample)

- stale_alpha_cutoff(1059min,-0.03%): n=1, total_pnl=$-13.17
- signal_decay(0.70): n=11, total_pnl=$-12.27
- signal_decay(0.77)+flow_reversal: n=15, total_pnl=$9.76
- signal_decay(0.47): n=2, total_pnl=$-9.30
- signal_decay(0.93): n=5, total_pnl=$-6.44
- signal_decay(0.83): n=7, total_pnl=$-6.03
- signal_decay(0.74): n=4, total_pnl=$5.75
- signal_decay(0.76): n=4, total_pnl=$5.54
- signal_decay(0.86): n=3, total_pnl=$-5.14
- signal_decay(0.74)+flow_reversal: n=3, total_pnl=$-4.42
- signal_decay(0.85): n=13, total_pnl=$3.84
- signal_decay(0.69)+flow_reversal: n=2, total_pnl=$3.71