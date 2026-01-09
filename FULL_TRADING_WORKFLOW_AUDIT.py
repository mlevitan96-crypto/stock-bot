#!/usr/bin/env python3
"""
Full Trading Workflow Audit
Comprehensive audit to verify:
1. Bot is seeing current open trades
2. Position reconciliation is working
3. Complete trading workflow is functioning
4. Exit evaluation is running correctly
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
    from config.registry import StateFiles, LogFiles, ConfigFiles, get_env, APIConfig
    import alpaca_trade_api as tradeapi
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


class TradingWorkflowAuditor:
    """Comprehensive audit of trading workflow and position tracking."""
    
    def __init__(self):
        self.api = None
        self.issues = []
        self.warnings = []
        self.info = []
        
    def connect_alpaca(self):
        """Connect to Alpaca API."""
        try:
            api_key = get_env("ALPACA_KEY") or get_env("ALPACA_API_KEY")
            api_secret = get_env("ALPACA_SECRET") or get_env("ALPACA_API_SECRET")
            base_url = get_env("ALPACA_BASE_URL", APIConfig.ALPACA_BASE_URL)
            
            if not api_key or not api_secret:
                raise ValueError("ALPACA_KEY and ALPACA_SECRET must be set in environment")
            
            self.api = tradeapi.REST(api_key, api_secret, base_url)
            # Test connection
            account = self.api.get_account()
            self.info.append(f"✅ Alpaca API connected (Account: {account.account_number})")
            return True
        except Exception as e:
            self.issues.append(f"❌ Failed to connect to Alpaca: {e}")
            return False
    
    def check_alpaca_positions(self) -> List[Dict]:
        """Get current positions from Alpaca."""
        try:
            positions = self.api.list_positions()
            alpaca_positions = []
            for p in positions:
                alpaca_positions.append({
                    "symbol": getattr(p, "symbol", ""),
                    "qty": float(getattr(p, "qty", 0)),
                    "side": getattr(p, "side", ""),
                    "avg_entry_price": float(getattr(p, "avg_entry_price", 0)),
                    "current_price": float(getattr(p, "current_price", 0)),
                    "market_value": float(getattr(p, "market_value", 0)),
                    "unrealized_pl": float(getattr(p, "unrealized_pl", 0)),
                    "unrealized_plpc": float(getattr(p, "unrealized_plpc", 0))
                })
            return alpaca_positions
        except Exception as e:
            self.issues.append(f"❌ Failed to fetch Alpaca positions: {e}")
            return []
    
    def check_executor_opens(self) -> Dict:
        """Check executor.opens state (from state file if available)."""
        executor_state_path = Path("state/executor_state.json")
        if executor_state_path.exists():
            try:
                with open(executor_state_path, "r") as f:
                    state = json.load(f)
                    opens = state.get("opens", {})
                    # Convert timestamp strings back to datetime for age calculation
                    for symbol, info in opens.items():
                        if "ts" in info and isinstance(info["ts"], str):
                            try:
                                info["ts"] = datetime.fromisoformat(info["ts"].replace("Z", "+00:00"))
                            except:
                                pass
                    return opens
            except Exception as e:
                self.warnings.append(f"⚠️ Failed to load executor state: {e}")
        return {}
    
    def check_position_metadata(self) -> Dict:
        """Check position metadata file."""
        metadata_path = StateFiles.POSITION_METADATA
        if metadata_path.exists():
            try:
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)
                    return metadata
            except Exception as e:
                self.warnings.append(f"⚠️ Failed to load position metadata: {e}")
        return {}
    
    def check_reconciliation_logs(self) -> List[Dict]:
        """Check recent reconciliation events."""
        reconciliation_log = Path("data/audit_positions_autofix.jsonl")
        events = []
        if reconciliation_log.exists():
            try:
                with open(reconciliation_log, "r") as f:
                    lines = f.readlines()
                    # Get last 20 events
                    for line in lines[-20:]:
                        try:
                            events.append(json.loads(line.strip()))
                        except:
                            pass
            except Exception as e:
                self.warnings.append(f"⚠️ Failed to read reconciliation log: {e}")
        return events
    
    def check_recent_exits(self) -> List[Dict]:
        """Check recent exit events."""
        # log_event("exit", ...) writes to logs/exit.jsonl (not exits.jsonl)
        exit_log = Path("logs/exit.jsonl")
        exits = []
        if exit_log.exists():
            try:
                with open(exit_log, "r") as f:
                    lines = f.readlines()
                    # Get last 50 exit events
                    for line in lines[-50:]:
                        try:
                            exits.append(json.loads(line.strip()))
                        except:
                            pass
            except Exception as e:
                self.warnings.append(f"⚠️ Failed to read exit log: {e}")
        return exits
    
    def check_recent_entries(self) -> List[Dict]:
        """Check recent entry/attribution events."""
        attribution_log = LogFiles.ATTRIBUTION
        entries = []
        if attribution_log.exists():
            try:
                with open(attribution_log, "r") as f:
                    lines = f.readlines()
                    # Get last 50 entries
                    for line in lines[-50:]:
                        try:
                            rec = json.loads(line.strip())
                            if rec.get("type") == "attribution" and not rec.get("trade_id", "").startswith("open_"):
                                entries.append(rec)
                        except:
                            pass
            except Exception as e:
                self.warnings.append(f"⚠️ Failed to read attribution log: {e}")
        return entries
    
    def check_main_loop_activity(self) -> Dict:
        """Check if main loop is running (check run.jsonl)."""
        run_log = Path("logs/run.jsonl")
        activity = {
            "last_cycle": None,
            "cycles_last_hour": 0,
            "cycles_last_day": 0,
            "is_active": False
        }
        
        if run_log.exists():
            try:
                with open(run_log, "r") as f:
                    lines = f.readlines()
                    if lines:
                        # Get last cycle
                        last_line = lines[-1]
                        try:
                            last_cycle = json.loads(last_line.strip())
                            activity["last_cycle"] = last_cycle.get("ts", "")
                            
                            # Count cycles in last hour and day
                            now = datetime.now(timezone.utc)
                            hour_ago = now.timestamp() - 3600
                            day_ago = now.timestamp() - 86400
                            
                            for line in lines[-100:]:  # Check last 100 cycles
                                try:
                                    cycle = json.loads(line.strip())
                                    ts_str = cycle.get("ts", "")
                                    if ts_str:
                                        if isinstance(ts_str, (int, float)):
                                            ts = datetime.fromtimestamp(ts_str, tz=timezone.utc)
                                        else:
                                            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                                            if ts.tzinfo is None:
                                                ts = ts.replace(tzinfo=timezone.utc)
                                        
                                        ts_timestamp = ts.timestamp()
                                        if ts_timestamp >= hour_ago:
                                            activity["cycles_last_hour"] += 1
                                        if ts_timestamp >= day_ago:
                                            activity["cycles_last_day"] += 1
                                except:
                                    pass
                            
                            # Consider active if cycle in last 5 minutes
                            if activity["last_cycle"]:
                                try:
                                    if isinstance(activity["last_cycle"], (int, float)):
                                        last_ts = datetime.fromtimestamp(activity["last_cycle"], tz=timezone.utc)
                                    else:
                                        last_ts = datetime.fromisoformat(activity["last_cycle"].replace("Z", "+00:00"))
                                        if last_ts.tzinfo is None:
                                            last_ts = last_ts.replace(tzinfo=timezone.utc)
                                    
                                    age_sec = (now - last_ts).total_seconds()
                                    activity["is_active"] = age_sec < 300  # 5 minutes
                                except:
                                    pass
                        except:
                            pass
            except Exception as e:
                self.warnings.append(f"⚠️ Failed to read run log: {e}")
        
        return activity
    
    def compare_positions(self, alpaca_positions: List[Dict], executor_opens: Dict, metadata: Dict):
        """Compare Alpaca positions with executor.opens and metadata."""
        alpaca_symbols = {p["symbol"] for p in alpaca_positions}
        executor_symbols = set(executor_opens.keys())
        metadata_symbols = set(metadata.keys())
        
        # Check for positions in Alpaca but not in executor
        missing_in_executor = alpaca_symbols - executor_symbols
        if missing_in_executor:
            self.issues.append(f"❌ Positions in Alpaca but NOT in executor.opens: {missing_in_executor}")
        else:
            self.info.append("✅ All Alpaca positions are in executor.opens")
        
        # Check for positions in executor but not in Alpaca
        orphaned_in_executor = executor_symbols - alpaca_symbols
        if orphaned_in_executor:
            self.warnings.append(f"⚠️ Positions in executor.opens but NOT in Alpaca: {orphaned_in_executor}")
        else:
            self.info.append("✅ No orphaned positions in executor.opens")
        
        # Check for positions in Alpaca but not in metadata
        missing_in_metadata = alpaca_symbols - metadata_symbols
        if missing_in_metadata:
            self.warnings.append(f"⚠️ Positions in Alpaca but NOT in metadata: {missing_in_metadata}")
        else:
            self.info.append("✅ All Alpaca positions have metadata")
        
        # Check position details match
        for pos in alpaca_positions:
            symbol = pos["symbol"]
            if symbol in executor_opens:
                exec_info = executor_opens[symbol]
                # Check quantity match (allow small floating point differences)
                exec_qty = abs(exec_info.get("qty", 0))
                alpaca_qty = abs(pos["qty"])
                if abs(exec_qty - alpaca_qty) > 0.01:
                    self.warnings.append(
                        f"⚠️ Quantity mismatch for {symbol}: executor={exec_qty}, Alpaca={alpaca_qty}"
                    )
                
                # Check entry price match (allow small differences)
                exec_entry = exec_info.get("entry_price", 0)
                alpaca_entry = pos["avg_entry_price"]
                if abs(exec_entry - alpaca_entry) > 0.01:
                    self.warnings.append(
                        f"⚠️ Entry price mismatch for {symbol}: executor={exec_entry:.2f}, Alpaca={alpaca_entry:.2f}"
                    )
                
                # Check entry_score exists
                entry_score = exec_info.get("entry_score", 0.0)
                if entry_score <= 0.0:
                    self.warnings.append(
                        f"⚠️ {symbol} has zero or missing entry_score in executor.opens"
                    )
                
                # Check age
                entry_ts = exec_info.get("ts")
                age_hours = 0.0
                if entry_ts:
                    try:
                        if isinstance(entry_ts, str):
                            # Try ISO format first
                            try:
                                entry_ts_parsed = datetime.fromisoformat(entry_ts.replace("Z", "+00:00"))
                            except:
                                # Try timestamp format
                                try:
                                    entry_ts_parsed = datetime.fromtimestamp(float(entry_ts), tz=timezone.utc)
                                except:
                                    entry_ts_parsed = None
                        elif isinstance(entry_ts, (int, float)):
                            entry_ts_parsed = datetime.fromtimestamp(entry_ts, tz=timezone.utc)
                        else:
                            entry_ts_parsed = entry_ts  # Already a datetime object
                        
                        if entry_ts_parsed:
                            now = datetime.now(timezone.utc)
                            if hasattr(entry_ts_parsed, 'tzinfo') and entry_ts_parsed.tzinfo is None:
                                entry_ts_parsed = entry_ts_parsed.replace(tzinfo=timezone.utc)
                            age_hours = (now - entry_ts_parsed).total_seconds() / 3600
                    except Exception as age_err:
                        # If age calculation fails, try to get from metadata
                        meta_entry_ts = metadata.get(symbol, {}).get("entry_ts")
                        if meta_entry_ts:
                            try:
                                meta_ts = datetime.fromisoformat(meta_entry_ts.replace("Z", "+00:00"))
                                if meta_ts.tzinfo is None:
                                    meta_ts = meta_ts.replace(tzinfo=timezone.utc)
                                now = datetime.now(timezone.utc)
                                age_hours = (now - meta_ts).total_seconds() / 3600
                            except:
                                pass
                
                self.info.append(
                    f"📊 {symbol}: qty={alpaca_qty}, entry=${alpaca_entry:.2f}, "
                    f"current=${pos['current_price']:.2f}, P&L={pos['unrealized_plpc']:.2f}%, "
                    f"age={age_hours:.1f}h, entry_score={entry_score:.2f}"
                )
    
    def check_exit_evaluation_activity(self, exits: List[Dict]):
        """Check if exit evaluation is running."""
        if not exits:
            self.warnings.append("⚠️ No exit events found in logs (exit evaluation may not be running)")
            return
        
        # Get most recent exit
        most_recent = None
        most_recent_ts = None
        
        for exit_event in exits:
            ts_str = exit_event.get("ts", "")
            if ts_str:
                try:
                    if isinstance(ts_str, (int, float)):
                        ts = datetime.fromtimestamp(ts_str, tz=timezone.utc)
                    else:
                        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        if ts.tzinfo is None:
                            ts = ts.replace(tzinfo=timezone.utc)
                    
                    if most_recent_ts is None or ts > most_recent_ts:
                        most_recent_ts = ts
                        most_recent = exit_event
                except:
                    pass
        
        if most_recent:
            now = datetime.now(timezone.utc)
            age_sec = (now - most_recent_ts).total_seconds()
            age_min = age_sec / 60
            
            if age_min < 10:
                self.info.append(f"✅ Exit evaluation active (last exit {age_min:.1f} minutes ago)")
            elif age_min < 60:
                self.warnings.append(f"⚠️ Last exit event was {age_min:.1f} minutes ago")
            else:
                self.issues.append(f"❌ Last exit event was {age_min:.1f} minutes ago (exit evaluation may not be running)")
        else:
            self.warnings.append("⚠️ Could not determine last exit event timestamp")
    
    def check_entry_activity(self, entries: List[Dict]):
        """Check if entry/execution is working."""
        if not entries:
            self.warnings.append("⚠️ No entry events found in logs (entry execution may not be working)")
            return
        
        # Get most recent entry
        most_recent = None
        most_recent_ts = None
        
        for entry in entries:
            ts_str = entry.get("ts", "")
            if ts_str:
                try:
                    if isinstance(ts_str, (int, float)):
                        ts = datetime.fromtimestamp(ts_str, tz=timezone.utc)
                    else:
                        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        if ts.tzinfo is None:
                            ts = ts.replace(tzinfo=timezone.utc)
                    
                    if most_recent_ts is None or ts > most_recent_ts:
                        most_recent_ts = ts
                        most_recent = entry
                except:
                    pass
        
        if most_recent:
            now = datetime.now(timezone.utc)
            age_sec = (now - most_recent_ts).total_seconds()
            age_hours = age_sec / 3600
            
            symbol = most_recent.get("symbol", "unknown")
            score = most_recent.get("score", 0.0)
            self.info.append(
                f"📈 Last entry: {symbol} at {most_recent_ts.strftime('%Y-%m-%d %H:%M:%S UTC')} "
                f"({age_hours:.1f} hours ago), score={score:.2f}"
            )
    
    def run_full_audit(self):
        """Run complete audit."""
        print("=" * 80)
        print("FULL TRADING WORKFLOW AUDIT")
        print("=" * 80)
        print()
        
        # 1. Connect to Alpaca
        print("1. Connecting to Alpaca API...")
        if not self.connect_alpaca():
            print("❌ Cannot proceed without Alpaca connection")
            return
        print()
        
        # 2. Get Alpaca positions
        print("2. Fetching current positions from Alpaca...")
        alpaca_positions = self.check_alpaca_positions()
        print(f"   Found {len(alpaca_positions)} positions in Alpaca")
        if alpaca_positions:
            for pos in alpaca_positions:
                print(f"   - {pos['symbol']}: {pos['qty']} @ ${pos['avg_entry_price']:.2f}, "
                      f"current=${pos['current_price']:.2f}, P&L={pos['unrealized_plpc']:.2f}%")
        print()
        
        # 3. Check executor state
        print("3. Checking executor.opens state...")
        executor_opens = self.check_executor_opens()
        print(f"   Found {len(executor_opens)} positions in executor.opens")
        print()
        
        # 4. Check position metadata
        print("4. Checking position metadata...")
        metadata = self.check_position_metadata()
        print(f"   Found {len(metadata)} positions in metadata")
        print()
        
        # 5. Compare positions
        print("5. Comparing positions across all sources...")
        self.compare_positions(alpaca_positions, executor_opens, metadata)
        print()
        
        # 6. Check main loop activity
        print("6. Checking main loop activity...")
        activity = self.check_main_loop_activity()
        if activity["is_active"]:
            print(f"   ✅ Main loop is ACTIVE")
        else:
            print(f"   ⚠️ Main loop may not be running (last cycle: {activity['last_cycle']})")
        print(f"   Cycles in last hour: {activity['cycles_last_hour']}")
        print(f"   Cycles in last day: {activity['cycles_last_day']}")
        print()
        
        # 7. Check exit evaluation
        print("7. Checking exit evaluation activity...")
        exits = self.check_recent_exits()
        print(f"   Found {len(exits)} recent exit events")
        self.check_exit_evaluation_activity(exits)
        print()
        
        # 8. Check entry activity
        print("8. Checking entry/execution activity...")
        entries = self.check_recent_entries()
        print(f"   Found {len(entries)} recent entry events")
        self.check_entry_activity(entries)
        print()
        
        # 9. Check reconciliation logs
        print("9. Checking reconciliation logs...")
        recon_events = self.check_reconciliation_logs()
        print(f"   Found {len(recon_events)} recent reconciliation events")
        if recon_events:
            last_recon = recon_events[-1]
            event_type = last_recon.get("event", "unknown")
            print(f"   Last event: {event_type}")
        print()
        
        # Summary
        print("=" * 80)
        print("AUDIT SUMMARY")
        print("=" * 80)
        print()
        
        if self.info:
            print("✅ INFO:")
            for msg in self.info:
                print(f"   {msg}")
            print()
        
        if self.warnings:
            print("⚠️ WARNINGS:")
            for msg in self.warnings:
                print(f"   {msg}")
            print()
        
        if self.issues:
            print("❌ ISSUES:")
            for msg in self.issues:
                print(f"   {msg}")
            print()
        
        # Overall status
        if self.issues:
            print("❌ AUDIT RESULT: ISSUES FOUND - Review and fix issues above")
        elif self.warnings:
            print("⚠️ AUDIT RESULT: WARNINGS FOUND - System may need attention")
        else:
            print("✅ AUDIT RESULT: ALL CHECKS PASSED - Trading workflow appears healthy")
        
        print()
        print("=" * 80)


if __name__ == "__main__":
    auditor = TradingWorkflowAuditor()
    auditor.run_full_audit()
