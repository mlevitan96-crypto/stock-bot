#!/usr/bin/env python3
"""
Fix dark_pool normalization - the API returns data but normalization is failing
"""

from droplet_client import DropletClient
import json

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("FIXING DARK_POOL NORMALIZATION")
        print("=" * 80)
        print()
        
        # 1. Test what the API actually returns
        print("1. TESTING API RESPONSE FORMAT")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from uw_flow_daemon import UWClient\n"
            "import os\n"
            "from dotenv import load_dotenv\n"
            "load_dotenv()\n"
            "client = UWClient()\n"
            "dp_data = client.get_dark_pool_levels('AAPL')\n"
            "print(f'API response type: {type(dp_data)}')\n"
            "print(f'API response length: {len(dp_data) if isinstance(dp_data, list) else \"NOT A LIST\"}')\n"
            "if isinstance(dp_data, list) and len(dp_data) > 0:\n"
            "    print(f'First item type: {type(dp_data[0])}')\n"
            "    print(f'First item: {dp_data[0]}')\n"
            "    print(f'First item keys: {list(dp_data[0].keys()) if isinstance(dp_data[0], dict) else \"NOT A DICT\"}')\n"
            "    # Check what field has premium\n"
            "    if isinstance(dp_data[0], dict):\n"
            "        for key in dp_data[0].keys():\n"
            "            val = dp_data[0][key]\n"
            "            if isinstance(val, (int, float)) or (isinstance(val, str) and val.replace('.', '').replace('-', '').isdigit()):\n"
            "                print(f'  {key}: {val} (numeric)')\n"
            "PYEOF",
            timeout=60
        )
        print(result['stdout'])
        print()
        
        # 2. Test normalization with real data
        print("2. TESTING NORMALIZATION")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from uw_flow_daemon import UWFlowDaemon\n"
            "import os\n"
            "from dotenv import load_dotenv\n"
            "load_dotenv()\n"
            "daemon = UWFlowDaemon()\n"
            "# Get real data\n"
            "dp_data = daemon.client.get_dark_pool_levels('AAPL')\n"
            "print(f'Raw data length: {len(dp_data) if isinstance(dp_data, list) else 0}')\n"
            "if isinstance(dp_data, list) and len(dp_data) > 0:\n"
            "    print(f'Raw data sample: {dp_data[0] if len(dp_data) > 0 else \"EMPTY\"}')\n"
            "    # Test normalization\n"
            "    normalized = daemon._normalize_dark_pool(dp_data)\n"
            "    print(f'Normalized result: {normalized}')\n"
            "    print(f'Normalized has data: {bool(normalized)}')\n"
            "else:\n"
            "    print('API returned empty list - this is the problem!')\n"
            "PYEOF",
            timeout=60
        )
        print(result['stdout'])
        print()
        
    except Exception as e:
        print(f"[ERROR] Fix failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

