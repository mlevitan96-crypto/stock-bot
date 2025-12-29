#!/usr/bin/env python3
"""
Deploy to Droplet, Diagnose, and Fix Trading Issues
Complete workflow: Git → Droplet → Diagnose → Fix → Verify
"""

import json
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

try:
    from droplet_client import DropletClient
    USE_DROPLET_CLIENT = True
except ImportError:
    USE_DROPLET_CLIENT = False
    print("Warning: droplet_client not available, using subprocess SSH")

def load_droplet_config() -> Dict:
    """Load droplet configuration"""
    config_file = Path("droplet_config.json")
    if not config_file.exists():
        raise FileNotFoundError("droplet_config.json not found")
    
    with config_file.open() as f:
        return json.load(f)

def run_ssh_command(host: str, command: str, use_ssh_config: bool = True) -> tuple:
    """Run command on droplet via SSH"""
    if USE_DROPLET_CLIENT:
        try:
            client = DropletClient()
            result = client.execute_command(command)
            return 0, result.get("stdout", ""), result.get("stderr", "")
        except Exception as e:
            # Fall back to subprocess
            pass
    
    if use_ssh_config:
        ssh_cmd = ["ssh", host, command]
    else:
        ssh_cmd = ["ssh", host, command]
    
    try:
        result = subprocess.run(
            ssh_cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)

def deploy_to_droplet() -> bool:
    """Step 1: Deploy latest code to droplet"""
    print("="*80)
    print("STEP 1: DEPLOYING TO DROPLET")
    print("="*80)
    
    config = load_droplet_config()
    host = config["host"]
    project_dir = config.get("project_dir", "~/stock-bot")
    
    print(f"Connecting to {host}...")
    print(f"Project directory: {project_dir}")
    
    # Pull latest code
    commands = [
        f"cd {project_dir} && git pull origin main",
        f"cd {project_dir} && git status --short"
    ]
    
    for cmd in commands:
        print(f"\nRunning: {cmd}")
        code, stdout, stderr = run_ssh_command(host, cmd)
        
        if code != 0:
            print(f"ERROR: Command failed with code {code}")
            if stderr:
                print(f"STDERR: {stderr}")
            return False
        
        if stdout:
            print(stdout)
    
        print("\n[OK] Deployment complete")
    return True

def run_diagnostics() -> Dict:
    """Step 2: Run diagnostic scripts on droplet"""
    print("\n" + "="*80)
    print("STEP 2: RUNNING DIAGNOSTICS")
    print("="*80)
    
    config = load_droplet_config()
    host = config["host"]
    project_dir = config.get("project_dir", "~/stock-bot")
    
    # Run fix script first
    print("\n1. Running auto-fix script...")
    cmd = f"cd {project_dir} && python3 fix_trading_issues.py"
    code, stdout, stderr = run_ssh_command(host, cmd)
    
    if stdout:
        try:
            print(stdout)
        except UnicodeEncodeError:
            print(stdout.encode('ascii', 'replace').decode('ascii'))
    if stderr and code != 0:
        try:
            print(f"ERROR: {stderr}")
        except UnicodeEncodeError:
            print(f"ERROR: {stderr.encode('ascii', 'replace').decode('ascii')}")
    
    # Run diagnostic script
    print("\n2. Running diagnostic script...")
    cmd = f"cd {project_dir} && python3 diagnose_no_trades.py"
    code, stdout, stderr = run_ssh_command(host, cmd)
    
    if stdout:
        try:
            print(stdout)
        except UnicodeEncodeError:
            print(stdout.encode('ascii', 'replace').decode('ascii'))
    if stderr and code != 0:
        try:
            print(f"ERROR: {stderr}")
        except UnicodeEncodeError:
            print(f"ERROR: {stderr.encode('ascii', 'replace').decode('ascii')}")
    
    # Parse results (basic)
    issues = []
    if "CRITICAL ISSUES" in stdout or "ERROR" in stdout:
        issues.append("Critical issues detected")
    
    return {
        "fix_exit_code": code,
        "diagnostic_exit_code": code,
        "issues": issues,
        "output": stdout
    }

def check_bot_status() -> Dict:
    """Step 3: Check if bot is running"""
    print("\n" + "="*80)
    print("STEP 3: CHECKING BOT STATUS")
    print("="*80)
    
    config = load_droplet_config()
    host = config["host"]
    
    # Check if bot process is running
    cmd = "ps aux | grep 'python.*main.py' | grep -v grep"
    code, stdout, stderr = run_ssh_command(host, cmd)
    
    bot_running = code == 0 and stdout.strip()
    
    # Check if UW daemon is running
    cmd = "ps aux | grep 'uw_flow_daemon' | grep -v grep"
    code, stdout, stderr = run_ssh_command(host, cmd)
    
    daemon_running = code == 0 and stdout.strip()
    
    # Check systemd service
    cmd = "systemctl is-active trading-bot.service 2>/dev/null || echo 'inactive'"
    code, stdout, stderr = run_ssh_command(host, cmd)
    service_status = stdout.strip() if stdout else "unknown"
    
    print(f"Bot process: {'RUNNING' if bot_running else 'NOT RUNNING'}")
    print(f"UW daemon: {'RUNNING' if daemon_running else 'NOT RUNNING'}")
    print(f"Systemd service: {service_status}")
    
    return {
        "bot_running": bot_running,
        "daemon_running": daemon_running,
        "service_status": service_status
    }

def fix_common_issues() -> bool:
    """Step 4: Fix common issues"""
    print("\n" + "="*80)
    print("STEP 4: FIXING COMMON ISSUES")
    print("="*80)
    
    config = load_droplet_config()
    host = config["host"]
    project_dir = config.get("project_dir", "~/stock-bot")
    
    fixes_applied = []
    
    # Fix 1: Restart bot if not running
    status = check_bot_status()
    if not status["bot_running"]:
        print("\nBot not running - attempting restart...")
        cmd = f"cd {project_dir} && systemctl restart trading-bot.service 2>&1 || echo 'systemd not available'"
        code, stdout, stderr = run_ssh_command(host, cmd)
        
        if "systemd not available" in stdout:
            # Try screen session
            print("Systemd not available - trying screen session...")
            cmd = f"cd {project_dir} && screen -dmS trading bash -c 'source venv/bin/activate && python3 main.py'"
            code, stdout, stderr = run_ssh_command(host, cmd)
        
        if code == 0:
            fixes_applied.append("Bot restarted")
            print("[OK] Bot restart attempted")
        else:
            print(f"[ERROR] Failed to restart bot: {stderr}")
    
    # Fix 2: Initialize adaptive weights if needed
    print("\nChecking adaptive weights...")
    cmd = f"cd {project_dir} && python3 -c \"import json; w = json.load(open('state/signal_weights.json')); print(len(w.get('weight_bands', {{}})))\" 2>&1 || echo '0'"
    code, stdout, stderr = run_ssh_command(host, cmd)
    
    try:
        component_count = int(stdout.strip()) if stdout.strip().isdigit() else 0
        if component_count != 21:
            print(f"Only {component_count}/21 components - initializing...")
            cmd = f"cd {project_dir} && python3 fix_trading_issues.py"
            code, stdout, stderr = run_ssh_command(host, cmd)
            if code == 0:
                fixes_applied.append("Adaptive weights initialized")
                print("[OK] Adaptive weights fixed")
    except:
        print("⚠ Could not check adaptive weights")
    
    # Fix 3: Check cache freshness
    print("\nChecking cache freshness...")
    cmd = f"cd {project_dir} && test -f data/uw_flow_cache.json && stat -c %Y data/uw_flow_cache.json | xargs -I {{}} date -d @{{}} +'%Y-%m-%d %H:%M:%S' || echo 'missing'"
    code, stdout, stderr = run_ssh_command(host, cmd)
    
    if "missing" in stdout:
        print("⚠ Cache file missing - UW daemon may need restart")
        if not status["daemon_running"]:
            print("Restarting UW daemon...")
            cmd = f"cd {project_dir} && systemctl restart trading-bot.service"
            run_ssh_command(host, cmd)
            fixes_applied.append("UW daemon restarted")
    
    if fixes_applied:
        print(f"\n[OK] Applied {len(fixes_applied)} fixes:")
        for fix in fixes_applied:
            print(f"  - {fix}")
    else:
        print("\n[OK] No fixes needed")
    
    return len(fixes_applied) > 0

def check_recent_logs() -> Dict:
    """Step 5: Check recent logs for errors"""
    print("\n" + "="*80)
    print("STEP 5: CHECKING RECENT LOGS")
    print("="*80)
    
    config = load_droplet_config()
    host = config["host"]
    project_dir = config.get("project_dir", "~/stock-bot")
    
    # Check for errors in logs
    cmd = f"cd {project_dir} && tail -50 logs/bot.log 2>/dev/null | grep -i 'error\\|exception\\|traceback' | tail -10 || echo 'No errors found'"
    code, stdout, stderr = run_ssh_command(host, cmd)
    
    errors = []
    if stdout and "No errors found" not in stdout:
        errors = stdout.strip().split('\n')
        print("⚠ Errors found in logs:")
        for error in errors[:5]:  # Show first 5
            print(f"  {error}")
    else:
        print("[OK] No errors in recent logs")
    
    # Check for signal generation
    cmd = f"cd {project_dir} && tail -50 logs/bot.log 2>/dev/null | grep -E 'cluster|composite_score|decide_and_execute' | tail -5 || echo 'No signal activity'"
    code, stdout, stderr = run_ssh_command(host, cmd)
    
    if stdout and "No signal activity" not in stdout:
        print("\n[OK] Signal activity detected:")
        print(stdout)
    else:
        print("\n[WARN] No recent signal activity")
    
    return {
        "errors": errors,
        "has_signal_activity": "No signal activity" not in (stdout or "")
    }

def verify_trading_readiness() -> bool:
    """Step 6: Verify trading readiness"""
    print("\n" + "="*80)
    print("STEP 6: VERIFYING TRADING READINESS")
    print("="*80)
    
    config = load_droplet_config()
    host = config["host"]
    project_dir = config.get("project_dir", "~/stock-bot")
    
    # Check readiness status
    cmd = f"cd {project_dir} && python3 -c 'import json; r = json.load(open(\"state/trading_readiness.json\")); print(r.get(\"overall_status\", \"UNKNOWN\"))' 2>/dev/null || echo 'UNKNOWN'"
    code, stdout, stderr = run_ssh_command(host, cmd)
    
    readiness = stdout.strip() if stdout else "UNKNOWN"
    print(f"Trading readiness: {readiness}")
    
    if readiness == "READY":
        print("[OK] System is READY for trading")
        return True
    elif readiness == "BLOCKED":
        print("[ERROR] System is BLOCKED - check failure points")
        return False
    else:
        print("[WARN] Readiness status unknown")
        return False

def main():
    """Main deployment and fix workflow"""
    print("\n" + "="*80)
    print("DEPLOY AND FIX TRADING - COMPLETE WORKFLOW")
    print("="*80)
    print("\nThis script will:")
    print("  1. Deploy latest code to droplet")
    print("  2. Run diagnostics")
    print("  3. Check bot status")
    print("  4. Fix common issues")
    print("  5. Check logs for errors")
    print("  6. Verify trading readiness")
    print("\n" + "="*80 + "\n")
    
    try:
        # Step 1: Deploy
        if not deploy_to_droplet():
            print("\n✗ Deployment failed")
            return 1
        
        # Step 2: Run diagnostics
        diag_results = run_diagnostics()
        
        # Step 3: Check status
        status = check_bot_status()
        
        # Step 4: Fix issues
        fixes_applied = fix_common_issues()
        
        # Step 5: Check logs
        log_results = check_recent_logs()
        
        # Step 6: Verify readiness
        ready = verify_trading_readiness()
        
        # Summary
        print("\n" + "="*80)
        print("DEPLOYMENT AND FIX SUMMARY")
        print("="*80)
        
        print(f"\nDeployment: {'[OK] SUCCESS' if True else '[ERROR] FAILED'}")
        print(f"Bot running: {'[OK] YES' if status['bot_running'] else '[ERROR] NO'}")
        print(f"UW daemon: {'[OK] YES' if status['daemon_running'] else '[ERROR] NO'}")
        print(f"Fixes applied: {'[OK] YES' if fixes_applied else '[OK] NO'}")
        print(f"Log errors: {'[WARN] YES' if log_results['errors'] else '[OK] NO'}")
        print(f"Signal activity: {'[OK] YES' if log_results['has_signal_activity'] else '[WARN] NO'}")
        print(f"Trading ready: {'[OK] YES' if ready else '[ERROR] NO'}")
        
        if not status['bot_running']:
            print("\n[CRITICAL] Bot is not running!")
            print("   Run on droplet: systemctl restart trading-bot.service")
        
        if not ready:
            print("\n[CRITICAL] System not ready for trading!")
            print("   Check failure points and fix issues")
        
        return 0 if (status['bot_running'] and ready) else 1
        
    except FileNotFoundError as e:
        print(f"\n[ERROR] Configuration error: {e}")
        print("   Create droplet_config.json with SSH connection details")
        return 1
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

