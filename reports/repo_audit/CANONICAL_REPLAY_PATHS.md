# Canonical Replay Paths

**Replay engine and scripts — single source of truth.** Generated 2026-02-27.

## Entry point

- **historical_replay_engine.py** — Backtest using UW flow alerts and Alpaca historical data. Reads attribution/log context; does not overwrite production logs.

## Config / registry

- Replay uses `config.registry` (Directories, LogFiles, etc.) for paths. It does not define its own report paths for production; replay outputs may go to reports/ or local dirs per script.

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/replay/run_equity_replay_campaign.py` | Replay campaign orchestration |
| `scripts/replay/equity_entry_replay.py` | Entry replay; can consume joined trades or effectiveness dir |
| `scripts/replay/equity_signal_ablation_replay.py` | Signal ablation replay |

## Data read (no look-forward)

- Attribution and exit data from logs (per registry); Alpaca historical bars.
- Effectiveness dirs (e.g. effectiveness_aggregates + joined source) may be used as input to some replay scripts.

## Shell

- `scripts/CURSOR_DROPLET_EQUITY_GOVERNANCE_AUTOPILOT.sh` and similar may set REPLAY_OVERLAY_CONFIG; ensure any path there points to existing config.

Cleanup must not remove historical_replay_engine.py or scripts/replay/*.py. Any moved report dirs used as replay input must be updated in script args or docs.
