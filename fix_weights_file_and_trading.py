#!/usr/bin/env python3
"""
Fix missing weights file and investigate why trading isn't happening
"""

from droplet_client import DropletClient
import json
import sys

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("FIXING WEIGHTS FILE AND INVESTIGATING TRADING ISSUE")
        print("=" * 80)
        print()
        
        # 1. Create default weights file
        print("1. Creating default weights file...")
        weights_v3 = {
            "options_flow": 2.4,
            "dark_pool": 1.3,
            "insider": 0.5,
            "iv_term_skew": 0.6,
            "smile_slope": 0.35,
            "whale_persistence": 0.7,
            "event_alignment": 0.4,
            "toxicity_penalty": -0.9,
            "temporal_motif": 0.6,
            "regime_modifier": 0.3,
            "congress": 0.9,
            "shorts_squeeze": 0.7,
            "institutional": 0.5,
            "market_tide": 0.4,
            "calendar_catalyst": 0.45,
            "etf_flow": 0.3,
            "greeks_gamma": 0.4,
            "ftd_pressure": 0.3,
            "iv_rank": 0.2,
            "oi_change": 0.35,
            "squeeze_score": 0.2
        }
        
        weights_payload = {
            "weights": weights_v3,
            "updated_at": int(time.time()),
            "updated_dt": "2026-01-06 00:00:00 UTC",
            "source": "default_weights_v3"
        }
        
        # Write to both locations (data/ and state/)
        weights_json = json.dumps(weights_payload, indent=2)
        
        # Write to data/uw_weights.json (where SRE check looks)
        cmd1 = f'cd /root/stock-bot && mkdir -p data state && echo \'{json.dumps(weights_payload)}\' > data/uw_weights.json'
        stdout1, stderr1, code1 = client._execute_with_cd(cmd1, 20)
        
        # Write to state/uw_weights.json (if system uses that)
        cmd2 = f'cd /root/stock-bot && echo \'{json.dumps(weights_payload)}\' > state/uw_weights.json'
        stdout2, stderr2, code2 = client._execute_with_cd(cmd2, 20)
        
        print(f"   Created data/uw_weights.json: {'OK' if code1 == 0 else 'FAILED'}")
        print(f"   Created state/uw_weights.json: {'OK' if code2 == 0 else 'FAILED'}")
        print()
        
        # 2. Check today's signals
        print("2. Checking today's signals...")
        stdout, stderr, code = client._execute_with_cd('cd /root/stock-bot && tail -200 logs/signals.jsonl 2>&1 | grep "2026-01-06" | wc -l', 20)
        signal_count = stdout.strip() if stdout else "0"
        print(f"   Signals today: {signal_count}")
        print()
        
        # 3. Check today's gate events
        print("3. Checking today's gate events...")
        stdout, stderr, code = client._execute_with_cd('cd /root/stock-bot && tail -200 logs/gate.jsonl 2>&1 | grep "2026-01-06" | tail -5', 30)
        if stdout:
            print("   Recent gate events:")
            for line in stdout.strip().split('\n')[:5]:
                if line.strip():
                    print(f"     {line[:150]}")
        else:
            print("   No gate events today")
        print()
        
        # 4. Check if market is open
        print("4. Checking market status...")
        stdout, stderr, code = client._execute_with_cd('cd /root/stock-bot && python3 -c "from datetime import datetime; import pytz; now = datetime.now(pytz.timezone(\"America/New_York\")); print(f\"ET: {now.strftime(\\\"%H:%M\\\")}\"); print(\"OPEN\" if 9 <= now.hour < 16 else \"CLOSED\")" 2>&1', 20)
        print(f"   Market status: {stdout.strip() if stdout else 'UNKNOWN'}")
        print()
        
        # 5. Test mock signal scoring
        print("5. Testing mock signal scoring...")
        stdout, stderr, code = client._execute_with_cd('cd /root/stock-bot && python3 -c "from mock_signal_injection import inject_perfect_whale_signal; score, success = inject_perfect_whale_signal(); print(f\"Mock signal score: {score:.2f}, Success: {success}\")" 2>&1', 30)
        if stdout:
            print(f"   {stdout.strip()}")
        else:
            print(f"   Error: {stderr[:200] if stderr else 'Unknown'}")
        print()
        
        print("=" * 80)
        print("FIX COMPLETE")
        print("=" * 80)
        
        return 0
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        client.close()

if __name__ == "__main__":
    import time
    sys.exit(main())
