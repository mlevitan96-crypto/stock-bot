# ACTION_CONTRACT — QUANT_CF_001

- **Type:** paper_extension
- **Owner:** QUANT
- **Change:** Re-run `run_blocked_why_pipeline.py` + merge-blocked bars fetch on a fixed cadence; no `main.py` threshold edits.
- **Scope/duration:** 30d rolling evidence windows; config frozen except bars date range.
- **Success metrics:** ['pnl_60m_expectancy displacement_blocked remains positive in new window', 'coverage rate for displacement_blocked rows stable or improves in BLOCKED_WHY_BARS_COVERAGE.json']
- **Kill criteria:** ['pnl_60m_expectancy displacement_blocked < 0 for two consecutive weekly rebuilds', 'coverage collapse >20% vs prior week without documented data outage']
- **Rollback:** Stop scheduled pipeline; archive evidence folder; no engine env changes required.
