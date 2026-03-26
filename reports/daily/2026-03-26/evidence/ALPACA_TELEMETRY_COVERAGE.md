# ALPACA TELEMETRY COVERAGE (SRE)
Generated: 2026-03-19T17:29:26.748739+00:00

## Log counts (tail)
- exit_attribution.jsonl: 500
- orders.jsonl: 500
- attribution.jsonl: 500
- run.jsonl: 300

## Required fields (exit_attribution sample)
- Required: ['trade_id', 'symbol', 'exit_timestamp', 'exit_reason', 'realized_pnl_usd', 'entry_timestamp']
- Records with missing required (sample 100): 100
- trade_id open_HOOD_2026-03-16T19:47:26.894321+00:00: missing ['exit_timestamp', 'realized_pnl_usd']
- trade_id open_MS_2026-03-16T19:48:20.419764+00:00: missing ['exit_timestamp', 'realized_pnl_usd']
- trade_id open_PLTR_2026-03-16T19:48:39.687885+00:00: missing ['exit_timestamp', 'realized_pnl_usd']
- trade_id open_SOFI_2026-03-16T19:48:49.608926+00:00: missing ['exit_timestamp', 'realized_pnl_usd']
- trade_id open_RIVN_2026-03-16T19:48:59.852992+00:00: missing ['exit_timestamp', 'realized_pnl_usd']
- trade_id open_INTC_2026-03-16T19:50:25.134213+00:00: missing ['exit_timestamp', 'realized_pnl_usd']
- trade_id open_BAC_2026-03-16T19:50:47.896102+00:00: missing ['exit_timestamp', 'realized_pnl_usd']
- trade_id open_AMD_2026-03-16T19:44:31.434091+00:00: missing ['exit_timestamp', 'realized_pnl_usd']
- trade_id open_COIN_2026-03-17T13:39:54.102745+00:00: missing ['exit_timestamp', 'realized_pnl_usd']
- trade_id open_C_2026-03-17T13:40:44.923068+00:00: missing ['exit_timestamp', 'realized_pnl_usd']

## Chain completeness
- Every trade should have: entry attempt → order → fill → exit attribution
- Timestamps: UTC; monotonic per trade (entry_ts < exit_ts)
