#!/usr/bin/env python3
"""
End-of-Week Forensic Performance Audit
Analyzes Jan 5-9, 2026 trading performance with deep-dive correlation analysis
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import statistics

# Try to import droplet client for remote data
try:
    from droplet_client import DropletClient
    HAS_DROPLET_CLIENT = True
except ImportError:
    HAS_DROPLET_CLIENT = False
    print("WARNING: droplet_client not available - will only use local data")

# Try to import Alpaca API for price verification
try:
    import alpaca_trade_api as tradeapi
    from config.registry import Config
    HAS_ALPACA = True
except ImportError:
    HAS_ALPACA = False
    print("WARNING: Alpaca API not available - price verification will be limited")

REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True, parents=True)

# Date range for audit
START_DATE = datetime(2026, 1, 5, tzinfo=timezone.utc)
END_DATE = datetime(2026, 1, 9, 23, 59, 59, tzinfo=timezone.utc)

class ForensicAuditor:
    """Comprehensive forensic audit analyzer."""
    
    def __init__(self):
        self.signal_history: List[Dict] = []
        self.shadow_outcomes: List[Dict] = []
        self.actual_trades: List[Dict] = []
        self.alpha_api = None
        
        if HAS_ALPACA:
            try:
                self.alpha_api = tradeapi.REST(
                    key_id=Config.ALPACA_KEY_ID,
                    secret_key=Config.ALPACA_SECRET_KEY,
                    base_url=Config.ALPACA_BASE_URL,
                    api_version='v2'
                )
            except Exception as e:
                print(f"WARNING: Could not initialize Alpaca API: {e}")
    
    def load_data_from_droplet(self) -> bool:
        """Load data files from droplet if available."""
        if not HAS_DROPLET_CLIENT:
            return False
        
        try:
            client = DropletClient()
            print("Loading data from droplet...")
            
            # Load signal history
            stdout, stderr, exit_code = client._execute_with_cd(
                "cd ~/stock-bot && cat state/signal_history.jsonl 2>/dev/null || echo ''",
                timeout=30
            )
            if stdout.strip():
                for line in stdout.strip().split('\n'):
                    if line.strip():
                        try:
                            self.signal_history.append(json.loads(line))
                        except:
                            pass
            
            # Load shadow outcomes
            stdout, stderr, exit_code = client._execute_with_cd(
                "cd ~/stock-bot && cat reports/shadow_outcomes.jsonl 2>/dev/null || echo ''",
                timeout=30
            )
            if stdout.strip():
                for line in stdout.strip().split('\n'):
                    if line.strip():
                        try:
                            self.shadow_outcomes.append(json.loads(line))
                        except:
                            pass
            
            # Load shadow positions state file for active positions
            stdout, stderr, exit_code = client._execute_with_cd(
                "cd ~/stock-bot && cat state/shadow_positions.json 2>/dev/null || echo '{}'",
                timeout=30
            )
            if stdout.strip():
                try:
                    shadow_state = json.loads(stdout)
                    positions = shadow_state.get("positions", {})
                    for symbol, pos_data in positions.items():
                        # Convert position data to outcome format
                        outcome = {
                            "symbol": symbol,
                            "direction": pos_data.get("direction", "bullish"),
                            "entry_price": pos_data.get("entry_price", 0),
                            "entry_score": pos_data.get("entry_score", 0),
                            "timestamp": datetime.fromtimestamp(pos_data.get("entry_time", 0), tz=timezone.utc).isoformat() if pos_data.get("entry_time") else "",
                            "current_price": pos_data.get("current_price", pos_data.get("entry_price", 0)),
                            "max_profit_pct": pos_data.get("max_profit_pct", 0),
                            "max_loss_pct": pos_data.get("max_loss_pct", 0),
                            "closed": pos_data.get("closed", False),
                            "status": "closed" if pos_data.get("closed") else "active",
                            "close_reason": pos_data.get("close_reason"),
                            "final_pnl_pct": pos_data.get("max_profit_pct", 0) if not pos_data.get("closed") or pos_data.get("max_profit_pct", 0) > abs(pos_data.get("max_loss_pct", 0)) else pos_data.get("max_loss_pct", 0)
                        }
                        self.shadow_outcomes.append(outcome)
                except Exception as e:
                    print(f"Warning: Could not parse shadow positions state: {e}")
            
            # Load actual trades from orders
            stdout, stderr, exit_code = client._execute_with_cd(
                "cd ~/stock-bot && cat data/live_orders.jsonl 2>/dev/null | tail -100 || echo ''",
                timeout=30
            )
            if stdout.strip():
                for line in stdout.strip().split('\n'):
                    if line.strip():
                        try:
                            order = json.loads(line)
                            if order.get("status") == "filled":
                                self.actual_trades.append(order)
                        except:
                            pass
            
            print(f"Loaded {len(self.signal_history)} signals, {len(self.shadow_outcomes)} shadow outcomes, {len(self.actual_trades)} actual trades")
            return True
        except Exception as e:
            print(f"Error loading from droplet: {e}")
            return False
    
    def load_local_data(self):
        """Load data from local files."""
        # Signal history
        signal_file = Path("state/signal_history.jsonl")
        if signal_file.exists():
            with signal_file.open("r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            self.signal_history.append(json.loads(line))
                        except:
                            pass
        
        # Shadow outcomes
        shadow_file = Path("reports/shadow_outcomes.jsonl")
        if shadow_file.exists():
            with shadow_file.open("r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            self.shadow_outcomes.append(json.loads(line))
                        except:
                            pass
        
        # Load shadow positions state file for active positions
        shadow_state_file = Path("state/shadow_positions.json")
        if shadow_state_file.exists():
            try:
                with shadow_state_file.open("r", encoding="utf-8") as f:
                    shadow_state = json.load(f)
                    positions = shadow_state.get("positions", {})
                    for symbol, pos_data in positions.items():
                        # Convert position data to outcome format
                        outcome = {
                            "symbol": symbol,
                            "direction": pos_data.get("direction", "bullish"),
                            "entry_price": pos_data.get("entry_price", 0),
                            "entry_score": pos_data.get("entry_score", 0),
                            "timestamp": datetime.fromtimestamp(pos_data.get("entry_time", 0), tz=timezone.utc).isoformat() if pos_data.get("entry_time") else "",
                            "current_price": pos_data.get("current_price", pos_data.get("entry_price", 0)),
                            "max_profit_pct": pos_data.get("max_profit_pct", 0),
                            "max_loss_pct": pos_data.get("max_loss_pct", 0),
                            "closed": pos_data.get("closed", False),
                            "status": "closed" if pos_data.get("closed") else "active",
                            "close_reason": pos_data.get("close_reason"),
                            "final_pnl_pct": pos_data.get("max_profit_pct", 0) if not pos_data.get("closed") or pos_data.get("max_profit_pct", 0) > abs(pos_data.get("max_loss_pct", 0)) else pos_data.get("max_loss_pct", 0)
                        }
                        self.shadow_outcomes.append(outcome)
            except Exception:
                pass
        
        # Actual trades - try multiple locations
        for orders_file in [Path("data/live_orders.jsonl"), Path("logs/orders.jsonl")]:
            if orders_file.exists():
                with orders_file.open("r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            try:
                                order = json.loads(line)
                                if order.get("status") == "filled":
                                    self.actual_trades.append(order)
                            except:
                                pass
                break
    
    def filter_by_date_range(self, records: List[Dict], date_field: str = "timestamp") -> List[Dict]:
        """Filter records to date range."""
        filtered = []
        for rec in records:
            try:
                # Try multiple timestamp fields
                ts_str = rec.get(date_field, "") or rec.get("_dt", "") or rec.get("filled_at", "") or rec.get("created_at", "")
                if not ts_str:
                    # If no timestamp, include it (don't filter out)
                    filtered.append(rec)
                    continue
                
                # Parse timestamp (various formats)
                dt = None
                if 'T' in ts_str:
                    # ISO format
                    try:
                        dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                    except:
                        try:
                            # Try without timezone
                            dt = datetime.strptime(ts_str[:19], "%Y-%m-%dT%H:%M:%S")
                            dt = dt.replace(tzinfo=timezone.utc)
                        except:
                            pass
                elif ' ' in ts_str:
                    # Space-separated format
                    try:
                        dt = datetime.strptime(ts_str[:19], "%Y-%m-%d %H:%M:%S")
                        dt = dt.replace(tzinfo=timezone.utc)
                    except:
                        pass
                
                if dt:
                    if START_DATE <= dt <= END_DATE:
                        filtered.append(rec)
                else:
                    # If we can't parse, include it (safer to include than exclude)
                    filtered.append(rec)
            except Exception:
                # On error, include the record
                filtered.append(rec)
        return filtered
    
    def get_price_at_time(self, symbol: str, timestamp: datetime, window_minutes: int = 5) -> Optional[float]:
        """Get price at or near a specific timestamp from Alpaca."""
        if not self.alpha_api:
            return None
        
        try:
            # Convert to EST for Alpaca
            est_tz = timezone(timedelta(hours=-5))
            est_time = timestamp.astimezone(est_tz)
            
            # Get bars around the time
            start = est_time - timedelta(minutes=window_minutes)
            end = est_time + timedelta(minutes=window_minutes)
            
            bars = self.alpha_api.get_bars(
                symbol,
                tradeapi.TimeFrame.Minute,
                start=start.strftime("%Y-%m-%d %H:%M:%S"),
                end=end.strftime("%Y-%m-%d %H:%M:%S"),
                limit=1
            ).df
            
            if not bars.empty:
                return float(bars.iloc[-1]['close'])
        except Exception as e:
            pass
        
        return None
    
    def calculate_shadow_pnl(self, shadow: Dict) -> Dict[str, Any]:
        """Calculate accurate P&L for a shadow trade, verifying with Alpaca."""
        symbol = shadow.get("symbol", "")
        direction = shadow.get("direction", "bullish")
        entry_price = shadow.get("entry_price", 0)
        entry_time_str = shadow.get("timestamp", "")
        
        if not entry_price or not entry_time_str:
            return {"pnl_pct": 0.0, "verified": False}
        
        try:
            entry_time = datetime.fromisoformat(entry_time_str.replace('Z', '+00:00'))
            
            # Verify entry price with Alpaca
            verified_entry = self.get_price_at_time(symbol, entry_time)
            if verified_entry:
                entry_price = verified_entry
            
            # Get current or exit price
            if shadow.get("status") == "closed":
                exit_time_str = shadow.get("timestamp")  # Use same timestamp if no exit time
                exit_price = shadow.get("exit_price", entry_price)
                if exit_price:
                    verified_exit = self.get_price_at_time(symbol, exit_time, window_minutes=10) if 'exit_time' in shadow else None
                    if verified_exit:
                        exit_price = verified_exit
            else:
                # Get latest price
                try:
                    latest = self.alpha_api.get_latest_trade(symbol)
                    exit_price = float(getattr(latest, "price", entry_price))
                except:
                    exit_price = shadow.get("current_price", entry_price)
            
            # Use max_profit_pct or max_loss_pct if available (more accurate for tracking)
            if shadow.get("max_profit_pct") is not None or shadow.get("max_loss_pct") is not None:
                # Use the better of max profit or max loss (whichever is more extreme)
                max_profit = shadow.get("max_profit_pct", 0.0)
                max_loss = shadow.get("max_loss_pct", 0.0)
                # For reporting, use max_profit_pct as it shows the best the trade achieved
                pnl_pct = max_profit if max_profit > abs(max_loss) else max_loss
            else:
                # Calculate P&L from prices
                if direction == "bullish":
                    pnl_pct = ((exit_price - entry_price) / entry_price) * 100
                else:
                    pnl_pct = ((entry_price - exit_price) / entry_price) * 100
            
            return {
                "pnl_pct": pnl_pct,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "max_profit_pct": shadow.get("max_profit_pct", pnl_pct if pnl_pct > 0 else 0),
                "max_loss_pct": shadow.get("max_loss_pct", pnl_pct if pnl_pct < 0 else 0),
                "verified": verified_entry is not None
            }
        except Exception as e:
            # Fallback to shadow data
            pnl_pct = shadow.get("final_pnl_pct") or shadow.get("max_profit_pct") or shadow.get("max_loss_pct") or 0.0
            return {"pnl_pct": pnl_pct, "max_profit_pct": shadow.get("max_profit_pct", 0.0), "max_loss_pct": shadow.get("max_loss_pct", 0.0), "verified": False, "error": str(e)}
    
    def analyze_blocked_trades_performance(self) -> Dict[str, Any]:
        """Analyze performance of blocked trades (> 3.0 blocked by capacity_limit)."""
        blocked_signals = [
            s for s in self.signal_history
            if s.get("final_score", 0) >= 3.0
            and "capacity_limit" in s.get("decision", "").lower()
        ]
        
        blocked_by_score = [
            s for s in self.signal_history
            if s.get("final_score", 0) >= 2.3
            and s.get("final_score", 0) < 3.0
            and ("blocked" in s.get("decision", "").lower() or "rejected" in s.get("decision", "").lower())
        ]
        
        # Match with shadow outcomes
        shadow_map = {s.get("symbol"): s for s in self.shadow_outcomes}
        
        capacity_blocked_results = []
        score_blocked_results = []
        
        for signal in blocked_signals:
            symbol = signal.get("symbol", "")
            shadow = shadow_map.get(symbol)
            if shadow:
                pnl_data = self.calculate_shadow_pnl(shadow)
                capacity_blocked_results.append({
                    "symbol": symbol,
                    "score": signal.get("final_score", 0),
                    "decision": signal.get("decision", ""),
                    "pnl_pct": pnl_data.get("pnl_pct", 0),
                    "verified": pnl_data.get("verified", False),
                    "alpha_signature": signal.get("metadata", {}).get("alpha_signature", {})
                })
        
        for signal in blocked_by_score:
            symbol = signal.get("symbol", "")
            shadow = shadow_map.get(symbol)
            if shadow:
                pnl_data = self.calculate_shadow_pnl(shadow)
                score_blocked_results.append({
                    "symbol": symbol,
                    "score": signal.get("final_score", 0),
                    "decision": signal.get("decision", ""),
                    "pnl_pct": pnl_data.get("pnl_pct", 0),
                    "verified": pnl_data.get("verified", False),
                    "alpha_signature": signal.get("metadata", {}).get("alpha_signature", {})
                })
        
        # Calculate metrics
        def calc_metrics(results):
            if not results:
                return {"count": 0, "win_rate": 0, "avg_pnl": 0, "total_pnl": 0, "winners": 0, "losers": 0}
            
            winners = [r for r in results if r["pnl_pct"] > 0]
            losers = [r for r in results if r["pnl_pct"] <= 0]
            win_rate = len(winners) / len(results) * 100 if results else 0
            avg_pnl = statistics.mean([r["pnl_pct"] for r in results]) if results else 0
            total_pnl = sum([r["pnl_pct"] for r in results])
            
            return {
                "count": len(results),
                "win_rate": round(win_rate, 2),
                "avg_pnl": round(avg_pnl, 2),
                "total_pnl": round(total_pnl, 2),
                "winners": len(winners),
                "losers": len(losers),
                "max_profit": round(max([r["pnl_pct"] for r in results], default=0), 2),
                "max_loss": round(min([r["pnl_pct"] for r in results], default=0), 2)
            }
        
        return {
            "capacity_limit_blocks": calc_metrics(capacity_blocked_results),
            "score_blocks": calc_metrics(score_blocked_results),
            "capacity_blocked_details": capacity_blocked_results,
            "score_blocked_details": score_blocked_results
        }
    
    def analyze_optimal_threshold(self) -> Dict[str, Any]:
        """Identify optimal score threshold based on virtual outcomes."""
        # Group signals by score buckets
        score_buckets = defaultdict(list)
        
        shadow_map = {s.get("symbol"): s for s in self.shadow_outcomes}
        
        for signal in self.signal_history:
            score = signal.get("final_score", 0)
            if score < 2.0:
                bucket = "2.0-2.3"
            elif score < 2.5:
                bucket = "2.3-2.5"
            elif score < 3.0:
                bucket = "2.5-3.0"
            elif score < 3.5:
                bucket = "3.0-3.5"
            elif score < 4.0:
                bucket = "3.5-4.0"
            else:
                bucket = "4.0+"
            
            symbol = signal.get("symbol", "")
            shadow = shadow_map.get(symbol)
            if shadow:
                pnl_data = self.calculate_shadow_pnl(shadow)
                score_buckets[bucket].append({
                    "score": score,
                    "pnl_pct": pnl_data.get("pnl_pct", 0),
                    "symbol": symbol
                })
        
        # Calculate metrics per bucket
        bucket_analysis = {}
        for bucket, results in score_buckets.items():
            if results:
                winners = [r for r in results if r["pnl_pct"] > 0]
                win_rate = len(winners) / len(results) * 100
                avg_pnl = statistics.mean([r["pnl_pct"] for r in results])
                
                bucket_analysis[bucket] = {
                    "count": len(results),
                    "win_rate": round(win_rate, 2),
                    "avg_pnl": round(avg_pnl, 2),
                    "total_pnl": round(sum([r["pnl_pct"] for r in results]), 2),
                    "winners": len(winners),
                    "losers": len(results) - len(winners)
                }
        
        # Find optimal threshold (highest win rate with reasonable count)
        optimal = None
        best_score = 0
        for bucket, metrics in bucket_analysis.items():
            # Score based on win_rate * avg_pnl * log(count) to balance quality and quantity
            score_value = metrics["win_rate"] * metrics["avg_pnl"] * (1 + statistics.log(metrics["count"]) if metrics["count"] > 0 else 0)
            if score_value > best_score and metrics["count"] >= 3:  # Need at least 3 samples
                best_score = score_value
                optimal = bucket
        
        return {
            "bucket_analysis": bucket_analysis,
            "optimal_threshold_bucket": optimal,
            "optimal_score_value": round(best_score, 2)
        }
    
    def analyze_alpha_signatures(self) -> Dict[str, Any]:
        """Correlate alpha signatures (RVOL, RSI, Sector Tide) with virtual winners."""
        winners = []
        losers = []
        
        shadow_map = {s.get("symbol"): s for s in self.shadow_outcomes}
        
        for signal in self.signal_history:
            symbol = signal.get("symbol", "")
            shadow = shadow_map.get(symbol)
            if not shadow:
                continue
            
            pnl_data = self.calculate_shadow_pnl(shadow)
            pnl_pct = pnl_data.get("pnl_pct", 0)
            
            alpha = signal.get("metadata", {}).get("alpha_signature", {})
            rvol = alpha.get("rvol")
            rsi = alpha.get("rsi")
            sector_tide_count = signal.get("sector_tide_count", 0)
            persistence_count = signal.get("persistence_count", 0)
            
            entry = {
                "symbol": symbol,
                "score": signal.get("final_score", 0),
                "pnl_pct": pnl_pct,
                "rvol": rvol,
                "rsi": rsi,
                "sector_tide_count": sector_tide_count,
                "persistence_count": persistence_count
            }
            
            if pnl_pct > 0:
                winners.append(entry)
            else:
                losers.append(entry)
        
        def calc_avg(field, entries):
            values = [e.get(field) for e in entries if e.get(field) is not None]
            try:
                return round(statistics.mean(values), 2) if values else None
            except statistics.StatisticsError:
                return None
        
        return {
            "winners": {
                "count": len(winners),
                "avg_rvol": calc_avg("rvol", winners),
                "avg_rsi": calc_avg("rsi", winners),
                "avg_sector_tide": calc_avg("sector_tide_count", winners),
                "avg_persistence": calc_avg("persistence_count", winners),
                "avg_score": calc_avg("score", winners),
                "avg_pnl": calc_avg("pnl_pct", winners)
            },
            "losers": {
                "count": len(losers),
                "avg_rvol": calc_avg("rvol", losers),
                "avg_rsi": calc_avg("rsi", losers),
                "avg_sector_tide": calc_avg("sector_tide_count", losers),
                "avg_persistence": calc_avg("persistence_count", losers),
                "avg_score": calc_avg("score", losers),
                "avg_pnl": calc_avg("pnl_pct", losers)
            },
            "correlation_insights": self._generate_correlation_insights(winners, losers)
        }
    
    def _generate_correlation_insights(self, winners: List[Dict], losers: List[Dict]) -> List[str]:
        """Generate human-readable correlation insights."""
        insights = []
        
        def compare_field(field_name, field_key):
            w_values = [w.get(field_key) for w in winners if w.get(field_key) is not None]
            l_values = [l.get(field_key) for l in losers if l.get(field_key) is not None]
            
            w_avg = statistics.mean(w_values) if w_values else None
            l_avg = statistics.mean(l_values) if l_values else None
            
            if w_avg is not None and l_avg is not None:
                diff = w_avg - l_avg
                pct_diff = (diff / l_avg * 100) if l_avg != 0 else 0
                insights.append(f"{field_name}: Winners avg {w_avg:.2f} vs Losers avg {l_avg:.2f} ({pct_diff:+.1f}%)")
            elif w_avg is not None:
                insights.append(f"{field_name}: Winners avg {w_avg:.2f} (no loser data)")
            elif l_avg is not None:
                insights.append(f"{field_name}: Losers avg {l_avg:.2f} (no winner data)")
        
        compare_field("RVOL", "rvol")
        compare_field("RSI", "rsi")
        compare_field("Sector Tide Count", "sector_tide_count")
        compare_field("Persistence Count", "persistence_count")
        compare_field("Entry Score", "score")
        
        return insights
    
    def analyze_holding_times(self) -> Dict[str, Any]:
        """Analyze average hold times for winners vs losers."""
        winner_times = []
        loser_times = []
        
        for shadow in self.shadow_outcomes:
            if shadow.get("status") != "closed":
                continue
            
            try:
                entry_time_str = shadow.get("timestamp", "")
                exit_time_str = shadow.get("timestamp", "")  # Assuming same if not specified
                
                if not entry_time_str:
                    continue
                
                entry_time = datetime.fromisoformat(entry_time_str.replace('Z', '+00:00'))
                
                # Try to get exit time from close_time or duration
                if "close_time" in shadow:
                    exit_time = datetime.fromisoformat(shadow["close_time"].replace('Z', '+00:00'))
                elif "duration_seconds" in shadow:
                    exit_time = entry_time + timedelta(seconds=shadow["duration_seconds"])
                else:
                    # Assume 60 minute duration for closed shadows
                    exit_time = entry_time + timedelta(minutes=60)
                
                duration_minutes = (exit_time - entry_time).total_seconds() / 60
                
                pnl_pct = shadow.get("final_pnl_pct", shadow.get("max_profit_pct", 0))
                
                if pnl_pct > 0:
                    winner_times.append(duration_minutes)
                else:
                    loser_times.append(duration_minutes)
            except Exception:
                continue
        
        def calc_time_stats(times):
            if not times:
                return {"count": 0, "avg_minutes": 0, "median_minutes": 0, "min_minutes": 0, "max_minutes": 0}
            
            return {
                "count": len(times),
                "avg_minutes": round(statistics.mean(times), 1),
                "median_minutes": round(statistics.median(times), 1),
                "min_minutes": round(min(times), 1),
                "max_minutes": round(max(times), 1)
            }
        
        return {
            "winners": calc_time_stats(winner_times),
            "losers": calc_time_stats(loser_times),
            "profit_target_analysis": {
                "current_target_pct": 0.75,
                "winner_avg_hold_minutes": calc_time_stats(winner_times).get("avg_minutes", 0),
                "recommendation": "KEEP" if calc_time_stats(winner_times).get("avg_minutes", 0) < 90 else "INCREASE"
            }
        }
    
    def calculate_actual_pnl(self) -> Dict[str, Any]:
        """Calculate actual P&L from filled trades."""
        if not self.actual_trades:
            return {"total_pnl": 0, "win_rate": 0, "count": 0}
        
        # This would need to match orders with exits
        # For now, return placeholder
        return {
            "total_pnl": 0,  # Would need exit data
            "win_rate": 0,
            "count": len(self.actual_trades),
            "note": "Exit data needed for accurate calculation"
        }
    
    def generate_data_export(self) -> Dict[str, Any]:
        """Generate raw data export of all signals."""
        export = {
            "audit_period": {
                "start": START_DATE.isoformat(),
                "end": END_DATE.isoformat()
            },
            "signals": []
        }
        
        shadow_map = {s.get("symbol"): s for s in self.shadow_outcomes}
        
        for signal in self.signal_history:
            symbol = signal.get("symbol", "")
            shadow = shadow_map.get(symbol)
            
            outcome = "Rejected"
            pnl_pct = None
            
            if "Ordered" in signal.get("decision", ""):
                outcome = "Filled"
            elif shadow:
                pnl_data = self.calculate_shadow_pnl(shadow)
                pnl_pct = pnl_data.get("pnl_pct", 0)
                if pnl_pct > 0:
                    outcome = "Virtual_Win"
                else:
                    outcome = "Virtual_Loss"
            
            export["signals"].append({
                "timestamp": signal.get("timestamp", ""),
                "symbol": symbol,
                "direction": signal.get("direction", ""),
                "raw_score": signal.get("raw_score", 0),
                "whale_boost": signal.get("whale_boost", 0),
                "final_score": signal.get("final_score", 0),
                "decision": signal.get("decision", ""),
                "outcome": outcome,
                "pnl_pct": pnl_pct,
                "sector": signal.get("sector", ""),
                "persistence_count": signal.get("persistence_count", 0),
                "sector_tide_count": signal.get("sector_tide_count", 0),
                "alpha_signature": signal.get("metadata", {}).get("alpha_signature", {})
            })
        
        return export
    
    def generate_markdown_report(self, analyses: Dict[str, Any]) -> str:
        """Generate comprehensive markdown report."""
        report = []
        report.append("# End-of-Week Forensic Performance Audit")
        report.append(f"**Period**: {START_DATE.strftime('%B %d')} - {END_DATE.strftime('%B %d, %Y')}")
        report.append(f"**Generated**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        report.append("")
        report.append("---")
        report.append("")
        
        # 1. Executive P&L Summary
        report.append("## 1. Executive P&L Summary (Actual vs. Virtual)")
        report.append("")
        actual_pnl = analyses.get("actual_pnl", {})
        blocked = analyses.get("blocked_trades", {})
        
        report.append(f"- **Actual Trades**: {actual_pnl.get('count', 0)} filled orders")
        report.append(f"- **Capacity-Limit Blocks**: {blocked.get('capacity_limit_blocks', {}).get('count', 0)} signals > 3.0")
        report.append(f"- **Score Blocks**: {blocked.get('score_blocks', {}).get('count', 0)} signals 2.3-3.0")
        report.append("")
        
        cap_blocks = blocked.get('capacity_limit_blocks', {})
        if cap_blocks.get('count', 0) > 0:
            report.append(f"### Capacity-Limit Blocked Performance")
            report.append(f"- **Total Virtual P&L**: {cap_blocks.get('total_pnl', 0):.2f}%")
            report.append(f"- **Win Rate**: {cap_blocks.get('win_rate', 0):.2f}%")
            report.append(f"- **Avg P&L**: {cap_blocks.get('avg_pnl', 0):.2f}%")
            report.append(f"- **Max Profit**: {cap_blocks.get('max_profit', 0):.2f}%")
            report.append(f"- **Max Loss**: {cap_blocks.get('max_loss', 0):.2f}%")
            report.append("")
        
        # 2. Blocked Trades Performance
        report.append("## 2. Blocked Trades Performance")
        report.append("")
        report.append("### Signals > 3.0 Blocked by Capacity Limit")
        report.append("")
        
        cap_details = blocked.get('capacity_blocked_details', [])
        if cap_details:
            report.append("| Symbol | Score | Decision | Virtual P&L % | Verified |")
            report.append("|--------|-------|----------|---------------|----------|")
            for detail in sorted(cap_details, key=lambda x: x.get('score', 0), reverse=True)[:20]:
                verified_mark = "YES" if detail.get('verified') else "NO"
                report.append(f"| {detail.get('symbol', '')} | {detail.get('score', 0):.2f} | {detail.get('decision', '')} | {detail.get('pnl_pct', 0):.2f}% | {verified_mark} |")
        else:
            report.append("*No capacity-limit blocks found in this period.*")
        report.append("")
        
        # 3. Optimal Threshold Analysis
        report.append("## 3. Optimal Threshold Analysis")
        report.append("")
        threshold = analyses.get("optimal_threshold", {})
        bucket_analysis = threshold.get("bucket_analysis", {})
        
        if bucket_analysis:
            report.append("### Score Bucket Performance")
            report.append("")
            report.append("| Score Range | Count | Win Rate % | Avg P&L % | Total P&L % | Winners | Losers |")
            report.append("|-------------|-------|------------|-----------|-------------|---------|--------|")
            for bucket, metrics in sorted(bucket_analysis.items()):
                report.append(f"| {bucket} | {metrics.get('count', 0)} | {metrics.get('win_rate', 0):.2f} | {metrics.get('avg_pnl', 0):.2f} | {metrics.get('total_pnl', 0):.2f} | {metrics.get('winners', 0)} | {metrics.get('losers', 0)} |")
            report.append("")
        
        optimal_bucket = threshold.get("optimal_threshold_bucket")
        if optimal_bucket:
            report.append(f"### **Optimal Threshold Recommendation**: {optimal_bucket}")
            report.append(f"- **Score Value**: {threshold.get('optimal_score_value', 0):.2f}")
            report.append("")
        
        # 4. Alpha Signature Correlation
        report.append("## 4. Alpha Signature Correlation")
        report.append("")
        alpha = analyses.get("alpha_signatures", {})
        winners_alpha = alpha.get("winners", {})
        losers_alpha = alpha.get("losers", {})
        
        report.append("### Winner vs Loser Alpha Signatures")
        report.append("")
        report.append("| Metric | Winners Avg | Losers Avg | Difference |")
        report.append("|--------|-------------|------------|------------|")
        
        if winners_alpha.get("avg_rvol") is not None:
            diff = (winners_alpha.get("avg_rvol", 0) - losers_alpha.get("avg_rvol", 0)) if losers_alpha.get("avg_rvol") else 0
            report.append(f"| RVOL | {winners_alpha.get('avg_rvol', 0):.2f} | {losers_alpha.get('avg_rvol', 0):.2f} | {diff:+.2f} |")
        
        if winners_alpha.get("avg_rsi") is not None:
            diff = (winners_alpha.get("avg_rsi", 0) - losers_alpha.get("avg_rsi", 0)) if losers_alpha.get("avg_rsi") else 0
            report.append(f"| RSI | {winners_alpha.get('avg_rsi', 0):.2f} | {losers_alpha.get('avg_rsi', 0):.2f} | {diff:+.2f} |")
        
        if winners_alpha.get("avg_sector_tide") is not None:
            diff = (winners_alpha.get("avg_sector_tide", 0) - losers_alpha.get("avg_sector_tide", 0)) if losers_alpha.get("avg_sector_tide") else 0
            report.append(f"| Sector Tide Count | {winners_alpha.get('avg_sector_tide', 0):.2f} | {losers_alpha.get('avg_sector_tide', 0):.2f} | {diff:+.2f} |")
        
        if winners_alpha.get("avg_persistence") is not None:
            diff = (winners_alpha.get("avg_persistence", 0) - losers_alpha.get("avg_persistence", 0)) if losers_alpha.get("avg_persistence") else 0
            report.append(f"| Persistence Count | {winners_alpha.get('avg_persistence', 0):.2f} | {losers_alpha.get('avg_persistence', 0):.2f} | {diff:+.2f} |")
        
        report.append("")
        report.append("### Key Insights")
        insights = alpha.get("correlation_insights", [])
        for insight in insights:
            report.append(f"- {insight}")
        report.append("")
        
        # 5. Holding Time Audit
        report.append("## 5. Holding Time Audit")
        report.append("")
        holding = analyses.get("holding_times", {})
        winners_time = holding.get("winners", {})
        losers_time = holding.get("losers", {})
        
        report.append("### Average Hold Times")
        report.append("")
        report.append("| Category | Count | Avg Minutes | Median Minutes | Min | Max |")
        report.append("|----------|-------|-------------|----------------|-----|-----|")
        report.append(f"| Winners | {winners_time.get('count', 0)} | {winners_time.get('avg_minutes', 0):.1f} | {winners_time.get('median_minutes', 0):.1f} | {winners_time.get('min_minutes', 0):.1f} | {winners_time.get('max_minutes', 0):.1f} |")
        report.append(f"| Losers | {losers_time.get('count', 0)} | {losers_time.get('median_minutes', 0):.1f} | {losers_time.get('median_minutes', 0):.1f} | {losers_time.get('min_minutes', 0):.1f} | {losers_time.get('max_minutes', 0):.1f} |")
        report.append("")
        
        profit_target = holding.get("profit_target_analysis", {})
        report.append(f"### Profit Target Analysis (Current: {profit_target.get('current_target_pct', 0)}%)")
        report.append(f"- **Winner Avg Hold Time**: {profit_target.get('winner_avg_hold_minutes', 0):.1f} minutes")
        report.append(f"- **Recommendation**: {profit_target.get('recommendation', 'KEEP')} current target")
        report.append("")
        
        return "\n".join(report)

def main():
    """Main execution."""
    print("=" * 80)
    print("END-OF-WEEK FORENSIC PERFORMANCE AUDIT")
    print("=" * 80)
    print()
    
    auditor = ForensicAuditor()
    
    # Load data
    print("Loading data...")
    if HAS_DROPLET_CLIENT:
        loaded = auditor.load_data_from_droplet()
        if not loaded:
            print("Falling back to local data...")
            auditor.load_local_data()
    else:
        auditor.load_local_data()
    
    # Filter to date range
    print(f"Filtering to date range: {START_DATE.date()} to {END_DATE.date()}...")
    auditor.signal_history = auditor.filter_by_date_range(auditor.signal_history)
    auditor.shadow_outcomes = auditor.filter_by_date_range(auditor.shadow_outcomes)
    auditor.actual_trades = auditor.filter_by_date_range(auditor.actual_trades, date_field="filled_at")
    
    print(f"Data loaded: {len(auditor.signal_history)} signals, {len(auditor.shadow_outcomes)} shadow outcomes, {len(auditor.actual_trades)} actual trades")
    print()
    
    # Perform analyses
    print("Performing analyses...")
    analyses = {
        "actual_pnl": auditor.calculate_actual_pnl(),
        "blocked_trades": auditor.analyze_blocked_trades_performance(),
        "optimal_threshold": auditor.analyze_optimal_threshold(),
        "alpha_signatures": auditor.analyze_alpha_signatures(),
        "holding_times": auditor.analyze_holding_times()
    }
    
    # Generate reports
    print("Generating reports...")
    
    # Markdown report
    markdown = auditor.generate_markdown_report(analyses)
    report_file = REPORTS_DIR / "WEEKLY_FORENSIC_AUDIT_2026-01-09.md"
    with report_file.open("w", encoding="utf-8") as f:
        f.write(markdown)
    print(f"[OK] Generated: {report_file}")
    
    # JSON data export
    data_export = auditor.generate_data_export()
    export_file = REPORTS_DIR / "WEEKLY_DATA_EXPORT_2026-01-09.json"
    with export_file.open("w", encoding="utf-8") as f:
        json.dump(data_export, f, indent=2)
    print(f"[OK] Generated: {export_file}")
    
    print()
    print("=" * 80)
    print("AUDIT COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
