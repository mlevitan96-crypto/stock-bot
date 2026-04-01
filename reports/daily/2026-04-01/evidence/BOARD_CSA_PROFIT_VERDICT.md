# BOARD_CSA_PROFIT_VERDICT

## Evidence anchors (droplet run 2026-04-01Z)

- **432** closed exits in `exit_attribution.jsonl`; **LONG** expectancy **+0.103** USD vs **SHORT** **−0.115** (tail = full file).
- Only **63** exits matched a pre-entry `score_snapshot` within 600s — **join sparsity** limits signal claims.
- **`signal_context.jsonl` row count 0** — cannot certify “full UW subfield granularity” for this dataset; contribution analysis is **score_snapshot components only**.

## Causal validity

- **Mostly associational.** Median splits on snapshots, regime/direction buckets — **not** IV or randomized.
- **Adversarial:** Positive sum PnL in-sample does **not** imply structural edge after costs not modeled here or out-of-sample drift.

## Integrity

- Read-only campaign script; no log mutation. Exit tail capped by `--max-exit-rows` (here: full file ≤ limit).

## Governance

- Action plan is **shadow-first**; production gate changes would violate mission constraints.
- Any “flip short bias” narrative is **rejected for live change** without shadow — LONG outperformed SHORT in this slice only.

