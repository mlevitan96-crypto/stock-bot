# Deployment Instructions - Audit Fixes

## Current Status

✅ **All fixes are committed locally**  
⚠️ **GitHub push is blocked** due to secrets in old commits (not current files)  
✅ **Manual deployment scripts are ready**

---

## Quick Deployment (Recommended)

### On Droplet:

```bash
cd ~/stock-bot

# Copy and run the manual fix script
# (Copy contents of APPLY_FIXES_MANUAL.sh from local repo)
cat > APPLY_FIXES_MANUAL.sh << 'SCRIPT_EOF'
[paste script content here]
SCRIPT_EOF

chmod +x APPLY_FIXES_MANUAL.sh
bash APPLY_FIXES_MANUAL.sh
```

The script will:
- ✅ Fix hardcoded paths
- ✅ Fix hardcoded API endpoints
- ✅ Add missing endpoint polling (insider, calendar, congress, institutional)
- ✅ Verify syntax

---

## Alternative: Manual Application

If the script doesn't work, apply fixes manually:

### 1. Fix `signals/uw_adaptive.py`
```python
# Add import at top:
from config.registry import StateFiles

# Change:
STATE_FILE = Path("data/adaptive_gate_state.json")
# To:
STATE_FILE = StateFiles.ADAPTIVE_GATE_STATE
```

### 2. Fix `uw_flow_daemon.py`
```python
# Add import near top:
from config.registry import APIConfig

# In UWClient.__init__, change:
self.base = "https://api.unusualwhales.com"
# To:
self.base = APIConfig.UW_BASE_URL
```

### 3. Fix `main.py`
```python
# Add import at top:
from config.registry import APIConfig

# In Config class, change:
ALPACA_BASE_URL = get_env("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
# To:
ALPACA_BASE_URL = get_env("ALPACA_BASE_URL", APIConfig.ALPACA_BASE_URL)
```

### 4. Add Missing Endpoints to `uw_flow_daemon.py`

Add these methods to `UWClient` class (after `get_max_pain`):
```python
def get_insider(self, ticker: str) -> Dict:
    raw = self._get(f"/api/insider/{ticker}")
    data = raw.get("data", {})
    if isinstance(data, list) and len(data) > 0:
        data = data[0]
    return data if isinstance(data, dict) else {}

def get_calendar(self, ticker: str) -> Dict:
    raw = self._get(f"/api/calendar/{ticker}")
    data = raw.get("data", {})
    if isinstance(data, list) and len(data) > 0:
        data = data[0]
    return data if isinstance(data, dict) else {}

def get_congress(self, ticker: str) -> Dict:
    raw = self._get(f"/api/congress/{ticker}")
    data = raw.get("data", {})
    if isinstance(data, list) and len(data) > 0:
        data = data[0]
    return data if isinstance(data, dict) else {}

def get_institutional(self, ticker: str) -> Dict:
    raw = self._get(f"/api/institutional/{ticker}")
    data = raw.get("data", {})
    if isinstance(data, list) and len(data) > 0:
        data = data[0]
    return data if isinstance(data, dict) else {}
```

Add to `SmartPoller.intervals`:
```python
"insider": 1800,          # 30 min
"calendar": 3600,         # 60 min
"congress": 1800,         # 30 min
"institutional": 1800,    # 30 min
```

Add polling calls in `_poll_ticker()` (after max_pain polling):
```python
# Poll insider
if self.poller.should_poll("insider"):
    try:
        insider_data = self.client.get_insider(ticker)
        if insider_data:
            self._update_cache(ticker, {"insider": insider_data})
            print(f"[UW-DAEMON] Updated insider for {ticker}", flush=True)
    except Exception as e:
        print(f"[UW-DAEMON] Error fetching insider: {e}", flush=True)

# Poll calendar
if self.poller.should_poll("calendar"):
    try:
        calendar_data = self.client.get_calendar(ticker)
        if calendar_data:
            self._update_cache(ticker, {"calendar": calendar_data})
            print(f"[UW-DAEMON] Updated calendar for {ticker}", flush=True)
    except Exception as e:
        print(f"[UW-DAEMON] Error fetching calendar: {e}", flush=True)

# Poll congress
if self.poller.should_poll("congress"):
    try:
        congress_data = self.client.get_congress(ticker)
        if congress_data:
            self._update_cache(ticker, {"congress": congress_data})
            print(f"[UW-DAEMON] Updated congress for {ticker}", flush=True)
    except Exception as e:
        print(f"[UW-DAEMON] Error fetching congress: {e}", flush=True)

# Poll institutional
if self.poller.should_poll("institutional"):
    try:
        institutional_data = self.client.get_institutional(ticker)
        if institutional_data:
            self._update_cache(ticker, {"institutional": institutional_data})
            print(f"[UW-DAEMON] Updated institutional for {ticker}", flush=True)
    except Exception as e:
        print(f"[UW-DAEMON] Error fetching institutional: {e}", flush=True)
```

---

## Verification

After applying fixes:

```bash
# Test syntax
python3 -m py_compile signals/uw_adaptive.py uw_flow_daemon.py main.py

# Should show no errors
```

---

## Deploy

```bash
# Stop existing
pkill -f "deploy_supervisor|uw.*daemon"
sleep 3

# Start supervisor
cd ~/stock-bot
source venv/bin/activate
nohup python3 deploy_supervisor.py > logs/supervisor.log 2>&1 &

# Wait and verify
sleep 15
pgrep -f "deploy_supervisor" && echo "✅ Supervisor running"
pgrep -f "uw_flow_daemon" && echo "✅ Daemon running"
```

---

**All fixes are ready - apply manually on droplet using the script or manual steps above!**
