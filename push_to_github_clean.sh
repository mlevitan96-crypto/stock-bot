#!/bin/bash
# Push files to GitHub using a clean branch (avoids secret scanning issues)
# Usage: ./push_to_github_clean.sh <file1> [file2] ... [commit_message]

set +e

if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

GITHUB_REPO="mlevitan96-crypto/stock-bot"
GITHUB_BRANCH="export-$(date +%Y%m%d-%H%M%S)"
GITHUB_USER="mlevitan96"
GITHUB_EMAIL="mlevitan96@gmail.com"

GITHUB_TOKEN="${GITHUB_TOKEN:-}"
if [ -f .env ] && grep -q "GITHUB_TOKEN" .env; then
    GITHUB_TOKEN=$(grep "GITHUB_TOKEN" .env | cut -d '=' -f2 | tr -d '"' | tr -d "'" | xargs)
fi

if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ ERROR: GITHUB_TOKEN not set in .env"
    exit 1
fi

if [ $# -eq 0 ]; then
    echo "Usage: $0 <file1> [file2] ... [commit_message]"
    exit 1
fi

COMMIT_MSG="Export files for analysis"
FILES=()
for arg in "$@"; do
    if [ -f "$arg" ] || [ -d "$arg" ] || [[ "$arg" == *"*"* ]]; then
        FILES+=("$arg")
    else
        COMMIT_MSG="$arg"
    fi
done

if [ ${#FILES[@]} -eq 0 ]; then
    FILES=("${@:1:$(($#-1))}")
    if [ $# -gt 1 ] && [ ! -f "${!$#}" ]; then
        COMMIT_MSG="${!$#}"
    fi
fi

EXPANDED_FILES=()
for file in "${FILES[@]}"; do
    if [[ "$file" == *"*"* ]]; then
        EXPANDED_FILES+=($file)
    elif [ -f "$file" ] || [ -d "$file" ]; then
        EXPANDED_FILES+=("$file")
    fi
done

if [ ${#EXPANDED_FILES[@]} -eq 0 ]; then
    echo "❌ No valid files found"
    exit 1
fi

echo "=================================================================================="
echo "PUSHING FILES TO GITHUB (CLEAN BRANCH)"
echo "=================================================================================="
echo ""
echo "Files: ${EXPANDED_FILES[@]}"
echo "Branch: $GITHUB_BRANCH"
echo "Commit: $COMMIT_MSG"
echo ""

# Configure git
if ! git config user.name > /dev/null 2>&1; then
    git config user.name "$GITHUB_USER"
    git config user.email "$GITHUB_EMAIL"
fi

git config advice.addIgnoredFile false 2>/dev/null || true

# Set up remote with token
current_remote=$(git remote get-url origin 2>/dev/null || echo "")
expected_url="https://${GITHUB_TOKEN}@github.com/${GITHUB_REPO}.git"
if [ -z "$current_remote" ] || [ "$current_remote" != "$expected_url" ]; then
    [ -n "$current_remote" ] && git remote remove origin 2>/dev/null || true
    git remote add origin "$expected_url" 2>/dev/null || \
    git remote set-url origin "$expected_url" 2>/dev/null || true
fi

# Create new branch from current HEAD (avoids problematic history)
git checkout -b "$GITHUB_BRANCH" 2>/dev/null || git checkout "$GITHUB_BRANCH" 2>/dev/null || true

# Add files
echo "Adding files..."
ADDED_ANY=0
for file in "${EXPANDED_FILES[@]}"; do
    if [ -f "$file" ] || [ -d "$file" ]; then
        git add -f "$file" >/dev/null 2>&1 && echo "  ✓ $file" && ADDED_ANY=1
    fi
done

[ $ADDED_ANY -eq 0 ] && echo "⚠️  No files added" && exit 0
git diff --staged --quiet 2>/dev/null && echo "⚠️  No changes" && exit 0

# Commit
echo "Committing..."
git commit -m "$COMMIT_MSG" >/dev/null 2>&1 || exit 0

# Push to new branch
echo "Pushing to branch: $GITHUB_BRANCH..."
PUSH_OUTPUT=$(git push -u origin "$GITHUB_BRANCH" 2>&1)
PUSH_EXIT=$?

if [ $PUSH_EXIT -eq 0 ]; then
    echo ""
    echo "=================================================================================="
    echo "✅ SUCCESS: Files pushed to GitHub"
    echo "=================================================================================="
    echo ""
    echo "Branch: $GITHUB_BRANCH"
    echo "Files:"
    for file in "${EXPANDED_FILES[@]}"; do
        echo "  https://github.com/${GITHUB_REPO}/blob/${GITHUB_BRANCH}/$file"
    done
    echo ""
    echo "Switch back to main: git checkout main"
    echo ""
else
    echo "❌ Push failed"
    echo ""
    echo "$PUSH_OUTPUT"
    exit 1
fi
