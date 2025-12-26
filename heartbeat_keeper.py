#!/usr/bin/env python3
"""
HealthSupervisor - Self-Monitoring and Healing System

Provides:
- Continuous heartbeat monitoring (daemon liveness, API connectivity)
- Periodic deep checks (data freshness, position tracking, performance)
- Auto-remediation (restart daemon, rebuild cache, circuit breakers)
- Severity tiers (INFO, WARN, CRITICAL) with escalation
- Unified health dashboard endpoint

Runs as background thread in main.py
"""

import os
import json
import time
import subprocess
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable

DATA_DIR = Path("data")
STATE_DIR = Path("state")
LOGS_DIR = Path("logs")

class HealthCheck:
    """Individual health check with severity and remediation."""
    
    def __init__(self, name: str, check_fn: Callable[[], Dict[str, Any]], 
                 interval_sec: int = 30, severity: str = "INFO",
                 remediation_fn: Optional[Callable[[], bool]] = None):
        self.name = name
        self.check_fn = check_fn
        self.interval_sec = interval_sec
        self.severity = severity
        self.remediation_fn = remediation_fn
        self.last_check_ts = 0
        self.last_status = "UNKNOWN"
        self.consecutive_failures = 0
    
    def should_run(self) -> bool:
        return (time.time() - self.last_check_ts) >= self.interval_sec
    
    def execute(self) -> Dict[str, Any]:
        try:
            result = self.check_fn()
            self.last_check_ts = time.time()
            
            if result.get("healthy", False):
                self.last_status = "HEALTHY"
                self.consecutive_failures = 0
            else:
                self.last_status = "UNHEALTHY"
                self.consecutive_failures += 1
                
                if self.remediation_fn and self.consecutive_failures >= 3:
                    result["remediation_attempted"] = self.remediation_fn()
            
            return {
                "check": self.name,
                "status": self.last_status,
                "severity": self.severity,
                "consecutive_failures": self.consecutive_failures,
                **result
            }
        except Exception as e:
            self.last_status = "ERROR"
            self.consecutive_failures += 1
            return {
                "check": self.name,
                "status": "ERROR",
                "severity": "CRITICAL",
                "error": str(e),
                "consecutive_failures": self.consecutive_failures
            }


class HealthSupervisor:
    """Main health monitoring and self-healing orchestrator."""
    
    def __init__(self):
        self.checks: List[HealthCheck] = []
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._register_all_checks()
    
    def _register_all_checks(self):
        """Register all health checks with intervals and remediations."""
        
        self.checks.append(HealthCheck(
            name="uw_daemon_liveness",
            check_fn=self._check_uw_daemon_alive,
            interval_sec=30,
            severity="CRITICAL",
            remediation_fn=self._restart_uw_daemon
        ))
        
        self.checks.append(HealthCheck(
            name="uw_cache_freshness",
            check_fn=self._check_uw_cache_fresh,
            interval_sec=60,
            severity="WARN",
            remediation_fn=self._rebuild_uw_cache
        ))
        
        self.checks.append(HealthCheck(
            name="position_tracking",
            check_fn=self._check_position_tracking,
            interval_sec=120,
            severity="CRITICAL",
            remediation_fn=None
        ))
        
        self.checks.append(HealthCheck(
            name="alpaca_connectivity",
            check_fn=self._check_alpaca_api,
            interval_sec=60,
            severity="CRITICAL",
            remediation_fn=None
        ))
        
        self.checks.append(HealthCheck(
            name="trade_execution_cadence",
            check_fn=self._check_trade_cadence,
            interval_sec=300,
            severity="WARN",
            remediation_fn=None
        ))
        
        self.checks.append(HealthCheck(
            name="performance_metrics",
            check_fn=self._check_performance,
            interval_sec=300,
            severity="WARN",
            remediation_fn=self._trigger_circuit_breaker
        ))
    
    def _check_uw_daemon_alive(self) -> Dict[str, Any]:
        """Check if UW flow daemon is running and updating cache."""
        # First check if daemon process is running
        try:
            result = subprocess.run(
                ["pgrep", "-f", "uw_flow_daemon"],
                capture_output=True,
                text=True,
                timeout=5
            )
            daemon_running = result.returncode == 0 and result.stdout.strip()
        except:
            daemon_running = False
        
        if not daemon_running:
            return {"healthy": False, "reason": "daemon_process_not_running"}
        
        # Then check cache file
        cache_file = DATA_DIR / "uw_flow_cache.json"
        if not cache_file.exists():
            return {"healthy": False, "reason": "cache_file_missing", "daemon_running": True}
        
        try:
            file_mtime = cache_file.stat().st_mtime
            age_sec = time.time() - file_mtime
            
            if age_sec > 600:
                return {"healthy": False, "reason": "cache_stale", "age_sec": int(age_sec), "daemon_running": True}
            
            cache = json.loads(cache_file.read_text())
            symbol_count = len([k for k in cache.keys() if not k.startswith("_")])
            
            return {"healthy": True, "cache_age_sec": int(age_sec), "symbols": symbol_count, "daemon_running": True}
        except Exception as e:
            return {"healthy": False, "reason": "cache_read_error", "error": str(e), "daemon_running": True}
    
    def _restart_uw_daemon(self) -> bool:
        """Attempt to restart UW daemon process."""
        try:
            # Check if running under systemd
            systemd_result = subprocess.run(
                ["systemctl", "is-active", "trading-bot.service"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if systemd_result.returncode == 0:
                # Running under systemd - restart the service to restart daemon
                subprocess.run(
                    ["systemctl", "restart", "trading-bot.service"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=10
                )
                return True
            else:
                # Not under systemd - try to restart via deploy_supervisor
                # Kill existing daemon processes first
                subprocess.run(["pkill", "-f", "uw_flow_daemon"], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL,
                             timeout=5)
                time.sleep(2)
                
                # Start daemon directly (fallback if not under systemd)
                daemon_path = Path(__file__).parent / "uw_flow_daemon.py"
                if daemon_path.exists():
                    venv_python = Path(__file__).parent / "venv" / "bin" / "python"
                    if venv_python.exists():
                        subprocess.Popen(
                            [str(venv_python), str(daemon_path)],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            cwd=str(Path(__file__).parent)
                        )
                        return True
                
                return False
        except Exception as e:
            # Log error but don't fail completely
            try:
                log_path = LOGS_DIR / "heartbeat.jsonl"
                with log_path.open("a") as f:
                    f.write(json.dumps({
                        "ts": datetime.utcnow().isoformat() + "Z",
                        "msg": "daemon_restart_failed",
                        "error": str(e)
                    }) + "\n")
            except:
                pass
            return False
    
    def _check_uw_cache_fresh(self) -> Dict[str, Any]:
        """Check if UW cache has recent data for watchlist symbols."""
        cache_file = DATA_DIR / "uw_flow_cache.json"
        if not cache_file.exists():
            return {"healthy": False, "reason": "cache_missing"}
        
        try:
            cache = json.loads(cache_file.read_text())
            watchlist = ["AAPL", "MSFT", "NVDA", "QQQ", "SPY", "TSLA"]
            missing = [s for s in watchlist if s not in cache]
            
            if missing:
                return {"healthy": False, "reason": "symbols_missing", "missing_count": len(missing)}
            
            return {"healthy": True, "symbols_cached": len(watchlist)}
        except Exception as e:
            return {"healthy": False, "reason": "cache_parse_error", "error": str(e)}
    
    def _rebuild_uw_cache(self) -> bool:
        """Trigger UW cache rebuild."""
        try:
            cache_file = DATA_DIR / "uw_flow_cache.json"
            if cache_file.exists():
                cache_file.rename(cache_file.with_suffix(".json.backup"))
            return True
        except Exception:
            return False
    
    def _check_position_tracking(self) -> Dict[str, Any]:
        """Verify position metadata is being tracked correctly."""
        metadata_file = STATE_DIR / "position_metadata.json"
        
        try:
            import alpaca_trade_api as tradeapi
            api_key = os.getenv("ALPACA_KEY")
            api_secret = os.getenv("ALPACA_SECRET")
            base_url = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
            
            if not api_key or not api_secret:
                return {"healthy": False, "reason": "missing_credentials"}
            
            api = tradeapi.REST(api_key, api_secret, base_url)
            alpaca_positions = api.list_positions()
            alpaca_count = len(alpaca_positions)
            
            metadata_count = 0
            if metadata_file.exists():
                metadata = json.loads(metadata_file.read_text())
                metadata_count = len(metadata)
            
            discrepancy = abs(alpaca_count - metadata_count)
            
            if discrepancy > 0:
                return {
                    "healthy": False,
                    "reason": "position_count_mismatch",
                    "alpaca_count": alpaca_count,
                    "metadata_count": metadata_count,
                    "discrepancy": discrepancy
                }
            
            return {"healthy": True, "position_count": alpaca_count}
        except Exception as e:
            return {"healthy": False, "reason": "check_failed", "error": str(e)}
    
    def _check_alpaca_api(self) -> Dict[str, Any]:
        """Check Alpaca API connectivity."""
        try:
            import alpaca_trade_api as tradeapi
            api_key = os.getenv("ALPACA_KEY")
            api_secret = os.getenv("ALPACA_SECRET")
            base_url = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
            
            if not api_key or not api_secret:
                return {"healthy": False, "reason": "missing_credentials"}
            
            api = tradeapi.REST(api_key, api_secret, base_url)
            account = api.get_account()
            
            return {
                "healthy": True,
                "account_status": getattr(account, "status", "unknown"),
                "equity": float(getattr(account, "equity", 0))
            }
        except Exception as e:
            return {"healthy": False, "reason": "api_error", "error": str(e)}
    
    def _check_trade_cadence(self) -> Dict[str, Any]:
        """Check if trades are being executed regularly during market hours."""
        orders_file = DATA_DIR / "live_orders.jsonl"
        if not orders_file.exists():
            return {"healthy": True, "reason": "no_orders_file_yet"}
        
        try:
            recent_orders = 0
            cutoff = time.time() - 3600
            
            for line in orders_file.read_text().splitlines()[-100:]:
                try:
                    event = json.loads(line)
                    event_type = event.get("event", "")
                    event_ts = event.get("_ts", 0)
                    
                    if event_ts > cutoff and event_type in ["MARKET_FILLED", "LIMIT_FILLED"]:
                        recent_orders += 1
                except:
                    pass
            
            now = datetime.now()
            is_market_hours = 9 <= now.hour < 16 and now.weekday() < 5
            
            if is_market_hours and recent_orders == 0:
                return {"healthy": False, "reason": "no_recent_trades", "market_hours": True}
            
            return {"healthy": True, "recent_trades_1h": recent_orders}
        except Exception as e:
            return {"healthy": False, "reason": "check_failed", "error": str(e)}
    
    def _check_performance(self) -> Dict[str, Any]:
        """Monitor performance metrics for degradation."""
        postmortem_file = DATA_DIR / "daily_postmortem.jsonl"
        if not postmortem_file.exists():
            return {"healthy": True, "reason": "no_postmortem_data_yet"}
        
        try:
            recent_trades = []
            cutoff = time.time() - (7 * 86400)
            
            for line in postmortem_file.read_text().splitlines()[-200:]:
                try:
                    event = json.loads(line)
                    if event.get("_ts", 0) > cutoff:
                        recent_trades.append(event)
                except:
                    pass
            
            if len(recent_trades) < 10:
                return {"healthy": True, "reason": "insufficient_data"}
            
            wins = sum(1 for t in recent_trades if float(t.get("pnl_usd", 0)) > 0)
            total = len(recent_trades)
            win_rate = wins / total if total > 0 else 0
            
            total_pnl = sum(float(t.get("pnl_usd", 0)) for t in recent_trades)
            
            if win_rate < 0.35:
                return {
                    "healthy": False,
                    "reason": "low_win_rate",
                    "win_rate": round(win_rate, 3),
                    "trades_7d": total,
                    "total_pnl_7d": round(total_pnl, 2)
                }
            
            if total_pnl < -1000:
                return {
                    "healthy": False,
                    "reason": "excessive_losses",
                    "total_pnl_7d": round(total_pnl, 2),
                    "win_rate": round(win_rate, 3)
                }
            
            return {
                "healthy": True,
                "win_rate_7d": round(win_rate, 3),
                "trades_7d": total,
                "total_pnl_7d": round(total_pnl, 2)
            }
        except Exception as e:
            return {"healthy": False, "reason": "check_failed", "error": str(e)}
    
    def _trigger_circuit_breaker(self) -> bool:
        """Halt new entries when performance degrades."""
        try:
            breaker_file = STATE_DIR / "circuit_breaker.json"
            breaker_file.parent.mkdir(exist_ok=True)
            breaker_file.write_text(json.dumps({
                "engaged": True,
                "reason": "performance_degradation",
                "timestamp": time.time(),
                "expires_at": time.time() + 3600
            }))
            return True
        except Exception:
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current health status of all systems."""
        status = {
            "timestamp": time.time(),
            "overall_healthy": True,
            "checks": []
        }
        
        for check in self.checks:
            if check.last_status in ["UNHEALTHY", "ERROR"]:
                status["overall_healthy"] = False
            
            status["checks"].append({
                "name": check.name,
                "status": check.last_status,
                "severity": check.severity,
                "last_check_age_sec": int(time.time() - check.last_check_ts),
                "consecutive_failures": check.consecutive_failures
            })
        
        return status
    
    def run_once(self):
        """Execute all checks that are due."""
        for check in self.checks:
            if check.should_run():
                result = check.execute()
                self._log_check_result(result)
    
    def _log_check_result(self, result: Dict[str, Any]):
        """Log health check result to telemetry."""
        log_file = DATA_DIR / "health_checks.jsonl"
        try:
            log_file.parent.mkdir(exist_ok=True)
            result["_ts"] = time.time()
            result["_dt"] = datetime.utcnow().isoformat()
            with log_file.open("a") as f:
                f.write(json.dumps(result) + "\n")
        except Exception:
            pass
    
    def start(self):
        """Start background health monitoring thread."""
        if self.running:
            return
        
        self.running = True
        self._stop_event.clear()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop health monitoring."""
        self.running = False
        self._stop_event.set()
    
    def _run_loop(self):
        """Background monitoring loop."""
        while self.running and not self._stop_event.is_set():
            try:
                self.run_once()
            except Exception as e:
                pass
            time.sleep(10)


_global_supervisor: Optional[HealthSupervisor] = None

def get_supervisor() -> HealthSupervisor:
    """Get or create global health supervisor instance."""
    global _global_supervisor
    if _global_supervisor is None:
        _global_supervisor = HealthSupervisor()
    return _global_supervisor

if __name__ == "__main__":
    """Run heartbeat keeper as standalone daemon."""
    supervisor = HealthSupervisor()
    supervisor.start()
    print("[HEARTBEAT-KEEPER] Started health monitoring daemon", flush=True)
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n[HEARTBEAT-KEEPER] Shutting down...", flush=True)
        supervisor.stop()
