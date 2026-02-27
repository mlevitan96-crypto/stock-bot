# Blocked-expectancy post-fix proof (droplet)

**Deployed:** MIN_EXEC_SCORE 3.0 → 2.5 (git reset --hard origin/main). Paper restarted with SCORE_SNAPSHOT_DEBUG=1.

## Confirmed commit on droplet
`4e45064 Config: adjust thresholds based on blocked-trade expectancy analysis`

## Post-change gate summary (recent cycles)

- considered=1, orders=0, gate_counts={'expectancy_blocked:score_floor_breach': 1}
- considered=14, orders=0, gate_counts={'score_below_min': 14}
- considered=13, orders=0, gate_counts={'expectancy_blocked:score_floor_breach': 13}

## Verdict
STILL BLOCKED by expectancy_blocked:score_floor_breach
