#!/bin/bash
# Setup GitHub export workflow on droplet
# Run this once to configure the export scripts

cd ~/stock-bot

echo "=================================================================================="
echo "SETTING UP GITHUB EXPORT WORKFLOW"
echo "=================================================================================="
echo ""

# 1. Pull latest scripts
echo "1. Pulling latest scripts from GitHub..."
git pull origin main || {
    echo "⚠️  Git pull failed - you may need to resolve conflicts first"
    exit 1
}

# 2. Make scripts executable
echo ""
echo "2. Making scripts executable..."
chmod +x push_to_github.sh export_for_analysis.sh setup_github_export.sh
echo "  ✓ Scripts are now executable"

# 3. Add GitHub token to .env if not exists
echo ""
echo "3. Configuring GitHub token..."
if [ -f .env ] && grep -q "GITHUB_TOKEN" .env; then
    echo "  ✓ GITHUB_TOKEN already in .env"
else
    echo "  Adding GITHUB_TOKEN to .env..."
    echo "" >> .env
    echo "# GitHub token for export workflow" >> .env
    echo "GITHUB_TOKEN=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" >> .env
    echo "  ✓ GITHUB_TOKEN added to .env"
fi

# 4. Configure git if needed
echo ""
echo "4. Configuring git..."
if ! git config user.name > /dev/null 2>&1; then
    git config user.name "mlevitan96"
    echo "  ✓ Git user.name configured"
fi

if ! git config user.email > /dev/null 2>&1; then
    git config user.email "mlevitan96@gmail.com"
    echo "  ✓ Git user.email configured"
fi

# 5. Test the setup
echo ""
echo "5. Testing setup..."
if [ -f push_to_github.sh ] && [ -x push_to_github.sh ]; then
    echo "  ✓ push_to_github.sh is ready"
else
    echo "  ❌ push_to_github.sh not found or not executable"
    exit 1
fi

if [ -f export_for_analysis.sh ] && [ -x export_for_analysis.sh ]; then
    echo "  ✓ export_for_analysis.sh is ready"
else
    echo "  ❌ export_for_analysis.sh not found or not executable"
    exit 1
fi

echo ""
echo "=================================================================================="
echo "✅ SETUP COMPLETE"
echo "=================================================================================="
echo ""
echo "You can now use:"
echo "  ./export_for_analysis.sh quick    # Quick export"
echo "  ./export_for_analysis.sh heartbeat # Export heartbeat files"
echo "  ./export_for_analysis.sh logs      # Export trading logs"
echo "  ./export_for_analysis.sh full       # Export everything"
echo ""
echo "Then ask the AI to analyze the files from GitHub!"
echo ""
