# Droplet Data Authority — SAFE_TO_APPLY PR Checklist

**Scope:** Institutionalize droplet-only data authority: Memory Bank rules, shared guard in analysis/replay/backtest/governance entrypoints, dashboard last-run visibility, board sign-off. No live trading logic changes.

---

## Deliverables

| Item | Path |
|------|------|
| Memory Bank: Droplet Data Authority | memory_bank/TELEMETRY_STANDARD.md (section "Droplet Data Authority (Non-Negotiable)") |
| Data Review checklist | memory_bank/TELEMETRY_ADDING_CHECKLIST.md (section "Data Review & Analysis Requirements") |
| Changelog | memory_bank/TELEMETRY_CHANGELOG.md (entry 2026-03-03 — Droplet Data Authority) |
| Shared guard | src/governance/droplet_authority.py |
| Enforcement | scripts/trade_visibility_review.py, scripts/replay/run_direction_replay_30d.py, scripts/backtest_governance_check.py, scripts/governance/run_board_review_on_droplet_data.py, scripts/governance/run_governance_48h_report_on_droplet.py |
| Droplet runner (flags) | scripts/replay/run_direction_replay_30d_on_droplet.py (DROPLET_RUN=1, --droplet-run, --deployed-commit) |
| Dashboard: last droplet run | /api/telemetry_health, /api/governance/status (last_droplet_analysis); Telemetry Health tab: banner or "Last droplet analysis run" card |
| Board review | reports/board/TELEMETRY_STANDARD_BOARD_REVIEW.md (Droplet Data Authority sign-off) |

---

## Gates (must pass)

- [ ] **Local analysis fails without droplet / dry-run:** Running any guarded script locally without `--allow-local-dry-run` exits non-zero with message "This analysis must be run on the droplet. Local results are invalid." (Verified 2026-03-03.)
- [ ] **Dry-run allowed:** Running with `--allow-local-dry-run` prints WARNING and completes (e.g. `python scripts/trade_visibility_review.py --allow-local-dry-run --since-hours 24`).
- [ ] **Dashboard:** Telemetry Health tab shows either "No authoritative data review has been run." or "Last droplet analysis run" (script, deployed_commit, run_ts).
- [ ] **No trading logic changed:** main.py and order/exit/sizing paths unchanged.

---

## Proof: local analysis fails without droplet flags

Run (from repo root, no `DROPLET_RUN` set, no `--allow-local-dry-run`):

```bash
python scripts/trade_visibility_review.py --since-hours 24
```

**Expected:** Exit code 1; stderr contains "ERROR: This analysis must be run on the droplet. Local results are invalid."

Optional (same expectation):

```bash
python scripts/replay/run_direction_replay_30d.py --days 7
python scripts/backtest_governance_check.py --backtest-dir reports/backtests/dummy --governance-out reports/governance/dummy
```

---

## Runbook / PR checklist

- **Before merge:** Run proof commands above; confirm exit 1 and error message. Run `python scripts/trade_visibility_review.py --allow-local-dry-run --since-hours 24` and confirm it completes with WARNING.
- **After deploy (droplet):** When running analysis on droplet, set `DROPLET_RUN=1` and pass `--droplet-run --deployed-commit $(git rev-parse HEAD)` so `state/last_droplet_analysis.json` is written and dashboard shows last run.

---

## Rollback

Revert: Memory Bank edits (TELEMETRY_STANDARD.md, TELEMETRY_ADDING_CHECKLIST.md, TELEMETRY_CHANGELOG.md), src/governance/droplet_authority.py, guard wiring in scripts (trade_visibility_review, run_direction_replay_30d, backtest_governance_check, run_board_review_on_droplet_data, run_governance_48h_report_on_droplet), run_direction_replay_30d_on_droplet.py (DROPLET_RUN/--droplet-run/--deployed-commit), dashboard.py (last_droplet_analysis in API + Telemetry Health UI), reports/board/TELEMETRY_STANDARD_BOARD_REVIEW.md (Droplet Data Authority sign-off). No trading logic to revert.

---

*Ref: memory_bank/TELEMETRY_STANDARD.md, memory_bank/TELEMETRY_ADDING_CHECKLIST.md, src/governance/droplet_authority.py, reports/board/TELEMETRY_STANDARD_BOARD_REVIEW.md.*
