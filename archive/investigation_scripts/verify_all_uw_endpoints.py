#!/usr/bin/env python3
"""
Verify ALL UW API endpoints against official API
Test each endpoint and document correct ones
"""

from droplet_client import DropletClient
import json
import time

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("VERIFYING ALL UW API ENDPOINTS")
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
            "print('Testing ALL UW API endpoints:')\n"
            "print('=' * 80)\n"
            "print()\n"
            "# All endpoints we're using\n"
            "endpoints = [\n"
            "    # Core endpoints\n"
            "    ('option_flow', '/api/option-trades/flow-alerts', {'symbol': ticker, 'limit': 10}),\n"
            "    ('darkpool_current', f'/api/darkpool/{ticker}', None),\n"
            "    ('darkpool_alt', f'/api/dark-pool/{ticker}', None),\n"
            "    ('greeks', f'/api/stock/{ticker}/greeks', None),\n"
            "    ('greek_exposure', f'/api/stock/{ticker}/greek-exposure', None),\n"
            "    ('top_net_impact', '/api/market/top-net-impact', {'limit': 10}),\n"
            "    ('market_tide', '/api/market/market-tide', None),\n"
            "    ('oi_change', f'/api/stock/{ticker}/oi-change', None),\n"
            "    ('etf_flow', f'/api/etfs/{ticker}/in-outflow', None),\n"
            "    ('iv_rank', f'/api/stock/{ticker}/iv-rank', None),\n"
            "    ('shorts_ftds', f'/api/shorts/{ticker}/ftds', None),\n"
            "    ('max_pain', f'/api/stock/{ticker}/max-pain', None),\n"
            "    ('insider', f'/api/insider/{ticker}', None),\n"
            "    ('calendar', f'/api/calendar/{ticker}', None),\n"
            "    ('congress', f'/api/congress/{ticker}', None),\n"
            "    ('institutional', f'/api/institutional/{ticker}', None),\n"
            "    # Alternative endpoints to test\n"
            "    ('congress_alt', '/api/congress', None),\n"
            "    ('institutional_alt', '/api/institutional', None),\n"
            "    ('insider_alt', '/api/insider', None),\n"
            "]\n"
            "results = {}\n"
            "for name, endpoint, params in endpoints:\n"
            "    try:\n"
            "        url = base + endpoint\n"
            "        r = requests.get(url, headers=headers, params=params, timeout=10)\n"
            "        status = r.status_code\n"
            "        if status == 200:\n"
            "            data = r.json()\n"
            "            data_field = data.get('data', {})\n"
            "            has_data = bool(data_field) and (\n"
            "                (isinstance(data_field, list) and len(data_field) > 0) or\n"
            "                (isinstance(data_field, dict) and len(data_field) > 0)\n"
            "            )\n"
            "            results[name] = {\n"
            "                'status': 'OK',\n"
            "                'endpoint': endpoint,\n"
            "                'has_data': has_data,\n"
            "                'data_type': type(data_field).__name__,\n"
            "                'data_length': len(data_field) if isinstance(data_field, (list, dict)) else 0\n"
            "            }\n"
            "            print(f'{name:25} {endpoint:40} [OK] has_data={has_data}')\n"
            "        elif status == 404:\n"
            "            results[name] = {'status': '404', 'endpoint': endpoint}\n"
            "            print(f'{name:25} {endpoint:40} [404] NOT FOUND')\n"
            "        else:\n"
            "            results[name] = {'status': str(status), 'endpoint': endpoint}\n"
            "            print(f'{name:25} {endpoint:40} [{status}] ERROR')\n"
            "    except Exception as e:\n"
            "        results[name] = {'status': 'ERROR', 'endpoint': endpoint, 'error': str(e)[:50]}\n"
            "        print(f'{name:25} {endpoint:40} [ERROR] {str(e)[:50]}')\n"
            "print()\n"
            "print('=' * 80)\n"
            "print('SUMMARY - CORRECT ENDPOINTS:')\n"
            "print('=' * 80)\n"
            "for name, result in results.items():\n"
            "    if result.get('status') == 'OK' and result.get('has_data'):\n"
            "        print(f'✅ {name:25} {result[\"endpoint\"]}')\n"
            "    elif result.get('status') == 'OK':\n"
            "        print(f'⚠️  {name:25} {result[\"endpoint\"]} (returns empty)')\n"
            "    elif result.get('status') == '404':\n"
            "        print(f'❌ {name:25} {result[\"endpoint\"]} (DOES NOT EXIST)')\n"
            "PYEOF",
            timeout=180
        )
        print(result['stdout'])
        print()
        
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

