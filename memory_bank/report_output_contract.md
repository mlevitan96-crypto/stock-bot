# Report output contract (memory)

- **Operator-visible:** only `reports/daily/<YYYY-MM-DD>/DAILY_MARKET_SESSION_REPORT.md` and optional `.json`.
- **Evidence-only writers:** detailed `.md`/`.json`/`.csv` must go under `reports/daily/<YYYY-MM-DD>/evidence/` only (no new top-level `reports/*.md` or `reports/audit/*`).
- **Assembly:** `scripts/audit/assemble_daily_market_session_report.py` runs **after** producers; embeds PnL table, signal attribution excerpt, learning status, CSA verdict lines, and links to evidence.
- **Paths helper:** `src/report_output/paths.py`.
- **Docs:** `docs/CANONICAL_DAILY_REPORT_CONTRACT.md`, `docs/REPORT_OUTPUT_CONTRACT.md`, `docs/REPO_REPORT_VISIBILITY_RULES.md`.
- **Lockdown:** `scripts/maintenance/repo_wide_report_cleanup.py` + strict `verify_report_layout.py` (no `reports/` sprawl outside `daily/` + `state/`).
