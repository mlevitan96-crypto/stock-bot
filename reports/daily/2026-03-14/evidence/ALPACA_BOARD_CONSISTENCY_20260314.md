# ALPACA — Board consistency check (Phase 4)

**Timestamp:** 20260314

## Checks

| Check | Value | Expected | Status |
|-------|-------|----------|--------|
| trades_total (board / freeze) | None / None | — | OK if consistent |
| TRADES_FROZEN.csv data rows | 1999 | = exit_attribution last N | CHECK |
| final_exits_count | None | = closed trades in exit_attribution | OK |
| Join coverage (entry) | None% | Phase 2 | N/A |
| Join coverage (exit) | None% | Phase 2 | N/A |

## Blockers

Blockers (if any) are in `reports/audit/GOVERNANCE_BLOCKER_*.md` or `ALPACA_JOIN_INTEGRITY_BLOCKER_*.md`. Consistency with observed data: board uses same TRADES_FROZEN and INPUT_FREEZE as this audit.

## Evidence

- **Dataset dir (droplet):** `/root/stock-bot/reports/alpaca_edge_2000_20260317_1732`
- **INPUT_FREEZE excerpt:**
```

```
