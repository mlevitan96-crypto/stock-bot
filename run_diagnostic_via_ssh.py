"""
Run comprehensive score diagnostic on droplet via SSH.
This script connects to droplet and runs the diagnostic.
"""

import subprocess
import sys

def run_via_ssh():
    """Run diagnostic on droplet via SSH."""
    print("=" * 80)
    print("RUNNING COMPREHENSIVE SCORE DIAGNOSTIC ON DROPLET")
    print("=" * 80)
    print()
    
    # SSH command to run
    ssh_command = """ssh alpaca 'cd ~/stock-bot && git pull origin main && source venv/bin/activate 2>/dev/null; python3 comprehensive_score_diagnostic.py 2>&1'"""
    
    print("Executing SSH command...")
    print(f"Command: {ssh_command[:100]}...")
    print()
    
    try:
        result = subprocess.run(
            ssh_command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        print("=" * 80)
        print("DIAGNOSTIC OUTPUT")
        print("=" * 80)
        print(result.stdout)
        
        if result.stderr:
            print("\n" + "=" * 80)
            print("ERRORS")
            print("=" * 80)
            print(result.stderr)
        
        print("\n" + "=" * 80)
        print(f"Exit code: {result.returncode}")
        print("=" * 80)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("ERROR: Command timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_via_ssh()
    sys.exit(0 if success else 1)
