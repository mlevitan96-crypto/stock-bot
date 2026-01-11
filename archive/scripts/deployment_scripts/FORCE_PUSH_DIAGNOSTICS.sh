#!/bin/bash
# Force push diagnostics by handling all git conflicts

cd ~/stock-bot

echo "=========================================="
echo "FORCE PUSHING DIAGNOSTICS TO GITHUB"
echo "=========================================="
echo ""

# Find the latest diagnostics directory
LATEST_DIAG=$(ls -td diagnostics_* 2>/dev/null | head -1)

if [ -z "$LATEST_DIAG" ]; then
    echo "❌ No diagnostics directory found"
    exit 1
fi

echo "Found diagnostics: $LATEST_DIAG"
echo ""

# Step 1: Stash everything
echo "[1] Stashing all changes..."
git stash push -u -m "Auto-stash before diagnostic push $(date +%s)" 2>/dev/null || true

# Step 2: Reset to match remote
echo "[2] Resetting to match remote..."
git fetch origin main
git reset --hard origin/main 2>/dev/null || git reset --hard HEAD

# Step 3: Add diagnostics
echo "[3] Adding diagnostics..."
git add "$LATEST_DIAG"/* "$LATEST_DIAG" 2>/dev/null || true

# Step 4: Commit
echo "[4] Committing diagnostics..."
git commit -m "Diagnostic data collection: $(basename $LATEST_DIAG)" 2>/dev/null || echo "Already committed"

# Step 5: Push (with force-with-lease for safety)
echo "[5] Pushing to GitHub..."
if git push origin main 2>&1; then
    echo ""
    echo "✅ SUCCESS: Diagnostics pushed to GitHub"
    echo "Directory: $LATEST_DIAG"
else
    echo ""
    echo "⚠️  Regular push failed, trying force-with-lease..."
    git push --force-with-lease origin main 2>&1 && echo "✅ Pushed with force-with-lease" || echo "❌ Push failed"
fi

echo ""
echo "Done. Check GitHub for the diagnostics."
