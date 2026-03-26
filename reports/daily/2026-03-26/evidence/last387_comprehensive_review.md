# Comprehensive Review — Board Input

**Scope:** last 387 exits. **Window:** 2026-03-04 to 2026-03-05. **End date:** 2026-03-05.

## Architecture (current)

- Entry: composite score (UW + flow + dark pool + gamma + vol + option volume), expectancy gate, capacity/displacement/momentum gates.
- Exit: signal_decay, time stop, trailing stop, regime-based exits; exit pressure v3.
- Universe: daily universe from UW + survivorship; sector/regime filters.
- Execution: Alpaca paper; cooldowns, concentration limits, max positions per cycle.
- Data: attribution.jsonl, exit_attribution.jsonl, master_trade_log.jsonl, blocked_trades.jsonl; EOD root cause, exit effectiveness v2, governance loop.

## PnL & activity

- **Total PnL (attribution):** $-97.76
- **Total PnL (exit attribution):** $-97.87
- **Total executed trades:** 809
- **Total exits:** 387
- **Win rate:** 20.0%
- **Avg hold (minutes):** 38.8
- **Blocked trades:** 2287

## Learning & telemetry (same scope)

- **Exits in scope:** 387
- **Telemetry-backed:** 387 (100.0%)
- **Ready for replay (≥100 exits, ≥90% telemetry):** Yes

## Counter-intelligence (blocked trades)

*C1 promoted: opportunity-cost ranking is first-class below (reporting only; no gating changes).*

- **Blocked in scope:** 2287
- `displacement_blocked`: 2014
- `max_positions_reached`: 238
- `expectancy_blocked:score_floor_breach`: 22
- `order_validation_failed`: 13

### Opportunity-cost ranked reasons (C1)

- `displacement_blocked`: blocked_count=2014, estimated_opportunity_cost_usd=-509.35, avg_score=4.45
- `max_positions_reached`: blocked_count=238, estimated_opportunity_cost_usd=-60.19, avg_score=3.19
- `expectancy_blocked:score_floor_breach`: blocked_count=22, estimated_opportunity_cost_usd=-5.56, avg_score=2.44
- `order_validation_failed`: blocked_count=13, estimated_opportunity_cost_usd=-3.29, avg_score=4.64

## Long vs short

- **long:** count=213, total_pnl_usd=-114.79, win_rate=36.6%
- **short:** count=143, total_pnl_usd=27.94, win_rate=51.7%
- **unknown:** count=31, total_pnl_usd=-11.02, win_rate=32.3%

## Exit reason distribution

- `unknown`: 809
- `signal_decay(0.70)`: 15
- `signal_decay(0.87)`: 12
- `signal_decay(0.86)`: 11
- `signal_decay(0.95)`: 11
- `signal_decay(0.64)`: 10
- `signal_decay(0.94)`: 10
- `signal_decay(0.80)`: 10
- `signal_decay(0.69)`: 9
- `signal_decay(0.91)`: 9
- `signal_decay(0.90)`: 9
- `signal_decay(0.85)`: 9
- `signal_decay(0.83)`: 8
- `signal_decay(0.87)+flow_reversal`: 8
- `signal_decay(0.82)+flow_reversal`: 7

## How to proceed

- Replay gate met (≥100 exits with ≥90% telemetry in scope). Run direction replay when ready.
- Review blocked trades: top reason 'displacement_blocked' (2014 blocks). Consider counter-intel report for missed opportunities.
- PnL negative in scope; use board personas for top 5 recommendations (entry/exit/gates).
- Board task: each persona 3 ideas → agree top 5 with owner, metric, success criteria.

## Board task

Each persona (Equity Skeptic, Wheel Advocate, Risk Officer, Promotion Judge, Customer Advocate, Innovation Officer, SRE) must produce **3 ideas** to improve PnL and stop losing money. Then the Board must **agree on the top 5** recommendations with owner, metric, and 3/5-day success criteria.

**Direction review:** If the market was down but almost all executed trades are long, the Board should consider: (1) Is LONG_ONLY enabled on droplet? (2) Is flow/cache sentiment skewed bullish? See reports/audit/LONG_SHORT_TRADE_LOGIC_AUDIT.md and run scripts/verify_long_short_on_droplet.py on droplet for direction mix and LONG_ONLY status.
