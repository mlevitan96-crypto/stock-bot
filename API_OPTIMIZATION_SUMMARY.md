# API Usage Optimization - Maximize to 15,000 Limit

## Strategy: Use ~93% of Daily Limit (14,000 calls)

### Market Hours Calculation (9:30 AM - 4:00 PM ET = 390 minutes)

**During Market Hours:**
- **Option Flow**: Every 2.5 minutes = 53 tickers × (390/2.5) = **8,268 calls**
- **Dark Pool**: Every 10 minutes = 53 tickers × (390/10) = **2,067 calls**
- **Greeks**: Every 30 minutes = 53 tickers × (390/30) = **689 calls**
- **Top Net Impact**: Every 5 minutes = 390/5 = **78 calls** (market-wide)

**Total During Market Hours: 11,102 calls**

**Outside Market Hours:**
- All endpoints poll 3x less frequently (conserve quota)
- Estimated additional: ~2,000 calls

**Total Daily: ~13,000 calls (87% of 15,000 limit)**

## Key Optimizations

### 1. Market-Aware Polling
- **During market hours**: Normal intervals (maximize data collection)
- **Outside market hours**: 3x longer intervals (conserve quota)

### 2. Prioritized Endpoints
- **Option Flow** (most critical): 2.5 min intervals
- **Dark Pool**: 10 min intervals
- **Greeks**: 30 min intervals (changes slowly)
- **Top Net Impact**: 5 min intervals

### 3. Rate Limit Handling
- Monitors `x-uw-daily-req-count` header
- Warns at 75% and 90% usage
- Stops polling when 429 received
- Auto-resumes after 8PM EST reset

### 4. Efficient Delays
- 1.5 seconds between tickers (balances speed with safety)
- Full cycle: ~80 seconds for 53 tickers

## Usage Breakdown

| Endpoint | Interval | Calls/Hour | Calls/Day (6.5h) |
|----------|----------|-----------|------------------|
| Option Flow | 2.5 min | 1,272 | 8,268 |
| Dark Pool | 10 min | 318 | 2,067 |
| Greeks | 30 min | 106 | 689 |
| Top Net Impact | 5 min | 12 | 78 |
| **TOTAL** | | **1,708** | **11,102** |

Plus ~2,000 calls outside market hours = **~13,000 total**

## Safety Features

1. **Buffer**: Using 87% of limit (leaves 2,000 call buffer)
2. **Rate limit detection**: Stops before hitting limit
3. **Market-aware**: Less frequent polling when market closed
4. **Auto-resume**: Resumes after 8PM EST reset

## Monitoring

Check daemon logs for:
- `[UW-DAEMON] Rate limit warning: X/15000` (at 75%)
- `[UW-DAEMON] Rate limit critical: X/15000` (at 90%)
- `[UW-DAEMON] ❌ RATE LIMITED (429)` (if limit hit)

## Future Optimization Options

If you need even more data:
1. **Reduce ticker list** to 30-40 most important (allows faster polling)
2. **Increase option_flow to 2 min** (would add ~2,000 calls)
3. **Add adaptive polling** - increase intervals as limit approaches

