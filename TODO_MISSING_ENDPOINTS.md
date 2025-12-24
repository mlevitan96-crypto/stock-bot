# Missing Endpoint Polling - Implementation Guide

## Missing Endpoints
- insider
- calendar  
- congress
- institutional

## Implementation Steps

1. Add polling methods to `uw_flow_daemon.py`:
   ```python
   def _poll_insider(self, ticker: str):
       # Poll insider trading data
       pass
   
   def _poll_calendar(self, ticker: str):
       # Poll calendar/events data
       pass
   
   def _poll_congress(self, ticker: str):
       # Poll congress trading data
       pass
   
   def _poll_institutional(self, ticker: str):
       # Poll institutional data
       pass
   ```

2. Add to SmartPoller intervals
3. Call from main polling loop
4. Store in cache with proper keys

See `config/uw_signal_contracts.py` for endpoint definitions.
