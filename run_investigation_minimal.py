#!/usr/bin/env python
import sys
import os
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from droplet_client import DropletClient
    import json
    
    print("Connecting to droplet...")
    client = DropletClient()
    
    # Upload investigation script
    print("Uploading investigation script...")
    script_path = project_root / "investigate_score_stagnation_on_droplet.py"
    if script_path.exists():
        with open(script_path, 'r') as f:
            script_content = f.read()
        
        # Create upload command
        upload_cmd = f"""python3 << 'SCRIPT_END'
import sys
script = '''{script_content.replace("'''", "\\'\\'\\'")}'''
with open('/root/stock-bot/investigate_score_stagnation_on_droplet.py', 'w') as f:
    f.write(script)
print("Uploaded")
SCRIPT_END"""
        
        result = client.execute_command(upload_cmd, timeout=30)
        print(f"Upload result: {result.get('stdout', '')[:100]}")
    
    # Run investigation
    print("\nRunning investigation on droplet...")
    result = client.execute_command(
        "cd /root/stock-bot && python3 investigate_score_stagnation_on_droplet.py",
        timeout=180
    )
    
    print("\n" + "="*80)
    print("INVESTIGATION RESULTS")
    print("="*80 + "\n")
    print(result.get('stdout', ''))
    
    if result.get('stderr'):
        print("\nSTDERR:")
        print(result.get('stderr'))
    
    # Save to file
    output_file = project_root / "droplet_investigation_results.txt"
    with open(output_file, 'w') as f:
        f.write("="*80 + "\n")
        f.write("DROPLET SCORE STAGNATION INVESTIGATION\n")
        f.write("="*80 + "\n\n")
        f.write(result.get('stdout', ''))
        if result.get('stderr'):
            f.write("\n\nSTDERR:\n" + result.get('stderr'))
    
    print(f"\nResults saved to: {output_file}")
    
    client.close()
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
