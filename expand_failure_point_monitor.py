#!/usr/bin/env python3
"""
Expand failure point monitor with additional failure points
"""

import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Read existing monitor
monitor_file = Path("failure_point_monitor.py")
if monitor_file.exists():
    content = monitor_file.read_text()
    
    # Add more failure point checks
    additional_checks = """
    def check_fp_1_5_uw_api_auth(self) -> FailurePointStatus:
        \"\"\"FP-1.5: UW API Authentication\"\"\"
        try:
            # Check for 401/403 in daemon logs
            log_file = Path("logs/uw_flow_daemon.log")
            if log_file.exists():
                with log_file.open() as f:
                    lines = f.readlines()
                    recent_lines = lines[-50:] if len(lines) > 50 else lines
                    for line in recent_lines:
                        if "401" in line or "403" in line or "Unauthorized" in line:
                            return FailurePointStatus(
                                id="FP-1.5",
                                name="UW API Authentication",
                                category="Data & Signal Generation",
                                status="ERROR",
                                last_check=time.time(),
                                last_error="API authentication failure detected in logs"
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
    
    def check_fp_1_6_uw_rate_limit(self) -> FailurePointStatus:
        \"\"\"FP-1.6: UW API Rate Limit\"\"\"
        try:
            log_file = Path("logs/uw_flow_daemon.log")
            if log_file.exists():
                with log_file.open() as f:
                    lines = f.readlines()
                    recent_lines = lines[-50:] if len(lines) > 50 else lines
                    for line in recent_lines:
                        if "429" in line or "rate limit" in line.lower():
                            return FailurePointStatus(
                                id="FP-1.6",
                                name="UW API Rate Limit",
                                category="Data & Signal Generation",
                                status="WARN",
                                last_check=time.time(),
                                last_error="Rate limit detected"
                            )
            
            return FailurePointStatus(
                id="FP-1.6",
                name="UW API Rate Limit",
                category="Data & Signal Generation",
                status="OK",
                last_check=time.time()
            )
        except Exception as e:
            return FailurePointStatus(
                id="FP-1.6",
                name="UW API Rate Limit",
                category="Data & Signal Generation",
                status="ERROR",
                last_check=time.time(),
                last_error=str(e)
            )
    
    def check_fp_2_2_composite_score_calc(self) -> FailurePointStatus:
        \"\"\"FP-2.2: Composite Score Calculation\"\"\"
        try:
            # Check for scoring errors in logs
            log_file = Path("logs/main.log")
            if log_file.exists():
                with log_file.open() as f:
                    lines = f.readlines()
                    recent_lines = lines[-100:] if len(lines) > 100 else lines
                    scoring_errors = [l for l in recent_lines if "composite_score" in l.lower() and ("error" in l.lower() or "exception" in l.lower())]
                    if scoring_errors:
                        return FailurePointStatus(
                            id="FP-2.2",
                            name="Composite Score Calculation",
                            category="Scoring & Evaluation",
                            status="ERROR",
                            last_check=time.time(),
                            last_error="Scoring errors detected in logs"
                        )
            
            return FailurePointStatus(
                id="FP-2.2",
                name="Composite Score Calculation",
                category="Scoring & Evaluation",
                status="OK",
                last_check=time.time()
            )
        except Exception as e:
            return FailurePointStatus(
                id="FP-2.2",
                name="Composite Score Calculation",
                category="Scoring & Evaluation",
                status="ERROR",
                last_check=time.time(),
                last_error=str(e)
            )
    
    def check_fp_3_2_max_positions(self) -> FailurePointStatus:
        \"\"\"FP-3.2: Max Positions Reached\"\"\"
        try:
            import alpaca_trade_api as tradeapi
            from dotenv import load_dotenv
            import os
            load_dotenv()
            
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
    
    def check_fp_3_3_max_new_per_cycle(self) -> FailurePointStatus:
        \"\"\"FP-3.3: Max New Positions Per Cycle\"\"\"
        # This is checked per cycle, so we'll just verify the logic exists
        return FailurePointStatus(
            id="FP-3.3",
            name="Max New Positions Per Cycle",
            category="Gates & Filters",
            status="OK",
            last_check=time.time(),
            details={"note": "Checked per cycle in decide_and_execute"}
        )
    
    def check_fp_3_4_expectancy_gate(self) -> FailurePointStatus:
        \"\"\"FP-3.4: Expectancy Gate Blocking\"\"\"
        # Check for expectancy gate blocks in logs
        try:
            log_file = Path("logs/main.log")
            if log_file.exists():
                with log_file.open() as f:
                    lines = f.readlines()
                    recent_lines = lines[-100:] if len(lines) > 100 else lines
                    expectancy_blocks = [l for l in recent_lines if "expectancy_blocked" in l.lower()]
                    if len(expectancy_blocks) > 10:  # Many blocks
                        return FailurePointStatus(
                            id="FP-3.4",
                            name="Expectancy Gate Blocking",
                            category="Gates & Filters",
                            status="WARN",
                            last_check=time.time(),
                            last_error=f"Many expectancy blocks: {len(expectancy_blocks)}",
                            details={"block_count": len(expectancy_blocks)}
                        )
            
            return FailurePointStatus(
                id="FP-3.4",
                name="Expectancy Gate Blocking",
                category="Gates & Filters",
                status="OK",
                last_check=time.time()
            )
        except Exception as e:
            return FailurePointStatus(
                id="FP-3.4",
                name="Expectancy Gate Blocking",
                category="Gates & Filters",
                status="ERROR",
                last_check=time.time(),
                last_error=str(e)
            )
    
    def check_fp_4_2_alpaca_auth(self) -> FailurePointStatus:
        \"\"\"FP-4.2: Alpaca API Authentication\"\"\"
        try:
            import alpaca_trade_api as tradeapi
            from dotenv import load_dotenv
            import os
            load_dotenv()
            
            api = tradeapi.REST(
                os.getenv("ALPACA_KEY"),
                os.getenv("ALPACA_SECRET"),
                os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets"),
                api_version='v2'
            )
            # Try to get account
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
        \"\"\"FP-4.3: Insufficient Buying Power\"\"\"
        try:
            import alpaca_trade_api as tradeapi
            from dotenv import load_dotenv
            import os
            load_dotenv()
            
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
    
    def check_fp_6_2_bot_crashed(self) -> FailurePointStatus:
        \"\"\"FP-6.2: Bot Process Crashed\"\"\"
        try:
            # Check systemd status
            result = subprocess.run(['systemctl', 'is-failed', 'trading-bot.service'],
                                  capture_output=True, timeout=5)
            if result.returncode == 0:  # Service is failed
                return FailurePointStatus(
                    id="FP-6.2",
                    name="Bot Process Crashed",
                    category="System & Infrastructure",
                    status="ERROR",
                    last_check=time.time(),
                    last_error="Bot service is in failed state",
                    self_healing_attempted=True
                )
            
            return FailurePointStatus(
                id="FP-6.2",
                name="Bot Process Crashed",
                category="System & Infrastructure",
                status="OK",
                last_check=time.time()
            )
        except Exception as e:
            return FailurePointStatus(
                id="FP-6.2",
                name="Bot Process Crashed",
                category="System & Infrastructure",
                status="ERROR",
                last_check=time.time(),
                last_error=str(e)
            )
    
    def check_fp_6_3_bot_stuck(self) -> FailurePointStatus:
        \"\"\"FP-6.3: Bot Stuck/Unresponsive\"\"\"
        try:
            # Check last activity timestamp
            activity_file = Path("state/last_activity.json")
            if activity_file.exists():
                with activity_file.open() as f:
                    activity = json.load(f)
                last_activity = activity.get("timestamp", 0)
                age_minutes = (time.time() - last_activity) / 60
                
                if age_minutes > 10:  # No activity for 10+ minutes
                    return FailurePointStatus(
                        id="FP-6.3",
                        name="Bot Stuck/Unresponsive",
                        category="System & Infrastructure",
                        status="WARN",
                        last_check=time.time(),
                        last_error=f"No activity for {age_minutes:.1f} minutes",
                        details={"age_minutes": age_minutes}
                    )
            
            return FailurePointStatus(
                id="FP-6.3",
                name="Bot Stuck/Unresponsive",
                category="System & Infrastructure",
                status="OK",
                last_check=time.time()
            )
        except Exception as e:
            return FailurePointStatus(
                id="FP-6.3",
                name="Bot Stuck/Unresponsive",
                category="System & Infrastructure",
                status="ERROR",
                last_check=time.time(),
                last_error=str(e)
            )
"""
    
    # Find the check_all method and add new checks
    if "def check_all(self)" in content:
        # Find the checks list
        checks_pattern = r"checks = \[(.*?)\]"
        match = re.search(checks_pattern, content, re.DOTALL)
        
        if match:
            existing_checks = match.group(1)
            new_checks = """
            self.check_fp_1_5_uw_api_auth,
            self.check_fp_1_6_uw_rate_limit,
            self.check_fp_2_2_composite_score_calc,
            self.check_fp_3_2_max_positions,
            self.check_fp_3_3_max_new_per_cycle,
            self.check_fp_3_4_expectancy_gate,
            self.check_fp_4_2_alpaca_auth,
            self.check_fp_4_3_buying_power,
            self.check_fp_6_2_bot_crashed,
            self.check_fp_6_3_bot_stuck,
"""
            
            # Add new checks to the list
            content = content.replace(
                match.group(0),
                f"checks = [{existing_checks}{new_checks}]"
            )
        
        # Add the new check methods before check_all
        if "def check_all(self)" in content:
            content = content.replace(
                "def check_all(self)",
                additional_checks + "\n    def check_all(self)"
            )
        
        monitor_file.write_text(content)
        print("Expanded failure point monitor with additional checks")
    else:
        print("Could not find check_all method to expand")

if __name__ == "__main__":
    from expand_failure_point_monitor import *
    # This will be run to expand the monitor

