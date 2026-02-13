# Wheel Strategy Root-Cause Report
**Generated:** 2026-02-10T16:40:17.881062+00:00Z
**Repo:** /root/stock-bot
**Lookback:** 7 days (since 2026-02-03)

## 1. Config and dispatch
- strategies.yaml: wheel.enabled = True
- strategies.context.strategy_context: importable

## 2. Wheel lifecycle events (logs/system_events.jsonl)
- wheel_run_started: 56
- wheel_order_submitted: 1
- wheel_order_filled: 1
- wheel_order_failed: 0
- wheel_run_failed: 0
- wheel_csp_skipped (by reason): {'no_spot': 672, 'capital_limit': 10, 'per_position_limit': 200, 'max_positions_reached': 2}

**Sample event lines (evidence):**
- `[wheel_run_started] {"timestamp": "2026-02-10T16:31:33.474006+00:00", "subsystem": "wheel", "event_type": "wheel_run_started", "strategy_id": "wheel", "reason": "ok", "ticker_count": 28}`
- `[wheel_run_started] {"timestamp": "2026-02-10T16:32:57.935085+00:00", "subsystem": "wheel", "event_type": "wheel_run_started", "strategy_id": "wheel", "reason": "ok", "ticker_count": 28}`
- `[wheel_run_started] {"timestamp": "2026-02-10T16:35:06.241629+00:00", "subsystem": "wheel", "event_type": "wheel_run_started", "strategy_id": "wheel", "reason": "ok", "ticker_count": 28}`
- `[wheel_regime_audit] {"timestamp": "2026-02-10T16:31:33.474314+00:00", "subsystem": "wheel", "event_type": "wheel_regime_audit", "strategy_id": "wheel", "regime_label": "chop", "modifier_only": true}`
- `[wheel_regime_audit] {"timestamp": "2026-02-10T16:32:57.935407+00:00", "subsystem": "wheel", "event_type": "wheel_regime_audit", "strategy_id": "wheel", "regime_label": "chop", "modifier_only": true}`
- `[wheel_regime_audit] {"timestamp": "2026-02-10T16:35:06.242112+00:00", "subsystem": "wheel", "event_type": "wheel_regime_audit", "strategy_id": "wheel", "regime_label": "chop", "modifier_only": true}`
- `[wheel_candidate_ranked] {"timestamp": "2026-02-10T16:31:39.498627+00:00", "subsystem": "wheel", "event_type": "wheel_candidate_ranked", "strategy_id": "wheel", "top_5_symbols": ["SPY", "QQQ", "DIA", ...`
- `[wheel_candidate_ranked] {"timestamp": "2026-02-10T16:33:03.642163+00:00", "subsystem": "wheel", "event_type": "wheel_candidate_ranked", "strategy_id": "wheel", "top_5_symbols": ["SPY", "QQQ", "DIA", ...`
- `[wheel_candidate_ranked] {"timestamp": "2026-02-10T16:35:13.989769+00:00", "subsystem": "wheel", "event_type": "wheel_candidate_ranked", "strategy_id": "wheel", "top_5_symbols": ["SPY", "QQQ", "DIA", ...`
- `[wheel_csp_skipped] {"timestamp": "2026-02-10T16:35:13.013171+00:00", "subsystem": "wheel", "event_type": "wheel_csp_skipped", "strategy_id": "wheel", "symbol": "KO", "reason": "per_position_limit"}`
- `[wheel_csp_skipped] {"timestamp": "2026-02-10T16:35:13.583358+00:00", "subsystem": "wheel", "event_type": "wheel_csp_skipped", "strategy_id": "wheel", "symbol": "WMT", "reason": "per_position_limit"}`
- `[wheel_csp_skipped] {"timestamp": "2026-02-10T16:35:13.988140+00:00", "subsystem": "wheel", "event_type": "wheel_csp_skipped", "strategy_id": "wheel", "symbol": "PFE", "reason": "per_position_limit"}`
- `[wheel_order_submitted] {"timestamp": "2026-02-10T16:39:04.890904+00:00", "subsystem": "wheel", "event_type": "wheel_order_submitted", "strategy_id": "wheel", "symbol": "XLF", "phase": "CSP", "order_i...`
- `[wheel_order_filled] {"timestamp": "2026-02-10T16:39:06.909553+00:00", "subsystem": "wheel", "event_type": "wheel_order_filled", "strategy_id": "wheel", "symbol": "XLF", "phase": "CSP", "order_id": "e...`

## 3. Telemetry and attribution
- telemetry.jsonl strategy_id=wheel (since 2026-02-03): 769
- attribution.jsonl strategy_id=wheel (since 2026-02-03): 0
- Sample telemetry (last 3):
  - {"timestamp": "2026-02-09T20:59:14.006852+00:00", "run_date": "2026-02-09", "strategy_id": "wheel", "event": "wheel_universe_selection", "wheel_universe_candidates": [{"symbol": "SPY", "wheel_suitability_score": 0.7709, "sector": "Broad Market", "passed": false}, {"symbol": "DIA", "wheel_suitability...
  - {"timestamp": "2026-02-09T21:00:10.280015+00:00", "run_date": "2026-02-09", "strategy_id": "wheel", "event": "wheel_universe_selection", "wheel_universe_candidates": [{"symbol": "SPY", "wheel_suitability_score": 0.7709, "sector": "Broad Market", "passed": false}, {"symbol": "DIA", "wheel_suitability...
  - {"timestamp": "2026-02-10T16:39:06.909758+00:00", "run_date": "2026-02-10", "symbol": "XLF", "strategy_id": "wheel", "side": "sell", "phase": "CSP", "option_type": "put", "qty": 1, "price": null, "order_id": "ef3ba040-08f9-4dbc-a3c8-fe70ff5f3c93", "strike": 51.5, "expiry": "2026-02-20", "dte": 10, "...

## 4. state/wheel_state.json
- mtime: 2026-02-10T16:39:06.911164+00:00
- open_csps keys: ['XLF']
- csp_history len: 0

## 5. Dashboard pipeline check
- _load_stock_closed_trades() reads: attribution.jsonl (strategy_id), exit_attribution.jsonl, telemetry.jsonl (strategy_id=wheel).
- /api/stockbot/wheel_analytics filters: trades where strategy_id == 'wheel'; premium_sum = sum(premium).
- If telemetry has strategy_id=wheel rows but dashboard shows 0: check timestamp cutoff (max_days=90), or premium/key fields missing.

**OUTCOME: Wheel FILLING** — wheel_order_filled > 0. Dashboard should show non-zero premium if telemetry has premium set; verify /api/stockbot/wheel_analytics and Wheel Strategy tab.