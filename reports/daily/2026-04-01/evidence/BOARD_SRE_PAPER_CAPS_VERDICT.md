# BOARD_SRE — Paper caps

- **IO:** `--log-cap-decisions` appends JSONL; rotate `logs/paper_cap_decisions.jsonl` like other logs.
- **CPU:** Single-pass replay O(n) on window rows.
- **Silent disable:** If `PAPER_CAPS_ENABLED` not set to `1`, caps branch still forces enabled inside evaluation for the second pass only via env injection in script — document in runplan.
