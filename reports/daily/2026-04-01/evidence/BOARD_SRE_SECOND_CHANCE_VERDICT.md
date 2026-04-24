# BOARD_SRE — Second-chance displacement (paper)

## Operational risk?

**Low.** Additive JSONL; worker is read-only to broker except `list_positions`.

## Timing / queue failure modes?

- Stale queue if worker not run → items sit until processed; **fail closed** on API errors (blocked).
- Clock skew: uses host epoch for `due_epoch`.

## Disk / log growth?

- Bounded by displacement_blocked rate × 2 lines per event if both scheduled+result logged; rotate `logs/second_chance_displacement.jsonl` like other logs.
