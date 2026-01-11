#!/bin/bash
# Manual Fix Application Script
# Use this if GitHub push is blocked
# Run on droplet: bash APPLY_FIXES_MANUAL.sh

cd ~/stock-bot

echo "=========================================="
echo "APPLYING AUDIT FIXES MANUALLY"
echo "=========================================="
echo ""

# Fix 1: Hardcoded path in signals/uw_adaptive.py
echo "[1] Fixing hardcoded path in signals/uw_adaptive.py..."
if grep -q 'Path("data/adaptive_gate_state.json")' signals/uw_adaptive.py 2>/dev/null; then
    sed -i 's|Path("data/adaptive_gate_state.json")|StateFiles.ADAPTIVE_GATE_STATE|g' signals/uw_adaptive.py
    # Add import if not present
    if ! grep -q "from config.registry import StateFiles" signals/uw_adaptive.py; then
        sed -i '1a from config.registry import StateFiles' signals/uw_adaptive.py
    fi
    echo "  [OK] Fixed hardcoded path"
else
    echo "  [INFO] Already fixed or not found"
fi

# Fix 2: Hardcoded API endpoint in uw_flow_daemon.py
echo ""
echo "[2] Fixing hardcoded API endpoint in uw_flow_daemon.py..."
if grep -q '"https://api.unusualwhales.com"' uw_flow_daemon.py 2>/dev/null; then
    # Add import
    if ! grep -q "from config.registry import APIConfig" uw_flow_daemon.py; then
        sed -i '/^import os/a from config.registry import APIConfig' uw_flow_daemon.py
    fi
    # Replace hardcoded URL
    sed -i 's|"https://api.unusualwhales.com"|APIConfig.UW_BASE_URL|g' uw_flow_daemon.py
    echo "  [OK] Fixed hardcoded API endpoint"
else
    echo "  [INFO] Already fixed or not found"
fi

# Fix 3: Hardcoded API endpoint in main.py
echo ""
echo "[3] Fixing hardcoded API endpoint in main.py..."
if grep -q '"https://paper-api.alpaca.markets"' main.py 2>/dev/null; then
    # Replace (APIConfig already imported)
    sed -i 's|get_env("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")|get_env("ALPACA_BASE_URL", APIConfig.ALPACA_BASE_URL)|g' main.py
    echo "  [OK] Fixed hardcoded API endpoint"
else
    echo "  [INFO] Already fixed or not found"
fi

# Fix 4: Add missing endpoint polling methods
echo ""
echo "[4] Adding missing endpoint polling methods..."
if ! grep -q "def get_insider" uw_flow_daemon.py 2>/dev/null; then
    python3 << 'PYEOF'
from pathlib import Path
import re

file_path = Path("uw_flow_daemon.py")
content = file_path.read_text(encoding='utf-8', errors='ignore')

# Find insertion point (after get_max_pain)
max_pain_match = re.search(r'def get_max_pain\(.*?\n.*?return data if isinstance\(data, dict\) else \{\}', content, re.DOTALL)
if max_pain_match:
    insert_pos = max_pain_match.end()
    new_methods = '''

    def get_insider(self, ticker: str) -> Dict:
        """Get insider trading data for a ticker."""
        raw = self._get(f"/api/insider/{ticker}")
        data = raw.get("data", {})
        if isinstance(data, list) and len(data) > 0:
            data = data[0]
        return data if isinstance(data, dict) else {}
    
    def get_calendar(self, ticker: str) -> Dict:
        """Get calendar/events data for a ticker."""
        raw = self._get(f"/api/calendar/{ticker}")
        data = raw.get("data", {})
        if isinstance(data, list) and len(data) > 0:
            data = data[0]
        return data if isinstance(data, dict) else {}
    
    def get_congress(self, ticker: str) -> Dict:
        """Get congress trading data for a ticker."""
        raw = self._get(f"/api/congress/{ticker}")
        data = raw.get("data", {})
        if isinstance(data, list) and len(data) > 0:
            data = data[0]
        return data if isinstance(data, dict) else {}
    
    def get_institutional(self, ticker: str) -> Dict:
        """Get institutional data for a ticker."""
        raw = self._get(f"/api/institutional/{ticker}")
        data = raw.get("data", {})
        if isinstance(data, list) and len(data) > 0:
            data = data[0]
        return data if isinstance(data, dict) else {}
'''
    content = content[:insert_pos] + new_methods + content[insert_pos:]
    file_path.write_text(content, encoding='utf-8')
    print("  [OK] Added missing client methods")
else:
    print("  [INFO] Methods may already exist or insertion point not found")
PYEOF
else
    echo "  [INFO] Client methods already exist"
fi

# Fix 5: Add polling intervals
echo ""
echo "[5] Adding polling intervals..."
if ! grep -q '"insider":' uw_flow_daemon.py 2>/dev/null; then
    sed -i '/"market_tide": 300,/a\            "insider": 1800,          # 30 min: Insider trading (changes slowly)\n            "calendar": 3600,         # 60 min: Calendar events (changes slowly)\n            "congress": 1800,         # 30 min: Congress trading (changes slowly)\n            "institutional": 1800,    # 30 min: Institutional data (changes slowly)' uw_flow_daemon.py
    echo "  [OK] Added polling intervals"
else
    echo "  [INFO] Polling intervals already added"
fi

# Fix 6: Add polling calls
echo ""
echo "[6] Adding polling calls in _poll_ticker..."
if ! grep -q "# Poll insider" uw_flow_daemon.py 2>/dev/null; then
    python3 << 'PYEOF'
from pathlib import Path
import re

file_path = Path("uw_flow_daemon.py")
content = file_path.read_text(encoding='utf-8', errors='ignore')

# Find insertion point (after max_pain polling, before final except)
max_pain_end = re.search(r'except Exception as e:.*?print\(f"\[UW-DAEMON\] Error fetching max_pain.*?Traceback.*?flush=True\)', content, re.DOTALL)
if max_pain_end:
    insert_pos = max_pain_end.end()
    new_polling = '''
            
            # Poll insider
            if self.poller.should_poll("insider"):
                try:
                    print(f"[UW-DAEMON] Polling insider for {ticker}...", flush=True)
                    insider_data = self.client.get_insider(ticker)
                    if insider_data:
                        self._update_cache(ticker, {"insider": insider_data})
                        print(f"[UW-DAEMON] Updated insider for {ticker}: {len(str(insider_data))} bytes", flush=True)
                    else:
                        print(f"[UW-DAEMON] insider for {ticker}: API returned empty", flush=True)
                except Exception as e:
                    print(f"[UW-DAEMON] Error fetching insider for {ticker}: {e}", flush=True)
            
            # Poll calendar
            if self.poller.should_poll("calendar"):
                try:
                    print(f"[UW-DAEMON] Polling calendar for {ticker}...", flush=True)
                    calendar_data = self.client.get_calendar(ticker)
                    if calendar_data:
                        self._update_cache(ticker, {"calendar": calendar_data})
                        print(f"[UW-DAEMON] Updated calendar for {ticker}: {len(str(calendar_data))} bytes", flush=True)
                    else:
                        print(f"[UW-DAEMON] calendar for {ticker}: API returned empty", flush=True)
                except Exception as e:
                    print(f"[UW-DAEMON] Error fetching calendar for {ticker}: {e}", flush=True)
            
            # Poll congress
            if self.poller.should_poll("congress"):
                try:
                    print(f"[UW-DAEMON] Polling congress for {ticker}...", flush=True)
                    congress_data = self.client.get_congress(ticker)
                    if congress_data:
                        self._update_cache(ticker, {"congress": congress_data})
                        print(f"[UW-DAEMON] Updated congress for {ticker}: {len(str(congress_data))} bytes", flush=True)
                    else:
                        print(f"[UW-DAEMON] congress for {ticker}: API returned empty", flush=True)
                except Exception as e:
                    print(f"[UW-DAEMON] Error fetching congress for {ticker}: {e}", flush=True)
            
            # Poll institutional
            if self.poller.should_poll("institutional"):
                try:
                    print(f"[UW-DAEMON] Polling institutional for {ticker}...", flush=True)
                    institutional_data = self.client.get_institutional(ticker)
                    if institutional_data:
                        self._update_cache(ticker, {"institutional": institutional_data})
                        print(f"[UW-DAEMON] Updated institutional for {ticker}: {len(str(institutional_data))} bytes", flush=True)
                    else:
                        print(f"[UW-DAEMON] institutional for {ticker}: API returned empty", flush=True)
                except Exception as e:
                    print(f"[UW-DAEMON] Error fetching institutional for {ticker}: {e}", flush=True)
'''
    content = content[:insert_pos] + new_polling + content[insert_pos:]
    file_path.write_text(content, encoding='utf-8')
    print("  [OK] Added polling calls")
else:
    print("  [INFO] Polling calls may already exist or insertion point not found")
PYEOF
else
    echo "  [INFO] Polling calls already added"
fi

# Verify syntax
echo ""
echo "[7] Verifying syntax..."
python3 -m py_compile signals/uw_adaptive.py uw_flow_daemon.py main.py 2>&1
if [ $? -eq 0 ]; then
    echo "  [OK] All syntax checks passed"
else
    echo "  [ERROR] Syntax errors found - review above"
    exit 1
fi

echo ""
echo "=========================================="
echo "FIXES APPLIED - READY TO DEPLOY"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Restart supervisor: pkill -f deploy_supervisor && nohup python3 deploy_supervisor.py > logs/supervisor.log 2>&1 &"
echo "  2. Monitor logs: tail -f logs/uw-daemon-pc.log"
echo ""
