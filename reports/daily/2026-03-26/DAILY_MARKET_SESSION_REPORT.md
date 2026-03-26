# Daily market session report — 2026-03-26

## Market session (ET)

```
# Alpaca PnL — market session scope (20260327_MKTS_FINAL)

## Canonical TODAY (ET session)

- **session_date_et:** `2026-03-26`
- **session_open_et:** `2026-03-26T09:30:00-04:00`
- **session_close_et:** `2026-03-26T16:00:00-04:00`
- **window_start_utc:** `2026-03-26T13:30:00Z` → epoch `1774531800.0`
- **window_end_utc:** `2026-03-26T20:00:00Z` → epoch `1774555200.0`

## Strict gate parameters

- `OPEN_TS_UTC_EPOCH` = max(STRICT_EPOCH_START, window_start_epoch) (runner)
- `EXIT_TS_UTC_EPOCH_MAX` = `1774555200.0`

```

## Trades

- **Executed (strict complete cohort):** 2 (seen 2)
- **Cohort trade_ids (count 2):** see evidence `ALPACA_MARKET_SESSION_COMPLETE_TRADE_IDS_*.json`
- **Blocked intents (log-derived hint):** 0

## Net PnL (cohort, reconciliation CSV)

**Sum net_pnl:** 7.5

| trade_id | symbol | side | entry_ts | exit_ts | qty | avg_entry | avg_exit | gross_pnl | fees | net_pnl | ledger_pnl | reconciliation_delta | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| open_MKT1_2026-03-26T14:00:00+00:00 | MKT1 | long | 2026-03-26T14:00:00+00:00 | 2026-03-26T17:00:00+00:00 | 10.0 | 100.0 | 101.0 | 10.0 | 0.0 | 10.0 | 10.0 | 0.0 | fees_not_joined_workspace_stub |
| open_MKT2_2026-03-26T15:30:00+00:00 | MKT2 | long | 2026-03-26T15:30:00+00:00 | 2026-03-26T17:45:00+00:00 | 5.0 | 100.0 | 99.5 | -2.5 | 0.0 | -2.5 | -2.5 | 0.0 | fees_not_joined_workspace_stub |


## Learning status

**verdict (from evidence JSON):** `LEARNING_SAFE`

```
# Alpaca learning status summary

## LEARNING SAFE — strict cohort complete; safe to treat as learning-greenlight input.

| Field | Value |
|---|---|
| timestamp_utc | `2026-03-26T22:18:32.103673+00:00` |
| window_hours | 2 |
| window_start_epoch | 1774548000.0 |
| window_end_epoch | 1774555200.0 |
| verdict | **LEARNING_SAFE** |
| trades_seen | 44 |
| trades_incomplete | 0 |
| sre_auto_repair.ran | False |
| sre_auto_repair.actions_applied | 0 |
| sre_auto_repair.residual_incompletes | 0 |
| exit_code | 0 |
| commit_sha | `235fe9ad407ad0a5ee19d0081b2396371438d9c4` |
| runner | `alpaca_forward_truth_runner` |

## Why this verdict

Process exited **0** (CERT_OK) with **trades_incomplete == 0** and at least one exit in the evaluated cohort. Forward truth contract + SRE engine completed; see `proof_links` for JSON evidence.

## Proof artifacts

- `reports/ALPACA_LAST_WINDOW_TRUTH_20260327_LAST_WINDOW.json`

## Notes

- synthesis_from_truth_json_and_exit_code
```

## Signal attribution (excerpt from evidence)

```
# SIGNAL_ATTRIBUTION (20260327_MKTS_FINAL)

n_trades=2

```json
{
  "note": "uw_attribution.jsonl not sliced in this bundle"
}
```

```

## CSA verdict (from evidence)

```
**Root cause:** none

CSA_VERDICT: PNL_REVIEW_COMPLETE
---
## CSA verdict line

**CSA_VERDICT: LAST_WINDOW_LEARNING_SAFE**
```

## Promotion decision

**YES** (from PnL closeout verdict line where applicable)

```
# Closeout (20260327_MKTS_FINAL)

| Check | OK |
|-------|-----|
| cohort list | True |
| reconciliation rows vs trades_complete | True |

**Root cause:** none

CSA_VERDICT: PNL_REVIEW_COMPLETE

```

## Evidence index (links — open files, do not paste raw JSON)

- Directory: `reports/daily/2026-03-26/evidence/`
- Run tag: `20260327_MKTS_FINAL`
