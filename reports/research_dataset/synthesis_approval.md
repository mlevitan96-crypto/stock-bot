# Research Table — Synthesis Approval (Phase 3)

**MODEL D:** All models contributed. Design approved with the following constraints:

- **Dataset range:** Build from available logs/score_snapshot.jsonl and state/blocked_trades.jsonl plus bars (Alpaca or data/bars). If multi-year bars exist, extend up to --years; otherwise document actual range in build_log.md.
- **Schema:** Canonical 22 components + group_sums + composite pre/post + macro horizons + labels as in multi_model_design.md.
- **Integrity:** Phase 4 audit must pass (schema parity, missingness, no leakage) before baseline edge tests.
- **Proceed** to implement build_research_table.py and run on droplet.
