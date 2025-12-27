#!/usr/bin/env python3
"""
Diagnose Why No Run Cycles - Check if run_once() is being called
"""

from droplet_client import DropletClient
import time

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("DIAGNOSING NO RUN CYCLES")
        print("=" * 80)
        print()
        
        # 1. Check if main.py is actually running
        print("1. MAIN.PY PROCESS STATUS")
        print("-" * 80)
        result = client.execute_command("ps aux | grep 'python.*main.py' | grep -v grep", timeout=10)
        print(result['stdout'] if result['stdout'] else 'Main.py NOT running')
        print()
        
        # 2. Check main.py logs for any activity
        print("2. MAIN.PY RECENT LOGS")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && tail -100 logs/run.jsonl 2>&1 | tail -20",
            timeout=10
        )
        print(result['stdout'][:2000] if result['stdout'] else 'No logs')
        print()
        
        # 3. Check if run_once is being called (check for "started" messages)
        print("3. CHECKING FOR RUN_ONCE CALLS")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && grep -r 'run_once.*started' logs/ 2>&1 | tail -10",
            timeout=10
        )
        print(result['stdout'][:1000] if result['stdout'] else 'No run_once started messages')
        print()
        
        # 4. Check main.py stdout/stderr from systemd
        print("4. MAIN.PY OUTPUT FROM SYSTEMD")
        print("-" * 80)
        result = client.execute_command(
            "journalctl -u trading-bot.service --since '10 minutes ago' --no-pager 2>&1 | grep -E 'main.py|run_once|START|DEBUG' | tail -30",
            timeout=10
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output[:3000])
        print()
        
        # 5. Check if main.py is stuck in initialization
        print("5. CHECKING MAIN.PY INITIALIZATION")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && timeout 30 python -c \"import sys; sys.path.insert(0, '.'); from main import run_once; print('run_once imported successfully'); result = run_once(); print(f'run_once returned: {result}')\" 2>&1",
            timeout=35
        )
        print(result['stdout'][:3000] if result['stdout'] else 'No output')
        print()
        
        # 6. Check if there's a main() function and how it calls run_once
        print("6. CHECKING MAIN FUNCTION")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && grep -A 50 'def main():' main.py | head -60",
            timeout=10
        )
        print(result['stdout'][:2000] if result['stdout'] else 'No main function found')
        print()
        
        # 7. Check if main.py has __main__ block
        print("7. CHECKING __MAIN__ BLOCK")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && tail -50 main.py | grep -A 20 '__main__'",
            timeout=10
        )
        print(result['stdout'][:2000] if result['stdout'] else 'No __main__ block found')
        print()
        
    except Exception as e:
        print(f"[ERROR] Diagnosis failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

