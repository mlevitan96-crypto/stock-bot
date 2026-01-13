#!/usr/bin/env python3
"""
Failure Point Monitor
Monitors all trading failure points and provides self-healing
"""

import json
import time
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class FailurePointStatus:
    """Status of a single failure point"""
    id: str
    name: str
    category: str
    status: str  # "OK", "WARN", "ERROR"
    last_check: float
    last_error: Optional[str] = None
    self_healing_attempted: bool = False
    self_healing_success: bool = False
    details: Dict = None

class FailurePointMonitor:
    """Monitors all failure points and provides self-healing"""
    
    def __init__(self):
        self.state_file = Path("state/failure_point_monitor.json")
        self.statuses: Dict[str, FailurePointStatus] = {}
        self._load_state()
    
    def _load_state(self):
        """Load previous state"""
        if self.state_file.exists():
            try:
                with self.state_file.open() as f:
                    data = json.load(f)
                for fp_id, status_data in data.get("statuses", {}).items():
                    self.statuses[fp_id] = FailurePointStatus(**status_data)
            except Exception as e:
                print(f"[WARN] Failed to load FP monitor state: {e}")
    
    def _save_state(self):
        """Save current state"""
        self.state_file.parent.mkdir(exist_ok=True)
        with self.state_file.open("w") as f:
            json.dump({
                "last_update": time.time(),
                "statuses": {fp_id: asdict(status) for fp_id, status in self.statuses.items()}
            }, f, indent=2)
    
    def check_fp_1_1_uw_daemon(self) -> FailurePointStatus:
        """FP-1.1: UW Daemon Running"""
        try:
            result = subprocess.run(['pgrep', '-f', 'uw_flow_daemon'], 
                                  capture_output=True, timeout=5)
            running = result.returncode == 0
            
            status = "OK" if running else "ERROR"
            error = None if running else "UW daemon not running"
            
            # Self-healing
            if not running:
                self._heal_uw_daemon()
            
            return FailurePointStatus(
                id="FP-1.1",
                name="UW Daemon Running",
                category="Data & Signal Generation",
                status=status,
                last_check=time.time(),
                last_error=error,
                details={"running": running}
            )
        except Exception as e:
            return FailurePointStatus(
                id="FP-1.1",
                name="UW Daemon Running",
                category="Data & Signal Generation",
                status="ERROR",
                last_check=time.time(),
                last_error=str(e)
            )
    
    def _heal_uw_daemon(self):
        """Self-heal: Restart UW daemon"""
        try:
            # Try systemd restart
            subprocess.run(['systemctl', 'restart', 'trading-bot.service'], 
                         timeout=10)
            print("[SELF-HEAL] Attempted to restart UW daemon via systemd")
        except Exception as e:
            print(f"[SELF-HEAL] Failed to restart UW daemon: {e}")
    
    def check_fp_1_2_cache_exists(self) -> FailurePointStatus:
        """FP-1.2: Cache File Exists"""
        cache_file = Path("data/uw_flow_cache.json")
        exists = cache_file.exists()
        size = cache_file.stat().st_size if exists else 0
        
        status = "OK" if exists and size > 0 else "ERROR"
        error = None if exists and size > 0 else "Cache file missing or empty"
        
        return FailurePointStatus(
            id="FP-1.2",
            name="Cache File Exists",
            category="Data & Signal Generation",
            status=status,
            last_check=time.time(),
            last_error=error,
            details={"exists": exists, "size": size}
        )
    
    def check_fp_1_3_cache_fresh(self) -> FailurePointStatus:
        """FP-1.3: Cache Fresh"""
        cache_file = Path("data/uw_flow_cache.json")
        if not cache_file.exists():
            return FailurePointStatus(
                id="FP-1.3",
                name="Cache Fresh",
                category="Data & Signal Generation",
                status="ERROR",
                last_check=time.time(),
                last_error="Cache file missing"
            )
        
        mtime = cache_file.stat().st_mtime
        age_minutes = (time.time() - mtime) / 60
        
        status = "OK" if age_minutes < 10 else "WARN" if age_minutes < 30 else "ERROR"
        error = None if age_minutes < 10 else f"Cache stale: {age_minutes:.1f} minutes"
        
        # Self-healing
        if age_minutes > 30:
            self._heal_uw_daemon()
        
        return FailurePointStatus(
            id="FP-1.3",
            name="Cache Fresh",
            category="Data & Signal Generation",
            status=status,
            last_check=time.time(),
            last_error=error,
            details={"age_minutes": age_minutes}
        )
    
    def check_fp_1_4_cache_has_symbols(self) -> FailurePointStatus:
        """FP-1.4: Cache Has Symbols"""
        cache_file = Path("data/uw_flow_cache.json")
        if not cache_file.exists():
            return FailurePointStatus(
                id="FP-1.4",
                name="Cache Has Symbols",
                category="Data & Signal Generation",
                status="ERROR",
                last_check=time.time(),
                last_error="Cache file missing"
            )
        
        try:
            with cache_file.open() as f:
                cache = json.load(f)
            symbols = [k for k in cache.keys() if k != "_metadata"]
            symbol_count = len(symbols)
            
            status = "OK" if symbol_count > 0 else "ERROR"
            error = None if symbol_count > 0 else "No symbols in cache"
            
            return FailurePointStatus(
                id="FP-1.4",
                name="Cache Has Symbols",
                category="Data & Signal Generation",
                status=status,
                last_check=time.time(),
                last_error=error,
                details={"symbol_count": symbol_count}
            )
        except Exception as e:
            return FailurePointStatus(
                id="FP-1.4",
                name="Cache Has Symbols",
                category="Data & Signal Generation",
                status="ERROR",
                last_check=time.time(),
                last_error=str(e)
            )
    
    def check_fp_2_1_weights_initialized(self) -> FailurePointStatus:
        """FP-2.1: Adaptive Weights Initialized"""
        weights_file = Path("state/signal_weights.json")
        if not weights_file.exists():
            # Self-healing: Initialize weights
            self._heal_weights_init()
            return FailurePointStatus(
                id="FP-2.1",
                name="Adaptive Weights Initialized",
                category="Scoring & Evaluation",
                status="ERROR",
                last_check=time.time(),
                last_error="Weights file missing",
                self_healing_attempted=True
            )
        
        try:
            with weights_file.open() as f:
                state = json.load(f)
            bands = state.get("weight_bands", {})
            component_count = len(bands)
            
            status = "OK" if component_count == 21 else "ERROR"
            error = None if component_count == 21 else f"Expected 21, found {component_count}"
            
            # Self-healing
            if component_count != 21:
                self._heal_weights_init()
            
            return FailurePointStatus(
                id="FP-2.1",
                name="Adaptive Weights Initialized",
                category="Scoring & Evaluation",
                status=status,
                last_check=time.time(),
                last_error=error,
                self_healing_attempted=(component_count != 21),
                details={"component_count": component_count}
            )
        except Exception as e:
            return FailurePointStatus(
                id="FP-2.1",
                name="Adaptive Weights Initialized",
                category="Scoring & Evaluation",
                status="ERROR",
                last_check=time.time(),
                last_error=str(e)
            )
    
    def _heal_weights_init(self):
        """Self-heal: Initialize weights"""
        try:
            import subprocess
            result = subprocess.run(['python3', 'fix_adaptive_weights_init.py'],
                                   capture_output=True, timeout=30, cwd=Path.cwd())
            if result.returncode == 0:
                print("[SELF-HEAL] Weights initialized successfully")
            else:
                print(f"[SELF-HEAL] Weight init failed: {result.stderr.decode()}")
        except Exception as e:
            print(f"[SELF-HEAL] Weight init error: {e}")
    
    def check_fp_3_1_freeze_state(self) -> FailurePointStatus:
        """
        FP-3.1: Freeze State
        
        NOTE: pre_market_freeze.flag mechanism removed - only checks governor_freezes.json
        This matches the actual freeze check in monitoring_guards.py:check_freeze_state()
        """
        freeze_file = Path("state/governor_freezes.json")
        
        frozen = False
        freeze_reason = None
        
        if freeze_file.exists():
            try:
                with freeze_file.open() as f:
                    freezes = json.load(f)
                    # Check for active freezes (value == True)
                    active_freezes = {k: v for k, v in freezes.items() if v == True}
                    if active_freezes:
                        frozen = True
                        freeze_reason = f"governor_freezes.json: {', '.join(active_freezes.keys())}"
            except Exception as e:
                # Don't block on check errors
                pass
        
        # NOTE: pre_market_freeze.flag is no longer checked (removed mechanism)
        # If it exists, it's stale and should be removed but won't block trading
        
        status = "OK" if not frozen else "ERROR"
        error = None if not frozen else f"Trading frozen: {freeze_reason}"
        
        return FailurePointStatus(
            id="FP-3.1",
            name="Freeze State",
            category="Gates & Filters",
            status=status,
            last_check=time.time(),
            last_error=error,
            details={"frozen": frozen, "reason": freeze_reason}
        )
    
    def check_fp_4_1_alpaca_connection(self) -> FailurePointStatus:
        """FP-4.1: Alpaca API Connection"""
        try:
            import alpaca_trade_api as tradeapi
            import os
            # Try to load dotenv if available, but don't fail if not
            try:
                from dotenv import load_dotenv
                load_dotenv()
            except ImportError:
                # dotenv not available, use environment variables directly
                pass
            
            api = tradeapi.REST(
                os.getenv("ALPACA_KEY"),
                os.getenv("ALPACA_SECRET"),
                os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets"),
                api_version='v2'
            )
            account = api.get_account()
            
            return FailurePointStatus(
                id="FP-4.1",
                name="Alpaca Connection",
                category="Execution & Broker",
                status="OK",
                last_check=time.time(),
                details={"connected": True}
            )
        except Exception as e:
            return FailurePointStatus(
                id="FP-4.1",
                name="Alpaca Connection",
                category="Execution & Broker",
                status="ERROR",
                last_check=time.time(),
                last_error=str(e)
            )
    
    def check_fp_6_1_bot_running(self) -> FailurePointStatus:
        """FP-6.1: Bot Process Running"""
        try:
            result = subprocess.run(['pgrep', '-f', 'python.*main.py'], 
                                  capture_output=True, timeout=5)
            running = result.returncode == 0
            
            status = "OK" if running else "ERROR"
            error = None if running else "Bot not running"
            
            # Self-healing
            if not running:
                self._heal_bot_restart()
            
            return FailurePointStatus(
                id="FP-6.1",
                name="Bot Running",
                category="System & Infrastructure",
                status=status,
                last_check=time.time(),
                last_error=error,
                details={"running": running}
            )
        except Exception as e:
            return FailurePointStatus(
                id="FP-6.1",
                name="Bot Running",
                category="System & Infrastructure",
                status="ERROR",
                last_check=time.time(),
                last_error=str(e)
            )
    
    def _heal_bot_restart(self):
        """Self-heal: Restart bot"""
        try:
            subprocess.run(['systemctl', 'restart', 'trading-bot.service'], 
                         timeout=10)
            print("[SELF-HEAL] Attempted to restart bot via systemd")
        except Exception as e:
            print(f"[SELF-HEAL] Failed to restart bot: {e}")
    
    def check_fp_1_5_uw_api_auth(self) -> FailurePointStatus:
        """FP-1.5: UW API Authentication"""
        try:
            log_file = Path("logs/uw_flow_daemon.log")
            if log_file.exists():
                with log_file.open() as f:
                    lines = f.readlines()
                    # Check only very recent lines (last 20) to avoid false positives
                    recent_lines = lines[-20:] if len(lines) > 20 else lines
                    # Also check if daemon is actually running and cache is being updated
                    daemon_running = False
                    try:
                        import subprocess
                        result = subprocess.run(['pgrep', '-f', 'uw_flow_daemon'], 
                                              capture_output=True, timeout=5)
                        daemon_running = result.returncode == 0
                    except:
                        pass
                    
                    # Only flag as error if we see recent auth errors AND daemon is running
                    # (if daemon isn't running, that's a different issue - FP-1.1)
                    auth_errors = [l for l in recent_lines if "401" in l or "403" in l or "Unauthorized" in l.lower()]
                    if auth_errors and daemon_running:
                        return FailurePointStatus(
                            id="FP-1.5",
                            name="UW API Authentication",
                            category="Data & Signal Generation",
                            status="ERROR",
                            last_check=time.time(),
                            last_error="Recent API authentication failure detected in logs"
                        )
            
            return FailurePointStatus(
                id="FP-1.5",
                name="UW API Authentication",
                category="Data & Signal Generation",
                status="OK",
                last_check=time.time()
            )
        except Exception as e:
            return FailurePointStatus(
                id="FP-1.5",
                name="UW API Authentication",
                category="Data & Signal Generation",
                status="ERROR",
                last_check=time.time(),
                last_error=str(e)
            )
    
    def check_fp_3_2_max_positions(self) -> FailurePointStatus:
        """FP-3.2: Max Positions Reached"""
        try:
            import alpaca_trade_api as tradeapi
            import os
            # Try to load dotenv if available, but don't fail if not
            try:
                from dotenv import load_dotenv
                load_dotenv()
            except ImportError:
                # dotenv not available, use environment variables directly
                pass
            
            api = tradeapi.REST(
                os.getenv("ALPACA_KEY"),
                os.getenv("ALPACA_SECRET"),
                os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets"),
                api_version='v2'
            )
            positions = api.list_positions()
            position_count = len(positions)
            max_positions = 16
            
            if position_count >= max_positions:
                return FailurePointStatus(
                    id="FP-3.2",
                    name="Max Positions Reached",
                    category="Gates & Filters",
                    status="WARN",
                    last_check=time.time(),
                    last_error=f"At max positions: {position_count}/{max_positions}",
                    details={"position_count": position_count, "max_positions": max_positions}
                )
            
            return FailurePointStatus(
                id="FP-3.2",
                name="Max Positions Reached",
                category="Gates & Filters",
                status="OK",
                last_check=time.time(),
                details={"position_count": position_count, "max_positions": max_positions}
            )
        except Exception as e:
            return FailurePointStatus(
                id="FP-3.2",
                name="Max Positions Reached",
                category="Gates & Filters",
                status="ERROR",
                last_check=time.time(),
                last_error=str(e)
            )
    
    def check_fp_4_2_alpaca_auth(self) -> FailurePointStatus:
        """FP-4.2: Alpaca API Authentication"""
        try:
            import alpaca_trade_api as tradeapi
            import os
            # Try to load dotenv if available, but don't fail if not
            try:
                from dotenv import load_dotenv
                load_dotenv()
            except ImportError:
                # dotenv not available, use environment variables directly
                pass
            
            api = tradeapi.REST(
                os.getenv("ALPACA_KEY"),
                os.getenv("ALPACA_SECRET"),
                os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets"),
                api_version='v2'
            )
            account = api.get_account()
            
            return FailurePointStatus(
                id="FP-4.2",
                name="Alpaca API Authentication",
                category="Execution & Broker",
                status="OK",
                last_check=time.time()
            )
        except Exception as e:
            error_str = str(e)
            if "401" in error_str or "403" in error_str or "Unauthorized" in error_str:
                return FailurePointStatus(
                    id="FP-4.2",
                    name="Alpaca API Authentication",
                    category="Execution & Broker",
                    status="ERROR",
                    last_check=time.time(),
                    last_error="Authentication failure"
                )
            return FailurePointStatus(
                id="FP-4.2",
                name="Alpaca API Authentication",
                category="Execution & Broker",
                status="ERROR",
                last_check=time.time(),
                last_error=str(e)
            )
    
    def check_fp_4_3_buying_power(self) -> FailurePointStatus:
        """FP-4.3: Insufficient Buying Power"""
        try:
            import alpaca_trade_api as tradeapi
            import os
            # Try to load dotenv if available, but don't fail if not
            try:
                from dotenv import load_dotenv
                load_dotenv()
            except ImportError:
                # dotenv not available, use environment variables directly
                pass
            
            api = tradeapi.REST(
                os.getenv("ALPACA_KEY"),
                os.getenv("ALPACA_SECRET"),
                os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets"),
                api_version='v2'
            )
            account = api.get_account()
            buying_power = float(account.buying_power)
            equity = float(account.equity)
            
            if buying_power < 100:  # Less than $100
                return FailurePointStatus(
                    id="FP-4.3",
                    name="Insufficient Buying Power",
                    category="Execution & Broker",
                    status="WARN",
                    last_check=time.time(),
                    last_error=f"Low buying power: ${buying_power:.2f}",
                    details={"buying_power": buying_power, "equity": equity}
                )
            
            return FailurePointStatus(
                id="FP-4.3",
                name="Insufficient Buying Power",
                category="Execution & Broker",
                status="OK",
                last_check=time.time(),
                details={"buying_power": buying_power, "equity": equity}
            )
        except Exception as e:
            return FailurePointStatus(
                id="FP-4.3",
                name="Insufficient Buying Power",
                category="Execution & Broker",
                status="ERROR",
                last_check=time.time(),
                last_error=str(e)
            )
    
    def check_all(self) -> Dict[str, FailurePointStatus]:
        """Check all failure points"""
        checks = [
            self.check_fp_1_1_uw_daemon,
            self.check_fp_1_2_cache_exists,
            self.check_fp_1_3_cache_fresh,
            self.check_fp_1_4_cache_has_symbols,
            self.check_fp_1_5_uw_api_auth,
            self.check_fp_2_1_weights_initialized,
            self.check_fp_3_1_freeze_state,
            self.check_fp_3_2_max_positions,
            self.check_fp_4_1_alpaca_connection,
            self.check_fp_4_2_alpaca_auth,
            self.check_fp_4_3_buying_power,
            self.check_fp_6_1_bot_running,
        ]
        
        for check_func in checks:
            try:
                status = check_func()
                self.statuses[status.id] = status
            except Exception as e:
                print(f"[ERROR] Failed to check {check_func.__name__}: {e}")
        
        self._save_state()
        return self.statuses
    
    def get_trading_readiness(self) -> Dict[str, Any]:
        """Get overall trading readiness status"""
        statuses = self.check_all()
        
        critical_fps = [fp for fp in statuses.values() if fp.status == "ERROR"]
        warning_fps = [fp for fp in statuses.values() if fp.status == "WARN"]
        
        if critical_fps:
            readiness = "BLOCKED"
            color = "red"
        elif warning_fps:
            readiness = "DEGRADED"
            color = "yellow"
        else:
            readiness = "READY"
            color = "green"
        
        return {
            "readiness": readiness,
            "color": color,
            "critical_count": len(critical_fps),
            "warning_count": len(warning_fps),
            "total_checked": len(statuses),
            "failure_points": {fp_id: asdict(status) for fp_id, status in statuses.items()},
            "critical_fps": [fp.id for fp in critical_fps],
            "warning_fps": [fp.id for fp in warning_fps]
        }

def get_failure_point_monitor() -> FailurePointMonitor:
    """Get singleton monitor instance"""
    global _monitor_instance
    if '_monitor_instance' not in globals():
        _monitor_instance = FailurePointMonitor()
    return _monitor_instance

if __name__ == "__main__":
    monitor = FailurePointMonitor()
    readiness = monitor.get_trading_readiness()
    print(json.dumps(readiness, indent=2, default=str))

