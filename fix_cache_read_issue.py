#!/usr/bin/env python3
"""Fix cache read issue - main.py can't read cache that exists."""

from droplet_client import DropletClient

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("FIXING CACHE READ ISSUE")
        print("=" * 80)
        print()
        
        # Check both paths
        print("1. CHECKING CACHE FILE PATHS")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && python3 << 'PYEOF'\n"
            "from pathlib import Path\n"
            "import json\n"
            "# Direct path\n"
            "direct_path = Path('data/uw_flow_cache.json')\n"
            "print(f'Direct path exists: {direct_path.exists()}')\n"
            "if direct_path.exists():\n"
            "    cache = json.load(open(direct_path))\n"
            "    symbols = [k for k in cache.keys() if not k.startswith('_')]\n"
            "    print(f'Direct read - symbols: {len(symbols)}')\n"
            "# Registry path\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from config.registry import CacheFiles\n"
            "registry_path = CacheFiles.UW_FLOW_CACHE\n"
            "print(f'Registry path: {registry_path}')\n"
            "print(f'Registry path exists: {registry_path.exists()}')\n"
            "if registry_path.exists():\n"
            "    cache2 = json.load(open(registry_path))\n"
            "    symbols2 = [k for k in cache2.keys() if not k.startswith('_')]\n"
            "    print(f'Registry read - symbols: {len(symbols2)}')\n"
            "# Check if paths are the same\n"
            "print(f'Paths match: {direct_path.absolute() == registry_path.absolute()}')\n"
            "PYEOF",
            timeout=60
        )
        print(result['stdout'])
        print()
        
        # Test read_uw_cache
        print("2. TESTING read_uw_cache()")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from main import read_uw_cache\n"
            "try:\n"
            "    cache = read_uw_cache()\n"
            "    symbols = [k for k in cache.keys() if not k.startswith('_')]\n"
            "    print(f'read_uw_cache() returns: {len(symbols)} symbols')\n"
            "    if symbols:\n"
            "        print(f'Symbols: {symbols[:10]}')\n"
            "    else:\n"
            "        print('No symbols found - checking cache content...')\n"
            "        print(f'All keys: {list(cache.keys())[:20]}')\n"
            "except Exception as e:\n"
            "    print(f'Error: {e}')\n"
            "    import traceback\n"
            "    traceback.print_exc()\n"
            "PYEOF",
            timeout=60
        )
        print(result['stdout'])
        print()
        
        # Check if cache file is being written correctly
        print("3. CHECKING CACHE FILE CONTENT")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && python3 << 'PYEOF'\n"
            "from pathlib import Path\n"
            "import json\n"
            "cache_path = Path('data/uw_flow_cache.json')\n"
            "if cache_path.exists():\n"
            "    with open(cache_path) as f:\n"
            "        content = f.read()\n"
            "    print(f'File size: {len(content)} bytes')\n"
            "    print(f'First 500 chars: {content[:500]}')\n"
            "    try:\n"
            "        cache = json.loads(content)\n"
            "        print(f'JSON valid: Yes')\n"
            "        print(f'Keys: {list(cache.keys())[:20]}')\n"
            "        symbols = [k for k in cache.keys() if not k.startswith('_')]\n"
            "        print(f'Symbols: {len(symbols)}')\n"
            "    except Exception as e:\n"
            "        print(f'JSON parse error: {e}')\n"
            "else:\n"
            "    print('Cache file does not exist')\n"
            "PYEOF",
            timeout=60
        )
        print(result['stdout'])
        print()
        
        print("=" * 80)
        print("NEXT STEPS")
        print("=" * 80)
        print("If cache file has symbols but read_uw_cache() returns 0,")
        print("there may be a path or reading issue. Check the paths above.")
        print()
        
    except Exception as e:
        print(f"[ERROR] Fix failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

