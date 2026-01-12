#!/usr/bin/env python3
"""
Run Score Stagnation Investigation on Droplet
This script will connect to the droplet, pull latest code, and run the investigation.
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from droplet_client import DropletClient
    
    print("=" * 80)
    print("RUNNING SCORE STAGNATION INVESTIGATION ON DROPLET")
    print("=" * 80)
    print()
    
    client = DropletClient()
    
    try:
        # Step 1: Pull latest code
        print("Step 1: Pulling latest code...")
        pull_result = client.git_pull()
        if pull_result.get('success'):
            print("✅ Code pulled successfully")
        else:
            print(f"⚠️  Git pull warning: {pull_result.get('stderr', '')[:100]}")
        print()
        
        # Step 2: Run investigation
        print("Step 2: Running investigation (this may take 2-3 minutes)...")
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
    print("\nPlease ensure:")
    print("1. droplet_client.py exists")
    print("2. droplet_config.json is configured")
    print("3. paramiko is installed: pip install paramiko")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
