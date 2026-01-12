#!/usr/bin/env python3
"""Run score stagnation investigation on droplet"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from droplet_client import DropletClient

def main():
    print("=" * 80)
    print("CONNECTING TO DROPLET FOR SCORE STAGNATION INVESTIGATION")
    print("=" * 80)
    
    try:
        client = DropletClient()
        print("✅ Droplet client initialized")
        
        # First, upload the investigation script if it doesn't exist
        print("\n📤 Uploading investigation script to droplet...")
        
        # Upload script using base64 encoding to avoid issues with heredoc
        script_content = Path("investigate_score_stagnation_on_droplet.py").read_text()
        import base64
        script_b64 = base64.b64encode(script_content.encode('utf-8')).decode('ascii')
        result = client.execute_command(
            f"cd /root/stock-bot && echo '{script_b64}' | base64 -d > investigate_score_stagnation_on_droplet.py && chmod +x investigate_score_stagnation_on_droplet.py",
            timeout=30
        )
        
        if result.get('exit_code') == 0:
            print("✅ Script uploaded")
        else:
            print(f"⚠️  Upload may have failed: {result.get('stderr', '')}")
        
        # Now run the investigation
        print("\n🔍 Running investigation on droplet...")
        print("-" * 80)
        
        result = client.execute_command(
            "cd /root/stock-bot && python3 investigate_score_stagnation_on_droplet.py",
            timeout=180
        )
        
        print("\n" + "=" * 80)
        print("INVESTIGATION RESULTS")
        print("=" * 80)
        
        stdout = result.get('stdout', '')
        stderr = result.get('stderr', '')
        exit_code = result.get('exit_code', -1)
        
        if stdout:
            print("\n=== STDOUT ===")
            print(stdout)
        
        if stderr:
            print("\n=== STDERR ===")
            print(stderr)
        
        print(f"\n=== EXIT CODE: {exit_code} ===")
        
        # Save results to file
        output_file = Path("droplet_investigation_results.txt")
        with open(output_file, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("DROPLET SCORE STAGNATION INVESTIGATION RESULTS\n")
            f.write("=" * 80 + "\n\n")
            f.write(stdout)
            if stderr:
                f.write("\n" + "=" * 80 + "\n")
                f.write("STDERR\n")
                f.write("=" * 80 + "\n\n")
                f.write(stderr)
        
        print(f"\n✅ Results saved to: {output_file}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
