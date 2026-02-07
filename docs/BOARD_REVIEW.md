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
   - `python scripts/board_daily_packager.py`
3. The packager:
   - Creates `board/eod/out/YYYY-MM-DD/`.
   - Combines all top-level `.md` files into `daily_board_review.md`.
   - Combines all top-level `.json` files into `daily_board_review.json`.
4. Git is updated and pushed; the droplet pulls latest as usual.

## Multi-Agent AI Board
The AI Board is defined via `.cursor/agents/` and operates as:

- Exit Specialist
- Performance Auditor
- SRE and Audit Officer
- Market Context Analyst
- Promotion Officer
- Innovation Officer
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

## Testing
To test on today's outputs:
1. Ensure EOD + board artifacts exist in `board/eod/out/`.
2. Run: `python scripts/board_daily_packager.py`
3. In Cursor, open `board/eod/out/YYYY-MM-DD/daily_board_review.md`.
4. Ask: "Run the Board Review on this file and tell me what the Board recommends."
