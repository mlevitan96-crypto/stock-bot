# SRE proof — telemetry chain emitters configured in prod

## Restart

`sudo systemctl restart stock-bot` after `git pull` to `1d80fd43`.

## `system_events.jsonl` (production)

Filtered line from `/root/stock-bot/logs/system_events.jsonl`:

```json
{"subsystem": "telemetry_chain", "event_type": "startup_banner", "severity": "INFO", "details": {
  "phase2_telemetry_enabled": true,
  "strict_runlog_telemetry_enabled": true,
  "strict_runlog_effective": true,
  "run_jsonl_abspath": "/root/stock-bot/logs/run.jsonl"
}}
```

**Interpretation:** At process start, strict runlog telemetry is **effective** and the bot logs the canonical `run.jsonl` path. This is additive instrumentation only (`log_system_event`).

## Journal note

`journalctl -u stock-bot` (tail in `chain_fix_mission/phase0_journal_stock_bot_tail600.txt`) also showed an `evaluate_exits` exception after restart; see `ALPACA_CHAIN_FIX_CONTEXT.md` and the `opens_info_not_dict` guard commit for mitigation.
