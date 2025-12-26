#!/usr/bin/env python3
"""
Continuous Failure Point Monitoring Service
Runs as a background service to continuously monitor failure points
"""

import time
import json
from pathlib import Path
from datetime import datetime
from failure_point_monitor import get_failure_point_monitor

def run_continuous_monitoring():
    """Run continuous monitoring loop"""
    print("[FP-MONITOR] Starting continuous monitoring service...")
    
    monitor = get_failure_point_monitor()
    log_file = Path("logs/failure_points.log")
    log_file.parent.mkdir(exist_ok=True)
    
    last_readiness = None
    alert_count = 0
    
    while True:
        try:
            # Check all failure points
            readiness = monitor.get_trading_readiness()
            current_readiness = readiness["readiness"]
            
            # Log status
            timestamp = datetime.now().isoformat()
            critical_count = readiness.get("critical_count", 0)
            warning_count = readiness.get("warning_count", 0)
            
            log_entry = f"{timestamp} | {current_readiness} | Critical: {critical_count}, Warnings: {warning_count}"
            
            # Add critical FPs if any
            if critical_count > 0:
                critical_fps = readiness.get("critical_fps", [])
                log_entry += f" | Critical FPs: {', '.join(critical_fps)}"
            
            # Write to log
            with log_file.open("a") as f:
                f.write(log_entry + "\n")
            
            # Alert on status change
            if last_readiness and last_readiness != current_readiness:
                print(f"[FP-MONITOR] ALERT: Readiness changed from {last_readiness} to {current_readiness}")
                alert_count += 1
                
                # If changed to BLOCKED, alert immediately
                if current_readiness == "BLOCKED":
                    print(f"[FP-MONITOR] CRITICAL: Trading is now BLOCKED!")
                    print(f"[FP-MONITOR] Critical FPs: {', '.join(readiness.get('critical_fps', []))}")
            
            # Print status every 10 cycles (50 minutes)
            if alert_count % 10 == 0:
                print(f"[FP-MONITOR] Status: {current_readiness} (Critical: {critical_count}, Warnings: {warning_count})")
            
            last_readiness = current_readiness
            
            # Wait 5 minutes before next check
            time.sleep(300)
            
        except KeyboardInterrupt:
            print("[FP-MONITOR] Stopping monitoring service...")
            break
        except Exception as e:
            print(f"[FP-MONITOR] Error: {e}")
            time.sleep(60)  # Wait before retry

if __name__ == "__main__":
    run_continuous_monitoring()

