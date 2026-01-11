# New Laptop Setup - Stock Bot Project

This document confirms the setup status on your new Windows laptop.

## ✅ Current Status

### Files & Folders
- ✅ **All project files accessible** - Complete stock-bot codebase visible
- ✅ **Git repository initialized** - `.git` directory present
- ✅ **Remote configured** - `https://github.com/mlevitan96-crypto/stock-bot`

### Git & GitHub Access
- ✅ **Git installed** - Version 2.52.0 at `C:\Program Files\Git\bin\git.exe`
- ✅ **GitHub remote configured** - Origin points to correct repository
- ✅ **Repository accessible** - Can fetch from GitHub
- ⚠️ **Note**: Git not in PATH by default (use helper script to add)

### Python Environment
- ⚠️ **Python not installed locally** - This is OK!
  - The bot runs on a **remote Ubuntu droplet**, not on Windows
  - Python is only needed if you want to run tests locally
  - To install (optional): https://www.python.org/downloads/

### SSH Configuration
- ✅ **SSH config exists** - Located at `%USERPROFILE%\.ssh\config`
- ⚠️ **Verify droplet host** - Check if 'alpaca' host is configured for droplet access

## Quick Start Commands

### Add Git to PATH (Current Session)
```powershell
$env:PATH += ";C:\Program Files\Git\bin"
```

### Run Setup Verification
```powershell
powershell -ExecutionPolicy Bypass -File .\setup_windows.ps1
```

### Basic Git Operations
```powershell
# Add Git to PATH first
$env:PATH += ";C:\Program Files\Git\bin"

# Check status
git status

# Pull latest code
git pull origin main

# Check branches
git branch -a
```

## Project Architecture

**Important**: The bot runs on a **remote Ubuntu droplet**, not on Windows.

- **Development**: Edit code on Windows laptop
- **Deployment**: Push to GitHub, then pull on droplet
- **Execution**: Bot runs on droplet via `deploy_supervisor.py`

## Required Setup on Droplet

The droplet needs these environment variables in `.env` file:

```
UW_API_KEY=your_unusual_whales_api_key
ALPACA_KEY=your_alpaca_api_key
ALPACA_SECRET=your_alpaca_secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets
TRADING_MODE=PAPER
```

See `MEMORY_BANK.md` for complete deployment instructions.

## Helper Scripts

- `setup_windows.ps1` - Comprehensive setup verification
- `add_git_to_path.ps1` - Quick Git PATH helper

## Next Steps

1. ✅ **File Access** - Ready
2. ✅ **Git Access** - Ready (just add to PATH)
3. ✅ **GitHub Access** - Ready
4. ⚠️ **SSH to Droplet** - Verify `~/.ssh/config` has 'alpaca' host
5. ⚠️ **Local Python** - Install only if needed for local testing

## Documentation

- **[MEMORY_BANK.md](MEMORY_BANK.md)** - Complete project knowledge base
- **[CONTEXT.md](CONTEXT.md)** - Quick project overview
- **[README.md](README.md)** - Deployment guide
- **[requirements.txt](requirements.txt)** - Python dependencies (for droplet)

---

**Status**: ✅ Ready for development work!
