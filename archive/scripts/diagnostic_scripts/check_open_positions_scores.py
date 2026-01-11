#!/usr/bin/env python3
"""
Check Current Composite Scores for Open Positions
Shows entry score vs current score for all open positions, including signal decay.
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from config.registry import StateFiles, LogFiles, get_env, APIConfig, CacheFiles, read_json
    import alpaca_trade_api as tradeapi
    import uw_composite_v2 as uw_v2
except ImportError as e:
    print(f"ERROR: Failed to import required modules: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

# Try to load dotenv if available (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not required if env vars are already set


def get_global_regime() -> str:
    """Fetch current market regime from regime detector state file."""
    try:
        regime_file = StateFiles.REGIME_DETECTOR
        if regime_file.exists():
            try:
                data = json.loads(regime_file.read_text())
                if isinstance(data, dict):
                    regime = data.get("current_regime") or data.get("regime") or None
                    if regime and isinstance(regime, str):
                        return regime
            except (json.JSONDecodeError, IOError):
                pass
    except Exception:
        pass
    return "mixed"  # Default


def check_open_positions_scores():
    """Check current composite scores for all open positions."""
    print("=" * 80)
    print("OPEN POSITIONS - CURRENT SCORES")
    print("=" * 80)
    print()
    
    # Connect to Alpaca
    try:
        api_key = get_env("ALPACA_KEY") or get_env("ALPACA_API_KEY")
        api_secret = get_env("ALPACA_SECRET") or get_env("ALPACA_API_SECRET")
        base_url = get_env("ALPACA_BASE_URL", APIConfig.ALPACA_BASE_URL)
        
        if not api_key or not api_secret:
            print("ERROR: ALPACA_KEY and ALPACA_SECRET must be set")
            return
        
        api = tradeapi.REST(api_key, api_secret, base_url)
        account = api.get_account()
        print(f"Account: {account.account_number}")
        print()
    except Exception as e:
        print(f"ERROR: Failed to connect to Alpaca: {e}")
        return
    
    # Get open positions
    try:
        positions = api.list_positions()
        if not positions:
            print("No open positions")
            return
    except Exception as e:
        print(f"ERROR: Failed to fetch positions: {e}")
        return
    
    # Load position metadata
    metadata = {}
    if StateFiles.POSITION_METADATA.exists():
        try:
            metadata = json.loads(StateFiles.POSITION_METADATA.read_text())
        except Exception:
            pass
    
    # Load UW cache (same way as main.py and dashboard)
    uw_cache = {}
    try:
        cache_file = CacheFiles.UW_FLOW_CACHE
        if cache_file.exists():
            uw_cache = read_json(cache_file, default={})
    except Exception as e:
        print(f"WARNING: Failed to load UW cache: {e}")
    
    # Get current regime
    current_regime = get_global_regime()
    
    print(f"Current Regime: {current_regime}")
    print(f"Open Positions: {len(positions)}")
    print()
    print("-" * 80)
    print()
    
    # Process each position
    results = []
    for pos in positions:
        symbol = getattr(pos, "symbol", "")
        if not symbol:
            continue
        
        qty = float(getattr(pos, "qty", 0))
        avg_entry = float(getattr(pos, "avg_entry_price", 0))
        current_price = float(getattr(pos, "current_price", avg_entry))
        unrealized_plpc = float(getattr(pos, "unrealized_plpc", 0))
        
        # Get entry score from metadata
        entry_score = metadata.get(symbol, {}).get("entry_score", 0.0)
        entry_ts_str = metadata.get(symbol, {}).get("entry_ts", "")
        
        # Calculate position age
        age_hours = 0.0
        if entry_ts_str:
            try:
                entry_ts = datetime.fromisoformat(entry_ts_str.replace("Z", "+00:00"))
                if entry_ts.tzinfo is None:
                    entry_ts = entry_ts.replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                age_hours = (now - entry_ts).total_seconds() / 3600
            except:
                pass
        
        # Get current composite score
        current_score = 0.0
        current_composite = None
        flow_reversal = False
        signal_decay = None
        
        try:
            enriched = uw_cache.get(symbol, {})
            if enriched:
                current_composite = uw_v2.compute_composite_score_v3(symbol, enriched, current_regime)
                if current_composite:
                    current_score = current_composite.get("score", 0.0)
                    
                    # Check for flow reversal
                    flow_sent = enriched.get("sentiment", "NEUTRAL")
                    entry_direction = metadata.get(symbol, {}).get("direction", "unknown")
                    if entry_direction == "bullish" and flow_sent == "BEARISH":
                        flow_reversal = True
                    elif entry_direction == "bearish" and flow_sent == "BULLISH":
                        flow_reversal = True
                    
                    # Calculate signal decay
                    if entry_score > 0 and current_score > 0:
                        signal_decay = current_score / entry_score
        except Exception as e:
            print(f"WARNING: Failed to compute current score for {symbol}: {e}")
        
        # Calculate P&L
        pnl_pct = unrealized_plpc
        
        results.append({
            "symbol": symbol,
            "qty": abs(qty),
            "entry_price": avg_entry,
            "current_price": current_price,
            "pnl_pct": pnl_pct,
            "entry_score": entry_score,
            "current_score": current_score,
            "signal_decay": signal_decay,
            "flow_reversal": flow_reversal,
            "age_hours": age_hours
        })
    
    # Sort by signal decay (most decayed first) or by current score
    results.sort(key=lambda x: (x["signal_decay"] or 1.0, -x["current_score"]))
    
    # Display results
    print(f"{'Symbol':<8} {'Qty':<6} {'Entry$':<8} {'Current$':<9} {'P&L%':<7} {'Entry':<6} {'Current':<7} {'Decay':<7} {'Age':<6} {'Flow':<5}")
    print(f"{'Score':<8} {'':<6} {'Price':<8} {'Price':<9} {'':<7} {'Score':<6} {'Score':<7} {'Ratio':<7} {'(h)':<6} {'Rev':<5}")
    print("-" * 80)
    
    for r in results:
        decay_str = f"{r['signal_decay']:.2f}" if r['signal_decay'] else "N/A"
        reversal_str = "YES" if r['flow_reversal'] else "NO"
        
        # Color coding: red if decay < 0.6, yellow if < 0.8
        decay_indicator = ""
        if r['signal_decay']:
            if r['signal_decay'] < 0.6:
                decay_indicator = " ⚠️"  # Critical decay
            elif r['signal_decay'] < 0.8:
                decay_indicator = " ⚡"  # Moderate decay
        
        print(f"{r['symbol']:<8} {r['qty']:<6.0f} ${r['entry_price']:<7.2f} ${r['current_price']:<8.2f} "
              f"{r['pnl_pct']:>6.2f}% {r['entry_score']:<6.2f} {r['current_score']:<7.2f} "
              f"{decay_str:<7} {r['age_hours']:<6.1f} {reversal_str:<5}{decay_indicator}")
    
    print("-" * 80)
    print()
    
    # Summary
    total_positions = len(results)
    positions_with_decay = sum(1 for r in results if r['signal_decay'] and r['signal_decay'] < 0.6)
    positions_with_reversal = sum(1 for r in results if r['flow_reversal'])
    
    print("SUMMARY:")
    print(f"  Total Positions: {total_positions}")
    print(f"  Positions with Critical Decay (<60%): {positions_with_decay}")
    print(f"  Positions with Flow Reversal: {positions_with_reversal}")
    print()
    
    # Show positions that may need attention
    if positions_with_decay > 0 or positions_with_reversal > 0:
        print("⚠️  POSITIONS THAT MAY NEED ATTENTION:")
        for r in results:
            if (r['signal_decay'] and r['signal_decay'] < 0.6) or r['flow_reversal']:
                reasons = []
                if r['signal_decay'] and r['signal_decay'] < 0.6:
                    reasons.append(f"signal decay ({r['signal_decay']:.2f})")
                if r['flow_reversal']:
                    reasons.append("flow reversal")
                print(f"  - {r['symbol']}: {', '.join(reasons)}")
        print()
    
    print("=" * 80)


if __name__ == "__main__":
    check_open_positions_scores()
