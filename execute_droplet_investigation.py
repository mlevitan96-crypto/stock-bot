#!/usr/bin/env python3
"""Execute score stagnation investigation on droplet"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    from droplet_client import DropletClient
    import json
    
    print("=" * 80)
    print("EXECUTING SCORE STAGNATION INVESTIGATION ON DROPLET")
    print("=" * 80)
    print()
    
    client = DropletClient()
    
    try:
        # Step 1: Pull latest code
        print("Step 1: Pulling latest code from GitHub...")
        result = client.git_pull()
        if result.get('success'):
            print("✅ Code pulled successfully")
        else:
            print(f"⚠️  Git pull issues: {result.get('stderr', '')[:200]}")
        print()
        
        # Step 2: Run investigation
        print("Step 2: Running comprehensive score stagnation investigation...")
        print("(This may take 2-3 minutes)")
        print()
        
        result = client.execute_command(
            "cd /root/stock-bot && python3 investigate_score_stagnation_on_droplet.py",
            timeout=240
        )
        
        stdout = result.get('stdout', '')
        stderr = result.get('stderr', '')
        exit_code = result.get('exit_code', -1)
        
        # Save results to file
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
        
        # Try to handle encoding issues
        try:
            print(stdout.encode('utf-8', errors='replace').decode('utf-8', errors='replace'))
        except:
            print(stdout)
        
        if stderr:
            print("\n" + "=" * 80)
            print("STDERR")
            print("=" * 80)
            try:
                print(stderr.encode('utf-8', errors='replace').decode('utf-8', errors='replace'))
            except:
                print(stderr)
        
        print("\n" + "=" * 80)
        print(f"Exit Code: {exit_code}")
        print(f"Results saved to: {output_file}")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error during investigation: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()
        
except Exception as e:
    print(f"❌ Failed to connect to droplet: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
