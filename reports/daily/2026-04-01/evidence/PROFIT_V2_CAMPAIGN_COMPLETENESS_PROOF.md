# PROFIT_V2_CAMPAIGN_COMPLETENESS_PROOF

End state after Phase 8 re-run on droplet (`run_alpaca_profit_discovery_campaign.py` exit **0**).

## Read-only profit discovery (Phase 0–10 base)

| Artifact | Status |
|----------|--------|
| `ALPACA_PROFIT_INTEL_DATA_INVENTORY.md` | Regenerated under this evidence dir |
| `ALPACA_PROFIT_DISCOVERY_META.json` | Present |
| Directional / signal / exit / blocked memos (`ALPACA_*.md`) | Present per prior campaign layout |

## V2 extensions (this mission)

| Gate | Evidence |
|------|----------|
| Bars sink non-empty | `alpaca_bars.jsonl` **49** lines, **~8.2 MB** |
| Exit timing joins complete | `PROFIT_V2_EXIT_TIMING_COUNTERFACTUALS.json` → `rows_with_full_horizons` **432** / **432** |
| UW uplift bootstrap | `PROFIT_V2_SIGNAL_UW_UPLIFT.json` — **63** matched pairs, per-component bootstrap block |
| Blocked reason classification | `PROFIT_V2_BLOCKED_MISSED_CAUSAL.json` — **8669** tail rows from `state/blocked_trades.jsonl`, top reasons enumerated |
| Known remaining gap | `logs/signal_context.jsonl` still **0** rows; **join substitute** = `score_snapshot` (documented) |

## Empty-sink hard gate

- **Bars:** **PASS** (non-empty).  
- **`signal_context`:** **FAIL** smoke test; **mitigated** by recovery path (A) — documented, no false claim of completeness for that file.

## Live trading

- Campaign + V2 scripts did **not** require **stock-bot restart**; see `PROFIT_V2_BASELINE_CONTEXT.md`.
