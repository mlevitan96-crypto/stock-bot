# INTRADAY FORENSIC FULL — 2026-03-09

**Source:** Droplet. exit_decision_trace + exit_attribution + blocked_trades.

## 1) Portfolio-level unrealized edge

- **Peak unrealized (USD):** 50.8495
- **Drawdown from peak to EOD (USD):** 60.8833
- **Had intraday profit window:** Yes

## 2) Why wasn't it captured?

Classifications: {"total_trades": 174, "never_green": 52, "green_reversal": 22, "eligible_but_late": 56, "eligible_and_timely": 13, "no_trace": 31, "ambiguous_trace": 0}

Attribution: exit eligibility lag (ELIGIBLE_BUT_LATE); reversal before eligibility (GREEN_REVERSAL); many trades never went green (52/174)

## 3) Displacement_blocked impact

- Blocked count: 2000
- Counterfactual: Bars not loaded; counterfactual PnL at 30m/60m/120m not computed. Run with data/bars or Alpaca to enable.

## 4) Single change that would have helped most

EXIT_TIMING: earlier exit when eligible would have captured some green-reversal and eligible-but-late trades. ENTRY_QUALITY: reducing never-green entries would reduce loss. One day is insufficient for parameter change.

## 5) What must NOT change based on one day

Do not relax exit thresholds or gating (displacement_blocked) based on 2026-03-09 alone.
