# ALPACA ENGINE — SRE VERDICT

- UTC `20260330_180816Z`

- `stock-bot` active: **active**
- `uw-flow-daemon` active: **active**

## Log health (heuristic)

- Recent `exit.jsonl` tail captured in ENGINE_STATE + below sample.

```
{"ts": "2026-03-30T18:07:39.657832+00:00", "msg": "profit_taking_acceleration", "symbol": "MA", "age_minutes": 31.3, "pnl_pct": 0.0, "new_trail_stop_pct": 0.5, "strategy_id": "equity"}
{"ts": "2026-03-30T18:07:39.678883+00:00", "msg": "profit_taking_acceleration", "symbol": "COP", "age_minutes": 31.3, "pnl_pct": 0.0, "new_trail_stop_pct": 0.5, "strategy_id": "equity"}
{"ts": "2026-03-30T18:07:39.679810+00:00", "msg": "profit_taking_acceleration", "symbol": "MRNA", "age_minutes": 31.3, "pnl_pct": 0.02, "new_trail_stop_pct": 0.5, "strategy_id": "equity"}
{"ts": "2026-03-30T18:07:39.701872+00:00", "msg": "profit_taking_acceleration", "symbol": "MS", "age_minutes": 31.3, "pnl_pct": 0.0, "new_trail_stop_pct": 0.5, "strategy_id": "equity"}
{"ts": "2026-03-30T18:07:39.740153+00:00", "msg": "profit_taking_acceleration", "symbol": "MSFT", "age_minutes": 31.3, "pnl_pct": 0.01, "new_trail_stop_pct": 0.5, "strategy_id": "equity"}
{"ts": "2026-03-30T18:07:39.740248+00:00", "msg": "profit_taking_acceleration", "symbol": "NIO", "age_minutes": 31.3, "pnl_pct": 0.01, "new_trail_stop_pct": 0.5, "strategy_id": "equity"}
{"ts": "2026-03-30T18:07:39.778113+00:00", "msg": "profit_taking_acceleration", "symbol": "NIO", "age_minutes": 31.3, "pnl_pct": 0.01, "new_trail_stop_pct": 0.5, "strategy_id": "equity"}
{"ts": "2026-03-30T18:07:39.778151+00:00", "msg": "profit_taking_acceleration", "symbol": "TSLA", "age_minutes": 31.3, "pnl_pct": 0.01, "new_trail_stop_pct": 0.5, "strategy_id": "equity"}
{"ts": "2026-03-30T18:07:39.800238+00:00", "msg": "profit_taking_acceleration", "symbol": "NVDA", "age_minutes": 31.3, "pnl_pct": 0.0, "new_trail_stop_pct": 0.5, "strategy_id": "equity"}
{"ts": "2026-03-30T18:07:39.819082+00:00", "msg": "profit_taking_acceleration", "symbol": "PFE", "age_minutes": 31.3, "pnl_pct": 0.0, "new_trail_stop_pct": 0.5, "strategy_id": "equity"}
{"ts": "2026-03-30T18:07:39.838474+00:00", "msg": "profit_taking_acceleration", "symbol": "PLTR", "age_minutes": 31.3, "pnl_pct": 0.02, "new_trail_stop_pct": 0.5, "strategy_id": "equity"}
{"ts": "2026-03-30T18:07:39.861013+00:00", "msg": "profit_taking_acceleration", "symbol": "RIVN", "age_minutes": 31.3, "pnl_pct": 0.01, "new_trail_stop_pct": 0.5, "strategy_id": "equity"}
{"ts": "2026-03-30T18:07:39.886993+00:00", "msg": "profit_taking_acceleration", "symbol": "SLB", "age_minutes": 31.3, "pnl_pct": 0.01, "new_trail_stop_pct": 0.5, "strategy_id": "equity"}
{"ts": "2026-03-30T18:07:39.908978+00:00", "msg": "profit_taking_acceleration", "symbol": "SOFI", "age_minutes": 31.3, "pnl_pct": 0.02, "new_trail_stop_pct": 0.5, "strategy_id": "equity"}
{"ts": "2026-03-30T18:07:39.965951+00:00", "msg": "profit_taking_acceleration", "symbol": "F", "age_minutes": 31.3, "pnl_pct": 0.0, "new_trail_stop_pct": 0.5, "strategy_id": "equity"}
{"ts": "2026-03-30T18:07:39.966169+00:00", "msg": "profit_taking_acceleration", "symbol": "TGT", "age_minutes": 31.3, "pnl_pct": 0.01, "new_trail_stop_pct": 0.5, "strategy_id": "equity"}
{"ts": "2026-03-30T18:07:39.987715+00:00", "msg": "profit_taking_acceleration", "symbol": "TSLA", "age_minutes": 31.3, "pnl_pct": 0.01, "new_trail_stop_pct": 0.5, "strategy_id": "equity"}
{"ts": "2026-03-30T18:07:40.008063+00:00", "msg": "profit_taking_acceleration", "symbol": "UNH", "age_minutes": 31.3, "pnl_pct": 0.0, "new_trail_stop_pct": 0.5, "strategy_id": "equity"}
{"ts": "2026-03-30T18:07:40.027661+00:00", "msg": "profit_taking_acceleration", "symbol": "WFC", "age_minutes": 31.3, "pnl_pct": 0.01, "new_trail_stop_pct": 0.5, "strategy_id": "equity"}
{"ts": "2026-03-30T18:07:40.118170+00:00", "msg": "profit_taking_acceleration", "symbol": "PLTR", "age_minutes": 31.3, "pnl_pct": 0.02, "new_trail_stop_pct": 0.5, "strategy_id": "equity"}
{"ts": "2026-03-30T18:07:40.137964+00:00", "msg": "profit_taking_acceleration", "symbol": "XLK", "age_minutes": 31.3, "pnl_pct": 0.01, "new_trail_stop_pct": 0.5, "strategy_id": "equity"}
{"ts": "2026-03-30T18:07:40.180296+00:00", "msg": "profit_taking_acceleration", "symbol": "GOOGL", "age_minutes": 31.3, "pnl_pct": 0.0, "new_trail_stop_pct": 0.5, "strategy_id": "equity"}
{"ts": "2026-03-30T18:07:40.199831+00:00", "msg": "profit_taking_acceleration", "symbol": "XLK", "age_minutes": 31.3, "pnl_pct": 0.01, "new_trail_stop_pct": 0.5, "strategy_id": "equity"}
{"ts": "2026-03-30T18:07:40.220212+00:00", "msg": "profit_taking_acceleration", "symbol": "NVDA", "age_minutes": 31.3, "pnl_pct": 0.0, "new_trail_stop_pct": 0.5, "strategy_id": "equity"}
{"ts": "2026-03-30T18:07:40.239876+00:00", "msg": "profit_taking_acceleration", "symbol": "SOFI", "age_minutes": 31.3, "pnl_pct": 0.02, "new_trail_stop_pct": 0.5, "strategy_id": "equity"}
{"ts": "2026-03-30T18:07:40.259574+00:00", "msg": "profit_taking_acceleration", "symbol": "AMD", "age_minutes": 31.3, "pnl_pct": 0.01, "new_trail_stop_pct": 0.5, "strategy_id": "equity"}
{"ts": "2026-03-30T18:07:40.277622+00:00", "msg": "profit_taking_acceleration", "symbol": "JPM", "age_minutes": 31.3, "pnl_pct": 0.0, "new_trail_stop_pct": 0.5, "strategy_id": "equity"}
{"ts": "2026-03-30T18:07:40.401890+00:00", "msg": "profit_taking_acceleration", "symbol": "C", "age_minutes": 31.3, "pnl_pct": 0.01, "new_trail_stop_pct": 0.5, "strategy_id": "equity"}
{"ts": "2026-03-30T18:07:40.440623+00:00", "msg": "profit_taking_acceleration", "symbol": "UNH", "age_minutes": 31.3, "pnl_pct": 0.0, "new_trail_stop_pct": 0.5, "strategy_id": "equity"}
{"ts": "2026-03-30T18:07:40.488773+00:00", "msg": "profit_taking_acceleration", "symbol": "HOOD", "age_minutes": 31.3, "pnl_pct": 0.02, "new_trail_stop_pct": 0.5, "strategy_id": "equity"}

```

## Notes

- Confirm `evaluate_exits` cadence via stock-bot logs / worker_debug if enabled.
- If `list_positions` works (Phase 1 API table), broker connectivity is OK.
