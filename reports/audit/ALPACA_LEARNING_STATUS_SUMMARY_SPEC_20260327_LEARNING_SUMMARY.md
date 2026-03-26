# Alpaca learning status summary — contract (canonical fields)

**Timestamp:** `20260327_LEARNING_SUMMARY`

## Required fields (JSON)

| Field | Type | Description |
|-------|------|-------------|
| `timestamp_utc` | string | ISO UTC from source truth run (`run_utc`) or synthesis time |
| `window_hours` | int | Evaluation window length |
| `window_start_epoch` | float \| null | `OPEN_TS_UTC_EPOCH` / `open_ts_epoch` |
| `window_end_epoch` | float \| null | `EXIT_TS_UTC_EPOCH_MAX` / `window_end_epoch` when bounded |
| `verdict` | enum | `LEARNING_SAFE` \| `LEARNING_NOT_SAFE` \| `NO_ACTIVITY` |
| `trades_seen` | int | Strict cohort size |
| `trades_incomplete` | int | Residual incompletes |
| `sre_auto_repair` | object | `ran` (bool), `actions_applied` (int), `residual_incompletes` (int) |
| `exit_code` | int | Forward truth runner process exit (0 / 1 / 2) |
| `commit_sha` | string | `git rev-parse HEAD` at emit time (short hash ok) |
| `runner` | string | e.g. `alpaca_forward_truth_runner` |
| `notes` | string[] | Human/debug strings |
| `proof_links` | string[] | Repo-relative paths to truth JSON (and incident JSON if present) |

## Verdict rules

- **LEARNING_SAFE:** `exit_code == 0`, `trades_incomplete == 0`, `trades_seen > 0`
- **NO_ACTIVITY:** `exit_code == 0`, `trades_seen == 0`
- **LEARNING_NOT_SAFE:** `exit_code` in `{1,2}` or `trades_incomplete > 0`

## Rolling artifacts (single canonical copy)

- `reports/ALPACA_LEARNING_STATUS_SUMMARY.json`
- `reports/audit/ALPACA_LEARNING_STATUS_SUMMARY.md`

Latest run overwrites both.
