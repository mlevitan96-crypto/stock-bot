# Real Trades Board Diagnostic (Multi-Model)

Generated: 2026-03-02T16:28:48.811005+00:00

---

# Prosecutor (Adversarial)

## Claim
Insufficient run.jsonl data or composite disabled. Enable composite (cache with symbols) and run at least one cycle.

## Verdict
**Adversarial:** Real trades are blocked either at composite (0 clusters) or at a post-composite gate (UW defer, expectancy score floor). Fix: raise scores or relax UW/expectancy for paper.

# Defender (Alternate / Fixes)

## What is already fixed
- **Freshness:** FRESHNESS_HALF_LIFE_MINUTES = 180 (was 15) so scores decay slower.
- **Conviction default:** Missing conviction now 0.5 in composite core so flow component contributes.
- **Execution path:** Inject test proved that with a passing cluster, orders are placed (SPY filled).

## What still blocks real trades
- **UW root-cause data:** `apply_uw_to_score` loads `board/eod/out/<date>/uw_root_cause.json`. When missing or no candidate for symbol, the code defers or penalizes → score drops or candidate skipped. On paper, set **UW_MISSING_INPUT_MODE=passthrough** so score is preserved when no board data.

## Verdict
**Defender:** Apply passthrough for paper; turn off inject test; confirm cache is populated. Then re-run one cycle and check clusters/orders.

# SRE (Checklist)

| Check | Status |
|-------|--------|
| Freeze (governor_freezes.json) | PASS |
| Kill switch | PASS |
| Armed (paper URL) | BLOCK |
| UW cache exists | PASS |
| Cache symbol count | 53 |
| INJECT_SIGNAL_TEST | (unset) |
| UW_MISSING_INPUT_MODE | reject |
| MIN_EXEC_SCORE (env) | (default 2.5) |
| UW root_cause latest (board/eod/out) | exists |

# Board Verdict

## Immediate actions (to get real trades)

1. **Set on droplet (e.g. in .env or systemd Environment):**
   - `UW_MISSING_INPUT_MODE=passthrough`  (preserve score when no UW root-cause data)
   - `INJECT_SIGNAL_TEST=0`  or remove it (so only real signals trade)
2. **Restart the bot:** `systemctl restart stock-bot` (or equivalent).
3. **After one cycle, verify:**
   - `tail -1 logs/run.jsonl` → clusters and orders; if clusters > 0 and orders > 0, real trade path is working.
   - If clusters still 0, run scoring audit: distribution of composite scores per symbol. Optionally set **ENTRY_THRESHOLD_BASE=2.5** (env) to allow more symbols through the composite gate (default 2.7).

## References
- Trade logic trace: reports/audit/TRADE_LOGIC_SIGNAL_TO_EXECUTION_TRACE.md
- All gates: reports/audit/ALL_GATES_CHECKLIST.md
- Dashboard P&L / symbol universe: reports/audit/DASHBOARD_PNL_AND_SYMBOL_UNIVERSE.md
