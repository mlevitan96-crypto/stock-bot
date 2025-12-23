# GitHub Export Workflow for Analysis

This workflow allows you to push files from the droplet to GitHub for AI analysis, eliminating the need to copy/paste console output.

## Quick Start

```bash
cd ~/stock-bot
git pull origin main  # Get the new scripts
chmod +x push_to_github.sh export_for_analysis.sh

# Quick export
./export_for_analysis.sh quick

# Or export specific types
./export_for_analysis.sh heartbeat
./export_for_analysis.sh logs
./export_for_analysis.sh full
```

## Scripts

### `push_to_github.sh`
Pushes any files to GitHub for analysis.

**Usage:**
```bash
./push_to_github.sh <file1> [file2] ... [commit_message]
```

**Examples:**
```bash
# Push single file
./push_to_github.sh state/bot_heartbeat.json

# Push multiple files
./push_to_github.sh logs/run.jsonl logs/trading.jsonl "Export logs for analysis"

# Push with glob pattern
./push_to_github.sh logs/*.jsonl "Export all logs"
```

### `export_for_analysis.sh`
Quick exports for common analysis scenarios.

**Usage:**
```bash
./export_for_analysis.sh [analysis_type]
```

**Analysis Types:**
- `heartbeat` or `hb` - Heartbeat files
- `logs` or `log` - Trading logs
- `state` or `st` - State files
- `cache` or `c` - UW cache
- `signals` or `sig` - Signal files
- `full` or `all` - All files (default)
- `quick` or `q` - Quick export (heartbeat + recent logs)

## Security

The GitHub token **MUST** be set in one of these ways:

1. **Recommended:** Add to `.env` file:
   ```bash
   echo "GITHUB_TOKEN=your_github_token_here" >> .env
   ```

2. Or export as environment variable:
   ```bash
   export GITHUB_TOKEN=your_github_token_here
   ```

The script will fail if the token is not set (security best practice).

## Workflow Example

1. **On droplet, export files:**
   ```bash
   ./export_for_analysis.sh heartbeat
   ```

2. **Ask AI to analyze:**
   ```
   Analyze the heartbeat file and logs/run.jsonl from the repo. 
   Why is the heartbeat stale?
   ```

3. **AI can now:**
   - Read full files (not partial console output)
   - See complete data structures
   - Perform deeper analysis
   - Cross-reference multiple files

## Benefits

✅ **No more copy/pasting** - Files pushed directly to GitHub  
✅ **Full file analysis** - AI sees complete data, not snippets  
✅ **Secure** - Token in .env (gitignored)  
✅ **Flexible** - Export any files or use presets  
✅ **Fast** - Quick commands for common scenarios  

## File Handling

The scripts use `git add -f` to force-add files even if they're in `.gitignore`. This is intentional for analysis purposes - you can always remove them later with:

```bash
git rm --cached <file>
git commit -m "Remove exported files"
```

## Troubleshooting

**Push fails:**
- Check GitHub token is valid
- Ensure you have write access to the repo
- Check network connectivity

**Files not found:**
- Verify file paths are correct
- Check if files exist: `ls -la <file>`

**Git errors:**
- Ensure git is configured: `git config user.name` and `git config user.email`
- Check you're on the right branch: `git branch`
