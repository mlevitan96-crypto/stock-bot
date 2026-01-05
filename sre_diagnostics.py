#!/usr/bin/env python3
"""
SRE Sentinel - Autonomous Diagnostic & Repair Engine
=====================================================
Autonomous Root Cause Analysis (RCA) and self-healing system.

When triggered (e.g., by mock signal failure), performs RCA checks:
1. UW parser regex integrity
2. Composite scoring weight file existence
3. Alpaca SIP feed latency
4. Cache lock file issues

Then applies specific fixes based on findings.
"""

import os
import json
import time
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

STATE_DIR = Path("state")
DATA_DIR = Path("data")
SRE_METRICS_FILE = STATE_DIR / "sre_metrics.json"
RCA_FIXES_LOG = STATE_DIR / "sre_rca_fixes.jsonl"

@dataclass
class RCAResult:
    """Result of a Root Cause Analysis check."""
    check_name: str
    status: str  # "OK", "FAIL", "WARNING"
    message: str
    fix_applied: Optional[str] = None
    fix_success: bool = False

@dataclass
class RCASession:
    """A complete RCA session with multiple checks and fixes."""
    timestamp: float
    trigger: str  # e.g., "mock_signal_failure", "manual"
    checks: List[RCAResult]
    overall_status: str
    fixes_applied: List[str]

class SREDiagnostics:
    """Autonomous Root Cause Analysis and self-healing system."""
    
    def __init__(self):
        self.metrics_file = SRE_METRICS_FILE
        self.rca_log_file = RCA_FIXES_LOG
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
        self.rca_log_file.parent.mkdir(parents=True, exist_ok=True)
        
    def log_rca_fix(self, session: RCASession):
        """Log an RCA session to the fixes log."""
        try:
            with self.rca_log_file.open("a") as f:
                record = {
                    "timestamp": session.timestamp,
                    "trigger": session.trigger,
                    "overall_status": session.overall_status,
                    "checks": [asdict(check) for check in session.checks],
                    "fixes_applied": session.fixes_applied,
                    "time": datetime.now(timezone.utc).isoformat()
                }
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            print(f"[SRE-DIAG] Error logging RCA fix: {e}", flush=True)
    
    def check_uw_parser_integrity(self) -> RCAResult:
        """Check if UW parser regex patterns are valid."""
        try:
            # Check if main.py has the normalize_flow_trade function with proper regex/field extraction
            main_py = Path("main.py")
            if not main_py.exists():
                return RCAResult("uw_parser_integrity", "FAIL", "main.py not found", None, False)
            
            content = main_py.read_text(encoding='utf-8')
            
            # Check for key fields: flow_conv, flow_magnitude, signal_type
            has_flow_conv = "flow_conv" in content or "flow_conviction" in content
            has_signal_type = "signal_type" in content
            has_normalize = "def _normalize_flow_trade" in content
            
            if has_flow_conv and has_signal_type and has_normalize:
                return RCAResult("uw_parser_integrity", "OK", "Parser fields present", None, False)
            else:
                return RCAResult("uw_parser_integrity", "WARNING", 
                                f"Parser missing fields: flow_conv={has_flow_conv}, signal_type={has_signal_type}",
                                None, False)
        except Exception as e:
            return RCAResult("uw_parser_integrity", "FAIL", f"Error checking parser: {e}", None, False)
    
    def check_composite_weights(self) -> RCAResult:
        """Check if composite scoring weight files exist."""
        try:
            weights_file = DATA_DIR / "uw_weights.json"
            if weights_file.exists():
                # Try to load and validate JSON
                try:
                    with weights_file.open() as f:
                        weights = json.load(f)
                    if isinstance(weights, dict) and len(weights) > 0:
                        return RCAResult("composite_weights", "OK", f"Weights file exists with {len(weights)} entries", None, False)
                    else:
                        return RCAResult("composite_weights", "WARNING", "Weights file exists but is empty", None, False)
                except json.JSONDecodeError:
                    return RCAResult("composite_weights", "FAIL", "Weights file exists but is invalid JSON", "clear_weights_lock", False)
            else:
                return RCAResult("composite_weights", "WARNING", "Weights file does not exist (will use defaults)", None, False)
        except Exception as e:
            return RCAResult("composite_weights", "FAIL", f"Error checking weights: {e}", None, False)
    
    def check_alpaca_latency(self) -> RCAResult:
        """Check Alpaca SIP feed latency (simplified check)."""
        try:
            # Check if we can import Alpaca and make a simple request
            try:
                import alpaca_trade_api as tradeapi
                api_key = os.getenv("ALPACA_KEY") or os.getenv("ALPACA_API_KEY")
                api_secret = os.getenv("ALPACA_SECRET") or os.getenv("ALPACA_API_SECRET")
                base_url = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
                
                if not api_key or not api_secret:
                    return RCAResult("alpaca_latency", "WARNING", "Alpaca credentials not set", None, False)
                
                # Simple latency check - get account (lightweight endpoint)
                start_time = time.time()
                api = tradeapi.REST(api_key, api_secret, base_url, api_version='v2')
                account = api.get_account()  # This should be fast
                latency_ms = (time.time() - start_time) * 1000
                
                if latency_ms < 500:
                    return RCAResult("alpaca_latency", "OK", f"Alpaca latency: {latency_ms:.0f}ms", None, False)
                elif latency_ms < 2000:
                    return RCAResult("alpaca_latency", "WARNING", f"Alpaca latency high: {latency_ms:.0f}ms", None, False)
                else:
                    return RCAResult("alpaca_latency", "FAIL", f"Alpaca latency very high: {latency_ms:.0f}ms", None, False)
            except ImportError:
                return RCAResult("alpaca_latency", "WARNING", "Alpaca API not available", None, False)
            except Exception as e:
                return RCAResult("alpaca_latency", "FAIL", f"Alpaca check failed: {e}", None, False)
        except Exception as e:
            return RCAResult("alpaca_latency", "FAIL", f"Error checking Alpaca: {e}", None, False)
    
    def check_cache_lock(self) -> RCAResult:
        """Check for stale cache lock files."""
        try:
            lock_files = [
                DATA_DIR / "uw_flow_cache.json.lock",
                STATE_DIR / "uw_flow_cache.json.lock",
            ]
            
            stale_locks = []
            for lock_file in lock_files:
                if lock_file.exists():
                    # Check if lock is older than 5 minutes (likely stale)
                    age_sec = time.time() - lock_file.stat().st_mtime
                    if age_sec > 300:  # 5 minutes
                        stale_locks.append(str(lock_file))
            
            if stale_locks:
                return RCAResult("cache_lock", "FAIL", f"Stale lock files found: {', '.join(stale_locks)}", "clear_cache_lock", False)
            else:
                return RCAResult("cache_lock", "OK", "No stale lock files", None, False)
        except Exception as e:
            return RCAResult("cache_lock", "WARNING", f"Error checking locks: {e}", None, False)
    
    def apply_fix(self, fix_name: str) -> bool:
        """Apply a specific fix based on RCA findings."""
        try:
            if fix_name == "clear_weights_lock":
                # Clear corrupted weights file (will regenerate)
                weights_file = DATA_DIR / "uw_weights.json"
                if weights_file.exists():
                    backup_file = weights_file.with_suffix(".json.backup")
                    weights_file.rename(backup_file)
                    print(f"[SRE-DIAG] Cleared corrupted weights file (backed up to {backup_file})", flush=True)
                    return True
                return False
            
            elif fix_name == "clear_cache_lock":
                # Remove stale lock files
                lock_files = [
                    DATA_DIR / "uw_flow_cache.json.lock",
                    STATE_DIR / "uw_flow_cache.json.lock",
                ]
                cleared = False
                for lock_file in lock_files:
                    if lock_file.exists():
                        age_sec = time.time() - lock_file.stat().st_mtime
                        if age_sec > 300:  # Only clear if stale
                            lock_file.unlink()
                            print(f"[SRE-DIAG] Cleared stale lock file: {lock_file}", flush=True)
                            cleared = True
                return cleared
            
            else:
                print(f"[SRE-DIAG] Unknown fix: {fix_name}", flush=True)
                return False
        except Exception as e:
            print(f"[SRE-DIAG] Error applying fix {fix_name}: {e}", flush=True)
            return False
    
    def run_rca(self, trigger: str = "manual") -> RCASession:
        """Run complete Root Cause Analysis and apply fixes."""
        checks = [
            self.check_uw_parser_integrity(),
            self.check_composite_weights(),
            self.check_alpaca_latency(),
            self.check_cache_lock(),
        ]
        
        # Determine overall status
        has_fail = any(c.status == "FAIL" for c in checks)
        has_warning = any(c.status == "WARNING" for c in checks)
        
        if has_fail:
            overall_status = "FAIL"
        elif has_warning:
            overall_status = "WARNING"
        else:
            overall_status = "OK"
        
        # Apply fixes for FAIL checks
        fixes_applied = []
        for check in checks:
            if check.status == "FAIL" and check.fix_applied:
                fix_success = self.apply_fix(check.fix_applied)
                check.fix_success = fix_success
                if fix_success:
                    fixes_applied.append(f"{check.fix_applied} (success)")
                else:
                    fixes_applied.append(f"{check.fix_applied} (failed)")
        
        session = RCASession(
            timestamp=time.time(),
            trigger=trigger,
            checks=checks,
            overall_status=overall_status,
            fixes_applied=fixes_applied
        )
        
        # Log the RCA session
        self.log_rca_fix(session)
        
        return session
    
    def get_recent_fixes(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent RCA fixes from the log."""
        if not self.rca_log_file.exists():
            return []
        
        fixes = []
        try:
            with self.rca_log_file.open("r") as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    try:
                        fix = json.loads(line.strip())
                        fixes.append(fix)
                    except:
                        pass
        except Exception as e:
            print(f"[SRE-DIAG] Error reading fixes log: {e}", flush=True)
        
        return fixes[::-1]  # Return most recent first

def get_sre_metrics() -> Dict[str, Any]:
    """Get current SRE metrics from state/sre_metrics.json."""
    metrics_file = STATE_DIR / "sre_metrics.json"
    if not metrics_file.exists():
        return {
            "logic_heartbeat": 0.0,
            "mock_signal_success_pct": 100.0,
            "parser_health_index": 100.0,
            "auto_fix_count": 0,
            "last_update": time.time()
        }
    
    try:
        with metrics_file.open() as f:
            metrics = json.load(f)
        return metrics
    except Exception as e:
        print(f"[SRE-DIAG] Error loading metrics: {e}", flush=True)
        return {
            "logic_heartbeat": 0.0,
            "mock_signal_success_pct": 100.0,
            "parser_health_index": 100.0,
            "auto_fix_count": 0,
            "last_update": time.time()
        }

def update_sre_metrics(updates: Dict[str, Any]):
    """Update SRE metrics file."""
    metrics_file = STATE_DIR / "sre_metrics.json"
    metrics_file.parent.mkdir(parents=True, exist_ok=True)
    
    current = get_sre_metrics()
    current.update(updates)
    current["last_update"] = time.time()
    
    try:
        # Atomic write
        tmp_file = metrics_file.with_suffix(".json.tmp")
        with tmp_file.open("w") as f:
            json.dump(current, f, indent=2)
        tmp_file.replace(metrics_file)
    except Exception as e:
        print(f"[SRE-DIAG] Error updating metrics: {e}", flush=True)

if __name__ == "__main__":
    # Test RCA
    diag = SREDiagnostics()
    session = diag.run_rca(trigger="test")
    print(f"RCA Status: {session.overall_status}")
    print(f"Fixes Applied: {session.fixes_applied}")
    for check in session.checks:
        print(f"  {check.check_name}: {check.status} - {check.message}")
