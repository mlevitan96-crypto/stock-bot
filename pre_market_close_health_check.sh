#!/bin/bash
# Pre-Market-Close Structural Health Check
# Run this script on the droplet to check system health before market close

cd ~/stock-bot || exit 1

echo "=========================================="
echo "Pre-Market-Close Structural Health Check"
echo "=========================================="
echo ""

# 1. Check if any 'Panic Boosts' were applied today
echo "1. Checking for Panic Regime Activity Today:"
echo "--------------------------------------------"
if [ -f "data/explainable_logs.jsonl" ]; then
    PANIC_COUNT=$(grep -i "panic" data/explainable_logs.jsonl 2>/dev/null | wc -l)
    if [ "$PANIC_COUNT" -gt 0 ]; then
        echo "   Found $PANIC_COUNT panic-related entries"
        echo "   Recent entries:"
        grep -i "panic" data/explainable_logs.jsonl | tail -n 5
    else
        echo "   No panic regime entries found today"
    fi
elif [ -f "logs/explainable_logs.jsonl" ]; then
    PANIC_COUNT=$(grep -i "panic" logs/explainable_logs.jsonl 2>/dev/null | wc -l)
    if [ "$PANIC_COUNT" -gt 0 ]; then
        echo "   Found $PANIC_COUNT panic-related entries"
        echo "   Recent entries:"
        grep -i "panic" logs/explainable_logs.jsonl | tail -n 5
    else
        echo "   No panic regime entries found today"
    fi
else
    echo "   [WARNING] explainable_logs.jsonl not found"
fi
echo ""

# 2. Verify current regime and threshold
echo "2. Current Regime and Threshold:"
echo "--------------------------------"
python3 << 'PYTHON_SCRIPT'
import json
import sys
from pathlib import Path

try:
    # Try to get regime from structural intelligence
    current_regime = "MIXED"
    confidence = 0.0
    try:
        from structural_intelligence import get_regime_detector
        regime_detector = get_regime_detector()
        current_regime, confidence = regime_detector.detect_regime()
        print(f"   Detected Regime: {current_regime} (confidence: {confidence:.2f})")
    except Exception as e:
        # Fallback: try signal_weights.json
        weights_file = Path("state/signal_weights.json")
        if weights_file.exists():
            weights = json.load(open(weights_file))
            current_regime = weights.get("current_regime", "MIXED")
            print(f"   Regime from state: {current_regime}")
        else:
            print(f"   Using default regime: {current_regime} (structural intelligence unavailable)")
    
    # Get threshold from SpecialistStrategyRotator
    try:
        from specialist_strategy_rotator import SpecialistStrategyRotator
        ssr = SpecialistStrategyRotator(current_regime, 2.0)
        threshold = ssr.get_proactive_threshold()
        print(f"   Active Threshold: {threshold:.2f}")
    except Exception as e:
        print(f"   [ERROR] Could not load SpecialistStrategyRotator: {e}")
        print(f"   Using default threshold: 2.0")
except Exception as e:
    print(f"   [ERROR] {e}")
    sys.exit(1)
PYTHON_SCRIPT
echo ""

# 3. Check Capacity (how many slots are open for MOC moves?)
echo "3. Position Capacity:"
echo "---------------------"
python3 << 'PYTHON_SCRIPT'
import json
from pathlib import Path

try:
    metadata_file = Path("state/position_metadata.json")
    if metadata_file.exists():
        meta = json.load(open(metadata_file))
        active_positions = len(meta)
        max_positions = 16  # MAX_CONCURRENT_POSITIONS from config
        free_capacity = max_positions - active_positions
        
        print(f"   Active Positions: {active_positions} / {max_positions}")
        print(f"   Free Capacity: {free_capacity}")
        
        if free_capacity > 0:
            print(f"   Status: OK - {free_capacity} slot(s) available for new entries")
        else:
            print(f"   Status: FULL - No capacity for new entries")
    else:
        print(f"   [WARNING] position_metadata.json not found")
        print(f"   Assuming 0 active positions, 16 free capacity")
except Exception as e:
    print(f"   [ERROR] {e}")
PYTHON_SCRIPT
echo ""

echo "=========================================="
echo "Health Check Complete"
echo "=========================================="
