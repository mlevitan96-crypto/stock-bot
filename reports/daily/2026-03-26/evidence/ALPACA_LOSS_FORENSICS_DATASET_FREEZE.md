# Alpaca Loss Forensics — Dataset Freeze

| Field | Value |
|---|---|
| Max trades cap | 2000 |
| Actual exits | 2000 |
| Join coverage | 67.55% |
| Exits missing trade_id | 0 |
| Duplicate trade_key in window | 3 |

## Partitions

- By exit day (UTC date from exit timestamp)
- By symbol
- By side (long/short)

**STATUS: HARD FAILURE** — see join blocker.
