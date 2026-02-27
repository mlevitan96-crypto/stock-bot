# SRE — Freshness, heartbeat, EOD, dashboard, systemd

**Persona:** SRE. **Intent:** Enforce freshness/heartbeat, EOD wiring, dashboard truth contract, systemd paths, file permissions.

## 1. Heartbeat and freshness
- **meta/last_write_heartbeat.json:** Updated on every CTR write (any stream). Schema: `{"ts_iso": "...", "ts_epoch": float, "stream": "<rel>"}` (or last stream that wrote). Single file; overwrite each time.
- **health/freshness.json:** Per-stream: `stream_id`, `last_ts`, `last_mtime`, `expected_max_age_sec`. Updated when that stream is written. EOD can require all required streams’ `last_mtime` within threshold (or FAIL).
- **Expected max age:** Document per stream (e.g. gate 300s, exit 600s, telemetry 600s). EOD script must have configurable thresholds.

## 2. EOD wiring
- EOD script (e.g. `scripts/run_eod_confirmation.sh`) must run dashboard truth audit. When CTR is authoritative (Phase 2+), contract must point to CTR paths; EOD must validate CTR heartbeat and freshness and **fail** if stale or missing (no silent inference).
- Failure mode: Exit non-zero, log clear message, so cron/monitoring can alert.

## 3. Dashboard truth contract
- Contract file (e.g. `/tmp/dashboard_contract.json` or repo copy) lists panels and their source paths. Phase 1: sources remain legacy. Phase 2: update contract to CTR paths (e.g. `truth/gates/expectancy.jsonl`). Contract must be single source of truth for “where to read”; no hardcoding in dashboard code without going through contract or config.

## 4. systemd paths
- **WorkingDirectory:** Must be repo root (e.g. `/root/stock-bot`) so legacy relative paths resolve correctly.
- **EnvironmentFile:** If used, ensure `TRUTH_ROUTER_ENABLED`, `TRUTH_ROUTER_MIRROR_LEGACY`, `STOCKBOT_TRUTH_ROOT` are documented and optional (defaults applied in code).
- **ReadWritePaths:** If unit uses namespace restriction, add `/var/lib/stock-bot` (or STOCKBOT_TRUTH_ROOT) so CTR is writable.

## 5. File permissions
- CTR directory: Recommended 0755; files 0644. Process user (e.g. root or stockbot) must own CTR root so heartbeat and stream files can be created.

## 6. Acceptance
- G2: CTR streams written and fresh during runtime (dashboard truth audit PASS when contract points to CTR).
- G3: EOD enforces CTR freshness + heartbeat; fails correctly when stale.
