# Displacement Counterfactual Lab

> **No data:** `displacement.jsonl` contained no `no_candidates_found` rows.

- **Generated (UTC):** `20260425T190142Z`
- **Root:** `C:\Dev\stock-bot`
- **Displacement log:** `C:\Dev\stock-bot\logs\displacement.jsonl`
- **Run log:** `C:\Dev\stock-bot\logs\run.jsonl`
- **Join:** `no_candidates_found` ↔ `trade_intent` blocked `max_positions_reached` within **±180s** and **|Δscore| ≤ 0.05**.
- **Rules attributed:** `in_cooldown, too_young` on `position_details.fail_reason`.
- **Pricing:** local `research_bars` / `price_bars` **1Day** `c` if present; else Alpaca Data API (unless `--skip-api`).

## Summary

| Metric | Value |
|--------|-------|
| `no_candidates_found` events | **0** |
| Matched to a blocked capacity `trade_intent` | **0** |
| Incumbent rows (`too_young` / `in_cooldown`) evaluated | **0** |
| Priced swap pairs (1d) | **0** |
| **Total opportunity cost** (Σ max(0, swap_edge_1d)) | **0.000000** |
| **Total opportunity cost** (Σ max(0, swap_edge_5d)) | **0.000000** |
| Mean swap edge 1d (where priced) | **n/a** |
| Mean candidate 1d fwd (long proxy) | **n/a** |
| Mean incumbent 1d fwd (long proxy) | **n/a** |

## Definitions

- **Swap edge (1d):** `candidate_fwd_1d - incumbent_fwd_1d` using the same calendar anchor bar.
- **Missed profit (row):** `max(0, swap_edge_1d)` — positive edge foregone by not rotating when the gate was `too_young` / `in_cooldown`.
- **Incumbent entry proxy:** daily **close** at anchor (last 1Day bar ≤ event `ts`) when `position_details` lacks a fill price.

- **CSV:** `C:\Dev\stock-bot\reports\Gemini\displacement_cost_20260425T190142Z.csv`
