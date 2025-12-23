#!/bin/bash
# Push files to GitHub for analysis
# Usage: ./push_to_github.sh <file1> [file2] ... [commit_message]

set -e

# Load .env if it exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Configuration
GITHUB_TOKEN="${GITHUB_TOKEN:-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}"
GITHUB_REPO="mlevitan96-crypto/stock-bot"
GITHUB_BRANCH="${GITHUB_BRANCH:-main}"
GITHUB_USER="mlevitan96"
GITHUB_EMAIL="mlevitan96@gmail.com"

# Check if files provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <file1> [file2] ... [commit_message]"
    echo ""
    echo "Examples:"
    echo "  $0 logs/run.jsonl"
    echo "  $0 state/bot_heartbeat.json 'Update heartbeat for analysis'"
    echo "  $0 logs/*.jsonl 'Export all logs'"
    echo "  $0 data/uw_flow_cache.json state/position_metadata.json 'Export state files'"
    exit 1
fi

# Get commit message (last arg if it doesn't exist as file)
COMMIT_MSG="Export files for analysis"
FILES=()
for arg in "$@"; do
    if [ -f "$arg" ] || [ -d "$arg" ] || [[ "$arg" == *"*"* ]]; then
        FILES+=("$arg")
    else
        COMMIT_MSG="$arg"
    fi
done

# If no files found, use all args except last as files
if [ ${#FILES[@]} -eq 0 ]; then
    FILES=("${@:1:$(($#-1))}")
    if [ $# -gt 1 ] && [ ! -f "${!$#}" ]; then
        COMMIT_MSG="${!$#}"
    fi
fi

# Expand globs
EXPANDED_FILES=()
for file in "${FILES[@]}"; do
    if [[ "$file" == *"*"* ]]; then
        EXPANDED_FILES+=($file)
    elif [ -f "$file" ] || [ -d "$file" ]; then
        EXPANDED_FILES+=("$file")
    else
        echo "⚠️  Warning: $file not found, skipping"
    fi
done

if [ ${#EXPANDED_FILES[@]} -eq 0 ]; then
    echo "❌ No valid files found to push"
    exit 1
fi

echo "=================================================================================="
echo "PUSHING FILES TO GITHUB FOR ANALYSIS"
echo "=================================================================================="
echo ""
echo "Files to push:"
for file in "${EXPANDED_FILES[@]}"; do
    echo "  - $file"
done
echo ""
echo "Commit message: $COMMIT_MSG"
echo ""

# Configure git if not already configured
if ! git config user.name > /dev/null 2>&1; then
    git config user.name "$GITHUB_USER"
    git config user.email "$GITHUB_EMAIL"
    echo "✓ Git configured"
fi

# Set up remote with token if not exists
if ! git remote get-url origin > /dev/null 2>&1 || ! git remote get-url origin | grep -q "$GITHUB_TOKEN"; then
    git remote remove origin 2>/dev/null || true
    git remote add origin "https://${GITHUB_TOKEN}@github.com/${GITHUB_REPO}.git" 2>/dev/null || \
    git remote set-url origin "https://${GITHUB_TOKEN}@github.com/${GITHUB_REPO}.git"
    echo "✓ Git remote configured"
fi

# Ensure we're on the right branch
git checkout "$GITHUB_BRANCH" 2>/dev/null || git checkout -b "$GITHUB_BRANCH"

# Add files
echo ""
echo "Adding files to git..."
for file in "${EXPANDED_FILES[@]}"; do
    if [ -f "$file" ] || [ -d "$file" ]; then
        git add "$file"
        echo "  ✓ Added: $file"
    fi
done

# Check if there are changes
if git diff --staged --quiet; then
    echo ""
    echo "⚠️  No changes to commit (files may already be up to date)"
    exit 0
fi

# Commit
echo ""
echo "Committing changes..."
git commit -m "$COMMIT_MSG" || {
    echo "⚠️  Commit failed (may be no changes)"
    exit 0
}

# Push
echo ""
echo "Pushing to GitHub..."
git push origin "$GITHUB_BRANCH" || {
    echo "❌ Push failed"
    exit 1
}

echo ""
echo "=================================================================================="
echo "✅ SUCCESS: Files pushed to GitHub"
echo "=================================================================================="
echo ""
echo "Files are now available at:"
echo "  https://github.com/${GITHUB_REPO}/blob/${GITHUB_BRANCH}/<file>"
echo ""
echo "You can now ask the AI to analyze these files directly from the repository."
echo ""
