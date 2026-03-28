# Alpaca live intent — postfix blocker summary

**STOP** — learning unblock conditions not met.

## Root cause

- **postfix_insufficient_recent_closes:** fewer than 5 `exit_attribution` rows with exit timestamp strictly after `NEW_DEPLOY_FLOOR_TS` (`1774670865`).
- Canary observed **zero** `entry_decision_made` rows after the same floor within the 5-minute wait window.

## Failing gate keys (implicit)

- Cannot evaluate last-5 postfix cohort (empty sample).
- LIVE `entry_decision_made` contract on postfix trades **not yet observable** (no new closes after floor).

## trade_ids

- *(none in postfix window)*

## Required operator actions

1. Re-run during active trading: extend canary (`--max-wait-sec 1800`) if desired.
2. Wait until ≥5 closes with `close_ts > 1774670865` (or refresh floor on next deploy and re-record).
3. Re-run:  
   `PYTHONPATH=. python3 scripts/audit/alpaca_postfix_learning_n_audit.py --root . --deploy-floor-ts <FLOOR> --n 5 --open-ts-epoch 0 --write-md reports/daily/<ET>/evidence/ALPACA_LAST5_LEARNING_ONLY_AUDIT_POSTFIX_<TS>.md`

## Unblock sentence

**Do not print** the learning-unblock line until **5/5 PASS** and CSA/SRE final positives.
