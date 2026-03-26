# Repo report inventory (global)

- **UTC:** 2026-03-26T23:15:28.597214+00:00
- **Scope:** `reports/**/*.md|.json|.csv` (excludes paths allowed as non-report: see `report_path_rules.py`; `reports/state/**` is permanent telemetry).
- **Retention rule for (C):** mtime age > 3 days and not referenced from any `DAILY_MARKET_SESSION_REPORT.md` text.

## Counts

| Class | Count | Meaning |
|-------|-------|---------|
| A — KEEP (canonical layout + state) | 80 | `daily/<date>/DAILY_*` or `daily/.../evidence/` or `reports/state/` |
| B — MOVE | 946 | Recent or referenced; target session `evidence/` |
| C — DELETE | 3 | Stale orphan disposable report |
| **Total scanned** | 1029 | |

## Sample — move (B) (first 40)

- `reports\ALPACA_BASELINE_20260326_2315Z.json` → `C:\Dev\stock-bot\reports\daily\2026-03-26\evidence/`
- `reports\ALPACA_DAILY_POST_MARKET_TELEGRAM_CLOSEOUT_20260325_231500Z.md` → `C:\Dev\stock-bot\reports\daily\2026-03-25\evidence/`
- `reports\ALPACA_DASHBOARD_DATA_SANITY_20260326_1900Z.json` → `C:\Dev\stock-bot\reports\daily\2026-03-26\evidence/`
- `reports\ALPACA_DASHBOARD_DEPLOY_ACTIVATION_CLOSEOUT_20260325_182052Z.md` → `C:\Dev\stock-bot\reports\daily\2026-03-25\evidence/`
- `reports\ALPACA_DASHBOARD_DROPLET_PROOF_20260326_1815Z.json` → `C:\Dev\stock-bot\reports\daily\2026-03-26\evidence/`
- `reports\ALPACA_DASHBOARD_DROPLET_PROOF_20260326_1900Z.json` → `C:\Dev\stock-bot\reports\daily\2026-03-26\evidence/`
- `reports\ALPACA_DASHBOARD_DROPLET_PROOF_20260326_2200Z.json` → `C:\Dev\stock-bot\reports\daily\2026-03-26\evidence/`
- `reports\ALPACA_DASHBOARD_DROPLET_PROOF_20260327_0100Z.json` → `C:\Dev\stock-bot\reports\daily\2026-03-27\evidence/`
- `reports\ALPACA_DASHBOARD_HTTP_TRACES_20260326_1815Z.json` → `C:\Dev\stock-bot\reports\daily\2026-03-26\evidence/`
- `reports\ALPACA_DASHBOARD_HTTP_TRACES_20260327_0100Z.json` → `C:\Dev\stock-bot\reports\daily\2026-03-27\evidence/`
- `reports\ALPACA_DASHBOARD_VERIFY_ALL_TABS_20260326_1815Z.json` → `C:\Dev\stock-bot\reports\daily\2026-03-26\evidence/`
- `reports\ALPACA_DASHBOARD_VERIFY_ALL_TABS_20260326_2020Z.json` → `C:\Dev\stock-bot\reports\daily\2026-03-26\evidence/`
- `reports\ALPACA_DASHBOARD_VERIFY_ALL_TABS_20260327_0100Z.json` → `C:\Dev\stock-bot\reports\daily\2026-03-27\evidence/`
- `reports\ALPACA_DROPLET_CERT_MISSION_20260326_STRICT_ZERO_FINAL.json` → `C:\Dev\stock-bot\reports\daily\2026-03-26\evidence/`
- `reports\ALPACA_DROPLET_CERT_MISSION_20260327_0200Z.json` → `C:\Dev\stock-bot\reports\daily\2026-03-27\evidence/`
- `reports\ALPACA_EDGE_BOARD_REVIEW_20260317_1547.md` → `C:\Dev\stock-bot\reports\daily\2026-03-17\evidence/`
- `reports\ALPACA_EDGE_BOARD_REVIEW_20260317_1629.md` → `C:\Dev\stock-bot\reports\daily\2026-03-17\evidence/`
- `reports\ALPACA_EDGE_BOARD_REVIEW_20260317_1708.md` → `C:\Dev\stock-bot\reports\daily\2026-03-17\evidence/`
- `reports\ALPACA_EDGE_BOARD_REVIEW_20260317_1721.md` → `C:\Dev\stock-bot\reports\daily\2026-03-17\evidence/`
- `reports\ALPACA_EDGE_PROMOTION_SHORTLIST_20260317_1547.md` → `C:\Dev\stock-bot\reports\daily\2026-03-17\evidence/`
- `reports\ALPACA_EDGE_PROMOTION_SHORTLIST_20260317_1708.md` → `C:\Dev\stock-bot\reports\daily\2026-03-17\evidence/`
- `reports\ALPACA_EDGE_PROMOTION_SHORTLIST_20260317_1721.md` → `C:\Dev\stock-bot\reports\daily\2026-03-17\evidence/`
- `reports\ALPACA_EVENT_FLOW_COUNTS_20260326_1622Z.json` → `C:\Dev\stock-bot\reports\daily\2026-03-26\evidence/`
- `reports\ALPACA_EVENT_FLOW_COUNTS_20260326_2015Z.json` → `C:\Dev\stock-bot\reports\daily\2026-03-26\evidence/`
- `reports\ALPACA_EXECUTION_TRUTH_COVERAGE_20260324_2109.md` → `C:\Dev\stock-bot\reports\daily\2026-03-24\evidence/`
- `reports\ALPACA_FASTLANE_25_BOARD_REVIEW_20260317_1525.md` → `C:\Dev\stock-bot\reports\daily\2026-03-17\evidence/`
- `reports\alpaca_fastlane_25_cycle_aggregate_20260317_1525.csv` → `C:\Dev\stock-bot\reports\daily\2026-03-17\evidence/`
- `reports\ALPACA_FORWARD_DROPLET_RAW_20260326_1905Z.json` → `C:\Dev\stock-bot\reports\daily\2026-03-26\evidence/`
- `reports\ALPACA_FORWARD_PARITY_COUNTS_20260326_1707Z.json` → `C:\Dev\stock-bot\reports\daily\2026-03-26\evidence/`
- `reports\ALPACA_FORWARD_POLL_20260327_0200Z.json` → `C:\Dev\stock-bot\reports\daily\2026-03-27\evidence/`
- `reports\ALPACA_FORWARD_POLL_20260327_0200Z_iter_1.json` → `C:\Dev\stock-bot\reports\daily\2026-03-27\evidence/`
- `reports\ALPACA_FORWARD_POLL_20260327_0200Z_iter_1.md` → `C:\Dev\stock-bot\reports\daily\2026-03-27\evidence/`
- `reports\ALPACA_FORWARD_POLL_20260327_0200Z_iter_2.json` → `C:\Dev\stock-bot\reports\daily\2026-03-27\evidence/`
- `reports\ALPACA_FORWARD_POLL_20260327_0200Z_iter_2.md` → `C:\Dev\stock-bot\reports\daily\2026-03-27\evidence/`
- `reports\ALPACA_FORWARD_POLL_20260327_0200Z_iter_3.json` → `C:\Dev\stock-bot\reports\daily\2026-03-27\evidence/`
- `reports\ALPACA_FORWARD_POLL_20260327_0200Z_iter_3.md` → `C:\Dev\stock-bot\reports\daily\2026-03-27\evidence/`
- `reports\ALPACA_FORWARD_POLL_20260327_0200Z_iter_4.json` → `C:\Dev\stock-bot\reports\daily\2026-03-27\evidence/`
- `reports\ALPACA_FORWARD_POLL_20260327_0200Z_iter_4.md` → `C:\Dev\stock-bot\reports\daily\2026-03-27\evidence/`
- `reports\ALPACA_FORWARD_POLL_20260327_0200Z_iter_5.json` → `C:\Dev\stock-bot\reports\daily\2026-03-27\evidence/`
- `reports\ALPACA_FORWARD_POLL_20260327_0200Z_iter_5.md` → `C:\Dev\stock-bot\reports\daily\2026-03-27\evidence/`
- … and 906 more

## Sample — delete (C) (first 60)

- `reports\daily\DAILY_REVIEW_2026-03-10.md`
- `reports\daily\PROMOTION_STATUS_2026-03-10.json`
- `reports\daily\SHADOW_ARTIFACT_INDEX_2026-03-10.json`

## Other report-like files (inventory only; not modified)

- **`artifacts/` + `backtests/`:** 15 files matching `*.md` / `*.json` / `*.csv` (backtest artifacts and similar — not under `reports/`; excluded from automated move/delete).
- **`memory_bank/`, `docs/`, `config/`, `src/`, `logs/`:** excluded by mission scope (not scanned as disposable reports).