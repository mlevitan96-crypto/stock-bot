# Dashboard Endpoint Schema Check

**Generated:** 2026-01-28T16:08:19.715054+00:00

**Symbol keys (sample):** ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'AMD', 'NFLX', 'INTC', 'SPY', 'QQQ', 'IWM', 'DIA', 'XLF']

- **AAPL:** keys=['market_tide', 'flow_trades', 'sentiment', 'conviction', 'total_premium', 'call_premium', 'put_premium', 'net_premium', 'trade_count', 'flow', '_last_update', 'iv_term_skew'], has_ts/last_update=False
- **MSFT:** keys=['market_tide', 'flow_trades', 'sentiment', 'conviction', 'total_premium', 'call_premium', 'put_premium', 'net_premium', 'trade_count', 'flow', '_last_update', 'iv_term_skew'], has_ts/last_update=False
- **GOOGL:** keys=['market_tide', 'flow_trades', 'sentiment', 'conviction', 'total_premium', 'call_premium', 'put_premium', 'net_premium', 'trade_count', 'flow', '_last_update', 'iv_term_skew'], has_ts/last_update=False

**Requirement:** symbol values are dicts; optional ts/last_update.