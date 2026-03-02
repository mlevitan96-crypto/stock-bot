# Trades Working Verification (2026-03-02)

## Summary

After pushing the root-cause fix (preserve composite score when UW quality low) and deploying to the droplet:

- **Pushed:** commit `79b7b43` — fix: preserve composite score when UW quality low (root cause); UW daemon on deploy; blocked-trades script
- **Deployed:** fetch+reset origin/main, then DropletClient().deploy() (pytest, restart stock-bot, UW daemon)
- **.env:** `UW_MISSING_INPUT_MODE=passthrough` set on droplet; stock-bot restarted

## Verification

1. **Droplet has fix:** `grep uw_low_quality_preserved_strong_composite board/eod/live_entry_adjustments.py` returns matches (commit 79b7b43).
2. **Trade intents entering:** In the last 300 lines of `logs/run.jsonl`, **17** records have `event_type=trade_intent` and `decision_outcome=entered` with scores 4.6–4.8 (e.g. SLB 4.765, INTC 4.671, NVDA 4.62), `blocked_reason=null`, and `final_decision.outcome=entered`, `all_gates_passed`.
3. **No more score=0.172 kill:** New flow preserves composite score; intents show real composite scores (4.x), not 0.172.
4. **Cache:** UW cache was fresh (0/53 stale) after daemon start; composite pass 14/15 symbols ≥ 2.7.

## Evidence (run.jsonl tail)

- `trade_intent` events with `decision_outcome: "entered"`, `blocked_reason: null`, `score: 4.765` (SLB), `4.671` (INTC), `4.621` (NVDA).
- `intelligence_trace.final_decision.outcome: "entered"`, `primary_reason: "all_gates_passed"`.
- All gates in trace: score_gate, capacity_gate, risk_gate, momentum_gate, directional_gate passed.

## Scripts added

- `scripts/confirm_trades_on_droplet.py` — counts trade_intent "entered" in last 300 lines and prints latest complete cycle.
- `scripts/verify_droplet_fix.py` — confirms droplet commit and presence of preserve_strong_composite fix.
- `scripts/fetch_recent_blocked_trades_from_droplet.py` — last N blocked_trades + UW daemon status (Unicode-safe).

## Status

**Trades are working:** composite-approved candidates keep their score into the expectancy gate; intents are logged as "entered" with full intelligence trace. The pipeline is effective end-to-end.
