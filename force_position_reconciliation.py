#!/usr/bin/env python3
"""
Force Immediate Position Reconciliation
Syncs bot's position_metadata.json with Alpaca API (authoritative source)
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from alpaca_trade_api import REST
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

load_dotenv()

def force_reconciliation():
    """Force immediate reconciliation - Alpaca API is authoritative"""
    
    print("=" * 80)
    print("FORCING IMMEDIATE POSITION RECONCILIATION")
    print("Alpaca API is the AUTHORITATIVE source")
    print("=" * 80)
    print()
    
    try:
        # 1. Get Alpaca positions (authoritative)
        print("1. Fetching positions from Alpaca API (authoritative source)...")
        api = REST(os.getenv('ALPACA_KEY'), os.getenv('ALPACA_SECRET'), 
                   os.getenv('ALPACA_BASE_URL'), api_version='v2')
        alpaca_positions = api.list_positions()
        alpaca_symbols = {p.symbol for p in alpaca_positions}
        print(f"   Alpaca API reports: {len(alpaca_positions)} positions")
        for p in alpaca_positions:
            print(f"   - {p.symbol}: {p.qty} shares @ {p.avg_entry_price}")
        print()
        
        # 2. Get bot's current metadata
        print("2. Reading bot's current metadata...")
        metadata_path = Path("state/position_metadata.json")
        if not metadata_path.exists():
            print("   WARNING: position_metadata.json does not exist, creating empty")
            metadata_path.parent.mkdir(exist_ok=True, parents=True)
            current_metadata = {}
        else:
            with metadata_path.open() as f:
                current_metadata = json.load(f)
        bot_symbols = {k for k in current_metadata.keys() if not k.startswith('_')}
        print(f"   Bot metadata has: {len(bot_symbols)} positions")
        for symbol in bot_symbols:
            print(f"   - {symbol}")
        print()
        
        # 3. Compare and identify discrepancies
        print("3. Identifying discrepancies...")
        only_in_bot = bot_symbols - alpaca_symbols
        only_in_alpaca = alpaca_symbols - bot_symbols
        
        print(f"   Positions only in bot (STALE, will be removed): {len(only_in_bot)}")
        if only_in_bot:
            for symbol in only_in_bot:
                print(f"     - {symbol}")
        
        print(f"   Positions only in Alpaca (MISSING, will be added): {len(only_in_alpaca)}")
        if only_in_alpaca:
            for symbol in only_in_alpaca:
                print(f"     - {symbol}")
        print()
        
        # 4. Reconcile: Alpaca is authoritative
        print("4. Reconciling (Alpaca API is authoritative)...")
        new_metadata = {}
        
        # Add all positions from Alpaca
        for pos in alpaca_positions:
            symbol = pos.symbol
            # Try to preserve existing metadata if it exists, but use Alpaca data as base
            existing = current_metadata.get(symbol, {})
            new_metadata[symbol] = {
                "entry_ts": existing.get("entry_ts") or datetime.utcnow().isoformat() + "Z",
                "entry_price": float(pos.avg_entry_price),
                "qty": int(pos.qty),
                "side": "short" if int(pos.qty) < 0 else "long",
                "reconciled_at": datetime.utcnow().isoformat() + "Z",
                "reconciled_from": "force_reconciliation_script",
                "unrealized_pl": float(pos.unrealized_pl) if hasattr(pos, 'unrealized_pl') else 0.0
            }
            # Preserve entry_score if it exists
            if "entry_score" in existing:
                new_metadata[symbol]["entry_score"] = existing["entry_score"]
        
        # Preserve metadata fields (if any)
        for key in current_metadata.keys():
            if key.startswith('_'):
                new_metadata[key] = current_metadata[key]
        
        # 5. Write reconciled metadata
        print("5. Writing reconciled metadata...")
        # Atomic write using temp file + rename
        temp_path = metadata_path.with_suffix('.json.tmp')
        with temp_path.open('w') as f:
            json.dump(new_metadata, f, indent=2)
        temp_path.replace(metadata_path)
        print(f"   ✅ Metadata written to {metadata_path}")
        print()
        
        # 6. Summary
        print("=" * 80)
        print("RECONCILIATION COMPLETE")
        print("=" * 80)
        print(f"Before: {len(bot_symbols)} positions in metadata")
        print(f"After:  {len(alpaca_symbols)} positions in metadata")
        print(f"Removed: {len(only_in_bot)} stale positions")
        print(f"Added: {len(only_in_alpaca)} missing positions")
        print()
        print("✅ Bot's metadata is now synced with Alpaca API (authoritative source)")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: Reconciliation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = force_reconciliation()
    sys.exit(0 if success else 1)
