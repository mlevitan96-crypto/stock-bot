#!/bin/bash
# Fix git and push diagnostics to GitHub

cd ~/stock-bot

echo "Fixing git and pushing diagnostics..."

# Find the latest diagnostics directory
LATEST_DIAG=$(ls -td diagnostics_* 2>/dev/null | head -1)

if [ -z "$LATEST_DIAG" ]; then
    echo "❌ No diagnostics directory found"
    exit 1
fi

echo "Found diagnostics: $LATEST_DIAG"

# Pull with rebase to integrate remote changes
echo "Pulling latest changes..."
git pull --rebase origin main

# Add diagnostics
echo "Adding diagnostics to git..."
git add "$LATEST_DIAG"/* "$LATEST_DIAG" 2>/dev/null || true

# Commit if not already committed
if ! git diff --cached --quiet; then
    git commit -m "Diagnostic data collection: $(basename $LATEST_DIAG)" 2>/dev/null || true
fi

# Push
echo "Pushing to GitHub..."
git push origin main

echo "✅ Diagnostics pushed to GitHub"
echo "Directory: $LATEST_DIAG"
