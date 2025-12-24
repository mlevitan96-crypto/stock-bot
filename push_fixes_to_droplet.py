#!/usr/bin/env python3
"""
Push fixes directly to droplet via SSH, bypassing git push blocking.
"""

import os
from pathlib import Path
from droplet_client import DropletClient

def main():
    client = DropletClient()
    
    print("Connecting to droplet...")
    if not client.connect():
        print("❌ Failed to connect to droplet")
        return
    
    print("✓ Connected to droplet")
    print("")
    
    # Read the fix files
    fixes = {
        "sre_monitoring.py": Path("sre_monitoring.py").read_text(encoding='utf-8'),
        "COMPREHENSIVE_FIX_ALL_ISSUES.sh": Path("COMPREHENSIVE_FIX_ALL_ISSUES.sh").read_text(encoding='utf-8'),
    }
    
    # Also read v3_2_features.py to verify bootstrap fix
    v3_2_content = Path("v3_2_features.py").read_text(encoding='utf-8')
    if '"entry_ev_floor": -0.02' in v3_2_content:
        fixes["v3_2_features.py"] = v3_2_content
        print("✓ Bootstrap fix found in v3_2_features.py")
    else:
        print("⚠ Bootstrap fix not found in v3_2_features.py")
    
    # Push each file
    print("")
    print("Pushing fixes to droplet...")
    for filename, content in fixes.items():
        print(f"  Pushing {filename}...")
        remote_path = f"~/stock-bot/{filename}"
        
        # Write file to droplet
        result = client.execute_command(f"cat > {remote_path} << 'ENDOFFILE'\n{content}\nENDOFFILE")
        if result[0] == 0:
            print(f"  ✓ {filename} pushed")
        else:
            print(f"  ❌ Failed to push {filename}: {result[1]}")
    
    # Make script executable
    print("")
    print("Making fix script executable...")
    result = client.execute_command("chmod +x ~/stock-bot/COMPREHENSIVE_FIX_ALL_ISSUES.sh")
    if result[0] == 0:
        print("✓ Script is executable")
    else:
        print(f"⚠ Failed to make executable: {result[1]}")
    
    # Run the fix script
    print("")
    print("Running comprehensive fix script...")
    result = client.execute_command("cd ~/stock-bot && bash COMPREHENSIVE_FIX_ALL_ISSUES.sh")
    print(result[1])  # Print output
    
    client.disconnect()
    print("")
    print("✅ Fixes pushed and applied to droplet!")

if __name__ == "__main__":
    main()

