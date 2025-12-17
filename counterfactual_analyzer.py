#!/usr/bin/env python3
"""
Counterfactual Trade Analyzer
==============================
Processes blocked trades to compute theoretical P&L and learn from missed opportunities.

Features:
- Computes theoretical P&L for blocked trades
- Tracks missed opportunities vs avoided losses
- Feeds counterfactual outcomes to learning engine
- Self-healing with automatic retry on errors
"""

import os
import json
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple
import alpaca_trade_api as tradeapi

DATA_DIR = Path("data")
STATE_DIR = Path("state")
LOGS_DIR = Path("logs")

BLOCKED_TRADES_FILE = STATE_DIR / "blocked_trades.jsonl"
COUNTERFACTUAL_RESULTS = DATA_DIR / "counterfactual_results.jsonl"
COUNTERFACTUAL_STATE = STATE_DIR / "counterfactual_state.json"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [COUNTERFACTUAL] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / "counterfactual_analyzer.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CounterfactualAnalyzer:
    """Analyzes blocked trades to compute theoretical outcomes."""
    
    def __init__(self):
        self.api = None
        self._init_alpaca()
        self.processed_count = 0
        self.error_count = 0
        self.last_processed_ts = 0
        
    def _init_alpaca(self):
        """Initialize Alpaca API for price data."""
        try:
            key = os.getenv("ALPACA_API_KEY") or os.getenv("ALPACA_KEY", "")
            secret = os.getenv("ALPACA_API_SECRET") or os.getenv("ALPACA_SECRET", "")
            base_url = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
            if key and secret:
                self.api = tradeapi.REST(key, secret, base_url)
                logger.info("Alpaca API initialized for counterfactual analysis")
        except Exception as e:
            logger.warning(f"Alpaca API not available: {e}")
    
    def get_historical_price(self, symbol: str, timestamp: datetime, lookback_hours: int = 24) -> Optional[float]:
        """Get price at a specific time using Alpaca bars."""
        if not self.api:
            return None
        
        try:
            # Convert to ET (Alpaca uses ET)
            et_timestamp = timestamp.astimezone(timezone(timedelta(hours=-5)))
            end_time = et_timestamp
            start_time = end_time - timedelta(hours=lookback_hours)
            
            # Get bars
            bars = self.api.get_bars(
                symbol,
                "1Min",
                start=start_time.strftime("%Y-%m-%dT%H:%M:%S-05:00"),
                end=end_time.strftime("%Y-%m-%dT%H:%M:%S-05:00"),
                limit=1000
            ).df
            
            if bars.empty:
                return None
            
            # Find closest bar to timestamp
            bars.index = bars.index.tz_localize(None)  # Remove timezone for comparison
            target = et_timestamp.replace(tzinfo=None)
            closest_idx = bars.index.get_indexer([target], method='nearest')[0]
            if closest_idx >= 0:
                return float(bars.iloc[closest_idx]['close'])
            
        except Exception as e:
            logger.debug(f"Error getting historical price for {symbol}: {e}")
        
        return None
    
    def compute_theoretical_pnl(self, blocked_trade: Dict[str, Any], exit_time: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """
        Compute theoretical P&L for a blocked trade.
        
        Args:
            blocked_trade: Blocked trade record with decision_price, direction, etc.
            exit_time: When to exit (default: 4 hours after entry, or market close)
        
        Returns:
            Dict with theoretical_pnl, exit_price, hold_duration, etc.
        """
        symbol = blocked_trade.get("symbol")
        decision_price = blocked_trade.get("decision_price")
        direction = blocked_trade.get("direction", "bullish")
        timestamp_str = blocked_trade.get("timestamp", "")
        
        if not symbol or not decision_price or not timestamp_str:
            return None
        
        try:
            entry_time = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            if entry_time.tzinfo is None:
                entry_time = entry_time.replace(tzinfo=timezone.utc)
        except Exception:
            return None
        
        # Determine exit time (default: 4 hours or market close, whichever comes first)
        if exit_time is None:
            # Market close is 4:00 PM ET = 9:00 PM UTC
            market_close_utc = entry_time.replace(hour=21, minute=0, second=0, microsecond=0)
            four_hours_later = entry_time + timedelta(hours=4)
            exit_time = min(market_close_utc, four_hours_later)
        
        # Get exit price
        exit_price = self.get_historical_price(symbol, exit_time)
        if exit_price is None:
            # Fallback: try to get current price if exit_time is recent
            if (datetime.now(timezone.utc) - exit_time).total_seconds() < 3600:
                try:
                    if self.api:
                        trade = self.api.get_latest_trade(symbol)
                        exit_price = float(getattr(trade, "price", 0.0))
                except:
                    pass
        
        if exit_price is None or exit_price <= 0:
            return None
        
        # Compute P&L
        hold_duration_min = (exit_time - entry_time).total_seconds() / 60.0
        
        if direction == "bullish" or direction == "buy":
            pnl_usd = (exit_price - decision_price) * 1  # Assume 1 share for counterfactual
            pnl_pct = ((exit_price - decision_price) / decision_price) * 100
        else:  # bearish/sell
            pnl_usd = (decision_price - exit_price) * 1
            pnl_pct = ((decision_price - exit_price) / decision_price) * 100
        
        return {
            "entry_price": decision_price,
            "exit_price": exit_price,
            "entry_time": entry_time.isoformat(),
            "exit_time": exit_time.isoformat(),
            "hold_duration_min": round(hold_duration_min, 1),
            "theoretical_pnl_usd": round(pnl_usd, 2),
            "theoretical_pnl_pct": round(pnl_pct, 4),
            "direction": direction,
            "symbol": symbol
        }
    
    def process_blocked_trades(self, lookback_hours: int = 24) -> Dict[str, Any]:
        """
        Process blocked trades and compute counterfactual outcomes.
        
        Returns:
            Summary of processed trades
        """
        if not BLOCKED_TRADES_FILE.exists():
            return {"processed": 0, "missed_opportunities": 0, "avoided_losses": 0, "errors": 0}
        
        results = {
            "processed": 0,
            "missed_opportunities": 0,
            "avoided_losses": 0,
            "errors": 0,
            "theoretical_pnl_total": 0.0
        }
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
        
        try:
            with BLOCKED_TRADES_FILE.open("r") as f:
                lines = f.readlines()
            
            processed_timestamps = set()
            state = self._load_state()
            if state:
                processed_timestamps = set(state.get("processed_timestamps", []))
            
            for line in lines:
                try:
                    blocked_trade = json.loads(line.strip())
                    
                    # Skip if already processed
                    timestamp = blocked_trade.get("timestamp", "")
                    if timestamp in processed_timestamps:
                        continue
                    
                    # Skip if outcome already tracked
                    if blocked_trade.get("outcome_tracked", False):
                        processed_timestamps.add(timestamp)
                        continue
                    
                    # Skip if too old
                    try:
                        trade_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        if trade_time < cutoff_time:
                            continue
                    except:
                        continue
                    
                    # Compute theoretical P&L
                    theoretical = self.compute_theoretical_pnl(blocked_trade)
                    if theoretical is None:
                        results["errors"] += 1
                        continue
                    
                    # Record result
                    result_record = {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "blocked_trade": blocked_trade,
                        "theoretical_outcome": theoretical,
                        "type": "missed_opportunity" if theoretical["theoretical_pnl_usd"] > 0 else "avoided_loss"
                    }
                    
                    # Save to results file
                    COUNTERFACTUAL_RESULTS.parent.mkdir(parents=True, exist_ok=True)
                    with COUNTERFACTUAL_RESULTS.open("a") as f:
                        f.write(json.dumps(result_record) + "\n")
                    
                    # Update counters
                    results["processed"] += 1
                    if theoretical["theoretical_pnl_usd"] > 0:
                        results["missed_opportunities"] += 1
                    else:
                        results["avoided_losses"] += 1
                    results["theoretical_pnl_total"] += theoretical["theoretical_pnl_usd"]
                    
                    # Mark as processed
                    processed_timestamps.add(timestamp)
                    
                    # Feed to learning engine (with lower weight)
                    self._feed_to_learning(blocked_trade, theoretical)
                    
                except Exception as e:
                    logger.warning(f"Error processing blocked trade: {e}")
                    results["errors"] += 1
                    continue
            
            # Save state
            self._save_state({"processed_timestamps": list(processed_timestamps)})
            
        except Exception as e:
            logger.error(f"Error processing blocked trades: {e}")
            results["errors"] += 1
        
        self.processed_count += results["processed"]
        self.error_count += results["errors"]
        self.last_processed_ts = time.time()
        
        return results
    
    def _feed_to_learning(self, blocked_trade: Dict[str, Any], theoretical: Dict[str, Any]):
        """Feed counterfactual outcome to learning engine with reduced weight."""
        try:
            from adaptive_signal_optimizer import get_optimizer
            
            optimizer = get_optimizer()
            if not optimizer:
                return
            
            # Extract feature vector from components
            components = blocked_trade.get("components", {})
            feature_vector = {}
            for comp, value in components.items():
                if isinstance(value, (int, float)):
                    feature_vector[comp] = float(value)
            
            # Use theoretical P&L with 0.5x weight (counterfactuals are less certain)
            pnl = theoretical["theoretical_pnl_usd"] * 0.5
            
            # Record as counterfactual trade
            optimizer.record_trade(
                feature_vector=feature_vector,
                pnl=pnl,
                regime=blocked_trade.get("regime", "neutral"),
                sector=blocked_trade.get("sector", "unknown"),
                trade_data={
                    "type": "counterfactual",
                    "theoretical_pnl": theoretical["theoretical_pnl_usd"],
                    "actual_pnl": None,
                    "hold_duration_min": theoretical["hold_duration_min"]
                }
            )
            
            logger.info(f"Fed counterfactual trade to learning: {blocked_trade.get('symbol')}, P&L: {pnl:.2f}")
            
        except Exception as e:
            logger.warning(f"Error feeding counterfactual to learning: {e}")
    
    def _load_state(self) -> Optional[Dict[str, Any]]:
        """Load processing state."""
        if COUNTERFACTUAL_STATE.exists():
            try:
                return json.loads(COUNTERFACTUAL_STATE.read_text())
            except:
                pass
        return None
    
    def _save_state(self, state: Dict[str, Any]):
        """Save processing state."""
        try:
            COUNTERFACTUAL_STATE.parent.mkdir(parents=True, exist_ok=True)
            COUNTERFACTUAL_STATE.write_text(json.dumps(state, indent=2))
        except Exception as e:
            logger.warning(f"Error saving state: {e}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of counterfactual analysis."""
        summary = {
            "total_processed": self.processed_count,
            "total_errors": self.error_count,
            "last_processed_ts": self.last_processed_ts
        }
        
        # Read recent results
        if COUNTERFACTUAL_RESULTS.exists():
            try:
                with COUNTERFACTUAL_RESULTS.open("r") as f:
                    lines = f.readlines()
                    recent = [json.loads(l) for l in lines[-100:]]
                    
                    missed = [r for r in recent if r.get("type") == "missed_opportunity"]
                    avoided = [r for r in recent if r.get("type") == "avoided_loss"]
                    
                    summary["recent_missed_opportunities"] = len(missed)
                    summary["recent_avoided_losses"] = len(avoided)
                    summary["recent_theoretical_pnl"] = sum(
                        r.get("theoretical_outcome", {}).get("theoretical_pnl_usd", 0.0)
                        for r in recent
                    )
            except:
                pass
        
        return summary


def main():
    """Run counterfactual analysis."""
    analyzer = CounterfactualAnalyzer()
    results = analyzer.process_blocked_trades(lookback_hours=24)
    
    logger.info(f"Counterfactual analysis complete: {results}")
    print(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    main()
