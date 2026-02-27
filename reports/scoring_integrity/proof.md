# Scoring Pipeline Integrity — Proof (Droplet)

**Fix deployed:** Expectancy gate now uses same score as min-score gate (adjusted score).

## Commit on droplet
`020e360 Fix: scoring pipeline integrity`

## Systemd health
- Paper run via tmux (stock_bot_paper_run); main systemd service status not required for this run.

## Post-fix gate summary (recent cycles)
- considered=17, gate_counts={'score_below_min': 17}, orders=0
- considered=13, gate_counts={'expectancy_blocked:score_floor_breach': 13}, orders=0
- considered=14, gate_counts={'expectancy_blocked:score_floor_breach': 14}, orders=0
- considered=14, gate_counts={'expectancy_blocked:score_floor_breach': 14}, orders=0
- considered=13, gate_counts={'expectancy_blocked:score_floor_breach': 13}, orders=0

## Verdict
STILL BLOCKED (dominant gate: expectancy_blocked:score_floor_breach)
