# Next Steps - Deploy Audit Fixes

## Current Situation

✅ **All fixes are committed locally**  
⚠️ **GitHub push is blocked** due to secrets in old commits (not current files)  
✅ **Fixes are ready to deploy**

---

## Option 1: Unblock GitHub Push (Recommended)

GitHub detected a secret in old commits. To push:

1. **Visit the unblock URL:**
   ```
   https://github.com/mlevitan96-crypto/stock-bot/security/secret-scanning/unblock-secret/37G6i1ZeYL7PuLmWFlDdeYVvfdq
   ```

2. **Allow the secret** (it's in old commits, not current files)

3. **Push again:**
   ```bash
   git push origin main
   ```

4. **Then on droplet:**
   ```bash
   cd ~/stock-bot
   git pull origin main
   ```

---

## Option 2: Apply Fixes Manually on Droplet

If you can't unblock GitHub push right now, apply fixes manually:

### Step 1: Copy Manual Fix Script to Droplet

**On your local machine**, copy the script content from `APPLY_FIXES_MANUAL.sh` and paste it into a file on the droplet:

```bash
# On droplet:
cd ~/stock-bot
cat > APPLY_FIXES_MANUAL.sh << 'SCRIPT_EOF'
[paste contents of APPLY_FIXES_MANUAL.sh here]
SCRIPT_EOF
chmod +x APPLY_FIXES_MANUAL.sh
```

### Step 2: Run Manual Fix Script

```bash
cd ~/stock-bot
bash APPLY_FIXES_MANUAL.sh
```

This will:
- ✅ Fix hardcoded paths
- ✅ Fix hardcoded API endpoints  
- ✅ Add missing endpoint polling
- ✅ Verify syntax

### Step 3: Deploy

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

## Option 3: Quick Manual Fixes (If Script Fails)

If the script doesn't work, apply fixes manually:

### Fix 1: signals/uw_adaptive.py
```python
# Change:
STATE_FILE = Path("data/adaptive_gate_state.json")

# To:
from config.registry import StateFiles
STATE_FILE = StateFiles.ADAPTIVE_GATE_STATE
```

### Fix 2: uw_flow_daemon.py
```python
# In UWClient.__init__, change:
self.base = "https://api.unusualwhales.com"

# To:
from config.registry import APIConfig
self.base = APIConfig.UW_BASE_URL
```

### Fix 3: main.py
```python
# In Config class, change:
ALPACA_BASE_URL = get_env("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")

# To:
ALPACA_BASE_URL = get_env("ALPACA_BASE_URL", APIConfig.ALPACA_BASE_URL)
```

### Fix 4: Add Missing Endpoints to uw_flow_daemon.py

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
    except Exception as e:
        print(f"[UW-DAEMON] Error fetching insider: {e}", flush=True)

# Poll calendar
if self.poller.should_poll("calendar"):
    try:
        calendar_data = self.client.get_calendar(ticker)
        if calendar_data:
            self._update_cache(ticker, {"calendar": calendar_data})
    except Exception as e:
        print(f"[UW-DAEMON] Error fetching calendar: {e}", flush=True)

# Poll congress
if self.poller.should_poll("congress"):
    try:
        congress_data = self.client.get_congress(ticker)
        if congress_data:
            self._update_cache(ticker, {"congress": congress_data})
    except Exception as e:
        print(f"[UW-DAEMON] Error fetching congress: {e}", flush=True)

# Poll institutional
if self.poller.should_poll("institutional"):
    try:
        institutional_data = self.client.get_institutional(ticker)
        if institutional_data:
            self._update_cache(ticker, {"institutional": institutional_data})
    except Exception as e:
        print(f"[UW-DAEMON] Error fetching institutional: {e}", flush=True)
```

---

## Verification

After applying fixes:

```bash
# Test syntax
python3 -m py_compile signals/uw_adaptive.py uw_flow_daemon.py main.py

# Re-run audit
python3 COMPREHENSIVE_CODE_AUDIT.py
# Should show reduced issues
```

---

## Summary

**Recommended:** Use Option 1 (unblock GitHub push) - fastest and cleanest  
**Alternative:** Use Option 2 (manual script) if unblock isn't possible  
**Fallback:** Use Option 3 (manual fixes) if script fails

All fixes are ready - just need to get them to the droplet!
