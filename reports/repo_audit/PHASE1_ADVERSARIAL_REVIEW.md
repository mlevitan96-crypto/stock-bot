# Phase 1 — Adversarial Review Notes

**Generated:** 2026-02-27

## Validation of Classifications

- **CANONICAL**: Derived from `config/registry.py`, `dashboard.py` (reports/equity_governance, reports/effectiveness_*), `scripts/governance/*`, `scripts/analysis/run_effectiveness_reports.py`, and MEMORY_BANK entry points. Cross-check: dashboard `/api/governance/status` and closed trades paths match CANONICAL_PATHS.json.
- **STALE/UNREFERENCED**: Conservative; many report dirs are "unreferenced" by code but kept for human review. Recommendation: archive, do not delete.
- **DEAD_CODE_MAP**: Entry points and imported modules excluded. Root-level one-off scripts (RUN_*_NOW.py, FIX_*.py) are candidates only; confirm no cron or manual runbook before removal.
- **archive/**: Classified as LEGACY/UNUSED; no production code imports from archive. Safe to keep as-is or move to reports/archive/ after PR.

## Gaps / Unknowns

1. **File age (90+ days)**: Not computed (would require `git log --follow --format=%cI -- <path>`). STALE currently means "not referenced by code" not "old by date".
2. **moltbot/**: Unclear if any workflow invokes it; marked UNKNOWN.
3. **self_healing/**, **api_management/**: Need grep confirmation that main.py or dashboard uses them.

## Multi-Model Review Checklist

- [x] FILE_INVENTORY aligns with CANONICAL_PATHS and DASHBOARD_ENDPOINT_MAP.
- [x] DEAD_CODE_MAP excludes all entry points and imported core.
- [x] No canonical path removed or marked DEAD.
- [ ] Second reviewer: confirm archive/ and root one-off scripts are safe to archive.
