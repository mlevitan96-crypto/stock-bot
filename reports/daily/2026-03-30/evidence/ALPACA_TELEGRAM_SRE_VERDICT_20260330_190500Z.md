# ALPACA_TELEGRAM_SRE_VERDICT_20260330_190500Z

**Verdict: OK (with operator follow-ups)**

## Scheduling

- `alpaca-telegram-integrity.timer` — 10-minute cadence; `OnUnitActiveSec=10min`; `Persistent=true`. **SRE note:** heavy warehouse subprocess throttled to RTH and every N cycles to limit CPU/API load.

## Paths

- Reads: `logs/exit_attribution.jsonl`, `reports/ALPACA_TRUTH_WAREHOUSE_COVERAGE_*.md`, strict gate code under `telemetry/`.
- Writes: `state/alpaca_*`, `logs/alpaca_telegram_integrity.log` (append-only, bounded line per run).
- Env: dual `EnvironmentFile` (`.env` + `.alpaca_env`) on unit — reduces “Telegram only in shell” drift.

## Failure modes

- Telegram failure does not raise (existing helper logs to `TELEGRAM_NOTIFICATION_LOG.md`).
- Warehouse timeout returns non-zero captured in JSON out; coverage may go stale → integrity alert fires (intended).
- **Single point of failure:** if `venv` or Python missing, unit fails — not auto-fixed (ambiguous).

## Log rotation

- Append log can grow; rely on host logrotate or periodic truncate (not implemented — operator action if multi-GB).

## postclose service

- Self-heal may `try-restart` failed `alpaca-postclose-deepdive.service` only (read-only trading).
