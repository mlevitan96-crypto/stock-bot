#!/usr/bin/env python3
"""
Enhanced Position Monitoring - Add to health checks
This script adds position state validation to detect discrepancies immediately.
"""

# This will be integrated into the health check system
# For now, this is a standalone validation function

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from alpaca_trade_api import REST
from dotenv import load_dotenv

load_dotenv()

def validate_position_state():
    """
    Validate position state - compare bot metadata with Alpaca API.
    Returns validation result with discrepancy details.
    """
    try:
        # Get Alpaca positions (authoritative)
        api = REST(os.getenv('ALPACA_KEY'), os.getenv('ALPACA_SECRET'), 
                   os.getenv('ALPACA_BASE_URL'), api_version='v2')
        alpaca_positions = api.list_positions()
        alpaca_symbols = {p.symbol for p in alpaca_positions}
        
        # Get bot metadata
        metadata_path = Path("state/position_metadata.json")
        if not metadata_path.exists():
            return {
                "valid": False,
                "error": "position_metadata.json does not exist",
                "alpaca_count": len(alpaca_symbols),
                "bot_count": 0
            }
        
        with metadata_path.open() as f:
            metadata = json.load(f)
        bot_symbols = {k for k in metadata.keys() if not k.startswith('_')}
        
        # Compare
        only_in_bot = bot_symbols - alpaca_symbols
        only_in_alpaca = alpaca_symbols - bot_symbols
        discrepancy = len(only_in_bot) > 0 or len(only_in_alpaca) > 0
        
        return {
            "valid": not discrepancy,
            "alpaca_count": len(alpaca_symbols),
            "bot_count": len(bot_symbols),
            "only_in_bot": list(only_in_bot),
            "only_in_alpaca": list(only_in_alpaca),
            "discrepancy": discrepancy
        }
    except Exception as e:
        return {
            "valid": False,
            "error": str(e),
            "alpaca_count": None,
            "bot_count": None
        }

if __name__ == "__main__":
    result = validate_position_state()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("valid") else 1)
