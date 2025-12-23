#!/bin/bash
# Resolve git conflicts and setup GitHub export workflow

cd ~/stock-bot

echo "=================================================================================="
echo "RESOLVING GIT CONFLICTS AND SETTING UP EXPORT WORKFLOW"
echo "=================================================================================="
echo ""

# 1. Check what's blocking
echo "1. Checking git status..."
if git status --porcelain | grep -q "RESTART_BOT_NOW.sh"; then
    echo "  ⚠️  Local changes detected in RESTART_BOT_NOW.sh"
    echo ""
    echo "  Options:"
    echo "    a) Stash changes (save for later)"
    echo "    b) Discard changes (use remote version)"
    echo "    c) Commit changes first"
    echo ""
    read -p "  Choose (a/b/c) [default: a]: " choice
    choice=${choice:-a}
    
    case $choice in
        a|A)
            echo "  Stashing local changes..."
            git stash push -m "Local changes to RESTART_BOT_NOW.sh"
            echo "  ✓ Changes stashed"
            ;;
        b|B)
            echo "  Discarding local changes..."
            git checkout -- RESTART_BOT_NOW.sh
            echo "  ✓ Changes discarded"
            ;;
        c|C)
            echo "  Committing local changes..."
            git add RESTART_BOT_NOW.sh
            git commit -m "Local changes to RESTART_BOT_NOW.sh"
            echo "  ✓ Changes committed"
            ;;
    esac
fi

# 2. Pull latest
echo ""
echo "2. Pulling latest from GitHub..."
git pull origin main || {
    echo "  ❌ Git pull failed"
    exit 1
}
echo "  ✓ Pulled latest changes"

# 3. Make scripts executable
echo ""
echo "3. Making scripts executable..."
chmod +x push_to_github.sh export_for_analysis.sh setup_github_export.sh 2>/dev/null || true
echo "  ✓ Scripts are now executable"

# 4. Add GitHub token to .env if not exists
echo ""
echo "4. Configuring GitHub token..."
if [ -f .env ] && grep -q "GITHUB_TOKEN" .env; then
    echo "  ✓ GITHUB_TOKEN already in .env"
else
    echo "  Adding GITHUB_TOKEN to .env..."
    echo "" >> .env
    echo "# GitHub token for export workflow" >> .env
    echo "GITHUB_TOKEN=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" >> .env
    echo "  ✓ GITHUB_TOKEN added to .env"
fi

# 5. Configure git if needed
echo ""
echo "5. Configuring git..."
if ! git config user.name > /dev/null 2>&1; then
    git config user.name "mlevitan96"
    echo "  ✓ Git user.name configured"
fi

if ! git config user.email > /dev/null 2>&1; then
    git config user.email "mlevitan96@gmail.com"
    echo "  ✓ Git user.email configured"
fi

# 6. Test the setup
echo ""
echo "6. Testing setup..."
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
echo "  ./export_for_analysis.sh full      # Export everything"
echo ""
echo "Then ask the AI to analyze the files from GitHub!"
echo ""
