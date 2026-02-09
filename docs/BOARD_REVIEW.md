# Daily Board Review Workflow

## Overview
The Daily Board Review runs after market close as part of the existing cron-driven EOD pipeline.  
It now produces a single markdown file and a single JSON file per day, stored under:

- `board/eod/out/YYYY-MM-DD/daily_board_review.md`
- `board/eod/out/YYYY-MM-DD/daily_board_review.json`

## Data Flow
1. Trading system runs and generates EOD + board artifacts into `board/eod/out/`.
2. Cron (or manual run) executes:
   - Existing EOD + board review script(s).
   - `python scripts/run_multi_day_analysis.py` (V3: multi-day analysis)
   - `python scripts/board_daily_packager.py`
3. The packager:
   - Creates `board/eod/out/YYYY-MM-DD/`.
   - Combines all top-level `.md` files into `daily_board_review.md`.
   - Combines all top-level `.json` files into `daily_board_review.json`.
   - Includes `multi_day_analysis.json` and `.md` if present (V3).
4. Git is updated and pushed; the droplet pulls latest as usual.

## Multi-Day Analysis (V3)
After the daily EOD pipeline, the multi-day analysis module runs automatically:
- Computes rolling 3-day, 5-day, 7-day windows
- Outputs: `board/eod/out/YYYY-MM-DD/multi_day_analysis.json` and `.md`
- Metrics: regime persistence/transition, volatility trend, sector rotation, attribution vs exit, churn, hold-time, exit-reason distribution, blocked trades, displacement sensitivity, capacity utilization, expectancy, MAE/MFE
- All agents incorporate multi-day trends in their analysis

## Multi-Agent AI Board
The AI Board is defined via `.cursor/agents/` and operates as:

- Exit Specialist
- Performance Auditor
- SRE and Audit Officer
- Market Context Analyst
- Promotion Officer
- Innovation Officer
- Regime Review Officer (V3)
- Board Synthesizer
- Customer Profit Advocate
- Board Review Orchestrator

The Board:
- Reviews EOD and replay artifacts.
- Produces a synthesized Board report.
- Is challenged by the Customer Profit Advocate.
- Produces a final customer-facing daily review.

## Triggers
- **Automatic (cron):** After EOD artifacts are generated, run:
  - `python scripts/board_daily_packager.py`
- **Manual Board Review:**
  - In Cursor, use either:
    - Natural language: "Run the Board Review on today's outputs."
    - Command: `/board-review`

## Interpretation Notes (Post-Remediation)

- **Regime:** Regime is a modifier only (sizing, filters); it never gates trading. Multi-day regime labels come from daily_universe_v2 `_meta.regime_label` (fallback NEUTRAL). See `docs/REGIME_DETECTION.md`.
- **Exit timing and hold-time:** Exit timing policy (min_hold_seconds, sensitivity mults) is applied via the governance shim; hold-floor skips are logged as `hold_floor_skipped`. Interpret hold-time and churn trends in multi-day analysis in that context. Use `scripts/exit_timing_diagnostic.py` for by-reason and by mode:strategy diagnostics.
- **Displacement and capacity:** See `docs/CAPACITY_AND_DISPLACEMENT.md`. Regime can influence policy but never fully block. Use `scripts/displacement_capacity_diagnostic.py` for blocked counts by reason and mode:strategy.
- **Attribution vs exit:** Use `scripts/attribution_exit_reconciliation.py` to compare attribution PnL vs exit_attribution PnL and explain gaps.

The Board should explicitly consider: regime health (non-UNKNOWN, modifier-only), exit timing health (hold-time/churn), displacement/capacity health (blocked counts), and attribution vs exit alignment.

## Testing
To test on today's outputs:
1. Ensure EOD + board artifacts exist in `board/eod/out/`.
2. Run: `python scripts/board_daily_packager.py`
3. In Cursor, open `board/eod/out/YYYY-MM-DD/daily_board_review.md`.
4. Ask: "Run the Board Review on this file and tell me what the Board recommends."
