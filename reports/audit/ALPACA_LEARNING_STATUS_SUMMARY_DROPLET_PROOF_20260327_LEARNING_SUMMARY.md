# Alpaca learning status summary — droplet proof

**Timestamp:** `20260327_LEARNING_SUMMARY`

## Procedure

`scripts/audit/run_alpaca_last_window_verify_droplet.py`: git sync, upload runner + SRE + `alpaca_learning_status_summary.py` + verify, run `alpaca_last_window_learning_verify.py`, fetch rolling summary files to workspace.

## Files present (droplet paths)

- `/root/stock-bot/reports/ALPACA_LEARNING_STATUS_SUMMARY.json`
- `/root/stock-bot/reports/audit/ALPACA_LEARNING_STATUS_SUMMARY.md`

## Verified snapshot (mirrored locally after run)

| Check | Expected (mission) | Observed |
|-------|-------------------|----------|
| `verdict` | `LEARNING_SAFE` | `LEARNING_SAFE` |
| `trades_seen` | `44` | `44` |
| `trades_incomplete` | `0` | `0` |
| `sre_auto_repair.ran` | `false` | `false` |
| `exit_code` | `0` | `0` |
| `commit_sha` | *(HEAD at verify)* | `235fe9a…` (full hash in JSON) |

Note: `commit_sha` reflects **`main` at verification time** (includes summary integration), not an older baseline.

## Source bundle

`reports/ALPACA_LAST_WINDOW_DROPLET_BUNDLE_20260327_LAST_WINDOW.json` (fetched keys include learning summary bodies).
