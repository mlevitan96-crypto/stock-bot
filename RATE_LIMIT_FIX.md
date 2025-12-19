# RATE LIMIT FIX - Daily Limit Exceeded

## Problem Identified

The API returned **HTTP 429 - Daily Request Limit Hit**:
- Daily limit: **15,000 requests**
- Current status: **LIMIT EXCEEDED**
- Limit resets: **8PM EST / 5PM PST** (after post-market closes)

## Root Cause

With 53 tickers and polling every 60 seconds:
- 53 tickers × 60 calls/hour = **3,180 calls/hour**
- Over 6.5 hours = **~20,000 calls** (EXCEEDS 15,000 limit!)

## Fixes Applied

### 1. Reduced Polling Intervals
- `option_flow`: 60s → **300s (5 min)**
- `top_net_impact`: 300s → **600s (10 min)**
- `greek_exposure`: 900s → **1800s (30 min)**
- `dark_pool_levels`: 120s → **300s (5 min)**

### 2. Increased Delay Between Tickers
- Delay: 0.5s → **2.0s** between tickers

### 3. Added Rate Limit Detection
- Now checks `x-uw-daily-req-count` and `x-uw-token-req-limit` headers
- Logs warnings at 75% and 90% usage
- Stops making calls when 429 is received

## New Usage Calculation

With 53 tickers and 5-minute intervals:
- 53 tickers × 12 calls/hour = **636 calls/hour**
- Over 6.5 hours = **~4,134 calls** (WELL UNDER 15,000 limit!)

## Deployment Steps

```bash
cd /root/stock-bot
git pull origin main --no-rebase
pkill -f uw_flow_daemon
sleep 2
# Restart supervisor (it will restart daemon with new code)
pkill -f deploy_supervisor
source venv/bin/activate
venv/bin/python deploy_supervisor.py
```

## Important Notes

1. **Limit resets at 8PM EST** - Until then, API will return 429
2. **After reset**, the daemon will resume with new, lower polling rates
3. **Monitor rate limit headers** - Check logs for warnings
4. **Consider reducing ticker list** - If you need more frequent updates, reduce the number of tickers monitored

## Verification

After restart, check daemon logs for:
- `[UW-DAEMON] Rate limit warning: X/15000` (if approaching limit)
- `[UW-DAEMON] Retrieved X flow trades` (when API starts working again)

## Long-term Optimization

Consider:
1. **Prioritize active tickers** - Only poll high-volume tickers frequently
2. **Reduce ticker list** - Focus on 20-30 most important tickers
3. **Market hours only** - Skip polling when market is closed
4. **Adaptive polling** - Increase intervals when approaching limit

