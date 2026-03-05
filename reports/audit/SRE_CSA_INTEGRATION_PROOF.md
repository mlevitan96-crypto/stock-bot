# SRE–CSA integration proof

**Generated (UTC):** 2026-03-05T18:01:36.828170+00:00

## Deployed commit

f1bf02b64996

## Health

- /api/telemetry_health: 200
- /api/learning_readiness: 200

## SRE scan

- SRE scan ran: True
- SRE status: ANOMALIES_DETECTED

## Sample SRE events (if any)

- `sre_0d5949758bde` RATE_ANOMALY exit_rate_per_min (confidence=MED)
- `sre_234f68a292d5` RATE_ANOMALY blocked_trades_per_min (confidence=HIGH)
- `sre_c3018e538d7d` SILENCE_ANOMALY exit_count (confidence=MED)

## CSA verdict referencing SRE

verdict=HOLD confidence=MED sre_high_impact_block=True

## Scheduler

SRE cron every 10 min active: True
