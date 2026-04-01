# Board — Quant officer verdict

- **Causal attribution:** Restoring `entry_decision_made`, `exit_intent`, `canonical_trade_id_resolved`, unified entry mirrors, and order rows **re-enables** strict join checks for the historical cohort; without this, PnL / learning packets that depend on strict completeness were not certifiable.
- **Backfill bias:** Rows are **synthetic strict repairs** derived from `exit_attribution.jsonl` (deterministic builder). Forward trades should rely on live emitters + `startup_banner` proof; backfill is explicitly additive and idempotent per `trade_id`.
- **Late-binding:** Not the primary failure mode here; resolver events remain tied to `mark_open` when intent/fill keys diverge; backfill supplies canonical edges where live stream was empty.
