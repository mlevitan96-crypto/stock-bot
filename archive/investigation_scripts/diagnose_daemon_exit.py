#!/usr/bin/env python3
"""Diagnose why daemon exits immediately."""

from droplet_client import DropletClient

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("DIAGNOSING DAEMON EXIT")
        print("=" * 80)
        print()
        
        # 1. Check daemon logs
        print("1. DAEMON LOGS (LAST 50 LINES)")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && tail -50 logs/uw_flow_daemon.log 2>&1",
            timeout=10
        )
        print(result['stdout'][:3000] if result['stdout'] else 'No logs')
        print()
        
        # 2. Check if API key is set
        print("2. CHECKING API KEY")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import os\n"
            "from dotenv import load_dotenv\n"
            "load_dotenv()\n"
            "api_key = os.getenv('UW_API_KEY')\n"
            "print(f'UW_API_KEY: {\"SET\" if api_key else \"NOT SET\"}')\n"
            "if api_key:\n"
            "    print(f'Length: {len(api_key)}')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        # 3. Try to start daemon manually and see error
        print("3. TESTING DAEMON START")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && timeout 10 python uw_flow_daemon.py 2>&1 | head -30",
            timeout=15
        )
        print(result['stdout'][:2000] if result['stdout'] else 'No output')
        print()
        
        # 4. Check supervisor process monitoring
        print("4. SUPERVISOR PROCESS MONITORING")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && tail -20 logs/supervisor.jsonl 2>&1 | tail -10",
            timeout=10
        )
        print(result['stdout'][:1500] if result['stdout'] else 'No supervisor logs')
        print()
        
    except Exception as e:
        print(f"[ERROR] Diagnosis failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

