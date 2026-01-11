#!/bin/bash
# Setup git hook to run investigation on pull
# Run this ONCE on the droplet

cd ~/stock-bot

echo "Setting up git post-merge hook..."

# Create hook directory if it doesn't exist
mkdir -p .git/hooks

# Create post-merge hook
cat > .git/hooks/post-merge << 'HOOKEOF'
#!/bin/bash
# This hook runs after git pull/merge
cd ~/stock-bot

# Only run if run_investigation_on_pull.sh exists
if [ -f "run_investigation_on_pull.sh" ]; then
    chmod +x run_investigation_on_pull.sh
    bash run_investigation_on_pull.sh >> /tmp/investigation_hook.log 2>&1 &
fi
HOOKEOF

chmod +x .git/hooks/post-merge

echo "✅ Git hook installed"
echo ""
echo "The hook will now run automatically on every 'git pull'"
echo ""
echo "To test it, run: git pull origin main"

