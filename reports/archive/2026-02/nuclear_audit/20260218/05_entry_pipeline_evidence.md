# 05 Entry pipeline evidence

## From logs/gate.jsonl (parsed)

- **candidate_count (considered last cycle):** 33
- **selected_count (orders last cycle):** 0

## Last cycle_summary entries (up to 5)
```
[
  {
    "considered": 0,
    "orders": 0,
    "gate_counts": {}
  },
  {
    "considered": 0,
    "orders": 0,
    "gate_counts": {}
  },
  {
    "considered": 0,
    "orders": 0,
    "gate_counts": {}
  },
  {
    "considered": 0,
    "orders": 0,
    "gate_counts": {}
  },
  {
    "considered": 0,
    "orders": 0,
    "gate_counts": {}
  }
]
```

## Aggregated gate_counts (top 20)
```
{
  "expectancy_blocked:score_floor_breach": 495,
  "score_below_min": 277
}
```

## Top rejection reasons (msg != cycle_summary)
```
{
  "expectancy_blocked": 483,
  "score_below_min": 277
}
```