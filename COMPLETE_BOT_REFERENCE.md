# Complete Bot Reference - Living Documentation

**Last Updated:** 2025-12-26  
**Status:** Active Reference Document  
**Purpose:** Comprehensive reference for all bot components, signals, learning, and operations

---

## Table of Contents

1. [Signal System Overview](#signal-system-overview)
2. [All 22 Signal Components](#all-22-signal-components)
3. [Signal Calculation Logic](#signal-calculation-logic)
4. [Data Flow & Sources](#data-flow--sources)
5. [Learning System](#learning-system)
6. [Adaptive Weights](#adaptive-weights)
7. [Composite Scoring](#composite-scoring)
8. [Trade Execution Flow](#trade-execution-flow)
9. [Historical Analysis & Findings](#historical-analysis--findings)
10. [Best Practices & Troubleshooting](#best-practices--troubleshooting)

---

## Signal System Overview

### Architecture

The bot uses a **composite scoring system** that combines 22 signal components into a single trade score. Each component:
- Pulls data from UW API or computes from cached data
- Has a default weight (importance)
- Can be adjusted by adaptive learning
- Contributes to the final composite score

### Signal Categories

1. **Core Signals (6)** - Always present, basic plan compatible
2. **V2 Signals (6)** - Full intelligence pipeline
3. **V3 Signals (5)** - Expanded intelligence
4. **Computed Signals (5)** - Derived from other signals

---

## All 22 Signal Components

### Core Signals (Always Present)

#### 1. `options_flow` (flow)
- **Source:** UW API `/api/flow/alerts`
- **Default Weight:** 2.4
- **Description:** Primary options flow sentiment (bullish/bearish)
- **Calculation:** Aggregated from flow trades, conviction score
- **Data Format:** `{sentiment: "BULLISH"|"BEARISH", conviction: float}`
- **Status:** ✅ Always working

#### 2. `dark_pool` (dark_pool)
- **Source:** UW API `/api/darkpool/{ticker}`
- **Default Weight:** 1.3
- **Description:** Off-exchange volume and sentiment
- **Calculation:** Uses `total_notional` from dark pool data
- **Data Format:** `{sentiment: "BULLISH"|"BEARISH"|"NEUTRAL", total_notional: float, off_lit_notional: float}`
- **Status:** ✅ Working (fixed to use `total_notional`)

#### 3. `insider` (insider)
- **Source:** UW API `/api/insider/{ticker}`
- **Default Weight:** 0.5
- **Description:** Insider trading activity
- **Calculation:** Sentiment + conviction modifier
- **Data Format:** `{sentiment: "BULLISH"|"BEARISH"|"NEUTRAL", conviction_modifier: float}`
- **Status:** ✅ Working

#### 4. `iv_term_skew` (iv_skew)
- **Source:** Computed from flow data
- **Default Weight:** 0.6
- **Description:** IV term structure skew (call vs put IV)
- **Calculation:** Computed from options flow
- **Data Format:** `float` (positive = call skew, negative = put skew)
- **Status:** ✅ Working

#### 5. `smile_slope` (smile)
- **Source:** Computed from flow data
- **Default Weight:** 0.35
- **Description:** Volatility smile slope
- **Calculation:** Computed from options flow
- **Data Format:** `float`
- **Status:** ✅ Working

#### 6. `freshness_factor` (freshness)
- **Source:** Computed from cache timestamps
- **Default Weight:** N/A (multiplier)
- **Description:** Data recency factor (0-1)
- **Calculation:** Decay based on time since last update
- **Data Format:** `float` (0.0 to 1.0)
- **Status:** ✅ Working

### V2 Signals (Full Intelligence Pipeline)

#### 7. `greeks_gamma` (greeks_gamma)
- **Source:** UW API `/api/greeks/{ticker}`
- **Default Weight:** 0.4
- **Description:** Gamma exposure for squeeze detection
- **Calculation:** `gamma_exposure = call_gamma - put_gamma` (if not directly available)
- **Thresholds:** 
  - > 500000: 0.5x contribution
  - > 100000: 0.25x contribution
  - > 10000: 0.1x contribution (NEW - added 2025-12-26)
- **Data Format:** `{call_gamma: float, put_gamma: float, gamma_exposure: float}`
- **Status:** ✅ Fixed (now calculates from call_gamma/put_gamma)

#### 8. `ftd_pressure` (ftd_pressure)
- **Source:** UW API `/api/shorts/{ticker}/ftds` or `/api/shorts/{ticker}`
- **Default Weight:** 0.3
- **Description:** Fails-to-deliver pressure for squeeze signals
- **Calculation:** Checks both `ftd` and `shorts` keys
- **Thresholds:**
  - > 200000: 1.0x contribution
  - > 100000: 0.67x contribution
  - > 50000: 0.33x contribution
  - > 10000: 0.1x contribution (NEW - added 2025-12-26)
- **Data Format:** `{ftd_count: int, squeeze_pressure: bool}`
- **Status:** ✅ Fixed (now checks both data keys)

#### 9. `iv_rank` (iv_rank)
- **Source:** UW API `/api/iv-rank/{ticker}`
- **Default Weight:** 0.2
- **Description:** IV rank percentile for options timing
- **Calculation:** Checks both `iv` and `iv_rank` keys, uses `iv_rank_1y` if needed
- **Thresholds:**
  - < 20: 1.0x contribution (low IV = opportunity)
  - < 30: 0.5x contribution
  - 30-70: 0.15x contribution (NEW - added 2025-12-26)
  - > 70: -0.5x contribution (high IV = caution)
  - > 80: -1.0x contribution
- **Data Format:** `{iv_rank: float, iv_rank_1y: float}`
- **Status:** ✅ Fixed (now includes middle range)

#### 10. `oi_change` (oi_change)
- **Source:** UW API `/api/oi/{ticker}`
- **Default Weight:** 0.35
- **Description:** Open interest changes for institutional positioning
- **Calculation:** Checks `oi_change` key first, then `oi`, calculates from `curr_oi` or `volume` if needed
- **Thresholds:**
  - > 50000 and BULLISH and flow>0: 1.0x contribution
  - > 20000 and BULLISH: 0.57x contribution
  - > 10000: 0.29x contribution
  - > 1000: 0.1x contribution (NEW - added 2025-12-26)
- **Data Format:** `{net_oi_change: float, oi_sentiment: str, curr_oi: int, volume: int}`
- **Status:** ✅ Fixed (now checks correct data key)

#### 11. `etf_flow` (etf_flow)
- **Source:** UW API `/api/etf-flow/{ticker}`
- **Default Weight:** 0.3
- **Description:** ETF in/outflows for market sentiment
- **Calculation:** Sentiment + risk-on flag
- **Data Format:** `{overall_sentiment: str, market_risk_on: bool}`
- **Status:** ⚠️ May be empty for non-ETF tickers (expected)

#### 12. `squeeze_score` (squeeze_score)
- **Source:** Computed from other signals
- **Default Weight:** 0.2
- **Description:** Combined squeeze indicator
- **Calculation:** Combines FTD + SI + gamma signals
- **Data Format:** `{signals: int, high_squeeze_potential: bool}`
- **Status:** ⚠️ May need to be computed from other signals

### V3 Signals (Expanded Intelligence)

#### 13. `congress` (congress)
- **Source:** UW API `/api/congress/{ticker}`
- **Default Weight:** 0.9
- **Description:** Congress/politician trading activity
- **Calculation:** Recent count, buys/sells, conviction boost
- **Data Format:** `{recent_count: int, buys: int, sells: int, net_sentiment: str, conviction_boost: float}`
- **Status:** ❌ Endpoint 404 (expected - per-ticker doesn't exist)

#### 14. `shorts_squeeze` (shorts_squeeze)
- **Source:** UW API `/api/shorts/{ticker}`
- **Default Weight:** 0.7
- **Description:** Short interest & squeeze potential
- **Calculation:** Interest %, days to cover, squeeze risk
- **Data Format:** `{interest_pct: float, days_to_cover: float, ftd_count: int, squeeze_risk: bool}`
- **Status:** ⚠️ May be missing data

#### 15. `institutional` (institutional)
- **Source:** UW API `/api/institutional/{ticker}`
- **Default Weight:** 0.5
- **Description:** 13F filings & institutional activity
- **Calculation:** Net buys/sells, total USD
- **Data Format:** `{net_buys: int, net_sells: int, total_usd: float}`
- **Status:** ❌ Endpoint 404 (expected - per-ticker doesn't exist)

#### 16. `market_tide` (market_tide)
- **Source:** UW API `/api/market-tide`
- **Default Weight:** 0.4
- **Description:** Market-wide options sentiment
- **Calculation:** Call/put premium ratio, alignment with flow
- **Thresholds:**
  - Aligned with flow: 0.4-1.0x contribution
  - Opposed to flow: -0.25x contribution
  - Moderate imbalance (> 0.15): 0.05x contribution (NEW - added 2025-12-26)
- **Data Format:** `{net_call_premium: str, net_put_premium: str, net_volume: int}` or `{call_premium: float, put_premium: float}`
- **Status:** ✅ Fixed (now handles both data formats)

#### 17. `calendar_catalyst` (calendar)
- **Source:** UW API `/api/calendar/{ticker}`
- **Default Weight:** 0.45
- **Description:** Earnings/FDA/Economic events
- **Calculation:** Upcoming events, alignment with flow
- **Data Format:** `{upcoming_events: list, earnings_date: str}`
- **Status:** ⚠️ May be empty if no events (expected)

### Computed Signals (Enrichment)

#### 18. `whale_persistence` (whale)
- **Source:** Computed from motifs
- **Default Weight:** 0.7
- **Description:** Large player patterns (derived from motifs)
- **Calculation:** Detects whale motifs, average conviction
- **Data Format:** `{detected: bool, avg_conviction: float}`
- **Status:** ✅ Working (returns 0.0 if no whales detected - correct)

#### 19. `event_alignment` (event)
- **Source:** Computed from events
- **Default Weight:** 0.4
- **Description:** Event/earnings alignment
- **Calculation:** Alignment score with flow direction
- **Data Format:** `float` (0.0 to 1.0)
- **Status:** ✅ Working

#### 20. `temporal_motif` (motif_bonus)
- **Source:** Computed from temporal patterns
- **Default Weight:** 0.5
- **Description:** Temporal patterns (staircase/burst)
- **Calculation:** Detects staircase/burst motifs
- **Data Format:** `{staircase: {detected: bool, steps: int, slope: float}, burst: {detected: bool, count: int, intensity: float}}`
- **Status:** ✅ Working (returns 0.0 if no motifs detected - correct)

#### 21. `toxicity_penalty` (toxicity_penalty)
- **Source:** Computed from signal staleness
- **Default Weight:** -0.9 (negative - penalty)
- **Description:** Signal staleness/crowding penalty
- **Calculation:** Toxicity score, applies penalty if > 0.5
- **Thresholds:**
  - > 0.5: -1.5x penalty
  - > 0.3: -0.5x penalty
- **Data Format:** `float` (0.0 to 1.0)
- **Status:** ✅ Working (returns 0.0 if toxicity < 0.5 - correct)

#### 22. `regime_modifier` (regime)
- **Source:** Computed from market regime
- **Default Weight:** 0.3
- **Description:** Market regime adjustment
- **Calculation:** RISK_ON/RISK_OFF/mixed alignment with flow
- **Regime Handling:**
  - RISK_ON + bullish flow: 1.15x factor
  - RISK_OFF + bearish flow: 1.10x factor
  - mixed/NEUTRAL: 1.02x factor (NEW - added 2025-12-26)
- **Data Format:** `str` ("RISK_ON"|"RISK_OFF"|"mixed"|"NEUTRAL")
- **Status:** ✅ Fixed (now handles "mixed" regime)

---

## Signal Calculation Logic

### Composite Score Calculation

The composite score is calculated in `uw_composite_v2.py::compute_composite_score_v3()`:

```python
composite_score = (
    flow_component +
    dp_component +
    insider_component +
    iv_component +
    smile_component +
    whale_score +
    event_component +
    motif_bonus +
    toxicity_component +
    regime_component +
    # V3 new components
    congress_component +
    shorts_component +
    inst_component +
    tide_component +
    calendar_component +
    # V2 new components
    greeks_gamma_component +
    ftd_pressure_component +
    iv_rank_component +
    oi_change_component +
    etf_flow_component +
    squeeze_score_component
) * freshness_factor
```

### Component Contribution Formula

Each component contributes:
```
component_contribution = weight * component_strength * alignment_factor
```

Where:
- `weight`: Default weight (from WEIGHTS_V3) * adaptive multiplier
- `component_strength`: Calculated from data (0.0 to 1.0 typically)
- `alignment_factor`: Alignment with flow direction (0.7 to 1.3)

### Entry Thresholds

Trades are executed if `composite_score >= threshold`:

- **base mode:** 2.0 (paper trading) / 3.5 (production)
- **canary mode:** 2.2 (paper) / 3.8 (production)
- **champion mode:** 2.5 (paper) / 4.2 (production)

---

## Data Flow & Sources

### UW API Data Flow

```
UW API Endpoints
    ↓
uw_flow_daemon.py (polls every N seconds)
    ↓
data/uw_flow_cache.json (cache file)
    ↓
main.py::read_uw_cache()
    ↓
uw_enrichment_v2.py::enrich_signal()
    ↓
uw_composite_v2.py::compute_composite_score_v3()
    ↓
main.py::decide_and_execute()
```

### Cache Structure

```json
{
  "AAPL": {
    "sentiment": "BULLISH",
    "conviction": 0.85,
    "dark_pool": {
      "sentiment": "BULLISH",
      "total_notional": 1500000.0,
      "off_lit_notional": 1200000.0
    },
    "insider": {
      "sentiment": "BULLISH",
      "conviction_modifier": 0.3
    },
    "greeks": {
      "call_gamma": 50000.0,
      "put_gamma": 30000.0,
      "gamma_exposure": 20000.0
    },
    "market_tide": {
      "net_call_premium": "1500000.0",
      "net_put_premium": "800000.0"
    },
    ...
  },
  "_metadata": {
    "last_update": 1234567890,
    "market_tide": {...}
  }
}
```

### Data Freshness

- **Cache TTL:** 5 minutes (signals considered fresh if < 5 min old)
- **Enrichment:** Updated every 60 seconds
- **Expansion:** Updated daily

---

## Learning System

### Overview

The bot uses an **adaptive learning system** that:
1. Tracks component performance in actual trades
2. Adjusts component weights based on outcomes
3. Prevents overfitting with minimum samples and confidence intervals
4. Learns from both wins and losses

### Learning Data Sources

1. **`logs/attribution.jsonl`** - All executed trades
   - P&L outcomes
   - Signal components at entry
   - Exit reasons
   - **Learning:** Component performance, entry/exit optimization

2. **`logs/exit.jsonl`** - All exit events
   - Exit reasons
   - Exit timing
   - **Learning:** Exit signal optimization

3. **`state/blocked_trades.jsonl`** - Blocked trades
   - Why trades were blocked
   - Signal components present
   - **Learning:** Counterfactual learning - were we too conservative?

4. **`logs/gate.jsonl`** - Gate blocking events
   - Which gates blocked which trades
   - **Learning:** Gate threshold optimization

5. **`data/uw_attribution.jsonl`** - UW blocked entries
   - Signal combinations that were blocked
   - **Learning:** UW signal pattern optimization

### Learning Process

#### 1. Trade Recording

When a trade is executed:
```python
# In main.py::log_exit_attribution()
learn_from_trade_close(
    trade_data={
        "symbol": symbol,
        "entry_score": entry_score,
        "components": components,  # All 22 components
        "pnl_pct": pnl_pct,
        "regime": regime,
        "sector": sector
    }
)
```

#### 2. Component Performance Tracking

The adaptive optimizer tracks:
- **Wins:** Trades where component was present and non-zero, and trade was profitable
- **Losses:** Trades where component was present and non-zero, and trade was unprofitable
- **EWMA Performance:** Exponentially weighted moving average of P&L
- **Sample Count:** Number of trades where component contributed

#### 3. Weight Updates

Weights are updated using Bayesian learning:
- **Minimum Samples:** 30 trades before updating
- **Wilson Confidence Interval:** 95% confidence required
- **Update Step:** 0.1x per update (gradual adjustment)
- **Weight Range:** 0.25x to 2.5x multiplier

#### 4. Weight Adjustment Logic

```python
# In adaptive_signal_optimizer.py::update_weights()

# Strong performer: Increase weight
if wilson_low > 0.55 and ewma_wr > 0.55 and ewma_pnl > 0:
    new_mult = min(2.5, current_mult + 0.1)

# Weak performer: Decrease weight
elif wilson_high < 0.45 or ewma_pnl < -0.02:
    new_mult = max(0.25, current_mult - 0.1)

# Neutral: Keep current weight
else:
    new_mult = current_mult
```

### Learning Frequency

- **Short-term:** Immediately after each trade (component tracking)
- **Medium-term:** Daily batch processing (weight updates)
- **Long-term:** Weekly/monthly review (threshold optimization)

---

## Adaptive Weights

### How Adaptive Weights Work

1. **Base Weights:** Defined in `WEIGHTS_V3` (default importance)
2. **Adaptive Multipliers:** Learned from performance (0.25x to 2.5x)
3. **Effective Weight:** `base_weight * adaptive_multiplier`

### Current State (2025-12-26)

**15 components reduced by 75%** (to 0.25x multiplier) due to:
- Historical poor performance (11% win rate)
- **Root cause:** Bugs prevented components from contributing (always 0.0)
- **Impact:** Even with bugs fixed, weights remain low

### Weight Recovery

Weights recover when:
1. Component performs well (win rate > 55%, positive P&L)
2. Minimum 30 samples collected
3. Wilson confidence interval > 95%

**Recovery rate:** +0.1x per update (gradual)

### Resetting Adaptive Weights

If weights learned from buggy components, reset to defaults:

```python
# Reset all multipliers to 1.0 (neutral)
for component in weight_bands:
    weight_bands[component].current = 1.0
    weight_bands[component].sample_count = 0
    weight_bands[component].wins = 0
    weight_bands[component].losses = 0
```

---

## Composite Scoring

### Score Calculation

```python
# In uw_composite_v2.py

# 1. Get adaptive weights
weights = get_weights()  # Merges WEIGHTS_V3 + adaptive multipliers

# 2. Calculate each component
flow_component = weights["options_flow"] * flow_conviction
dp_component = weights["dark_pool"] * dp_strength
# ... (all 22 components)

# 3. Sum all components
composite_raw = sum(all_components)

# 4. Apply freshness decay
composite_score = composite_raw * freshness_factor

# 5. Clamp to 0-8
composite_score = max(0.0, min(8.0, composite_score))
```

### Score Interpretation

- **0.0-2.0:** Weak signal (below threshold)
- **2.0-3.5:** Moderate signal (base threshold)
- **3.5-4.5:** Strong signal (canary threshold)
- **4.5+:** Very strong signal (champion threshold)

---

## Trade Execution Flow

### Decision Process

```
1. Read UW cache (data/uw_flow_cache.json)
   ↓
2. Generate clusters from flow trades
   ↓
3. Enrich signals (uw_enrichment_v2.py)
   ↓
4. Calculate composite score (uw_composite_v2.py)
   ↓
5. Check entry threshold
   ↓
6. Check gates (freeze, max positions, etc.)
   ↓
7. Execute trade (if all checks pass)
   ↓
8. Log trade (logs/attribution.jsonl)
   ↓
9. Learn from outcome (adaptive_signal_optimizer.py)
```

### Gates

1. **Freeze State:** Trading halted (performance, pre-market, etc.)
2. **Max Positions:** Already at maximum positions
3. **Score Threshold:** Composite score below entry threshold
4. **Market Status:** Market closed or pre-market
5. **Risk Limits:** Exceeded risk parameters

---

## Historical Analysis & Findings

### Key Findings (2025-12-26)

1. **Bugs were primary cause of poor performance**
   - Components returned 0.0 in 100% of historical trades
   - Components had data but bugs prevented calculation
   - Adaptive weights learned from buggy components

2. **Component bugs fixed:**
   - `greeks_gamma`: Now calculates from `call_gamma`/`put_gamma`
   - `iv_rank`: Now includes middle range (30-70)
   - `oi_change`: Now checks correct data key
   - `ftd_pressure`: Now checks both `ftd` and `shorts` keys
   - `market_tide`: Now handles both data formats
   - `regime_modifier`: Now handles "mixed" regime

3. **Expected impact:**
   - +0.02 to +0.05 points per trade from component fixes
   - More components contributing to scores
   - Better signal quality

### Historical Performance

- **Total trades:** 296
- **Winning trades:** 61 (20.6%)
- **Losing trades:** 79 (26.7%)
- **Win rate:** 43.5% (of completed trades)
- **Score distribution:**
  - Winning: avg 4.48
  - Losing: avg 4.18
  - **Finding:** Scores very close (0.30 difference)

---

## Best Practices & Troubleshooting

### Signal Health Checks

1. **Check cache file exists:** `data/uw_flow_cache.json`
2. **Check daemon running:** `systemctl status trading-bot.service`
3. **Check component values:** Use `complete_signal_audit.py`
4. **Check adaptive weights:** Use `investigate_adaptive_weights.py`

### Common Issues

#### Issue: All components returning 0.0

**Symptoms:**
- Dashboard shows "no_recent_signals" for all components
- Composite scores are very low (< 1.0)

**Causes:**
1. UW daemon not running
2. Cache file empty or missing
3. Component bugs (data format mismatch)

**Solutions:**
1. Restart daemon: `systemctl restart trading-bot.service`
2. Check cache file: `cat data/uw_flow_cache.json | jq '.AAPL'`
3. Run signal audit: `python complete_signal_audit.py`

#### Issue: Adaptive weights too low

**Symptoms:**
- Components have data but scores still low
- Weights reduced to 0.25x (minimum)

**Causes:**
1. Historical poor performance
2. Learned from buggy components
3. Not enough samples for recovery

**Solutions:**
1. Reset adaptive weights (if learned from bugs)
2. Wait for more samples (minimum 30)
3. Check if components are actually contributing

#### Issue: Scores below threshold

**Symptoms:**
- No trades executing
- Scores consistently below 2.0

**Causes:**
1. Components not contributing (bugs)
2. Adaptive weights too low
3. Thresholds too high

**Solutions:**
1. Fix component bugs
2. Reset adaptive weights
3. Lower thresholds (paper trading only)

### Monitoring

1. **Dashboard:** Check signal health status
2. **Logs:** `tail -f logs/main.log | grep "composite_score"`
3. **State file:** `cat state/signal_weights.json | jq '.weight_bands'`

### Maintenance

1. **Daily:** Check daemon status, review logs
2. **Weekly:** Review adaptive weights, check component performance
3. **Monthly:** Review historical performance, adjust thresholds

---

## File Locations

### Core Files
- `main.py` - Main trading logic
- `uw_composite_v2.py` - Composite scoring
- `uw_enrichment_v2.py` - Signal enrichment
- `uw_flow_daemon.py` - UW API polling daemon
- `adaptive_signal_optimizer.py` - Learning system

### Data Files
- `data/uw_flow_cache.json` - UW API cache
- `state/signal_weights.json` - Adaptive weights state
- `logs/attribution.jsonl` - Trade attribution logs
- `logs/exit.jsonl` - Exit event logs
- `state/blocked_trades.jsonl` - Blocked trade logs

### Documentation
- `COMPLETE_BOT_REFERENCE.md` - This file (living documentation)
- `HISTORICAL_PERFORMANCE_ANALYSIS_REPORT.md` - Historical analysis
- `FINAL_COMPLETE_SIGNAL_AUDIT.md` - Signal audit results

---

## Update Log

### 2025-12-26
- Added all 22 signal components documentation
- Added signal calculation logic
- Added learning system documentation
- Added adaptive weights documentation
- Added historical analysis findings
- Added troubleshooting guide

---

**This is a living document. Update it whenever:**
- New signals are added
- Component logic changes
- Learning system changes
- New findings from analysis
- Best practices evolve

