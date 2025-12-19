#!/bin/bash
# Setup script for Ubuntu externally-managed Python environment

echo "=========================================="
echo "SETTING UP PYTHON ENVIRONMENT"
echo "=========================================="
echo ""

# Check if venv exists
if [ -d "venv" ]; then
    echo "✅ Virtual environment exists"
    echo "   Activating: source venv/bin/activate"
    source venv/bin/activate
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✅ Virtual environment created and activated"
fi
echo ""

# Install dependencies
echo "Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt
echo ""

echo "=========================================="
echo "ENVIRONMENT READY"
echo "=========================================="
echo ""
echo "To use this environment:"
echo "  source venv/bin/activate"
echo ""
echo "Then start services:"
echo "  screen -dmS trading python3 main.py"
echo "  screen -dmS dashboard python3 dashboard.py"
echo ""
