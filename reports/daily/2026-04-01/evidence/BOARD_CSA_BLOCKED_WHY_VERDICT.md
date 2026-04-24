# BOARD_CSA_BLOCKED_WHY_VERDICT

Mandatory questions (citations only):

1. **Did we satisfy WHY Levels 1–5 without gaps?**  
   **YES.** `BLOCKED_WHY_DIAGNOSIS.json` → `why_levels_1_to_5` enumerates L1–L5 with pointers to `BLOCKED_WHY_BARS_COVERAGE.json`, `BLOCKED_COUNTERFACTUAL_PNL_FULL.json`, `BLOCKED_GATE_SCORECARD.json`, `main.py` displacement path.

2. **Are any claims correlational but presented as causal?**  
   **YES — risk called out.** Counterfactual PnL uses **post-decision** bars; positive `pnl_60m` does **not** prove the trade would have been entered or filled at modeled prices. Artifacts label Variant A/B/C formulas in `BLOCKED_WHY_BARS_COVERAGE.json` → `formulas`.

3. **Are we weakening integrity or creating silent failure modes?**  
   **NO change to live execution path** in this mission (`BLOCKED_WHY_CONTEXT.md` live-impact note). New scripts are audit-only; bars fetch is read-only HTTP.

4. **Are we creating multiple “truth sinks” without canonicalization?**  
   **NO new canonical sink.** Blocked universe remains `state/blocked_trades.jsonl`; counterfactual outputs are **derived** JSON under `reports/daily/2026-04-01/evidence/`.

5. **What would falsify the primary recognition failure claim?**  
   **Evidence that would falsify:** (a) `evaluate_displacement` returns `policy_allowed=True` for rows logged `displacement_blocked` (contradicts `main.py` ~9529–9530 guard), or (b) recomputation shows majority of `displacement_blocked` rows lack `policy_reason` / `displaced_symbol` alignment with code path, or (c) bar timestamps are misaligned so `pnl_60m` replay is invalid (would show in `BLOCKED_WHY_BARS_COVERAGE.json` coverage collapse).

**STOP:** **not** issued — no `BOARD_STOP_BLOCKER.md`.
