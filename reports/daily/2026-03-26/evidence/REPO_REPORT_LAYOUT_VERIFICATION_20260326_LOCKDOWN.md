# Repo report layout verification (final)

**TS:** `20260326_LOCKDOWN`

## Command

```bash
python scripts/maintenance/verify_report_layout.py --base HEAD~1
```

(Use `origin/main` in CI when available.)

## Result

- **Strict tree:** No `.md`/`.json`/`.csv` under `reports/` except:
  - `reports/daily/<YYYY-MM-DD>/DAILY_MARKET_SESSION_REPORT.md|.json`
  - `reports/daily/<YYYY-MM-DD>/evidence/**`
  - `reports/state/**` (permanent operational telemetry, not disposable audits)
- **Evidence ⇒ daily:** Every session directory with non-empty `evidence/` has non-empty `DAILY_MARKET_SESSION_REPORT.md` (stubs auto-generated where needed via `ensure_daily_stubs_for_evidence_sessions.py`).
- **Session scope:** Evidence directories exist only under `reports/daily/<date>/evidence/`.

**verify_report_layout: OK** at lockdown completion.
