#!/bin/bash
# One-time fix for push_to_github.sh on droplet
# Run this to fix the export script

cd ~/stock-bot

echo "Fixing push_to_github.sh..."

# Fix 1: Change set -e to set +e (don't exit on warnings)
sed -i 's/^set -e$/set +e/' push_to_github.sh

# Fix 2: Add git config to disable warnings BEFORE git add
sed -i '/# Add files (force-add/i\
# Disable gitignore warnings\
git config advice.addIgnoredFile false 2>/dev/null || true\
' push_to_github.sh

# Fix 3: Change git add to redirect ALL output
sed -i 's/git add -f "\$file" 2>\/dev\/null || true/git add -f "$file" >\/dev\/null 2>\&1 || true/' push_to_github.sh

echo "✓ Script fixed"
echo ""
echo "Now try: ./export_for_analysis.sh quick"
