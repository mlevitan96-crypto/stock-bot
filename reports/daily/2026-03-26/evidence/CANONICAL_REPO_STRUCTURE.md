# Canonical Repo Structure

**Truth root for repo cleanup.** Generated 2026-02-27. See also CANONICAL_PATHS.json.

## Top-level layout

```
stock-bot/
├── main.py                    # Core trading engine
├── dashboard.py               # Flask dashboard (port 5000)
├── deploy_supervisor.py       # Orchestrates dashboard + main
├── historical_replay_engine.py # Replay backtest
├── droplet_client.py          # SSH/droplet operations
├── executive_summary_generator.py
├── config/                    # Single source of truth: config/registry.py
├── data/                      # Runtime caches (uw_flow_cache.json, etc.)
├── state/                     # Bot state (heartbeat, positions, regime)
├── logs/                      # attribution.jsonl, exit_attribution.jsonl, etc.
├── board/eod/                 # EOD and cron scripts
├── scripts/
│   ├── governance/           # Governance loop, board review, recommendation
│   ├── analysis/             # Effectiveness, expectancy gate diagnostic
│   └── replay/               # Replay campaigns
├── src/                       # Exit attribution, infra, intel
├── utils/                     # state_io, system_events, signal_normalization
├── strategies/                # equity_strategy
├── structural_intelligence/   # market_context_v2, regime_posture, symbol_risk
├── telemetry/                 # Score telemetry, exit_attribution_enhancer
├── validation/                # scenarios/test_*.py
├── reports/                   # Outputs (governance, effectiveness, signal_review, etc.)
├── docs/                      # Contracts, runbooks
├── configs/                   # backtest_config, param_grid
└── archive/                   # Legacy (do not use for production paths)
```

## What is canonical

- **Paths**: All path truth is in `config/registry.py` (Directories, CacheFiles, StateFiles, LogFiles). Dashboard uses `_DASHBOARD_ROOT` + same relative paths.
- **Entry points**: main.py, dashboard.py, historical_replay_engine.py, deploy_supervisor.py; EOD: board/eod/run_stock_quant_officer_eod.py and run_eod_on_droplet.py.
- **Governance**: reports/equity_governance/, reports/effectiveness_baseline_blame (or effectiveness_*), state/equity_governance_loop_state.json.
- **Replay**: historical_replay_engine.py; scripts under scripts/replay/.
- **Deploy**: deploy_supervisor.py, droplet_client.py, board/eod/deploy_on_droplet.sh, scripts/governance/deploy_and_start_governance_loop_on_droplet.py.
- **Exit attribution schema**: `logs/exit_attribution.jsonl` records use `attribution_components` with `signal_id` values that all start with the **`exit_`** prefix (e.g. exit_flow_deterioration). Enforced by src/exit/exit_score_v2.py and validation/scenarios/test_exit_attribution_phase4.py.

## What is not canonical

- **archive/**: Legacy scripts; do not reference from production code.
- **Root one-off scripts** (RUN_*_NOW.py, FIX_*.py, etc.): Manual/diagnostic only.
- **Reports outside** reports/equity_governance, reports/effectiveness_*, reports/signal_review, reports/governance, reports/_dashboard: One-off or historical; can be archived.
