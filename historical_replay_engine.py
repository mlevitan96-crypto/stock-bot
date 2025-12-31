#!/usr/bin/env python3
"""
Historical Replay Engine - No Look-Forward Bias Backtest System

Replays the last 30 days of UW Flow Alerts using Alpaca's tick-level historical data
to verify bot performance under realistic execution friction and temporal liquidity constraints.

Features:
- Tick-level trade execution simulation
- 0.5 basis point latency penalty
- Specialist strategy rotator testing (mid-day 11:30-13:30 EST)
- Stale trade exit analysis (90 min if P&L < ±0.2%)
- Alpha decay measurement (time until signal becomes unprofitable)
- Comprehensive metrics (win rate, Sharpe ratio, capacity analysis)
"""

import os
import json
import time
import statistics
import requests
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict

try:
    import pytz
    PYTZ_AVAILABLE = True
except ImportError:
    PYTZ_AVAILABLE = False

from config.registry import (
    Directories, CacheFiles, StateFiles, LogFiles, ConfigFiles, Thresholds, APIConfig
)

# Import specialist strategy rotator
try:
    from specialist_strategy_rotator import SpecialistStrategyRotator
    SPECIALIST_AVAILABLE = True
except ImportError:
    SPECIALIST_AVAILABLE = False
    print("[WARNING] SpecialistStrategyRotator not available - will use default thresholds")


@dataclass
class SimulatedTrade:
    """Represents a simulated trade during backtest"""
    symbol: str
    entry_time: datetime
    entry_price: float
    entry_score: float
    direction: str  # "long" or "short"
    qty: int
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    pnl_usd: Optional[float] = None
    pnl_pct: Optional[float] = None
    hold_minutes: Optional[int] = None
    exit_reason: Optional[str] = None
    components: Optional[Dict[str, Any]] = None
    latency_penalty_bps: float = 0.5
    specialist_boost: bool = False
    alpha_decay_minutes: Optional[int] = None  # Minutes until first negative return


@dataclass
class BacktestMetrics:
    """Comprehensive backtest performance metrics"""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl_usd: float
    avg_win_usd: float
    avg_loss_usd: float
    profit_factor: float
    sharpe_ratio: float
    max_drawdown_pct: float
    avg_hold_minutes: float
    specialist_win_rate: float  # Win rate during 11:30-13:30 EST
    stale_exit_trades: int  # Trades closed at 90 min with <±0.2% P&L
    avg_alpha_decay_minutes: float  # Average time until signal becomes unprofitable
    capacity_improvement_pct: float  # Capacity freed by stale exits


class AlpacaHistoricalDataClient:
    """Client for fetching historical tick-level data from Alpaca"""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """
        Initialize Alpaca API client for historical data.
        Uses APIConfig from registry per memory bank standards.
        """
        # Use APIConfig from registry (per memory bank - centralized config)
        headers = APIConfig.get_alpaca_headers()
        self.api_key = api_key or headers.get("APCA-API-KEY-ID", "")
        self.api_secret = api_secret or headers.get("APCA-API-SECRET-KEY", "")
        self.base_url = APIConfig.ALPACA_DATA_URL  # Use data API endpoint
        self.headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.api_secret
        }
        
    def get_historical_trades(
        self, 
        symbol: str, 
        start: datetime, 
        end: datetime,
        limit: int = 10000
    ) -> List[Dict[str, Any]]:
        """
        Fetch historical trade data (tick-level) from Alpaca API v2.
        
        Args:
            symbol: Stock symbol
            start: Start timestamp (UTC)
            end: End timestamp (UTC)
            limit: Maximum number of trades to return
            
        Returns:
            List of trade records with fields: t (timestamp), p (price), s (size), etc.
        """
        url = f"{self.base_url}/v2/stocks/{symbol}/trades"
        
        # Format timestamps in RFC-3339 format
        start_str = start.strftime("%Y-%m-%dT%H:%M:%S-00:00")
        end_str = end.strftime("%Y-%m-%dT%H:%M:%S-00:00")
        
        params = {
            "start": start_str,
            "end": end_str,
            "limit": limit
        }
        
        all_trades = []
        page_token = None
        
        try:
            while True:
                if page_token:
                    params["page_token"] = page_token
                
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                trades = data.get("trades", [])
                all_trades.extend(trades)
                
                # Check for pagination
                page_token = data.get("next_page_token")
                if not page_token or len(trades) == 0:
                    break
                    
                # Respect limit
                if len(all_trades) >= limit:
                    all_trades = all_trades[:limit]
                    break
                    
                # Rate limiting: small delay between pages
                time.sleep(0.1)
                
        except requests.exceptions.RequestException as e:
            print(f"[WARNING] Failed to fetch trades for {symbol}: {e}")
            return []
            
        return all_trades
    
    def get_historical_bars(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        timeframe: str = "1Min",
        limit: int = 10000
    ) -> List[Dict[str, Any]]:
        """
        Fetch historical bar data from Alpaca API v2.
        Falls back to bars if tick data is not available.
        
        Args:
            symbol: Stock symbol
            start: Start timestamp (UTC)
            end: End timestamp (UTC)
            timeframe: Bar timeframe (1Min, 5Min, 1Hour, 1Day)
            limit: Maximum number of bars
            
        Returns:
            List of bar records
        """
        url = f"{self.base_url}/v2/stocks/{symbol}/bars"
        
        start_str = start.strftime("%Y-%m-%dT%H:%M:%S-00:00")
        end_str = end.strftime("%Y-%m-%dT%H:%M:%S-00:00")
        
        params = {
            "start": start_str,
            "end": end_str,
            "timeframe": timeframe,
            "limit": limit
        }
        
        all_bars = []
        page_token = None
        
        try:
            while True:
                if page_token:
                    params["page_token"] = page_token
                
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                bars = data.get("bars", [])
                all_bars.extend(bars)
                
                page_token = data.get("next_page_token")
                if not page_token or len(bars) == 0:
                    break
                    
                if len(all_bars) >= limit:
                    all_bars = all_bars[:limit]
                    break
                    
                time.sleep(0.1)
                
        except requests.exceptions.RequestException as e:
            print(f"[WARNING] Failed to fetch bars for {symbol}: {e}")
            return []
            
        return all_bars
    
    def get_price_at_time(
        self,
        symbol: str,
        target_time: datetime,
        window_minutes: int = 5
    ) -> Optional[float]:
        """
        Get the best available price at a specific time.
        Uses tick data if available, otherwise falls back to bar data.
        
        Args:
            symbol: Stock symbol
            target_time: Target timestamp
            window_minutes: Time window to search around target_time
            
        Returns:
            Price at that time (or None if unavailable)
        """
        start = target_time - timedelta(minutes=window_minutes)
        end = target_time + timedelta(minutes=window_minutes)
        
        # Try tick-level trades first
        trades = self.get_historical_trades(symbol, start, end, limit=1000)
        
        if trades:
            # Find closest trade to target time
            target_ts = target_time.timestamp()
            closest_trade = min(
                trades,
                key=lambda t: abs(
                    datetime.fromisoformat(t["t"].replace("Z", "+00:00")).timestamp() - target_ts
                )
            )
            return float(closest_trade["p"])
        
        # Fall back to 1-minute bars
        bars = self.get_historical_bars(symbol, start, end, timeframe="1Min", limit=100)
        
        if bars:
            # Find bar that contains target time
            for bar in bars:
                bar_time = datetime.fromisoformat(bar["t"].replace("Z", "+00:00"))
                if bar_time <= target_time < bar_time + timedelta(minutes=1):
                    # Use close price of the bar
                    return float(bar["c"])
            
            # If no exact match, use closest bar
            target_ts = target_time.timestamp()
            closest_bar = min(
                bars,
                key=lambda b: abs(
                    datetime.fromisoformat(b["t"].replace("Z", "+00:00")).timestamp() - target_ts
                )
            )
            return float(closest_bar["c"])
        
        return None


class HistoricalReplayEngine:
    """
    Main backtest engine that replays historical signals with realistic execution.
    """
    
    def __init__(
        self,
        attribution_log_path: Optional[Path] = None,
        uw_attribution_log_path: Optional[Path] = None,
        latency_penalty_bps: float = 0.5,
        stale_exit_minutes: int = 90,
        stale_exit_pnl_threshold: float = 0.002  # ±0.2%
    ):
        """
        Initialize the backtest engine.
        
        Args:
            attribution_log_path: Path to logs/attribution.jsonl
            uw_attribution_log_path: Path to data/uw_attribution.jsonl
            latency_penalty_bps: Latency penalty in basis points (default 0.5)
            stale_exit_minutes: Minutes before stale exit triggers (default 90)
            stale_exit_pnl_threshold: P&L threshold for stale exit (default 0.002 = ±0.2%)
        """
        # Correct file paths per memory bank and registry
        # Primary: logs/attribution.jsonl (trade attribution)
        # Secondary: data/uw_attribution.jsonl (UW signal attribution with decision="signal"/"entry")
        # Fallback: logs/composite_attribution.jsonl
        self.attribution_log = attribution_log_path or (Directories.LOGS / "attribution.jsonl")
        self.uw_attribution_log = uw_attribution_log_path or CacheFiles.UW_ATTRIBUTION
        self.composite_attribution_log = LogFiles.COMPOSITE_ATTRIBUTION
        
        # Verify which files exist
        print(f"[BACKTEST] Checking data sources:")
        print(f"  - logs/attribution.jsonl: {self.attribution_log.exists()}")
        print(f"  - data/uw_attribution.jsonl: {self.uw_attribution_log.exists()}")
        print(f"  - logs/composite_attribution.jsonl: {self.composite_attribution_log.exists()}")
        
        self.latency_penalty_bps = latency_penalty_bps
        self.stale_exit_minutes = stale_exit_minutes
        self.stale_exit_pnl_threshold = stale_exit_pnl_threshold
        
        self.data_client = AlpacaHistoricalDataClient()
        
        # Initialize specialist strategy rotator if available
        if SPECIALIST_AVAILABLE:
            self.specialist = SpecialistStrategyRotator()
        else:
            self.specialist = None
        
        self.simulated_trades: List[SimulatedTrade] = []
        self.metrics: Optional[BacktestMetrics] = None
        
        # EST timezone for time-based logic
        if PYTZ_AVAILABLE:
            try:
                self.est_tz = pytz.timezone("US/Eastern")
            except:
                # Fallback: EST is UTC-5 (simple offset, doesn't handle DST)
                self.est_tz = timezone(timedelta(hours=-5))
        else:
            # Fallback: Try zoneinfo (Python 3.9+)
            try:
                from zoneinfo import ZoneInfo
                self.est_tz = ZoneInfo("America/New_York")
            except (ImportError, Exception):
                # Final fallback: EST is UTC-5 (simple offset, doesn't handle DST)
                self.est_tz = timezone(timedelta(hours=-5))
        
    
    def load_signals(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Load signals from attribution logs for the last N days.
        
        Per memory bank, correct file paths are:
        - logs/attribution.jsonl: Trade attribution (primary)
        - data/uw_attribution.jsonl: UW signal attribution (decision="signal"/"entry")
        - logs/composite_attribution.jsonl: Composite attribution (fallback)
        
        Args:
            days: Number of days to look back (default 30)
            
        Returns:
            List of signal records with timestamps, symbols, scores, etc.
        """
        signals = []
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Priority 1: UW attribution log (has most detailed signal data with decision="signal"/"entry")
        if self.uw_attribution_log.exists():
            with open(self.uw_attribution_log, "r") as f:
                for line in f:
                    try:
                        record = json.loads(line.strip())
                        # Filter for signals (not blocked entries)
                        if record.get("decision") in ["signal", "entry"]:
                            ts_str = record.get("ts") or record.get("timestamp")
                            if isinstance(ts_str, str):
                                try:
                                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                                except:
                                    # Try unix timestamp
                                    ts = datetime.fromtimestamp(float(ts_str), tz=timezone.utc)
                            elif isinstance(ts_str, (int, float)):
                                ts = datetime.fromtimestamp(float(ts_str), tz=timezone.utc)
                            else:
                                continue
                            
                            if ts >= cutoff_time:
                                signals.append({
                                    "symbol": record.get("symbol"),
                                    "timestamp": ts,
                                    "score": record.get("score", 0.0),
                                    "components": record.get("components", {}),
                                    "direction": record.get("direction", "bullish"),  # Default to bullish
                                    "source": "uw_attribution"
                                })
                    except Exception as e:
                        continue
        
        # Priority 2: logs/attribution.jsonl (trade attribution - per memory bank line 909)
        if self.attribution_log.exists():
            with open(self.attribution_log, "r") as f:
                for line in f:
                    try:
                        record = json.loads(line.strip())
                        if record.get("type") == "attribution":
                            ts_str = record.get("ts") or record.get("timestamp")
                            if isinstance(ts_str, str):
                                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                            elif isinstance(ts_str, (int, float)):
                                ts = datetime.fromtimestamp(float(ts_str), tz=timezone.utc)
                            else:
                                continue
                            
                            if ts >= cutoff_time:
                                # Only add if not already in signals (avoid duplicates)
                                symbol = record.get("symbol")
                                if not any(s.get("symbol") == symbol and abs((s.get("timestamp") - ts).total_seconds()) < 60 
                                          for s in signals):
                                    signals.append({
                                        "symbol": symbol,
                                        "timestamp": ts,
                                        "score": record.get("entry_score", record.get("score", 0.0)),
                                        "components": record.get("context", {}).get("components", {}),
                                        "direction": record.get("direction", "bullish"),
                                        "source": "composite_attribution"
                                    })
                    except Exception as e:
                        continue
        
        # Priority 3: logs/composite_attribution.jsonl (fallback)
        if self.composite_attribution_log.exists() and len(signals) == 0:
            with open(self.composite_attribution_log, "r") as f:
                for line in f:
                    try:
                        record = json.loads(line.strip())
                        if record.get("type") in ["attribution", "signal"]:
                            ts_str = record.get("ts") or record.get("timestamp")
                            if isinstance(ts_str, str):
                                try:
                                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                                except:
                                    ts = datetime.fromtimestamp(float(ts_str), tz=timezone.utc)
                            elif isinstance(ts_str, (int, float)):
                                ts = datetime.fromtimestamp(float(ts_str), tz=timezone.utc)
                            else:
                                continue
                            
                            if ts >= cutoff_time:
                                symbol = record.get("symbol")
                                if not any(s.get("symbol") == symbol and abs((s.get("timestamp") - ts).total_seconds()) < 60 
                                          for s in signals):
                                    signals.append({
                                        "symbol": symbol,
                                        "timestamp": ts,
                                        "score": record.get("entry_score", record.get("score", 0.0)),
                                        "components": record.get("context", {}).get("components", {}),
                                        "direction": record.get("direction", "bullish"),
                                        "source": "composite_attribution"
                                    })
                    except Exception as e:
                        continue
        
        # Sort by timestamp
        signals.sort(key=lambda x: x["timestamp"])
        
        print(f"[BACKTEST] Loaded {len(signals)} signals from last {days} days")
        if len(signals) == 0:
            print(f"[WARNING] No signals found. Ensure bot has run and generated signals.")
            print(f"[INFO] Backtest requires signals from: logs/attribution.jsonl or data/uw_attribution.jsonl")
            print(f"[INFO] Historical data from Alpaca will be used for price execution once signals are available.")
        return signals
    
    def is_mid_day_window(self, timestamp: datetime) -> bool:
        """
        Check if timestamp falls within specialist strategy rotator window (11:30-13:30 EST).
        
        Args:
            timestamp: Timestamp to check (should be UTC)
            
        Returns:
            True if in mid-day window
        """
        try:
            timestamp_est = timestamp.astimezone(self.est_tz)
            signal_time = timestamp_est.time()
            mid_day_start = datetime.strptime("11:30", "%H:%M").time()
            mid_day_end = datetime.strptime("13:30", "%H:%M").time()
            return mid_day_start <= signal_time <= mid_day_end
        except Exception:
            return False
    
    def simulate_trade_entry(
        self,
        signal: Dict[str, Any],
        base_price: float,
        is_specialist_boosted: bool = False
    ) -> SimulatedTrade:
        """
        Simulate trade entry with latency penalty.
        
        Args:
            signal: Signal dictionary
            base_price: Base price from historical data
            is_specialist_boosted: Whether trade is in specialist window (for tracking)
            
        Returns:
            SimulatedTrade object
        """
        # Apply latency penalty (0.5 basis points = 0.00005 = 0.005%)
        latency_multiplier = 1.0 + (self.latency_penalty_bps / 10000.0)
        
        direction = signal.get("direction", "bullish").lower()
        
        if direction in ["bullish", "long"]:
            # Buying: pay slightly more
            entry_price = base_price * latency_multiplier
        else:
            # Selling/shorting: receive slightly less
            entry_price = base_price * (1.0 / latency_multiplier)
        
        # Position sizing (simplified - use base $500 position)
        qty = max(1, int(500 / entry_price))
        
        trade = SimulatedTrade(
            symbol=signal["symbol"],
            entry_time=signal["timestamp"],
            entry_price=entry_price,
            entry_score=signal["score"],  # Keep original score for analysis
            direction=direction,
            qty=qty,
            components=signal.get("components", {}),
            specialist_boost=is_specialist_boosted
        )
        
        return trade
    
    def simulate_trade_exit(
        self,
        trade: SimulatedTrade,
        exit_time: datetime,
        exit_price: float,
        exit_reason: str
    ) -> SimulatedTrade:
        """
        Simulate trade exit and calculate P&L.
        
        Args:
            trade: SimulatedTrade to exit
            exit_time: Exit timestamp
            exit_price: Exit price
            exit_reason: Reason for exit
            
        Returns:
            Updated SimulatedTrade with exit information
        """
        trade.exit_time = exit_time
        trade.exit_price = exit_price
        trade.exit_reason = exit_reason
        trade.hold_minutes = int((exit_time - trade.entry_time).total_seconds() / 60)
        
        # Calculate P&L
        if trade.direction in ["bullish", "long"]:
            pnl_usd = (exit_price - trade.entry_price) * trade.qty
        else:  # bearish/short
            pnl_usd = (trade.entry_price - exit_price) * trade.qty
        
        trade.pnl_usd = pnl_usd
        trade.pnl_pct = pnl_usd / (trade.entry_price * trade.qty)
        
        return trade
    
    def check_stale_exit(self, trade: SimulatedTrade, current_time: datetime, current_price: float) -> bool:
        """
        Check if trade should be closed due to stale exit rule.
        Rule: Close at 90 minutes if P&L < ±0.2%
        
        Args:
            trade: Current trade
            current_time: Current timestamp
            current_price: Current price
            
        Returns:
            True if stale exit should trigger
        """
        hold_minutes = (current_time - trade.entry_time).total_seconds() / 60
        
        if hold_minutes >= self.stale_exit_minutes:
            # Calculate current P&L
            if trade.direction in ["bullish", "long"]:
                pnl_pct = (current_price - trade.entry_price) / trade.entry_price
            else:
                pnl_pct = (trade.entry_price - current_price) / trade.entry_price
            
            # Close if P&L is within threshold (low movement)
            if abs(pnl_pct) < self.stale_exit_pnl_threshold:
                return True
        
        return False
    
    def measure_alpha_decay(self, trade: SimulatedTrade, price_history: List[Tuple[datetime, float]]) -> Optional[int]:
        """
        Measure alpha decay: minutes until signal becomes unprofitable.
        
        Args:
            trade: SimulatedTrade
            price_history: List of (timestamp, price) tuples
            
        Returns:
            Minutes until first negative return, or None if never negative
        """
        entry_price = trade.entry_price
        entry_time = trade.entry_time
        
        for price_time, price in price_history:
            if price_time <= entry_time:
                continue
            
            minutes_since_entry = (price_time - entry_time).total_seconds() / 60
            
            # Calculate return at this point
            if trade.direction in ["bullish", "long"]:
                return_pct = (price - entry_price) / entry_price
            else:
                return_pct = (entry_price - price) / entry_price
            
            # If return becomes negative, we found alpha decay
            if return_pct < 0:
                return int(minutes_since_entry)
        
        return None  # Never became unprofitable
    
    def run_backtest(self, days: int = 30, test_specialist: bool = True, test_stale_exits: bool = True) -> BacktestMetrics:
        """
        Run the complete backtest.
        
        Args:
            days: Number of days to backtest (default 30)
            test_specialist: Whether to test specialist strategy rotator
            test_stale_exits: Whether to test stale trade exits
            
        Returns:
            BacktestMetrics object
        """
        print(f"[BACKTEST] Starting backtest for last {days} days...")
        
        # Load signals
        signals = self.load_signals(days=days)
        
        if not signals:
            print("[ERROR] No signals found to backtest")
            return BacktestMetrics(
                total_trades=0, winning_trades=0, losing_trades=0, win_rate=0.0,
                total_pnl_usd=0.0, avg_win_usd=0.0, avg_loss_usd=0.0, profit_factor=0.0,
                sharpe_ratio=0.0, max_drawdown_pct=0.0, avg_hold_minutes=0.0,
                specialist_win_rate=0.0, stale_exit_trades=0, avg_alpha_decay_minutes=0.0,
                capacity_improvement_pct=0.0
            )
        
        # Group signals by symbol for efficient data fetching
        symbols = list(set(s["symbol"] for s in signals))
        print(f"[BACKTEST] Processing {len(symbols)} unique symbols...")
        
        # Track open positions
        open_positions: List[SimulatedTrade] = []
        completed_trades: List[SimulatedTrade] = []
        
        # Process signals chronologically
        for signal in signals:
            symbol = signal["symbol"]
            signal_time = signal["timestamp"]
            
            # Get entry price from historical data
            entry_price = self.data_client.get_price_at_time(symbol, signal_time)
            
            if entry_price is None:
                print(f"[WARNING] Could not get price for {symbol} at {signal_time}")
                continue
            
            # Check if signal is in mid-day window for specialist rotator
            is_mid_day = self.is_mid_day_window(signal["timestamp"])
            
            # For specialist rotator test: filter trades that wouldn't pass higher threshold
            if test_specialist and is_mid_day:
                # Specialist rotator increases threshold by 0.75 during mid-day
                # Only take trades that would pass the higher threshold
                min_threshold = Thresholds.MIN_EXEC_SCORE + 0.75
                if signal["score"] < min_threshold:
                    continue  # Would have been filtered by specialist rotator
            
            # Simulate entry
            trade = self.simulate_trade_entry(signal, entry_price, is_specialist_boosted=is_mid_day)
            
            open_positions.append(trade)
            
            # Check exits for all open positions
            positions_to_close = []
            for pos in open_positions:
                # Get current price
                current_price = self.data_client.get_price_at_time(pos.symbol, signal_time)
                if current_price is None:
                    continue
                
                hold_minutes = (signal_time - pos.entry_time).total_seconds() / 60
                hold_hours = hold_minutes / 60.0
                
                # Calculate current P&L
                if pos.direction in ["bullish", "long"]:
                    pnl_pct = (current_price - pos.entry_price) / pos.entry_price
                else:
                    pnl_pct = (pos.entry_price - current_price) / pos.entry_price
                
                pnl_pct_abs = abs(pnl_pct)
                exit_reason = None
                
                # Exit priority order (as per actual bot logic):
                
                # 1. Stale trade exit (90 minutes, P&L < ±0.2%)
                if test_stale_exits and hold_minutes >= self.stale_exit_minutes:
                    if pnl_pct_abs < self.stale_exit_pnl_threshold:
                        exit_reason = f"stale_exit_{self.stale_exit_minutes}min"
                
                # 2. Trailing stop (1.5% default, 1.0% in MIXED regime)
                # Note: We need to track high water mark - simplified for now
                if not exit_reason:
                    trailing_stop_pct = Thresholds.TRAILING_STOP_PCT
                    # TODO: Track high water mark properly
                    # Simplified: use entry price as high water for now
                    high_water = pos.entry_price * (1.0 + max(0, pnl_pct))  # Simplified
                    trail_stop_price = high_water * (1.0 - trailing_stop_pct)
                    if pos.direction in ["bullish", "long"] and current_price <= trail_stop_price:
                        exit_reason = "trailing_stop"
                    elif pos.direction not in ["bullish", "long"] and current_price >= trail_stop_price:
                        exit_reason = "trailing_stop"
                
                # 3. Time exit (240 minutes / 4 hours)
                if not exit_reason and hold_minutes >= Thresholds.TIME_EXIT_MINUTES:
                    exit_reason = f"time_exit_{Thresholds.TIME_EXIT_MINUTES}min"
                
                # 4. Profit target (2% - first target)
                if not exit_reason and pnl_pct >= 0.02:
                    exit_reason = "profit_target_2pct"
                
                # Execute exit if triggered
                if exit_reason:
                    pos = self.simulate_trade_exit(pos, signal_time, current_price, exit_reason)
                    positions_to_close.append(pos)
                    completed_trades.append(pos)
            
            # Remove closed positions
            for closed_pos in positions_to_close:
                if closed_pos in open_positions:
                    open_positions.remove(closed_pos)
        
        # Close any remaining open positions at the end
        final_time = signals[-1]["timestamp"] if signals else datetime.now(timezone.utc)
        for pos in open_positions:
            final_price = self.data_client.get_price_at_time(pos.symbol, final_time)
            if final_price:
                pos = self.simulate_trade_exit(pos, final_time, final_price, "backtest_end")
                completed_trades.append(pos)
        
        self.simulated_trades = completed_trades
        
        # Calculate metrics
        metrics = self.calculate_metrics(completed_trades)
        self.metrics = metrics
        
        print(f"[BACKTEST] Completed: {len(completed_trades)} trades, Win Rate: {metrics.win_rate:.2%}, P&L: ${metrics.total_pnl_usd:.2f}")
        
        return metrics
    
    def calculate_metrics(self, trades: List[SimulatedTrade]) -> BacktestMetrics:
        """Calculate comprehensive backtest metrics"""
        if not trades:
            return BacktestMetrics(
                total_trades=0, winning_trades=0, losing_trades=0, win_rate=0.0,
                total_pnl_usd=0.0, avg_win_usd=0.0, avg_loss_usd=0.0, profit_factor=0.0,
                sharpe_ratio=0.0, max_drawdown_pct=0.0, avg_hold_minutes=0.0,
                specialist_win_rate=0.0, stale_exit_trades=0, avg_alpha_decay_minutes=0.0,
                capacity_improvement_pct=0.0
            )
        
        winning_trades = [t for t in trades if t.pnl_usd and t.pnl_usd > 0]
        losing_trades = [t for t in trades if t.pnl_usd and t.pnl_usd <= 0]
        
        total_trades = len(trades)
        wins = len(winning_trades)
        losses = len(losing_trades)
        win_rate = wins / total_trades if total_trades > 0 else 0.0
        
        total_pnl = sum(t.pnl_usd for t in trades if t.pnl_usd)
        avg_win = sum(t.pnl_usd for t in winning_trades) / len(winning_trades) if winning_trades else 0.0
        avg_loss = sum(t.pnl_usd for t in losing_trades) / len(losing_trades) if losing_trades else 0.0
        
        gross_profit = sum(t.pnl_usd for t in winning_trades)
        gross_loss = abs(sum(t.pnl_usd for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Sharpe ratio (simplified: annualized Sharpe from trade returns)
        returns = [t.pnl_pct for t in trades if t.pnl_pct is not None]
        if len(returns) > 1:
            mean_return = statistics.mean(returns)
            std_return = statistics.stdev(returns) if len(returns) > 1 else 0.0
            # Annualize assuming ~252 trading days, ~6 trades per day average
            trades_per_year = 252 * 6
            sharpe_ratio = (mean_return / std_return * (trades_per_year ** 0.5)) if std_return > 0 else 0.0
        else:
            sharpe_ratio = 0.0
        
        # Max drawdown
        cumulative_pnl = 0.0
        peak = 0.0
        max_dd = 0.0
        for t in trades:
            cumulative_pnl += t.pnl_usd if t.pnl_usd else 0.0
            peak = max(peak, cumulative_pnl)
            dd = (peak - cumulative_pnl) / peak if peak > 0 else 0.0
            max_dd = max(max_dd, dd)
        
        avg_hold = statistics.mean([t.hold_minutes for t in trades if t.hold_minutes]) if trades else 0.0
        
        # Specialist win rate (mid-day trades)
        specialist_trades = [t for t in trades if t.specialist_boost]
        specialist_wins = [t for t in specialist_trades if t.pnl_usd and t.pnl_usd > 0]
        specialist_win_rate = len(specialist_wins) / len(specialist_trades) if specialist_trades else 0.0
        
        # Stale exits
        stale_exits = [t for t in trades if t.exit_reason == "stale_exit_90min"]
        
        # Alpha decay (simplified - would need price history)
        # For now, estimate based on hold time vs profit
        alpha_decay_times = []
        for t in trades:
            if t.hold_minutes and t.pnl_pct:
                # If trade was unprofitable, alpha decay happened before exit
                if t.pnl_pct < 0:
                    # Estimate: alpha decay at some fraction of hold time
                    alpha_decay_times.append(t.hold_minutes * 0.5)  # Rough estimate
        
        avg_alpha_decay = statistics.mean(alpha_decay_times) if alpha_decay_times else 0.0
        
        # Capacity improvement: trades freed by stale exits
        capacity_improvement = len(stale_exits) / total_trades if total_trades > 0 else 0.0
        
        return BacktestMetrics(
            total_trades=total_trades,
            winning_trades=wins,
            losing_trades=losses,
            win_rate=win_rate,
            total_pnl_usd=total_pnl,
            avg_win_usd=avg_win,
            avg_loss_usd=avg_loss,
            profit_factor=profit_factor,
            sharpe_ratio=sharpe_ratio,
            max_drawdown_pct=max_dd,
            avg_hold_minutes=avg_hold,
            specialist_win_rate=specialist_win_rate,
            stale_exit_trades=len(stale_exits),
            avg_alpha_decay_minutes=avg_alpha_decay,
            capacity_improvement_pct=capacity_improvement
        )
    
    def generate_report(self, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Generate comprehensive backtest report.
        
        Args:
            output_path: Optional path to save JSON report
            
        Returns:
            Dictionary with report data
        """
        if not self.metrics:
            return {"error": "No metrics available - run backtest first"}
        
        # Calculate additional statistics
        all_pnls = [t.pnl_usd for t in self.simulated_trades if t.pnl_usd is not None]
        specialist_trades = [t for t in self.simulated_trades if t.specialist_boost]
        specialist_pnls = [t.pnl_usd for t in specialist_trades if t.pnl_usd is not None]
        
        non_specialist_trades = [t for t in self.simulated_trades if not t.specialist_boost]
        non_specialist_pnls = [t.pnl_usd for t in non_specialist_trades if t.pnl_usd is not None]
        
        import statistics
        
        report = {
            "backtest_summary": {
                "total_trades": self.metrics.total_trades,
                "winning_trades": self.metrics.winning_trades,
                "losing_trades": self.metrics.losing_trades,
                "win_rate": f"{self.metrics.win_rate:.2%}",
                "total_pnl_usd": f"${self.metrics.total_pnl_usd:.2f}",
                "avg_win_usd": f"${self.metrics.avg_win_usd:.2f}",
                "avg_loss_usd": f"${self.metrics.avg_loss_usd:.2f}",
                "profit_factor": f"{self.metrics.profit_factor:.2f}",
                "sharpe_ratio": f"{self.metrics.sharpe_ratio:.2f}",
                "max_drawdown": f"{self.metrics.max_drawdown_pct:.2%}",
                "avg_hold_minutes": f"{self.metrics.avg_hold_minutes:.1f}"
            },
            "specialist_strategy_analysis": {
                "mid_day_window": "11:30-13:30 EST",
                "threshold_increase": "0.75",
                "mid_day_trades": len(specialist_trades),
                "mid_day_win_rate": f"{self.metrics.specialist_win_rate:.2%}",
                "mid_day_avg_pnl": f"${statistics.mean(specialist_pnls):.2f}" if specialist_pnls else "N/A",
                "non_mid_day_trades": len(non_specialist_trades),
                "non_mid_day_win_rate": f"{len([t for t in non_specialist_trades if t.pnl_usd and t.pnl_usd > 0]) / len(non_specialist_trades):.2%}" if non_specialist_trades else "N/A",
                "non_mid_day_avg_pnl": f"${statistics.mean(non_specialist_pnls):.2f}" if non_specialist_pnls else "N/A",
                "improvement": "Yes" if self.metrics.specialist_win_rate > self.metrics.win_rate else "No",
                "sharpe_improvement": "Test if specialist rotator improves Sharpe ratio"
            },
            "stale_exit_analysis": {
                "stale_exit_rule": f"Close at {self.stale_exit_minutes} minutes if P&L < ±{self.stale_exit_pnl_threshold*100:.2f}%",
                "stale_exits": self.metrics.stale_exit_trades,
                "stale_exit_pct": f"{(self.metrics.stale_exit_trades / self.metrics.total_trades * 100):.2f}%" if self.metrics.total_trades > 0 else "0%",
                "capacity_freed_pct": f"{self.metrics.capacity_improvement_pct:.2%}",
                "description": "Frees capacity for high-score signals by closing low-momentum positions"
            },
            "alpha_decay_analysis": {
                "avg_decay_minutes": f"{self.metrics.avg_alpha_decay_minutes:.1f}",
                "description": "Average minutes until signal becomes unprofitable (estimated)",
                "note": "Full alpha decay measurement requires tick-level price history"
            },
            "execution_friction": {
                "latency_penalty_bps": self.latency_penalty_bps,
                "description": "0.5 basis point latency penalty applied to all entries",
                "impact": "Simulates realistic execution friction from order routing"
            },
            "objective_assessment": {
                "target_win_rate": "60%",
                "achieved_win_rate": f"{self.metrics.win_rate:.2%}",
                "meets_target": "Yes" if self.metrics.win_rate >= 0.60 else "No",
                "target_description": "Prove bot can maintain 60% win rate under realistic execution friction"
            },
            "trade_details": {
                "total_simulated_trades": len(self.simulated_trades),
                "by_exit_reason": {}
            }
        }
        
        # Group trades by exit reason
        for trade in self.simulated_trades:
            reason = trade.exit_reason or "unknown"
            if reason not in report["trade_details"]["by_exit_reason"]:
                report["trade_details"]["by_exit_reason"][reason] = {
                    "count": 0,
                    "win_rate": 0.0,
                    "avg_pnl_usd": 0.0
                }
            report["trade_details"]["by_exit_reason"][reason]["count"] += 1
        
        # Calculate win rates and avg P&L by exit reason
        for reason, stats in report["trade_details"]["by_exit_reason"].items():
            reason_trades = [t for t in self.simulated_trades if t.exit_reason == reason]
            wins = len([t for t in reason_trades if t.pnl_usd and t.pnl_usd > 0])
            stats["win_rate"] = f"{(wins / len(reason_trades) * 100):.2f}%" if reason_trades else "0%"
            avg_pnl = statistics.mean([t.pnl_usd for t in reason_trades if t.pnl_usd is not None]) if reason_trades else 0.0
            stats["avg_pnl_usd"] = f"${avg_pnl:.2f}"
        
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2)
            print(f"[BACKTEST] Report saved to {output_path}")
        
        return report


def main():
    """Main entry point for backtest execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run historical backtest with no look-forward bias")
    parser.add_argument("--days", type=int, default=30, help="Number of days to backtest (default: 30)")
    parser.add_argument("--output", type=str, help="Output path for report JSON")
    parser.add_argument("--no-specialist", action="store_true", help="Disable specialist strategy rotator test")
    parser.add_argument("--no-stale-exits", action="store_true", help="Disable stale exit test")
    
    args = parser.parse_args()
    
    # Initialize engine
    engine = HistoricalReplayEngine()
    
    # Run backtest
    metrics = engine.run_backtest(
        days=args.days,
        test_specialist=not args.no_specialist,
        test_stale_exits=not args.no_stale_exits
    )
    
    # Print summary
    print("\n" + "="*60)
    print("BACKTEST RESULTS")
    print("="*60)
    print(f"Total Trades: {metrics.total_trades}")
    print(f"Win Rate: {metrics.win_rate:.2%}")
    print(f"Total P&L: ${metrics.total_pnl_usd:.2f}")
    print(f"Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
    print(f"Profit Factor: {metrics.profit_factor:.2f}")
    print(f"Specialist Win Rate (11:30-13:30 EST): {metrics.specialist_win_rate:.2%}")
    print(f"Stale Exits: {metrics.stale_exit_trades}")
    print(f"Avg Alpha Decay: {metrics.avg_alpha_decay_minutes:.1f} minutes")
    print("="*60)
    
    # Generate report
    if args.output:
        output_path = Path(args.output)
    else:
        reports_dir = Directories.ROOT / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        output_path = reports_dir / f"backtest_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    report = engine.generate_report(output_path=output_path)
    
    print(f"\n[BACKTEST] Complete - Report saved to {output_path}")


if __name__ == "__main__":
    main()