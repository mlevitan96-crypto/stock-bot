#!/usr/bin/env python3
"""
Investigate why components with data are returning 0.0
"""

from droplet_client import DropletClient

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("INVESTIGATING ZERO COMPONENTS WITH DATA")
        print("=" * 80)
        print()
        
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from main import read_uw_cache\n"
            "from uw_composite_v2 import compute_market_tide_component, compute_congress_component, compute_shorts_component, compute_institutional_component, _to_num\n"
            "from uw_enrichment_v2 import enrich_signal\n"
            "\n"
            "cache = read_uw_cache()\n"
            "symbol = 'AAPL'\n"
            "enriched = enrich_signal(symbol, cache, 'mixed')\n"
            "\n"
            "print('INVESTIGATING COMPONENTS WITH DATA BUT RETURNING 0.0:')\n"
            "print('=' * 80)\n"
            "print()\n"
            "\n"
            "# 1. Market Tide\n"
            "print('1. MARKET TIDE:')\n"
            "tide_data = enriched.get('market_tide', {})\n"
            "print(f'  Data exists: {bool(tide_data)}')\n"
            "print(f'  Data keys: {list(tide_data.keys()) if isinstance(tide_data, dict) else \"NOT DICT\"}')\n"
            "print(f'  Data value: {tide_data}')\n"
            "flow_sign = 1 if enriched.get('sentiment') == 'BULLISH' else (-1 if enriched.get('sentiment') == 'BEARISH' else 0)\n"
            "tide_comp, tide_notes = compute_market_tide_component(tide_data, flow_sign)\n"
            "print(f'  Component result: {tide_comp}')\n"
            "print(f'  Notes: {tide_notes}')\n"
            "print()\n"
            "\n"
            "# 2. Greeks Gamma\n"
            "print('2. GREEKS GAMMA:')\n"
            "greeks_data = enriched.get('greeks', {})\n"
            "print(f'  Data exists: {bool(greeks_data)}')\n"
            "print(f'  Data keys: {list(greeks_data.keys())[:10] if isinstance(greeks_data, dict) else \"NOT DICT\"}')\n"
            "gamma_exposure = _to_num(greeks_data.get('gamma_exposure', 0))\n"
            "gamma_squeeze = greeks_data.get('gamma_squeeze_setup', False)\n"
            "print(f'  gamma_exposure: {gamma_exposure}')\n"
            "print(f'  gamma_squeeze_setup: {gamma_squeeze}')\n"
            "print(f'  Threshold check: > 500000 = {abs(gamma_exposure) > 500000}, > 100000 = {abs(gamma_exposure) > 100000}')\n"
            "print()\n"
            "\n"
            "# 3. IV Rank\n"
            "print('3. IV RANK:')\n"
            "iv_data = enriched.get('iv_rank', {})\n"
            "print(f'  Data exists: {bool(iv_data)}')\n"
            "print(f'  Data keys: {list(iv_data.keys()) if isinstance(iv_data, dict) else \"NOT DICT\"}')\n"
            "iv_rank_val = _to_num(iv_data.get('iv_rank', 50))\n"
            "print(f'  iv_rank value: {iv_rank_val}')\n"
            "print(f'  Threshold check: < 20 = {iv_rank_val < 20}, < 30 = {iv_rank_val < 30}, > 80 = {iv_rank_val > 80}, > 70 = {iv_rank_val > 70}')\n"
            "print()\n"
            "\n"
            "# 4. OI Change\n"
            "print('4. OI CHANGE:')\n"
            "oi_data = enriched.get('oi_change', {})\n"
            "print(f'  Data exists: {bool(oi_data)}')\n"
            "print(f'  Data keys: {list(oi_data.keys())[:10] if isinstance(oi_data, dict) else \"NOT DICT\"}')\n"
            "net_oi = _to_num(oi_data.get('net_oi_change', 0))\n"
            "oi_sentiment = oi_data.get('oi_sentiment', 'NEUTRAL')\n"
            "print(f'  net_oi_change: {net_oi}')\n"
            "print(f'  oi_sentiment: {oi_sentiment}')\n"
            "print(f'  flow_sign: {flow_sign}')\n"
            "print(f'  Threshold check: > 50000 and BULLISH and flow>0 = {net_oi > 50000 and oi_sentiment == \"BULLISH\" and flow_sign > 0}')\n"
            "print()\n"
            "\n"
            "# 5. FTD Pressure\n"
            "print('5. FTD PRESSURE:')\n"
            "ftd_data = enriched.get('ftd', {})\n"
            "print(f'  Data exists: {bool(ftd_data)}')\n"
            "print(f'  Data keys: {list(ftd_data.keys()) if isinstance(ftd_data, dict) else \"NOT DICT\"}')\n"
            "ftd_count = _to_num(ftd_data.get('ftd_count', 0))\n"
            "ftd_squeeze = ftd_data.get('squeeze_pressure', False)\n"
            "print(f'  ftd_count: {ftd_count}')\n"
            "print(f'  squeeze_pressure: {ftd_squeeze}')\n"
            "print(f'  Threshold check: > 200000 = {ftd_count > 200000}, > 100000 = {ftd_count > 100000}, > 50000 = {ftd_count > 50000}')\n"
            "print()\n"
            "\n"
            "# 6. Smile Slope\n"
            "print('6. SMILE SLOPE:')\n"
            "smile_slope = enriched.get('smile_slope', 0)\n"
            "print(f'  smile_slope value: {smile_slope}')\n"
            "print(f'  abs(smile_slope): {abs(smile_slope)}')\n"
            "print()\n"
            "\n"
            "# 7. Regime\n"
            "print('7. REGIME MODIFIER:')\n"
            "regime = 'mixed'\n"
            "print(f'  regime: {regime}')\n"
            "print(f'  flow_sign: {flow_sign}')\n"
            "aligned = (regime == 'RISK_ON' and flow_sign == +1) or (regime == 'RISK_OFF' and flow_sign == -1)\n"
            "opposite = (regime == 'RISK_ON' and flow_sign == -1) or (regime == 'RISK_OFF' and flow_sign == +1)\n"
            "print(f'  aligned: {aligned}, opposite: {opposite}')\n"
            "print(f'  regime_factor calculation: RISK_ON/ RISK_OFF not matched (regime is mixed)')\n"
            "print()\n"
            "PYEOF",
            timeout=120
        )
        print(result['stdout'])
        print()
        
    except Exception as e:
        print(f"[ERROR] Investigation failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

