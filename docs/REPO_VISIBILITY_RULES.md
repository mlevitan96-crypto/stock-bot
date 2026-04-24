# Repository visibility rules (reports)

Prefer the focused doc **`docs/REPO_REPORT_VISIBILITY_RULES.md`** for the report sidebar contract; this file remains as a short alias.

## Sidebar / operator visibility

Only these paths are treated as **first-class** for human operators:

```
reports/daily/<YYYY-MM-DD>/DAILY_MARKET_SESSION_REPORT.md
reports/daily/<YYYY-MM-DD>/DAILY_MARKET_SESSION_REPORT.json
```

## Evidence (non–operator-visible)

```
reports/daily/<YYYY-MM-DD>/evidence/**
```

All other paths under `reports/` (including `reports/audit/`, top-level `reports/*.md`, etc.) are **legacy or disposable evidence** and MUST NOT be added by new automation. Prefer `evidence/` for any new artifact.

## Pruning

- Canonical `DAILY_*`: retained indefinitely (by policy; not deleted by retention job).
- `evidence/`: retained **N** calendar days (default **3**) after session date, then deleted by `scripts/maintenance/prune_stale_reports.py`.
- Legacy `reports/**` outside `reports/daily/`: deleted when file mtime age exceeds **N** days.

## Enforcement

- CI: `.github/workflows/report_layout.yml` runs `scripts/maintenance/verify_report_layout.py` on pull requests.
- Local: `make verify_report_layout` (optional).
