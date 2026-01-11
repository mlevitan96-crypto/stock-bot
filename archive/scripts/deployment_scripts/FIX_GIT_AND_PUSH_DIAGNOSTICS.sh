#!/bin/bash
# Fix git non-fast-forward and push diagnostics

cd ~/stock-bot

echo "Fixing git and pushing diagnostics..."

# Pull with rebase to integrate remote changes
git pull --rebase origin main

# Now push diagnostics
git push origin main

echo "✅ Diagnostics pushed to GitHub"
