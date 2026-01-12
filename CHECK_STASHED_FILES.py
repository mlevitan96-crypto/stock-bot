#!/usr/bin/env python3
"""
Check what files were stashed on the droplet
This helps determine if stashed changes are important
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    from droplet_client import DropletClient
    
    print("=" * 80)
    print("CHECKING STASHED FILES ON DROPLET")
    print("=" * 80)
    print()
    
    client = DropletClient()
    
    try:
        # Check stash list
        print("Checking git stash...")
        result = client.execute_command("cd /root/stock-bot && git stash list", timeout=10)
        stdout = result.get('stdout', '')
        
        if stdout.strip():
            print("✅ Stash entries found:")
            print(stdout)
            print()
            
            # Show what's in the most recent stash
            print("Showing contents of most recent stash:")
            result2 = client.execute_command(
                "cd /root/stock-bot && git stash show -p --stat",
                timeout=30
            )
            
            stdout2 = result2.get('stdout', '')
            if stdout2:
                # Show summary first
                lines = stdout2.split('\n')
                summary_lines = [l for l in lines if '|' in l or 'files changed' in l.lower()]
                
                print("\nSummary:")
                for line in summary_lines[:20]:
                    print(f"  {line}")
                
                print(f"\nFull diff (showing first 100 lines):")
                for line in lines[:100]:
                    print(line)
                
                if len(lines) > 100:
                    print(f"\n... ({len(lines) - 100} more lines)")
            else:
                print("  No changes in stash (empty or already applied)")
        else:
            print("⚠️  No stash entries found")
            print("  Files may have been discarded during reset")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()
        
except Exception as e:
    print(f"❌ Error connecting to droplet: {e}")
    print("\nRun manually on droplet:")
    print("  git stash list")
    print("  git stash show -p")
    sys.exit(1)
