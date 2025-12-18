# Unusual Whales API Endpoint Analysis

## Currently Used Endpoints

### Core Trading Signals (in `uw_flow_daemon.py`)
1. ✅ `/api/option-trades/flow-alerts` - Option flow alerts (most critical)
2. ✅ `/api/darkpool/{ticker}` - Dark pool levels
3. ✅ `/api/stock/{ticker}/greeks` - Greek exposure
4. ✅ `/api/market/top-net-impact` - Top net impact symbols

### Macro Intelligence (in `signals/uw_macro.py`)
5. ✅ `/api/market/sector-tide` - Sector-wide sentiment
6. ✅ `/api/shorts/{symbol}/data` - Short interest data
7. ✅ `/api/shorts/{symbol}/ftds` - Fails-to-deliver
8. ✅ `/api/stock/{symbol}/spot-exposures/strike` - Spot gamma exposures
9. ✅ `/api/etfs/{symbol}/in_outflow` - ETF flows
10. ✅ `/api/institution/{symbol}/ownership` - Institutional ownership
11. ✅ `/api/seasonality/{symbol}/monthly` - Seasonality patterns

### Additional (in `main.py`)
12. ✅ `/api/stock/{ticker}/volatility/realized` - Realized volatility
13. ✅ `/api/stock/{ticker}/historic-option-volume` - Historic option volume

## Potential Additional Endpoints (Based on Signal Components)

Based on `config/uw_signal_contracts.py`, we have signal components defined but may not be using all endpoints:

### High Priority - Likely Available

1. **Insider Trading** (`insider` signal component exists)
   - Potential: `/api/insider/{ticker}` or `/api/insider-trades/{ticker}`
   - Value: Insider buying/selling patterns
   - Usage: Add to daemon, poll every 15-30 min

2. **Congress/Politician Trading** (`congress` signal component exists)
   - Potential: `/api/congress/{ticker}` or `/api/politician-trades/{ticker}`
   - Value: Politician trading activity (often predictive)
   - Usage: Add to daemon, poll every 30-60 min

3. **Earnings/Events Calendar** (`calendar_catalyst` signal component exists)
   - Potential: `/api/calendar/{ticker}` or `/api/events/{ticker}`
   - Value: Upcoming earnings, events that could move stock
   - Usage: Poll daily, cache for week

4. **IV Term Structure** (`iv_term_skew` signal component exists)
   - Potential: `/api/stock/{ticker}/iv-term-structure` or `/api/stock/{ticker}/iv-skew`
   - Value: IV skew across expirations (predicts direction)
   - Usage: Poll every 15-30 min

5. **Volatility Smile** (`smile_slope` signal component exists)
   - Potential: `/api/stock/{ticker}/volatility-smile` or `/api/stock/{ticker}/smile`
   - Value: Volatility smile slope (market sentiment)
   - Usage: Poll every 15-30 min

6. **Open Interest Changes** (`oi_change` signal component exists)
   - Potential: `/api/stock/{ticker}/oi-change` (may already exist in contracts)
   - Value: OI changes indicate new positions
   - Usage: Poll every 10-15 min

7. **IV Rank** (`iv_rank` signal component exists)
   - Potential: `/api/stock/{ticker}/iv-rank` or `/api/stock/{ticker}/volatility/rank`
   - Value: IV percentile (cheap/expensive options)
   - Usage: Poll every 15-30 min

### Medium Priority

8. **Unusual Activity Alerts**
   - Potential: `/api/alerts/{ticker}` or `/api/unusual-activity/{ticker}`
   - Value: Pre-filtered unusual activity
   - Usage: Could reduce need to filter flow-alerts

9. **Option Chain Data**
   - Potential: `/api/stock/{ticker}/option-chain` or `/api/options/{ticker}/chain`
   - Value: Full option chain with OI, volume, IV
   - Usage: Poll every 5-10 min for active tickers

10. **Market Regime Indicators**
    - Potential: `/api/market/regime` or `/api/market/vix-term-structure`
    - Value: Market-wide regime (bull/bear/neutral)
    - Usage: Poll every 5-10 min

11. **Sweep/Block Detection**
    - Potential: `/api/option-trades/sweeps/{ticker}` or `/api/option-trades/blocks/{ticker}`
    - Value: Large institutional sweeps/blocks
    - Usage: Poll every 2-5 min (high frequency)

12. **Unusual Volume Alerts**
    - Potential: `/api/volume-alerts/{ticker}` or `/api/unusual-volume/{ticker}`
    - Value: Unusual volume spikes
    - Usage: Poll every 5-10 min

## Implementation Recommendations

### Phase 1: High-Value, Low-Frequency (Add Now)
These won't significantly impact rate limits:

1. **Insider Trading** - Poll every 30 min
   - Estimated: 53 tickers × 2 calls/hour × 6.5 hours = 689 calls/day
   
2. **Congress Trading** - Poll every 60 min
   - Estimated: 53 tickers × 1 call/hour × 6.5 hours = 345 calls/day

3. **Earnings Calendar** - Poll once daily per ticker
   - Estimated: 53 tickers × 1 call = 53 calls/day

4. **IV Rank** - Poll every 30 min
   - Estimated: 53 tickers × 2 calls/hour × 6.5 hours = 689 calls/day

**Phase 1 Total: ~1,776 calls/day**

### Phase 2: Medium-Frequency (Add if Rate Limit Allows)
5. **IV Term Structure** - Poll every 15 min
   - Estimated: 53 tickers × 4 calls/hour × 6.5 hours = 1,378 calls/day

6. **Volatility Smile** - Poll every 15 min
   - Estimated: 53 tickers × 4 calls/hour × 6.5 hours = 1,378 calls/day

7. **Open Interest Changes** - Poll every 10 min
   - Estimated: 53 tickers × 6 calls/hour × 6.5 hours = 2,067 calls/day

**Phase 2 Total: ~4,823 calls/day**

### Current Usage + Phase 1 + Phase 2
- Current: ~13,000 calls/day
- Phase 1: ~1,776 calls/day
- Phase 2: ~4,823 calls/day
- **Total: ~19,599 calls/day** (EXCEEDS 15,000 limit)

### Revised Strategy: Selective Addition

**Option A: Add Phase 1 Only**
- Current: ~13,000 calls/day
- Phase 1: ~1,776 calls/day
- **Total: ~14,776 calls/day** (98% of limit - SAFE)

**Option B: Add Phase 1 + Reduce Other Frequencies**
- Reduce option_flow from 2.5 min to 3 min: saves ~1,378 calls/day
- Add Phase 1: +1,776 calls/day
- Net: +398 calls/day
- **Total: ~13,398 calls/day** (89% of limit - SAFE)

**Option C: Prioritize Active Tickers**
- Only poll new endpoints for top 20 tickers
- Phase 1 (20 tickers): ~670 calls/day
- Phase 2 (20 tickers): ~1,820 calls/day
- **Total: ~15,490 calls/day** (103% - slightly over, but manageable with market-aware polling)

## Recommended Next Steps

1. **Test endpoint availability** - Try each endpoint to confirm it exists
2. **Start with Phase 1** - Add insider, congress, earnings, IV rank
3. **Monitor rate limits** - Watch for 75%+ usage warnings
4. **Add Phase 2 selectively** - Only if rate limit allows

## Endpoint Testing Script Needed

Create a script to test which endpoints are available:
```python
endpoints_to_test = [
    "/api/insider/{ticker}",
    "/api/congress/{ticker}",
    "/api/calendar/{ticker}",
    "/api/stock/{ticker}/iv-rank",
    "/api/stock/{ticker}/iv-term-structure",
    "/api/stock/{ticker}/volatility-smile",
    "/api/stock/{ticker}/oi-change",
    # ... etc
]
```
