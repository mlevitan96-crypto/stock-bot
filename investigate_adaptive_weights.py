#!/usr/bin/env python3
"""
Investigate why adaptive weights are reducing component contributions
"""

from droplet_client import DropletClient

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("ADAPTIVE WEIGHTS INVESTIGATION")
        print("=" * 80)
        print()
        
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from uw_composite_v2 import WEIGHTS_V3, get_weight, get_adaptive_weights\n"
            "from adaptive_signal_optimizer import get_optimizer\n"
            "import json\n"
            "\n"
            "print('DEFAULT WEIGHTS (WEIGHTS_V3):')\n"
            "print('-' * 80)\n"
            "for comp, weight in sorted(WEIGHTS_V3.items()):\n"
            "    print(f'{comp:25} = {weight:6.3f}')\n"
            "\n"
            "print()\n"
            "print('ADAPTIVE WEIGHTS (from optimizer):')\n"
            "print('-' * 80)\n"
            "adaptive = get_adaptive_weights()\n"
            "if adaptive:\n"
            "    for comp, weight in sorted(adaptive.items()):\n"
            "        print(f'{comp:25} = {weight:6.3f}')\n"
            "    print(f'\\nTotal adaptive weights: {len(adaptive)}')\n"
            "else:\n"
            "    print('No adaptive weights (using defaults)')\n"
            "\n"
            "print()\n"
            "print('CURRENT WEIGHTS (default + adaptive):')\n"
            "print('-' * 80)\n"
            "components = list(WEIGHTS_V3.keys())\n"
            "for comp in sorted(components):\n"
            "    default = WEIGHTS_V3.get(comp, 0)\n"
            "    current = get_weight(comp)\n"
            "    if default != current:\n"
            "        pct_change = ((current - default) / default * 100) if default != 0 else 0\n"
            "        print(f'{comp:25} = {default:6.3f} -> {current:6.3f} ({pct_change:+.1f}%)')\n"
            "\n"
            "print()\n"
            "print('CHECKING OPTIMIZER STATE:')\n"
            "print('-' * 80)\n"
            "optimizer = get_optimizer()\n"
            "if optimizer:\n"
            "    print(f'Optimizer exists: {type(optimizer).__name__}')\n"
            "    try:\n"
            "        state = optimizer.get_state()\n"
            "        print(f'State keys: {list(state.keys()) if isinstance(state, dict) else \"NOT DICT\"}')\n"
            "        if isinstance(state, dict):\n"
            "            entry_weights = state.get('entry_weights', {})\n"
            "            print(f'Entry weights: {len(entry_weights)} components')\n"
            "            for comp, weight in list(entry_weights.items())[:10]:\n"
            "                print(f'  {comp:25} = {weight}')\n"
            "    except Exception as e:\n"
            "        print(f'Error getting state: {e}')\n"
            "else:\n"
            "    print('No optimizer found')\n"
            "\n"
            "print()\n"
            "print('CHECKING STATE FILE:')\n"
            "print('-' * 80)\n"
            "from pathlib import Path\n"
            "state_file = Path('state/signal_weights.json')\n"
            "if state_file.exists():\n"
            "    with state_file.open() as f:\n"
            "        state = json.load(f)\n"
            "    print(f'State file exists: {len(state)} keys')\n"
            "    print(f'Keys: {list(state.keys())}')\n"
            "    entry_weights = state.get('entry_weights', {})\n"
            "    if entry_weights:\n"
            "        print(f'\\nEntry weights in file:')\n"
            "        for comp, weight in list(entry_weights.items())[:15]:\n"
            "            print(f'  {comp:25} = {weight}')\n"
            "else:\n"
            "    print('State file does not exist')\n"
            "PYEOF",
            timeout=120
        )
        print(result['stdout'])
        print()
        
    except Exception as e:
        print(f"[ERROR] Investigation failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

