"""Execute diagnostic on droplet via SSH"""
import subprocess
import sys

def run_ssh_command(command):
    """Run command on droplet via SSH"""
    ssh_cmd = ["ssh", "alpaca", command]
    try:
        result = subprocess.run(
            ssh_cmd,
            capture_output=True,
            text=True,
            timeout=600
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)

def main():
    print("=" * 80)
    print("RUNNING SCORE DIAGNOSTIC ON DROPLET")
    print("=" * 80)
    print()
    
    # Step 1: Pull latest code
    print("Step 1: Pulling latest code...")
    exit_code, stdout, stderr = run_ssh_command(
        "cd /root/stock-bot && git fetch origin main && git reset --hard origin/main"
    )
    if exit_code == 0:
        print("[OK] Code pulled")
    else:
        print(f"[WARNING] {stderr[:200]}")
    print()
    
    # Step 2: Run diagnostic
    print("Step 2: Running comprehensive score diagnostic...")
    exit_code, stdout, stderr = run_ssh_command(
        "cd /root/stock-bot && python3 comprehensive_score_diagnostic.py"
    )
    
    print("\n" + "=" * 80)
    print("DIAGNOSTIC OUTPUT")
    print("=" * 80)
    print(stdout)
    
    if stderr:
        print("\n" + "=" * 80)
        print("ERRORS")
        print("=" * 80)
        print(stderr)
    
    # Step 3: Get sample data
    print("\n" + "=" * 80)
    print("Step 3: Sample cache data...")
    print("=" * 80)
    
    exit_code2, stdout2, stderr2 = run_ssh_command(
        """cd /root/stock-bot && python3 -c "
import json
cache = json.load(open('data/uw_flow_cache.json'))
syms = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'SPY']
for s in syms:
    if s in cache:
        d = cache[s]
        print(f'{s}: sent={d.get(\"sentiment\")}, conv={d.get(\"conviction\", 0):.3f}, fresh={d.get(\"freshness\", 1.0):.3f}')
" """
    )
    print(stdout2)
    
    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
