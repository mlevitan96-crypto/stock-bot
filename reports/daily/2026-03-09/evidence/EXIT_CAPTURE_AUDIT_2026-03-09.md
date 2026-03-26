# Exit Capture Audit

**Date:** 2026-03-09
**Trades analyzed:** 300

## Trade shape summary

- MFE/MAE present: 298 / 300
- Green then red (MFE>0, PnL<0): 10 (3.3%)
- Median hold winners (min): 35.967837616666664
- Median hold losers (min): 34.850591900000005
- **Winners cut earlier than losers:** No
- **Majority green→red:** No

## Trade frequency

- Trades/day (window): 79.7
- Trades/symbol (top): INTC=12, TSLA=11, AMD=10, NVDA=10, COP=10, MRNA=9, XLK=8, DIA=8, IWM=8, F=8

## By exit reason

| Reason | Count | Win rate % | Avg PnL |
|--------|-------|------------|---------|
| signal_decay(0.84) | 16 | 18.8 | -1.2515 |
| signal_decay(0.69) | 15 | 86.7 | 0.4963 |
| signal_decay(0.77) | 13 | 15.4 | -1.03 |
| signal_decay(0.83) | 12 | 16.7 | -0.5214 |
| signal_decay(0.70) | 12 | 50.0 | -0.2613 |
| signal_decay(0.86) | 10 | 20.0 | -1.1395 |
| signal_decay(0.82) | 10 | 50.0 | -0.2656 |
| signal_decay(0.71) | 10 | 60.0 | 0.767 |
| signal_decay(0.61)+flow_reversal | 8 | 37.5 | -0.175 |
| signal_decay(0.81) | 7 | 28.6 | -1.4886 |
| signal_decay(0.93)+flow_reversal | 7 | 14.3 | -0.5729 |
| signal_decay(0.85) | 6 | 16.7 | -0.9333 |
| signal_decay(0.78) | 6 | 16.7 | -3.1394 |
| signal_decay(0.61) | 6 | 16.7 | -0.3683 |
| signal_decay(0.91)+flow_reversal | 6 | 50.0 | 0.2233 |
| signal_decay(0.89) | 5 | 0.0 | -2.19 |
| signal_decay(0.94) | 5 | 0.0 | -1.1207 |
| signal_decay(0.86)+flow_reversal | 5 | 20.0 | -0.414 |
| signal_decay(0.64) | 5 | 40.0 | -0.692 |
| signal_decay(0.87) | 4 | 25.0 | -1.6975 |
| signal_decay(0.88) | 4 | 0.0 | -3.9925 |
| signal_decay(0.79) | 4 | 0.0 | -4.9267 |
| signal_decay(0.94)+flow_reversal | 3 | 33.3 | 0.2992 |
| signal_decay(0.43) | 3 | 66.7 | 1.0982 |
| signal_decay(0.85)+flow_reversal | 3 | 0.0 | -0.3333 |
| signal_decay(0.44)+flow_reversal | 3 | 100.0 | 0.13 |
| signal_decay(0.42) | 3 | 66.7 | 0.0267 |
| signal_decay(0.75)+flow_reversal | 3 | 0.0 | -1.8 |
| signal_decay(0.93) | 3 | 66.7 | 0.8667 |
| signal_decay(0.78)+flow_reversal | 3 | 33.3 | -0.0233 |
| signal_decay(0.76)+flow_reversal | 3 | 0.0 | -0.7233 |
| signal_decay(0.68) | 3 | 33.3 | 0.0933 |
| signal_decay(0.63) | 3 | 0.0 | -1.1633 |
| signal_decay(0.75) | 3 | 33.3 | -1.2467 |
| signal_decay(0.55) | 2 | 100.0 | 0.15 |
| signal_decay(0.46) | 2 | 0.0 | -0.695 |
| signal_decay(0.53) | 2 | 0.0 | -0.72 |
| signal_decay(0.63)+flow_reversal | 2 | 100.0 | 1.09 |
| signal_decay(0.64)+flow_reversal | 2 | 50.0 | -2.415 |
| stale_alpha_cutoff(146min,0.00%) | 2 | 100.0 | 0.585 |
| signal_decay(0.82)+flow_reversal | 2 | 50.0 | -0.26 |
| signal_decay(0.60)+flow_reversal | 2 | 50.0 | 0.06 |
| stale_alpha_cutoff(146min,0.01%) | 2 | 100.0 | 0.885 |
| signal_decay(0.62) | 2 | 0.0 | -1.1003 |
| signal_decay(0.66) | 2 | 50.0 | -1.805 |
| signal_decay(0.83)+flow_reversal | 2 | 0.0 | -0.77 |
| signal_decay(0.76) | 2 | 0.0 | -0.76 |
| signal_decay(0.52)+flow_reversal | 2 | 50.0 | -0.07 |
| signal_decay(0.79)+flow_reversal | 2 | 0.0 | -0.44 |
| signal_decay(0.67)+flow_reversal | 2 | 50.0 | -0.45 |
| signal_decay(0.66)+flow_reversal | 2 | 0.0 | -0.38 |
| signal_decay(0.92) | 2 | 50.0 | 0.045 |
| unknown | 2 | 100.0 | 0.0 |
| signal_decay(0.70)+flow_reversal | 1 | 0.0 | -0.23 |
| signal_decay(0.90)+flow_reversal | 1 | 100.0 | 5.73 |
| flow_reversal+stale_alpha_cutoff(1114min | 1 | 100.0 | 0.24 |
| signal_decay(0.67)+stale_alpha_cutoff(10 | 1 | 100.0 | 1.3433 |
| signal_decay(0.84)+flow_reversal+stale_a | 1 | 0.0 | -0.41 |
| signal_decay(0.85)+stale_alpha_cutoff(10 | 1 | 0.0 | -0.63 |
| signal_decay(0.87)+stale_alpha_cutoff(10 | 1 | 100.0 | 0.4 |
| signal_decay(0.50)+stale_alpha_cutoff(11 | 1 | 100.0 | 0.0 |
| signal_decay(0.57) | 1 | 0.0 | -1.06 |
| signal_decay(0.81)+stale_alpha_cutoff(11 | 1 | 100.0 | 1.59 |
| signal_decay(0.90) | 1 | 0.0 | -0.38 |
| signal_decay(0.45)+flow_reversal | 1 | 100.0 | 2.79 |
| signal_decay(0.50) | 1 | 0.0 | -0.28 |
| signal_decay(0.44) | 1 | 0.0 | -0.62 |
| signal_decay(0.72)+flow_reversal | 1 | 100.0 | 1.7133 |
| signal_decay(0.48) | 1 | 100.0 | 0.05 |
| signal_decay(0.40) | 1 | 100.0 | 0.42 |
| signal_decay(0.92)+flow_reversal | 1 | 0.0 | -0.8 |
| flow_reversal+drawdown(3.5%)+stale_alpha | 1 | 0.0 | -5.34 |
| flow_reversal+stale_alpha_cutoff(145min, | 1 | 0.0 | -1.895 |
| flow_reversal+stale_alpha_cutoff(145min, | 1 | 100.0 | 3.3 |
| flow_reversal+stale_alpha_cutoff(144min, | 1 | 0.0 | -5.04 |
| flow_reversal+stale_alpha_cutoff(144min, | 1 | 0.0 | -1.11 |
| signal_decay(0.72)+flow_reversal+stale_a | 1 | 100.0 | 0.33 |
| signal_decay(0.80)+flow_reversal+stale_a | 1 | 0.0 | -2.52 |
| signal_decay(0.71)+flow_reversal | 1 | 0.0 | -0.13 |
| signal_decay(0.56)+flow_reversal | 1 | 0.0 | -0.28 |
| signal_decay(0.91) | 1 | 0.0 | -0.24 |
| signal_decay(0.54)+flow_reversal | 1 | 100.0 | 0.87 |
| signal_decay(0.51) | 1 | 0.0 | -0.38 |
| signal_decay(0.54) | 1 | 0.0 | -0.59 |
| flow_reversal+stale_alpha_cutoff(148min, | 1 | 0.0 | -1.56 |
| stale_alpha_cutoff(147min,0.01%) | 1 | 100.0 | 1.5 |
| signal_decay(0.74) | 1 | 100.0 | 0.61 |
| signal_decay(0.67) | 1 | 0.0 | -0.28 |
| signal_decay(0.43)+flow_reversal | 1 | 0.0 | -0.85 |
| signal_decay(0.62)+flow_reversal | 1 | 100.0 | 0.06 |
| signal_decay(0.59) | 1 | 0.0 | -0.12 |
| signal_decay(0.47) | 1 | 100.0 | 1.04 |
| signal_decay(0.87)+flow_reversal | 1 | 0.0 | -0.3 |
| signal_decay(0.80)+flow_reversal | 1 | 0.0 | -0.6933 |
| signal_decay(0.58) | 1 | 100.0 | 0.96 |
| signal_decay(0.84)+flow_reversal | 1 | 0.0 | -0.25 |
| signal_decay(0.47)+flow_reversal | 1 | 0.0 | -1.29 |
| signal_decay(0.42)+flow_reversal | 1 | 100.0 | 0.42 |
| signal_decay(0.38)+flow_reversal | 1 | 100.0 | 0.17 |
| signal_decay(0.69)+flow_reversal | 1 | 100.0 | 0.17 |
| signal_decay(0.80)+stale_alpha_cutoff(39 | 1 | 100.0 | 0.81 |
| signal_decay(0.71)+flow_reversal+stale_a | 1 | 0.0 | -0.26 |
| signal_decay(0.80) | 1 | 0.0 | -9.68 |