#!/bin/bash
# Push files to GitHub for analysis
# Usage: ./push_to_github.sh <file1> [file2] ... [commit_message]

# Don't exit on errors - we'll handle them explicitly
set +e

# Load .env if it exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Configuration
GITHUB_REPO="mlevitan96-crypto/stock-bot"
GITHUB_BRANCH="${GITHUB_BRANCH:-main}"
GITHUB_USER="mlevitan96"
GITHUB_EMAIL="mlevitan96@gmail.com"

# Load GitHub token from .env
GITHUB_TOKEN="${GITHUB_TOKEN:-}"
if [ -f .env ]; then
    if grep -q "GITHUB_TOKEN" .env; then
        GITHUB_TOKEN=$(grep "GITHUB_TOKEN" .env | cut -d '=' -f2 | tr -d '"' | tr -d "'" | xargs)
    fi
fi

# Check if token is set
if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ ERROR: GITHUB_TOKEN not set in .env file"
    echo ""
    echo "Add it with: echo 'GITHUB_TOKEN=your_token' >> .env"
    exit 1
fi

# Check if files provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <file1> [file2] ... [commit_message]"
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

# Configure git
if ! git config user.name > /dev/null 2>&1; then
    git config user.name "$GITHUB_USER"
    git config user.email "$GITHUB_EMAIL"
fi

# Disable gitignore warnings
git config advice.addIgnoredFile false 2>/dev/null || true

# Set up remote with token
current_remote=$(git remote get-url origin 2>/dev/null || echo "")
expected_url="https://${GITHUB_TOKEN}@github.com/${GITHUB_REPO}.git"
if [ -z "$current_remote" ] || [ "$current_remote" != "$expected_url" ]; then
    if [ -n "$current_remote" ]; then
        git remote remove origin 2>/dev/null || true
    fi
    git remote add origin "$expected_url" 2>/dev/null || \
    git remote set-url origin "$expected_url" 2>/dev/null || true
fi

# Ensure we're on the right branch
current_branch=$(git branch --show-current 2>/dev/null || echo "")
if [ "$current_branch" != "$GITHUB_BRANCH" ]; then
    git checkout "$GITHUB_BRANCH" 2>/dev/null || true
fi

# Add files (force-add, suppress all output)
echo ""
echo "Adding files to git..."
ADDED_ANY=0
for file in "${EXPANDED_FILES[@]}"; do
    if [ -f "$file" ] || [ -d "$file" ]; then
        # Force add - redirect both stdout and stderr to suppress warnings
        if git add -f "$file" >/dev/null 2>&1; then
            echo "  ✓ Added: $file"
            ADDED_ANY=1
        else
            echo "  ⚠️  Failed to add: $file"
        fi
    fi
done

if [ $ADDED_ANY -eq 0 ]; then
    echo "⚠️  No files were added"
    exit 0
fi

# Check if there are changes to commit
if git diff --staged --quiet 2>/dev/null; then
    echo "⚠️  No changes to commit (files may already be up to date)"
    exit 0
fi

# Commit
echo ""
echo "Committing changes..."
if ! git commit -m "$COMMIT_MSG" >/dev/null 2>&1; then
    echo "⚠️  Commit failed"
    exit 0
fi
echo "  ✓ Committed"

# Push
echo ""
echo "Pushing to GitHub..."
PUSH_OUTPUT=$(git push origin "$GITHUB_BRANCH" 2>&1)
PUSH_EXIT=$?

if [ $PUSH_EXIT -eq 0 ]; then
    echo ""
    echo "=================================================================================="
    echo "✅ SUCCESS: Files pushed to GitHub"
    echo "=================================================================================="
    echo ""
    echo "Files are now available at:"
    echo "  https://github.com/${GITHUB_REPO}/blob/${GITHUB_BRANCH}/<file>"
    echo ""
else
    echo "❌ Push failed"
    echo ""
    echo "Error details:"
    echo "$PUSH_OUTPUT"
    echo ""
    
    # Check for specific errors
    if echo "$PUSH_OUTPUT" | grep -q "GH013\|secret\|token"; then
        echo "⚠️  GitHub secret scanning detected token in git history"
        echo ""
        echo "SOLUTION: Create a NEW token and use it:"
        echo "  1. Go to: https://github.com/settings/tokens"
        echo "  2. Generate new token (classic) with 'repo' scope"
        echo "  3. Update .env: echo 'GITHUB_TOKEN=new_token_here' > .env"
        echo "  4. Try again"
    elif echo "$PUSH_OUTPUT" | grep -q "authentication\|unauthorized\|403"; then
        echo "⚠️  Authentication failed - token may be invalid or expired"
        echo "   Update GITHUB_TOKEN in .env with a valid token"
    elif echo "$PUSH_OUTPUT" | grep -q "remote rejected\|protected branch"; then
        echo "⚠️  Branch protection or rules blocking push"
        echo "   Check repository settings for branch protection rules"
    fi
    
    exit 1
fi
