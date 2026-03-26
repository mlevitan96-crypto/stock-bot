# Comprehensive Review — Board Input

**Scope:** 30 days. **Window:** 2026-02-03 to 2026-03-04. **End date:** 2026-03-04.

## Architecture (current)

- Entry: composite score (UW + flow + dark pool + gamma + vol + option volume), expectancy gate, capacity/displacement/momentum gates.
- Exit: signal_decay, time stop, trailing stop, regime-based exits; exit pressure v3.
- Universe: daily universe from UW + survivorship; sector/regime filters.
- Execution: Alpaca paper; cooldowns, concentration limits, max positions per cycle.
- Data: attribution.jsonl, exit_attribution.jsonl, master_trade_log.jsonl, blocked_trades.jsonl; EOD root cause, exit effectiveness v2, governance loop.

## PnL & activity

- **Total PnL (attribution):** $-136.47
- **Total PnL (exit attribution):** $-279.79
- **Total executed trades:** 2000
- **Total exits:** 2000
- **Win rate:** 20.2%
- **Avg hold (minutes):** 11.8
- **Blocked trades:** 2000

## Learning & telemetry (same scope)

- **Exits in scope:** 2000
- **Telemetry-backed:** 387 (19.35%)
- **Ready for replay (≥100 exits, ≥90% telemetry):** No

## Counter-intelligence (blocked trades)

- **Blocked in scope:** 2000
- `displacement_blocked`: 1079
- `max_positions_reached`: 672
- `expectancy_blocked:score_floor_breach`: 151
- `order_validation_failed`: 82
- `max_new_positions_per_cycle`: 16

## Long vs short

- **long:** count=224, total_pnl_usd=-11.76, win_rate=44.6%
- **short:** count=132, total_pnl_usd=-9.38, win_rate=43.9%
- **unknown:** count=1644, total_pnl_usd=-258.64, win_rate=38.8%

## Exit reason distribution

- `unknown`: 2000
- `signal_decay(0.76)`: 153
- `signal_decay(0.75)`: 129
- `signal_decay(0.91)`: 127
- `signal_decay(0.77)`: 92
- `signal_decay(0.92)`: 86
- `signal_decay(0.90)`: 78
- `signal_decay(0.93)`: 71
- `signal_decay(0.74)`: 65
- `signal_decay(0.78)`: 48
- `signal_decay(0.73)`: 34
- `signal_decay(0.83)`: 32
- `signal_decay(0.89)`: 31
- `signal_decay(0.79)`: 30
- `signal_decay(0.94)`: 30

## How to proceed

- Continue capture: need 387/100 telemetry-backed in last-100 window; run replay when ≥90%.
- Review blocked trades: top reason 'displacement_blocked' (1079 blocks). Consider counter-intel report for missed opportunities.
- PnL negative in scope; use board personas for top 5 recommendations (entry/exit/gates).
- Board task: each persona 3 ideas → agree top 5 with owner, metric, success criteria.

## Board task

Each persona (Equity Skeptic, Wheel Advocate, Risk Officer, Promotion Judge, Customer Advocate, Innovation Officer, SRE) must produce **3 ideas** to improve PnL and stop losing money. Then the Board must **agree on the top 5** recommendations with owner, metric, and 3/5-day success criteria.

**Direction review:** If the market was down but almost all executed trades are long, the Board should consider: (1) Is LONG_ONLY enabled on droplet? (2) Is flow/cache sentiment skewed bullish? See reports/audit/LONG_SHORT_TRADE_LOGIC_AUDIT.md and run scripts/verify_long_short_on_droplet.py on droplet for direction mix and LONG_ONLY status.
