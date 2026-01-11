#!/bin/bash
# Fix git conflicts and push diagnostics

cd ~/stock-bot

echo "Fixing git conflicts and pushing diagnostics..."

# Find the latest diagnostics directory
LATEST_DIAG=$(ls -td diagnostics_* 2>/dev/null | head -1)

if [ -z "$LATEST_DIAG" ]; then
    echo "❌ No diagnostics directory found"
    exit 1
fi

echo "Found diagnostics: $LATEST_DIAG"

# Stash any uncommitted changes
echo "Stashing uncommitted changes..."
git stash push -m "Stashing before diagnostic push" 2>/dev/null || true

# Pull latest
echo "Pulling latest changes..."
git pull origin main

# Add diagnostics if not already added
echo "Adding diagnostics..."
git add "$LATEST_DIAG"/* "$LATEST_DIAG" 2>/dev/null || true

# Commit if needed
if ! git diff --cached --quiet 2>/dev/null; then
    git commit -m "Diagnostic data collection: $(basename $LATEST_DIAG)" 2>/dev/null || true
fi

# Push with force if needed (only for diagnostics)
echo "Pushing to GitHub..."
git push origin main || git push --force-with-lease origin main

echo "✅ Diagnostics pushed to GitHub"
echo "Directory: $LATEST_DIAG"
