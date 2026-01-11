#!/bin/bash
# Find the correct bot directory and run diagnostics

echo "=========================================="
echo "FINDING BOT DIRECTORY"
echo "=========================================="

# Try common locations
POSSIBLE_DIRS=(
    "$HOME/stock-bot"
    "$HOME/trading-bot"
    "$HOME/trading-bot-current"
    "/root/stock-bot"
    "/root/trading-bot"
    "$(pwd)"
)

BOT_DIR=""
for dir in "${POSSIBLE_DIRS[@]}"; do
    if [ -d "$dir" ] && [ -f "$dir/main.py" ]; then
        BOT_DIR="$dir"
        echo "✅ Found bot at: $BOT_DIR"
        break
    fi
done

if [ -z "$BOT_DIR" ]; then
    echo "❌ Could not find bot directory"
    echo "Searching for main.py..."
    find ~ -name "main.py" -type f 2>/dev/null | head -5
    exit 1
fi

cd "$BOT_DIR"
echo "Working directory: $(pwd)"
echo ""

echo "=========================================="
echo "PULLING LATEST CODE"
echo "=========================================="
git pull origin main
echo ""

echo "=========================================="
echo "RUNNING FULL SYSTEM AUDIT"
echo "=========================================="
if [ -f "FULL_SYSTEM_AUDIT.py" ]; then
    python3 FULL_SYSTEM_AUDIT.py
else
    echo "⚠️  FULL_SYSTEM_AUDIT.py not found"
fi
echo ""

echo "=========================================="
echo "RUNNING EXECUTION DIAGNOSIS"
echo "=========================================="
if [ -f "DIAGNOSE_BOT_EXECUTION.py" ]; then
    python3 DIAGNOSE_BOT_EXECUTION.py
else
    echo "⚠️  DIAGNOSE_BOT_EXECUTION.py not found"
fi
echo ""

echo "=========================================="
echo "CHECKING BOT STATUS"
echo "=========================================="
if [ -f "CHECK_BOT_STATUS.sh" ]; then
    chmod +x CHECK_BOT_STATUS.sh
    ./CHECK_BOT_STATUS.sh
else
    echo "⚠️  CHECK_BOT_STATUS.sh not found"
    echo ""
    echo "Manual checks:"
    echo "1. Process:"
    ps aux | grep "main.py" | grep -v grep
    echo ""
    echo "2. Recent run cycles:"
    if [ -f "logs/run.jsonl" ]; then
        tail -3 logs/run.jsonl
    else
        echo "  logs/run.jsonl does not exist"
    fi
    echo ""
    echo "3. Worker logs:"
    if [ -f "logs/worker.jsonl" ]; then
        tail -3 logs/worker.jsonl
    else
        echo "  logs/worker.jsonl does not exist"
    fi
fi
echo ""

echo "=========================================="
echo "DIAGNOSTICS COMPLETE"
echo "=========================================="
