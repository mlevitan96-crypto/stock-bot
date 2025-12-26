#!/usr/bin/env python3
"""
Test REAL API endpoints to find which ones work and return data
"""

from droplet_client import DropletClient
import json

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("TESTING REAL API ENDPOINTS")
        print("=" * 80)
        print()
        
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "import requests\n"
            "import os\n"
            "from dotenv import load_dotenv\n"
            "load_dotenv()\n"
            "api_key = os.getenv('UW_API_KEY')\n"
            "base = 'https://api.unusualwhales.com'\n"
            "headers = {'Authorization': f'Bearer {api_key}'}\n"
            "ticker = 'AAPL'\n"
            "print('Testing API endpoints for REAL data:')\n"
            "print()\n"
            "# Test dark_pool - try both variations\n"
            "endpoints = [\n"
            "    ('darkpool (current)', f'/api/darkpool/{ticker}'),\n"
            "    ('dark-pool (alt)', f'/api/dark-pool/{ticker}'),\n"
            "    ('darkpool market', '/api/darkpool'),\n"
            "    ('market_tide', '/api/market/market-tide'),\n"
            "    ('congress per-ticker', f'/api/congress/{ticker}'),\n"
            "    ('congress market', '/api/congress'),\n"
            "    ('institutional per-ticker', f'/api/institutional/{ticker}'),\n"
            "    ('institutional market', '/api/institutional'),\n"
            "    ('etf_flow', f'/api/etfs/{ticker}/in-outflow'),\n"
            "    ('oi_change', f'/api/stock/{ticker}/oi-change'),\n"
            "    ('iv_rank', f'/api/stock/{ticker}/iv-rank'),\n"
            "    ('shorts_ftds', f'/api/shorts/{ticker}/ftds'),\n"
            "]\n"
            "for name, endpoint in endpoints:\n"
            "    try:\n"
            "        url = base + endpoint\n"
            "        r = requests.get(url, headers=headers, timeout=10)\n"
            "        print(f'{name} ({endpoint}):')\n"
            "        print(f'  Status: {r.status_code}')\n"
            "        if r.status_code == 200:\n"
            "            data = r.json()\n"
            "            data_field = data.get('data', {})\n"
            "            if isinstance(data_field, list):\n"
            "                print(f'  Data: LIST with {len(data_field)} items')\n"
            "                if len(data_field) > 0:\n"
            "                    print(f'  First item keys: {list(data_field[0].keys())[:5]}')\n"
            "                    print(f'  HAS REAL DATA: YES')\n"
            "                else:\n"
            "                    print(f'  HAS REAL DATA: NO (empty list)')\n"
            "            elif isinstance(data_field, dict):\n"
            "                print(f'  Data: DICT with keys: {list(data_field.keys())[:5]}')\n"
            "                if len(data_field) > 0:\n"
            "                    print(f'  HAS REAL DATA: YES')\n"
            "                else:\n"
            "                    print(f'  HAS REAL DATA: NO (empty dict)')\n"
            "            else:\n"
            "                print(f'  Data type: {type(data_field).__name__}')\n"
            "        elif r.status_code == 404:\n"
            "            print(f'  ERROR: 404 - Endpoint does not exist')\n"
            "        else:\n"
            "            print(f'  ERROR: {r.status_code} - {r.text[:100]}')\n"
            "    except Exception as e:\n"
            "        print(f'{name} ({endpoint}): ERROR - {str(e)[:100]}')\n"
            "    print()\n"
            "PYEOF",
            timeout=120
        )
        print(result['stdout'])
        print()
        
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

