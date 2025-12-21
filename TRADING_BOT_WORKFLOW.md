# Alpaca Trading Bot Complete Workflow Documentation

## Table of Contents
1. [Signal Generation](#signal-generation)
2. [Signal Review & Scoring](#signal-review--scoring)
3. [Trading Execution](#trading-execution)
4. [Trade Monitoring & Exit Review](#trade-monitoring--exit-review)
5. [Learning Engine](#learning-engine)
6. [Exit Decisions](#exit-decisions)
7. [Post-Trade Review](#post-trade-review)
8. [Timing & Updates](#timing--updates)
9. [UW Integration Details](#uw-integration-details)
10. [Alpaca Integration Details](#alpaca-integration-details)

---

## Signal Generation

### Overview
The bot generates trading signals by polling Unusual Whales (UW) API endpoints and processing options flow data into actionable clusters.

### UW Data Sources

The bot integrates with multiple UW API endpoints to gather comprehensive market intelligence:

#### Core Flow Signals
- **Options Flow Alerts** (`/api/flow/alerts`)
  - Real-time options trades (sweeps, blocks, single-leg)
  - Premium, volume, direction (bullish/bearish)
  - Expiry dates and strike prices
  - Flow type classification

- **Dark Pool Data** (`/api/dark-pool`)
  - Off-exchange volume and premium
  - Print count and average premium
  - Sentiment classification (BULLISH/BEARISH/MIXED)

- **Insider Trading** (`/api/insider`)
  - Net buys vs. sells
  - Total USD volume
  - Conviction modifier (-0.05 to +0.05)

#### Expanded Intelligence (V3)
- **Congress/Politician Trading** (`/api/congress`)
  - Recent politician trades
  - Buy/sell counts
  - Net sentiment and conviction boost

- **Short Interest & Squeeze** (`/api/shorts`)
  - Short interest percentage
  - Days to cover
  - Fails-to-deliver (FTD) count
  - Squeeze risk flag

- **Institutional Activity** (`/api/institutional`)
  - 13F filings data
  - Institutional flow alignment

- **Market Tide** (`/api/market-tide`)
  - Market-wide options sentiment
  - Net premium flows

- **Calendar Catalysts** (`/api/calendar`)
  - Earnings dates
  - FDA approvals
  - Economic events

- **ETF Flows** (`/api/etf-flow`)
  - ETF in/outflows
  - Sector rotation signals

#### Advanced Features (V2)
- **Greeks & Gamma** (`/api/greeks`)
  - Gamma exposure
  - Delta exposure
  - Squeeze detection

- **IV Term Skew** (computed)
  - Front-month vs. back-month IV
  - Event timing signals

- **Open Interest Changes** (`/api/oi`)
  - OI delta changes
  - Institutional positioning

### Signal Polling Process

1. **Smart Polling** (`SmartPoller` class)
   - Polls UW API every 60 seconds (configurable via `RUN_INTERVAL_SEC`)
   - Implements exponential backoff on API errors
   - Caches responses to reduce API calls
   - Handles rate limiting gracefully

2. **Data Filtering** (`base_filter` function)
   - **Expiry Filter**: Only trades expiring within `MAX_EXPIRY_DAYS` (default: 7 days)
   - **Volume Filter**: `volume > open_interest` (ensures new activity)
   - **Flow Type Filter**: Only accepts:
     - `sweep`: Large orders split across multiple exchanges
     - `block`: Large single-exchange trades
     - `singleleg`: Large single-leg institutional trades
   - **Premium Filter**: Minimum `MIN_PREMIUM_USD` (default: $100,000)

3. **Clustering** (`cluster_signals` function)
   - Groups trades by:
     - Symbol (ticker)
     - Direction (bullish/bearish)
     - Time window (`CLUSTER_WINDOW_SEC`, default: 600 seconds = 10 minutes)
   - **Cluster Requirements**:
     - Minimum `CLUSTER_MIN_SWEEPS` trades (default: 3)
     - Clusters within time window are aggregated
   - **Cluster Data Structure**:
     ```python
     {
       "ticker": "AAPL",
       "direction": "bullish",  # or "bearish"
       "count": 5,  # number of trades in cluster
       "start_ts": "2025-01-15T10:30:00Z",
       "end_ts": "2025-01-15T10:35:00Z",
       "avg_premium": 250000.0,  # average premium in USD
       "trades": [...]  # raw trade data
     }
     ```

### Cache Management

- **UW Flow Cache** (`state/uw_flow_cache.json`)
  - Persists signal data between cycles
  - Updated every polling cycle
  - Enriched with computed features (IV skew, smile slope, etc.)
  - Structure per symbol:
    ```json
    {
      "AAPL": {
        "sentiment": "BULLISH",
        "conviction": 0.75,
        "clusters": [...],
        "dark_pool": {...},
        "insider": {...},
        "expanded_intel": {...}
      }
    }
    ```

---

## Signal Review & Scoring

### Composite Scoring System (V3)

The bot uses a sophisticated multi-factor scoring system that combines all available signals into a single composite score (0-5 scale).

#### Scoring Components

**Core Flow Signals** (Base weights):
- **Options Flow** (weight: 2.4)
  - Sentiment: BULLISH/BEARISH/NEUTRAL
  - Conviction: 0.0-1.0 (confidence in direction)
  - Component = `W_FLOW * conviction`

- **Dark Pool** (weight: 1.3)
  - Sentiment alignment with flow
  - Total premium (log-scaled magnitude)
  - Print count
  - Component = `W_DARK * (base + log_magnitude)`

- **Insider** (weight: 0.5)
  - Net buys vs. sells
  - Total USD volume
  - Conviction modifier (-0.05 to +0.05)
  - Component = `W_INSIDER * (0.50 ± modifier)`

**V2 Advanced Features**:
- **IV Term Skew** (weight: 0.6)
  - Front-month vs. back-month IV difference
  - Positive = near-term event expected
  - Range: -0.15 to +0.15

- **Smile Slope** (weight: 0.35)
  - OTM calls vs. OTM puts skew
  - Positive = bullish skew
  - Range: -0.10 to +0.10

- **Whale Persistence** (weight: 0.7)
  - Sustained high conviction (>0.70) over time
  - Duration-based bonus

- **Event Alignment** (weight: 0.4)
  - Alignment with earnings/FDA/economic events
  - Calendar catalyst boost

- **Toxicity Penalty** (weight: -0.9, **negative**)
  - Detects conflicting signals (low agreement)
  - Reduces score when signals disagree
  - Threshold: <0.30 agreement = penalty

- **Temporal Motif** (weight: 0.5)
  - Pattern detection:
    - Staircase: Progressive conviction increase
    - Sweep/Block: Sudden large flow
    - Burst: High-frequency clusters
  - Pattern-based bonuses

- **Regime Modifier** (weight: 0.3)
  - Market regime adjustments
  - RISK_ON: Amplifies bullish signals
  - RISK_OFF: Amplifies bearish signals

**V3 Expanded Intelligence**:
- **Congress** (weight: 0.9)
  - Politician trading activity
  - Alignment bonus when congress trades same direction as flow
  - Opposition penalty when conflicting

- **Shorts Squeeze** (weight: 0.7)
  - High short interest (>15%) with bullish flow
  - Days to cover >5
  - FTD pressure
  - Squeeze risk flag

- **Institutional** (weight: 0.5)
  - 13F filings alignment
  - Block size analysis

- **Market Tide** (weight: 0.4)
  - Market-wide sentiment
  - Net premium flows

- **Calendar Catalyst** (weight: 0.45)
  - Earnings/FDA/economic events
  - Event proximity bonus

- **ETF Flow** (weight: 0.3)
  - ETF in/outflows
  - Sector rotation signals

**V2 Full Intelligence Pipeline**:
- **Greeks Gamma** (weight: 0.4)
  - Gamma exposure for squeeze detection
  - Negative gamma = squeeze potential

- **FTD Pressure** (weight: 0.3)
  - Fails-to-deliver count
  - Delivery pressure signals

- **IV Rank** (weight: 0.2)
  - IV rank for options timing
  - Can be negative (low IV)

- **OI Change** (weight: 0.35)
  - Open interest delta changes
  - Institutional positioning indicator

- **Squeeze Score** (weight: 0.2)
  - Combined squeeze indicator bonus

#### Composite Score Calculation

```python
raw_score = (
    flow_component +
    dark_pool_component +
    insider_component +
    iv_term_skew_component +
    smile_slope_component +
    whale_persistence_component +
    event_alignment_component +
    temporal_motif_component +
    regime_modifier_component +
    congress_component +
    shorts_squeeze_component +
    institutional_component +
    market_tide_component +
    calendar_catalyst_component +
    etf_flow_component +
    greeks_gamma_component +
    ftd_pressure_component +
    iv_rank_component +
    oi_change_component +
    squeeze_score_component -
    toxicity_penalty
)

score = clip(raw_score, 0.0, 5.0)  # Cap at 5.0
```

#### Adaptive Weight Optimization

The bot continuously learns which signals are most predictive:

- **Weight Multipliers**: Each component has an adaptive multiplier (0.25x to 2.5x)
- **Learning Method**: Bayesian updates with EWMA smoothing
- **Update Frequency**: Weekly (after sufficient samples)
- **Anti-Overfitting**: Wilson confidence intervals, minimum sample requirements (30+ trades)

**Weight Adjustment Rules**:
- **Boost** (up to 2.5x): Wilson lower bound >0.55, EWMA win rate >0.55, positive P&L
- **Penalize** (down to 0.25x): Wilson upper bound <0.45, EWMA win rate <0.45
- **Mean Revert**: Decay toward 1.0x when win rate is neutral (0.48-0.52)

### Entry Gating

Before a signal can trade, it must pass multiple gates:

#### 1. Composite Score Threshold
- **Base Threshold**: 2.7 (configurable)
- **Canary Stage**: 2.9 (after 50+ trades)
- **Champion Stage**: 3.2 (after 200+ trades with strong performance)
- **Adaptive Threshold**: Adjusts based on:
  - Bucket performance (2.5-3.0, 3.0-4.0, 4.0+)
  - Current drawdown (tightens in drawdown)
  - Win rate by score bucket

#### 2. Toxicity Check
- **Block if**: Signal agreement <0.30 (conflicting signals)
- **Block if**: Toxicity score >0.90 (highly toxic flow)

#### 3. Freshness Check
- **Block if**: Signal freshness <0.30 (stale data)

#### 4. Regime Gating
- **Block if**: Symbol profile indicates poor performance in current regime
- **Block if**: Regime confidence too low

#### 5. Theme Risk Limits
- **Block if**: Theme exposure would exceed `MAX_THEME_NOTIONAL_USD` (default: $50,000)
- Prevents over-concentration in single theme/sector

#### 6. Symbol Exposure Limits
- **Block if**: Already have position in same symbol
- **Exception**: Position flipping allowed for high-conviction signals (score >=4.0)

#### 7. Cooldown Period
- **Block if**: Symbol was recently traded (within `COOLDOWN_MINUTES_PER_TICKER`, default: 15 minutes)
- Prevents overtrading same symbol

#### 8. Expectancy Gate (V3.2)
- **Block if**: Expected value (EV) below stage-specific floor:
  - **Base**: EV >= -0.02
  - **Canary**: EV >= 0.00
  - **Champion**: EV >= 0.02
- **Exploration Quota**: Allows low-EV trades for learning (limited per day)

#### 9. Risk Management Gates
- **Symbol Exposure**: Max position size per symbol
- **Sector Exposure**: Max notional per sector/theme
- **Order Validation**: Size validation against buying power
- **Spread Watchdog**: Blocks trades with spread >50 bps (illiquid)

#### 10. Broker Health
- **Block if**: Broker connectivity degraded (reduce-only mode)
- **Block if**: Not armed for live trading (when `TRADING_MODE=LIVE`)
- **Block if**: Positions not reconciled (prevents double-entry)

### Signal Attribution Logging

Every signal evaluation is logged to `data/uw_attribution.jsonl`:

```json
{
  "ts": 1705320000,
  "symbol": "AAPL",
  "score": 3.45,
  "decision": "signal",  // or "rejected"
  "source": "uw_v3",
  "components": {
    "options_flow": 1.8,
    "dark_pool": 0.9,
    "insider": 0.3,
    "congress": 0.2,
    ...
  },
  "toxicity": 0.15,
  "freshness": 0.95,
  "notes": "flow BULLISH(0.75); dp BULLISH($2.5M, 12 prints); aligned(flow=dp)"
}
```

---

## Trading Execution

### What It Takes to Trade

A signal must pass all gates above, then:

1. **Position Sizing Calculation**
   - **Base Size**: `SIZE_BASE_USD` (default: $500) / current price
   - **Conviction Boost**: +20% if strong flow (conviction >=0.70) and aligned
   - **Conviction Penalty**: -20% if strong but opposite signals
   - **IV Skew Alignment**: +25% if IV skew aligns with direction
   - **Whale Persistence**: +20% if whale activity sustained
   - **Toxicity Penalty**: -25% if high toxicity
   - **Skew Conflict**: -30% if IV skew conflicts with direction
   - **Minimum Notional**: Must be >= `MIN_NOTIONAL_USD` (default: $100)
   - **Maximum**: Capped by buying power and position limits

2. **Order Routing** (`route_order` function)
   - **Entry Mode**: `MAKER_BIAS` (default) - tries to join NBBO
   - **Fallback**: `midpoint` if maker fails
   - **Last Resort**: `market_fallback` if midpoint fails
   - **Post-Only**: Default enabled (avoids paying spread)
   - **Tolerance**: `ENTRY_TOLERANCE_BPS` (default: 10 bps)
   - **Retries**: Up to `ENTRY_MAX_RETRIES` (default: 3) with `ENTRY_RETRY_SLEEP_SEC` (1.0s) delay

3. **Regime-Aware Execution**
   - **High Vol Negative Gamma**: AGGRESSIVE (cross spread immediately)
   - **Downtrend Flow Heavy**: AGGRESSIVE
   - **Low Vol Uptrend**: PASSIVE (join NBBO to capture spread)
   - **Default**: NEUTRAL

### Alpaca Integration

#### Order Submission

```python
# Buy order (bullish signal)
order = api.submit_order(
    symbol=symbol,
    qty=qty,
    side="buy",
    type="limit",
    time_in_force="day",
    limit_price=limit_price,
    order_class="simple"
)

# Sell order (bearish signal) - SHORT position
order = api.submit_order(
    symbol=symbol,
    qty=qty,
    side="sell",
    type="limit",
    time_in_force="day",
    limit_price=limit_price,
    order_class="simple"
)
```

#### Position Tracking

- **Internal State** (`AlpacaExecutor.opens`):
  ```python
  {
    "AAPL": {
      "ts": datetime(...),  # entry timestamp
      "entry_price": 150.25,
      "qty": 25,
      "side": "buy",  # or "sell"
      "direction": "bullish",  # or "bearish"
      "entry_score": 3.45,
      "components": {...},  # signal components at entry
      "high_water": 152.00,  # highest price since entry
      "trail_dist": 1.50,  # trailing stop distance
      "targets": [...]  # profit targets for scaling out
    }
  }
  ```

- **Persistent Metadata** (`state/position_metadata.json`):
  - Survives bot restarts
  - Includes entry score, components, regime, direction
  - Used for post-trade attribution

#### Position Reconciliation

- **On Startup**: Reconciles Alpaca positions with internal state
- **Every Cycle**: Validates positions match (health check)
- **Auto-Fix**: Corrects divergences automatically
- **Metadata Sync**: Ensures entry timestamps and scores are preserved

### Execution Quality Tracking

Every order execution is logged to `data/execution_quality.jsonl`:

```json
{
  "ts": 1705320000,
  "symbol": "AAPL",
  "side": "buy",
  "qty": 25,
  "entry_price": 150.25,
  "decision_price": 150.30,
  "fill_price": 150.28,
  "slippage_bps": 2.0,
  "spread_bps": 5.0,
  "order_type": "limit",
  "latency_ms": 120
}
```

---

## Trade Monitoring & Exit Review

### Continuous Monitoring

Every trading cycle (60 seconds), the bot evaluates all open positions for exit signals.

### Exit Signal Components

The bot monitors multiple exit signals simultaneously:

#### 1. **Trailing Stop**
- **Default**: `TRAILING_STOP_PCT` (default: 1.5%)
- **Dynamic**: Can be tightened based on flow reversal
- **High Water Mark**: Tracks highest price since entry
- **Stop Calculation**: `high_water * (1 - TRAILING_STOP_PCT)`
- **Trigger**: Current price <= trail stop

#### 2. **Time-Based Exit**
- **Standard**: `TIME_EXIT_MINUTES` (default: 240 minutes = 4 hours)
- **Stale Positions**: `TIME_EXIT_DAYS_STALE` (default: 12 days)
  - Only if P&L < `TIME_EXIT_STALE_PNL_THRESH_PCT` (default: 3%)
- **Trigger**: Age >= time limit

#### 3. **Signal Decay**
- **Calculation**: `current_composite_score / entry_score`
- **Threshold**: Decay ratio <0.70 triggers exit consideration
- **Contribution**: Decay contributes to exit urgency score

#### 4. **Flow Reversal**
- **Detection**: 
  - LONG position + BEARISH flow = reversal
  - SHORT position + BULLISH flow = reversal
- **Action**: Tightens trailing stop by 20% (0.80x multiplier)
- **Contribution**: Major factor in exit urgency

#### 5. **Profit Targets** (Scaling Out)
- **Tiers**: Configurable (default: 2%, 5%, 10%)
- **Fractions**: Configurable (default: 30%, 30%, 40%)
- **Action**: Partially closes position at each target
- **Logging**: Each scale-out logged separately for attribution

#### 6. **Drawdown Velocity**
- **Calculation**: `(high_water_pct - current_pnl_pct) / age_hours`
- **Threshold**: Drawdown >3% with high velocity
- **Contribution**: Velocity-based urgency score

#### 7. **Momentum Reversal**
- **Detection**: 
  - LONG position + negative momentum (<-0.5) = reversal
  - SHORT position + positive momentum (>0.5) = reversal
- **Contribution**: Momentum magnitude * weight

#### 8. **Regime Protection**
- **High Vol Negative Gamma**: Exits LONG positions if P&L < -0.5%
- **Manual Override**: Protects against regime-specific risks

#### 9. **Adaptive Exit Urgency** (V3.2)
- **Score Calculation**: Combines all exit signals into urgency (0-10)
- **Recommendations**:
  - **EXIT** (urgency >=6.0): Immediate close
  - **REDUCE** (urgency >=3.0): Consider partial close
  - **HOLD** (urgency <3.0): Continue monitoring
- **Primary Reason**: Identifies dominant exit factor

#### 10. **Opportunity Displacement**
- **Trigger**: New signal with score advantage >=2.0
- **Conditions**:
  - Position age >= `DISPLACEMENT_MIN_AGE_HOURS` (default: 4 hours)
  - Position P&L near breakeven (within `DISPLACEMENT_MAX_PNL_PCT`, default: 1%)
  - New signal significantly stronger
- **Action**: Closes old position to make room for new signal
- **Cooldown**: Symbol on cooldown for `DISPLACEMENT_COOLDOWN_HOURS` (default: 6 hours)

### Exit Evaluation Process

```python
def evaluate_exits():
    for symbol, position_info in open_positions:
        # 1. Calculate position metrics
        age_hours = (now - entry_ts).total_seconds() / 3600
        pnl_pct = (current_price - entry_price) / entry_price * 100
        high_water_pct = (high_water - entry_price) / entry_price * 100
        
        # 2. Get current signals
        current_composite = compute_composite_score(symbol)
        flow_reversal = check_flow_reversal(position, current_signals)
        
        # 3. Calculate exit urgency
        exit_urgency = compute_exit_urgency({
            "entry_score": entry_score,
            "current_pnl_pct": pnl_pct,
            "age_hours": age_hours,
            "high_water_pct": high_water_pct
        }, {
            "composite_score": current_composite,
            "flow_reversal": flow_reversal,
            "momentum": momentum
        })
        
        # 4. Check exit triggers
        if exit_urgency["recommendation"] == "EXIT":
            close_position(symbol, reason=exit_urgency["primary_reason"])
        elif trailing_stop_hit or time_exit_hit:
            close_position(symbol, reason=build_composite_close_reason(...))
```

### Composite Close Reason

Exit reasons are combined into a composite string:

```
"time_exit(240h)+signal_decay(0.65)+flow_reversal"
"trail_stop(-1.2%)+drawdown(3.5%)"
"profit_target(5%)+momentum_reversal"
"displaced_by_NVDA+stale_position"
```

This provides full attribution for post-trade analysis.

---

## Learning Engine

### Adaptive Signal Weight Optimization

The bot continuously learns which signals are most predictive through Bayesian weight updates.

#### Learning Components

1. **SignalWeightModel**
   - Manages weight bands for all 20+ signal components
   - Multipliers range: 0.25x to 2.5x
   - Base weights from `WEIGHTS_V3` configuration
   - Effective weight = base_weight * multiplier

2. **DirectionalConvictionEngine**
   - Aggregates all signals into net long/short conviction
   - Calculates signal agreement (consensus strength)
   - Applies toxicity penalty for conflicting signals
   - Produces confidence intervals

3. **ExitSignalModel**
   - Separate adaptive weights for exit decisions
   - Tracks exit component performance:
     - Entry decay
     - Adverse flow
     - Drawdown velocity
     - Time decay
     - Momentum reversal
     - Volume exhaustion
     - Support break

4. **LearningOrchestrator**
   - Records trade outcomes with feature vectors
   - Tracks component performance:
     - Wins/losses per component
     - EWMA win rate
     - EWMA P&L
     - Sector-specific performance
     - Regime-specific performance
   - Updates weights weekly (after 30+ samples)
   - Uses Wilson confidence intervals for statistical rigor

#### Learning Process

**1. Trade Recording** (`record_trade_outcome`):
```python
{
  "trade_data": {
    "entry_ts": "2025-01-15T10:30:00Z",
    "exit_ts": "2025-01-15T14:30:00Z",
    "direction": "LONG",
    "symbol": "AAPL"
  },
  "feature_vector": {
    "options_flow": 0.75,
    "dark_pool": 0.60,
    "insider": 0.30,
    "congress": 0.20,
    ...
  },
  "pnl": 0.025,  # 2.5% profit
  "regime": "RISK_ON",
  "sector": "Technology"
}
```

**2. Component Performance Tracking**:
- For each component, tracks:
  - Wins when component was present
  - Losses when component was present
  - Total P&L contribution
  - EWMA win rate (alpha=0.15)
  - EWMA P&L
  - Contribution values when winning vs. losing

**3. Weight Updates** (weekly):
- **Boost** (multiplier += 0.05):
  - Wilson lower bound >0.55
  - EWMA win rate >0.55
  - Positive EWMA P&L
- **Penalize** (multiplier -= 0.05):
  - Wilson upper bound <0.45
  - EWMA win rate <0.45
- **Mean Revert** (decay toward 1.0):
  - Win rate neutral (0.48-0.52)
  - Decay = (current - 1.0) * 0.1

**4. State Persistence**:
- Weights saved to `state/signal_weights.json`
- Learning history to `data/weight_learning.jsonl`
- Component performance tracked in memory, persisted weekly

### Per-Ticker Learning (Optional)

When `ENABLE_PER_TICKER_LEARNING=true`:

- **Bayesian Profiles** (`profiles.json`):
  - Per-symbol confidence scores
  - Component weights per symbol
  - Entry/exit bandit actions
  - Sample counts

- **Feature Store** (`feature_store/{symbol}.jsonl`):
  - Historical feature vectors per symbol
  - Used for symbol-specific weight tuning

- **Daily Updates**: Profiles updated daily if `MIN_SAMPLES_DAILY_UPDATE` (40) reached
- **Weekly Retrain**: Full profile retraining weekly if `MIN_SAMPLES_WEEKLY_UPDATE` (200) reached

### Shadow Lab (Experimental Features)

- **Shadow Experiments**: Tests new strategies without affecting production
- **Promotion Criteria**:
  - Minimum trades: `EXP_MIN_TRADES` (60)
  - Minimum confidence: `EXP_MIN_CONF` (0.5)
  - Sharpe delta: `PROMOTE_MIN_DELTA_SHARPE` (0.15)
  - Max drawdown increase: `PROMOTE_MAX_DD_INCREASE` (0.02)
- **Weekly Evaluation**: Promotes experiments to production if criteria met
- **Rollback**: Auto-rollback if performance degrades after promotion

---

## Exit Decisions

### Exit Decision Process

Exits are evaluated every cycle (60 seconds) for all open positions.

### Exit Triggers (Priority Order)

1. **Adaptive Exit Urgency** (V3.2)
   - **EXIT** (urgency >=6.0): Immediate close
   - **REDUCE** (urgency >=3.0): Consider partial close
   - **HOLD** (urgency <3.0): Continue monitoring

2. **Regime Protection** (Manual Override)
   - High vol negative gamma + LONG position + P&L < -0.5%
   - Immediate exit regardless of other signals

3. **Stale Position Exit**
   - Age >= `TIME_EXIT_DAYS_STALE` (12 days)
   - AND P&L < `TIME_EXIT_STALE_PNL_THRESH_PCT` (3%)
   - Frees capital for better opportunities

4. **Trailing Stop**
   - Current price <= `high_water * (1 - TRAILING_STOP_PCT)`
   - Protects profits, limits losses

5. **Time Exit**
   - Age >= `TIME_EXIT_MINUTES` (240 minutes = 4 hours)
   - Prevents positions from becoming stale

6. **Profit Targets** (Scaling Out)
   - Partial closes at 2%, 5%, 10% profit
   - Locks in gains progressively

### Exit Urgency Calculation

```python
urgency = 0.0

# Signal decay
if entry_score > 0:
    decay_ratio = current_score / entry_score
    if decay_ratio < 0.70:
        urgency += (1 - decay_ratio) * weight("entry_decay")

# Flow reversal
if flow_reversal:
    urgency += 2.0 * weight("adverse_flow")

# Drawdown velocity
if drawdown > 3.0:
    dd_velocity = drawdown / max(1, age_hours / 24)
    urgency += min(3.0, dd_velocity * 0.5) * weight("drawdown_velocity")

# Time decay
if age_hours > 72:
    urgency += min(2.0, (age_hours - 72) / 48) * weight("time_decay")

# Momentum reversal
if momentum_reversal:
    urgency += abs(momentum) * weight("momentum_reversal")

# Loss limit
if current_pnl < -5.0:
    urgency += 2.0

# Recommendation
if urgency >= 6.0:
    recommendation = "EXIT"
elif urgency >= 3.0:
    recommendation = "REDUCE"
else:
    recommendation = "HOLD"
```

### Exit Execution

When exit is triggered:

1. **Order Submission**:
   ```python
   api.close_position(symbol)  # Market order to close
   ```

2. **Attribution Logging**:
   - Composite close reason
   - Entry/exit prices
   - P&L (realized)
   - Holding period
   - Signal components at entry
   - Exit signals that triggered

3. **State Cleanup**:
   - Remove from `opens` dict
   - Remove from `high_water` dict
   - Remove from position metadata
   - Clear cooldown (if applicable)

4. **Learning Update**:
   - Record trade outcome for weight optimization
   - Update per-ticker profiles (if enabled)
   - Update component performance tracking

---

## Post-Trade Review

### Attribution Logging

Every closed trade is logged to `logs/attribution.jsonl`:

```json
{
  "type": "attribution",
  "trade_id": "AAPL_2025-01-15T14:30:00Z",
  "symbol": "AAPL",
  "pnl_usd": 125.50,
  "pnl_pct": 0.025,
  "hold_minutes": 240.0,
  "context": {
    "close_reason": "time_exit(240h)+signal_decay(0.65)",
    "entry_price": 150.25,
    "exit_price": 155.00,
    "side": "buy",
    "qty": 25,
    "entry_score": 3.45,
    "components": {
      "options_flow": 1.8,
      "dark_pool": 0.9,
      "insider": 0.3,
      ...
    },
    "market_regime": "RISK_ON",
    "direction": "bullish"
  }
}
```

### Daily Reports

**End-of-Day Report** (`reports/report_YYYY-MM-DD.json`):
- Total P&L (realized + unrealized)
- Win rate
- Trades closed
- Positions open
- By-symbol breakdown
- Timeline of trades

**UW Weight Tuner Report** (`data/uw_reports/uw_attribution_YYYY-MM-DD.json`):
- Composite score buckets (2.5-3.0, 3.0-4.0, 4.0+)
- Win rate by bucket
- Component attribution analysis
- Weight adjustments made

### Learning Updates

**Daily** (after market close):
- Update adaptive weights if sufficient samples
- Update per-ticker profiles
- Generate daily reports
- Run UW weight tuner

**Weekly** (Friday after close):
- Full weight optimization cycle
- Weekly weight adjustments
- Shadow lab promotion decisions
- Stability decay (reduces weights toward neutral)
- Comprehensive learning orchestrator:
  - Counterfactual analysis
  - Weight variation experiments
  - Timing optimization
  - Sizing optimization

### Performance Tracking

**Component Performance** (`adaptive_signal_optimizer`):
- Win rate per component
- EWMA win rate
- EWMA P&L
- Sector-specific performance
- Regime-specific performance
- Wilson confidence intervals

**Bucket Performance** (composite score buckets):
- Win rate by bucket (2.5-3.0, 3.0-4.0, 4.0+)
- Average P&L by bucket
- Sample counts
- Used for adaptive threshold adjustment

---

## Timing & Updates

### Main Trading Cycle

- **Frequency**: Every `RUN_INTERVAL_SEC` (default: 60 seconds)
- **During Market Hours**: Full signal generation, scoring, execution, exit evaluation
- **After Market Close**: Signal generation continues, but no new entries (exits still evaluated)

### Cycle Sequence

1. **Freeze Check** (0s)
   - Check if trading is frozen (manual override)
   - Halt if frozen

2. **UW Cache Read** (1s)
   - Load cached signal data
   - Enrich with computed features

3. **Signal Generation** (2-5s)
   - Poll UW API (if needed)
   - Filter and cluster trades
   - Build composite scores

4. **Signal Review** (5-8s)
   - Apply entry gates
   - Sort by composite score
   - Build confirmation layers

5. **Execution** (8-15s)
   - Evaluate entry decisions
   - Submit orders to Alpaca
   - Update position tracking

6. **Exit Evaluation** (15-20s)
   - Evaluate all open positions
   - Calculate exit urgency
   - Close positions if triggered

7. **Metrics & Logging** (20-25s)
   - Compute daily metrics
   - Log telemetry
   - Health checks

8. **Optimization** (25-30s)
   - Apply adaptive optimizations (if safe)
   - Generate cycle monitoring summary

### Daily Tasks

**After Market Close**:
- Generate end-of-day report
- Update adaptive weights (if sufficient samples)
- Run UW weight tuner daily report
- Update per-ticker profiles (if enabled)
- Emergency override check (if win rate <30% or P&L < -$1000)

### Weekly Tasks

**Friday After Market Close**:
- Weekly weight adjustments
- Shadow lab promotion decisions
- Stability decay (reduces weights toward neutral)
- Comprehensive learning orchestrator:
  - Counterfactual analysis
  - Weight variation experiments
  - Timing optimization
  - Sizing optimization
- Per-ticker profile retraining (if enabled)

### Background Services

**Cache Enrichment Service** (every 60 seconds):
- Enriches UW cache with computed features
- Updates IV skew, smile slope, motifs
- Maintains temporal history

**Self-Healing Monitor** (every 5 minutes):
- Detects and fixes common issues
- Position reconciliation
- Cache corruption fixes
- API connectivity recovery

**Comprehensive Learning** (daily after close):
- Runs once per day after market close
- Counterfactual trade analysis
- Weight variation experiments
- Timing and sizing optimization

**Position Reconciliation Loop** (continuous):
- Validates Alpaca positions match internal state
- Auto-fixes divergences
- Updates metadata

---

## UW Integration Details

### API Endpoints Used

1. **Flow Alerts**: `/api/flow/alerts`
   - Real-time options trades
   - Filters: sweeps, blocks, single-leg
   - Returns: trades with premium, volume, direction

2. **Dark Pool**: `/api/dark-pool`
   - Off-exchange volume
   - Sentiment classification
   - Print count and premium

3. **Insider**: `/api/insider`
   - Net buys/sells
   - Total USD volume
   - Conviction modifier

4. **Congress**: `/api/congress`
   - Politician trading activity
   - Buy/sell counts
   - Net sentiment

5. **Shorts**: `/api/shorts`
   - Short interest percentage
   - Days to cover
   - FTD count
   - Squeeze risk

6. **Institutional**: `/api/institutional`
   - 13F filings
   - Institutional flow

7. **Market Tide**: `/api/market-tide`
   - Market-wide sentiment
   - Net premium flows

8. **Calendar**: `/api/calendar`
   - Earnings dates
   - FDA approvals
   - Economic events

9. **ETF Flow**: `/api/etf-flow`
   - ETF in/outflows
   - Sector rotation

10. **Greeks**: `/api/greeks`
    - Gamma exposure
    - Delta exposure

11. **Open Interest**: `/api/oi`
    - OI delta changes
    - Institutional positioning

### Rate Limiting

- **Smart Polling**: Implements exponential backoff
- **Caching**: Aggressive caching to reduce API calls
- **Error Handling**: Graceful degradation on API errors
- **Timeout**: 15-second timeout per request

### Data Freshness

- **Cache TTL**: Signals considered fresh if <5 minutes old
- **Enrichment**: Computed features updated every 60 seconds
- **Expansion**: Expanded intelligence updated daily

---

## Alpaca Integration Details

### API Usage

1. **Account Info**: `api.get_account()`
   - Equity, buying power, cash
   - Used for position sizing and risk checks

2. **List Positions**: `api.list_positions()`
   - Current open positions
   - Used for exposure checks and exit evaluation

3. **Submit Order**: `api.submit_order(...)`
   - Entry orders (buy/sell)
   - Limit orders with maker bias

4. **Close Position**: `api.close_position(symbol)`
   - Market order to close
   - Used for exits

5. **Get Bars**: `api.get_bars(symbol, "1Min", limit=...)`
   - Price history for ATR calculation
   - Used for dynamic stops

6. **Get Quote**: `api.get_quote(symbol)`
   - Current bid/ask
   - Used for spread checks and pricing

### Order Types

- **Limit Orders**: Default for entries (maker bias)
- **Market Orders**: Used for exits (immediate execution)
- **Post-Only**: Enabled by default (avoids paying spread)

### Position Management

- **Reconciliation**: On startup and every cycle
- **Metadata Persistence**: Survives bot restarts
- **High Water Tracking**: Tracks best price for trailing stops
- **Profit Targets**: Partial closes at profit levels

### Risk Management

- **Buying Power Checks**: Validates order size
- **Exposure Limits**: Symbol and sector limits
- **Spread Watchdog**: Blocks illiquid trades
- **Order Validation**: Pre-submission validation

### Paper vs. Live Trading

- **Paper Mode** (default): `TRADING_MODE=PAPER`
  - Uses Alpaca paper trading API
  - No real money at risk

- **Live Mode**: `TRADING_MODE=LIVE`
  - Requires `LIVE_TRADING_ACK` environment variable
  - Additional safety checks
  - Manual acknowledgment required

---

## Summary

This trading bot implements a sophisticated multi-factor signal generation and execution system that:

1. **Generates Signals**: Polls UW API, filters trades, clusters by symbol/direction/time
2. **Reviews Signals**: Composite scoring (20+ components), adaptive weights, multiple gates
3. **Executes Trades**: Position sizing, order routing, Alpaca integration
4. **Monitors Trades**: Continuous exit evaluation, multiple exit signals, adaptive urgency
5. **Learns Continuously**: Bayesian weight optimization, per-ticker learning, shadow lab
6. **Reviews Post-Trade**: Attribution logging, daily/weekly reports, performance tracking

The system is designed for robustness, with extensive error handling, position reconciliation, self-healing capabilities, and comprehensive logging for post-trade analysis and continuous improvement.
