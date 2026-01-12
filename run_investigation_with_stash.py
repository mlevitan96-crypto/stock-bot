#!/usr/bin/env python3
"""
Run investigation on droplet after handling local git changes
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    from droplet_client import DropletClient
    
    print("=" * 80)
    print("RUNNING SCORE STAGNATION INVESTIGATION ON DROPLET")
    print("=" * 80)
    print()
    
    client = DropletClient()
    
    try:
        # Step 1: Stash local changes and pull
        print("Step 1: Stashing local changes and pulling latest code...")
        result = client.execute_command(
            "git stash push -m 'Auto-stash before investigation' && git pull origin main",
            timeout=60
        )
        
        if result.get('success'):
            print("✅ Code pulled successfully")
            if result.get('stdout'):
                print(f"   {result.get('stdout')[:200]}")
        else:
            print(f"⚠️  Git pull issues: {result.get('stderr', '')[:200]}")
            # Try force reset if stash doesn't work
            print("\nTrying force reset to origin/main...")
            result2 = client.execute_command(
                "git fetch origin main && git reset --hard origin/main",
                timeout=60
            )
            if result2.get('success'):
                print("✅ Force reset successful")
            else:
                print(f"⚠️  Force reset also failed: {result2.get('stderr', '')[:200]}")
        print()
        
        # Step 2: Verify script exists
        print("Step 2: Verifying investigation script exists...")
        result = client.execute_command(
            "test -f investigate_score_stagnation_on_droplet.py && echo 'EXISTS' || echo 'NOT_FOUND'",
            timeout=10
        )
        if 'EXISTS' in result.get('stdout', ''):
            print("✅ Investigation script found")
        else:
            print("❌ Investigation script not found - script may not have been pulled")
            print("   Attempting to list files...")
            list_result = client.execute_command("ls -la *.py | head -20", timeout=10)
            print(list_result.get('stdout', ''))
            return
        print()
        
        # Step 3: Run investigation
        print("Step 3: Running comprehensive score stagnation investigation...")
        print("(This may take 2-3 minutes)")
        print()
        
        result = client.execute_command(
            "python3 investigate_score_stagnation_on_droplet.py",
            timeout=300
        )
        
        stdout = result.get('stdout', '')
        stderr = result.get('stderr', '')
        exit_code = result.get('exit_code', -1)
        
        # Save results
        output_file = Path("droplet_investigation_results.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("DROPLET SCORE STAGNATION INVESTIGATION RESULTS\n")
            f.write("=" * 80 + "\n\n")
            f.write(stdout)
            if stderr:
                f.write("\n\n" + "=" * 80 + "\n")
                f.write("STDERR\n")
                f.write("=" * 80 + "\n\n")
                f.write(stderr)
        
        # Print results
        print("=" * 80)
        print("INVESTIGATION RESULTS")
        print("=" * 80)
        print()
        print(stdout)
        
        if stderr:
            print("\n" + "=" * 80)
            print("STDERR")
            print("=" * 80)
            print(stderr)
        
        print("\n" + "=" * 80)
        print(f"Exit Code: {exit_code}")
        print(f"✅ Results saved to: {output_file}")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()
        
except ImportError as e:
    print(f"❌ Error: Could not import droplet_client: {e}")
    print("\nPlease run manually on droplet:")
    print("  cd /root/stock-bot")
    print("  git stash")
    print("  git pull origin main")
    print("  python3 investigate_score_stagnation_on_droplet.py")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
