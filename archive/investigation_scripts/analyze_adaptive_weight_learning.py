#!/usr/bin/env python3
"""
Analyze how adaptive weights learn - component-specific vs overall performance
"""

from droplet_client import DropletClient

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("ADAPTIVE WEIGHT LEARNING ANALYSIS")
        print("=" * 80)
        print()
        
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from pathlib import Path\n"
            "import json\n"
            "\n"
            "print('ANALYZING ADAPTIVE WEIGHT LEARNING LOGIC')\n"
            "print('=' * 80)\n"
            "print()\n"
            "\n"
            "# Load adaptive optimizer code to understand learning\n"
            "optimizer_file = Path('adaptive_signal_optimizer.py')\n"
            "if optimizer_file.exists():\n"
            "    with optimizer_file.open() as f:\n"
            "        content = f.read()\n"
            "    \n"
            "    # Find record_trade method\n"
            "    if 'def record_trade' in content:\n"
            "        start = content.find('def record_trade')\n"
            "        end = content.find('def ', start + 50)\n"
            "        method = content[start:end] if end > 0 else content[start:start+2000]\n"
            "        print('record_trade method (first 2000 chars):')\n"
            "        print('-' * 80)\n"
            "        print(method[:2000])\n"
            "        print()\n"
            "    \n"
            "    # Find update_weights method\n"
            "    if 'def update_weights' in content:\n"
            "        start = content.find('def update_weights')\n"
            "        end = content.find('def ', start + 50)\n"
            "        method = content[start:end] if end > 0 else content[start:start+2000]\n"
            "        print('update_weights method (first 2000 chars):')\n"
            "        print('-' * 80)\n"
            "        print(method[:2000])\n"
            "        print()\n"
            "\n"
            "# Load state file to see actual learning data\n"
            "state_file = Path('state/signal_weights.json')\n"
            "if state_file.exists():\n"
            "    with state_file.open() as f:\n"
            "        state = json.load(f)\n"
            "    \n"
            "    weight_bands = state.get('weight_bands', {})\n"
            "    \n"
            "    print('COMPONENT PERFORMANCE DATA:')\n"
            "    print('-' * 80)\n"
            "    print('Format: Component | Samples | Wins | Losses | Win Rate | EWMA P&L | Current Multiplier')\n"
            "    print('-' * 80)\n"
            "    \n"
            "    for comp, band in sorted(weight_bands.items()):\n"
            "        samples = band.get('sample_count', 0)\n"
            "        wins = band.get('wins', 0)\n"
            "        losses = band.get('losses', 0)\n"
            "        win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0\n"
            "        ewma = band.get('ewma_performance', 0)\n"
            "        current = band.get('current', 1.0)\n"
            "        \n"
            "        print(f'{comp:25} | {samples:7} | {wins:4} | {losses:6} | {win_rate:7.1f}% | {ewma:10.4f} | {current:6.3f}x')\n"
            "    \n"
            "    print()\n"
            "    print('ANALYSIS:')\n"
            "    print('-' * 80)\n"
            "    \n"
            "    # Check if all components have same performance (suggests bug)\n"
            "    same_performance = []\n"
            "    for comp, band in weight_bands.items():\n"
            "        if band.get('sample_count', 0) == 296 and band.get('wins', 0) == 33 and band.get('losses', 0) == 263:\n"
            "            same_performance.append(comp)\n"
            "    \n"
            "    if same_performance:\n"
            "        print(f'Components with IDENTICAL performance (296 samples, 33W/263L): {len(same_performance)}')\n"
            "        print(f'This suggests they were ALL present in the same trades (bug indicator)')\n"
            "        print(f'Components: {same_performance[:10]}')\n"
            "        print()\n"
            "    \n"
            "    # Check if components with 0 samples have default weights\n"
            "    zero_samples = []\n"
            "    for comp, band in weight_bands.items():\n"
            "        if band.get('sample_count', 0) == 0:\n"
            "            zero_samples.append(comp)\n"
            "    \n"
            "    if zero_samples:\n"
            "        print(f'Components with ZERO samples (never learned): {len(zero_samples)}')\n"
            "        print(f'These should use default weights: {zero_samples}')\n"
            "        print()\n"
            "\n"
            "print()\n"
            "PYEOF",
            timeout=120
        )
        print(result['stdout'])
        print()
        
    except Exception as e:
        print(f"[ERROR] Analysis failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

