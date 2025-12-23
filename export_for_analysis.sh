#!/bin/bash
# Export common files for analysis and push to GitHub
# Usage: ./export_for_analysis.sh [analysis_type]

set -e

cd ~/stock-bot

ANALYSIS_TYPE="${1:-full}"

echo "=================================================================================="
echo "EXPORTING FILES FOR ANALYSIS"
echo "=================================================================================="
echo ""

case "$ANALYSIS_TYPE" in
    "heartbeat"|"hb")
        echo "Exporting heartbeat files..."
        ./push_to_github.sh \
            state/bot_heartbeat.json \
            logs/heartbeat.jsonl \
            "Export heartbeat files for analysis"
        ;;
    
    "logs"|"log")
        echo "Exporting log files..."
        ./push_to_github.sh \
            logs/run.jsonl \
            logs/trading.jsonl \
            logs/orders.jsonl \
            logs/exits.jsonl \
            "Export trading logs for analysis"
        ;;
    
    "state"|"st")
        echo "Exporting state files..."
        ./push_to_github.sh \
            state/position_metadata.json \
            state/governor_freezes.json \
            state/signal_weights.json \
            "Export state files for analysis"
        ;;
    
    "cache"|"c")
        echo "Exporting cache files..."
        ./push_to_github.sh \
            data/uw_flow_cache.json \
            "Export UW cache for analysis"
        ;;
    
    "signals"|"sig")
        echo "Exporting signal files..."
        ./push_to_github.sh \
            logs/signals.jsonl \
            logs/gate.jsonl \
            logs/composite_attribution.jsonl \
            "Export signal files for analysis"
        ;;
    
    "full"|"all"|"")
        echo "Exporting all files for full analysis..."
        
        # Export in batches to avoid huge commits
        ./push_to_github.sh \
            state/bot_heartbeat.json \
            state/position_metadata.json \
            state/governor_freezes.json \
            "Export state files for analysis"
        
        ./push_to_github.sh \
            logs/run.jsonl \
            logs/trading.jsonl \
            logs/orders.jsonl \
            "Export trading logs for analysis"
        
        ./push_to_github.sh \
            logs/signals.jsonl \
            logs/gate.jsonl \
            logs/composite_attribution.jsonl \
            "Export signal files for analysis"
        
        echo ""
        echo "✅ Full export complete"
        ;;
    
    "quick"|"q")
        echo "Quick export (most recent files only)..."
        # Use clean branch version to avoid secret scanning issues
        if [ -f "./push_to_github_clean.sh" ]; then
            ./push_to_github_clean.sh \
                state/bot_heartbeat.json \
                logs/run.jsonl \
                "Quick export for analysis"
        else
            ./push_to_github.sh \
                state/bot_heartbeat.json \
                logs/run.jsonl \
                "Quick export for analysis"
        fi
        ;;
    
    *)
        echo "Usage: $0 [analysis_type]"
        echo ""
        echo "Analysis types:"
        echo "  heartbeat, hb    - Heartbeat files"
        echo "  logs, log        - Trading logs"
        echo "  state, st        - State files"
        echo "  cache, c         - UW cache"
        echo "  signals, sig     - Signal files"
        echo "  full, all        - All files (default)"
        echo "  quick, q         - Quick export (heartbeat + recent logs)"
        echo ""
        exit 1
        ;;
esac

echo ""
echo "=================================================================================="
echo "EXPORT COMPLETE"
echo "=================================================================================="
echo ""
echo "Next steps:"
echo "1. Ask the AI to analyze the files from GitHub"
echo "2. Example: 'Analyze the heartbeat file and logs/run.jsonl from the repo'"
echo ""
