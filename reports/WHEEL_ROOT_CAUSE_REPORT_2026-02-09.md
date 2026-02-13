# Wheel Strategy Root-Cause Report
**Generated:** 2026-02-09T22:50:57.232020+00:00Z
**Repo:** /root/stock-bot
**Lookback:** 1 days (since 2026-02-08)

## 1. Config and dispatch
- strategies.yaml: wheel.enabled = True
- strategies.context.strategy_context: importable

## 2. Wheel lifecycle events (logs/system_events.jsonl)
- wheel_run_started: 6
- wheel_order_submitted: 0
- wheel_order_filled: 0
- wheel_order_failed: 0
- wheel_run_failed: 0
- wheel_csp_skipped (by reason): {'no_spot': 60}

**Sample event lines (evidence):**
- `[wheel_run_started] {"timestamp": "2026-02-09T20:56:09.923278+00:00", "subsystem": "wheel", "event_type": "wheel_run_started", "strategy_id": "wheel", "reason": "ok", "ticker_count": 10}`
- `[wheel_run_started] {"timestamp": "2026-02-09T20:56:59.141947+00:00", "subsystem": "wheel", "event_type": "wheel_run_started", "strategy_id": "wheel", "reason": "ok", "ticker_count": 10}`
- `[wheel_run_started] {"timestamp": "2026-02-09T20:58:06.587482+00:00", "subsystem": "wheel", "event_type": "wheel_run_started", "strategy_id": "wheel", "reason": "ok", "ticker_count": 10}`
- `[wheel_regime_audit] {"timestamp": "2026-02-09T20:56:09.925839+00:00", "subsystem": "wheel", "event_type": "wheel_regime_audit", "strategy_id": "wheel", "regime_label": "chop", "modifier_only": true}`
- `[wheel_regime_audit] {"timestamp": "2026-02-09T20:56:59.142491+00:00", "subsystem": "wheel", "event_type": "wheel_regime_audit", "strategy_id": "wheel", "regime_label": "chop", "modifier_only": true}`
- `[wheel_regime_audit] {"timestamp": "2026-02-09T20:58:06.590229+00:00", "subsystem": "wheel", "event_type": "wheel_regime_audit", "strategy_id": "wheel", "regime_label": "chop", "modifier_only": true}`
- `[wheel_csp_skipped] {"timestamp": "2026-02-09T21:00:10.281864+00:00", "subsystem": "wheel", "event_type": "wheel_csp_skipped", "strategy_id": "wheel", "symbol": "KO", "reason": "no_spot"}`
- `[wheel_csp_skipped] {"timestamp": "2026-02-09T21:00:10.281982+00:00", "subsystem": "wheel", "event_type": "wheel_csp_skipped", "strategy_id": "wheel", "symbol": "WMT", "reason": "no_spot"}`
- `[wheel_csp_skipped] {"timestamp": "2026-02-09T21:00:10.282068+00:00", "subsystem": "wheel", "event_type": "wheel_csp_skipped", "strategy_id": "wheel", "symbol": "XOM", "reason": "no_spot"}`

**OUTCOME B: Wheel RUNNING but ALWAYS SKIPPING**
- **Evidence:** wheel_run_started > 0 but wheel_order_submitted == 0.
- **Skip reasons (ranked):**
  - no_spot: 60
- **Code path:** strategies/wheel_strategy.py _run_csp_phase() — skips per ticker for: earnings_window, iv_rank, no_spot, no_contracts_in_range, capital_limit, per_position_limit, insufficient_buying_power, existing_order, max_positions_reached.
- **Fix:** Address top skip reason: e.g. no_contracts_in_range → relax DTE or check Alpaca options API; no_spot → quote API; capital/buying_power → account size.