#!/bin/bash
# Restart bot and monitor displacement/exit logs

echo "=========================================="
echo "FINDING AND STOPPING BOT PROCESS"
echo "=========================================="

# Find the bot process
PID=$(ps aux | grep "python.*main.py" | grep -v grep | awk '{print $2}')

if [ -z "$PID" ]; then
    echo "⚠️  No bot process found"
else
    echo "Found bot process: $PID"
    echo "Stopping..."
    kill $PID
    sleep 3
    
    # Check if it's still running
    if ps -p $PID > /dev/null 2>&1; then
        echo "Process still running, force killing..."
        kill -9 $PID
        sleep 2
    fi
    echo "✅ Bot stopped"
fi

echo ""
echo "=========================================="
echo "STARTING BOT IN SCREEN SESSION"
echo "=========================================="

# Start in screen session
echo "Starting bot..."
screen -dmS trading bash -c "cd ~/stock-bot && python3 main.py 2>&1 | tee -a logs/bot_startup.log"
sleep 5

# Verify it's running
NEW_PID=$(ps aux | grep "python.*main.py" | grep -v grep | awk '{print $2}')
if [ -z "$NEW_PID" ]; then
    echo "❌ Bot failed to start"
    echo ""
    echo "Checking for errors..."
    if [ -f "logs/bot_startup.log" ]; then
        tail -20 logs/bot_startup.log
    else
        echo "No startup log found. Trying to start manually to see error:"
        echo ""
        python3 main.py 2>&1 | head -30
    fi
    exit 1
else
    echo "✅ Bot started (PID: $NEW_PID)"
fi

echo ""
echo "=========================================="
echo "MONITORING LOGS (Ctrl+C to stop)"
echo "=========================================="
echo ""
echo "Watching for displacement and exit events..."
echo ""

# Monitor logs in real-time
tail -f logs/displacement.jsonl logs/exit.jsonl 2>/dev/null | grep --line-buffered -E "DEBUG DISPLACEMENT|DEBUG EXITS|no_candidates_found|positions_to_close" || {
    echo "⚠️  Log files not found yet, waiting 10 seconds..."
    sleep 10
    tail -f logs/displacement.jsonl logs/exit.jsonl 2>/dev/null | grep --line-buffered -E "DEBUG DISPLACEMENT|DEBUG EXITS|no_candidates_found|positions_to_close" || echo "Still no logs - check if bot is running: ps aux | grep main.py"
}
