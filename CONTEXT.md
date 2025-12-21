# Trading Bot - Project Context

> **🔴 CRITICAL: ALWAYS check [MEMORY_BANK.md](MEMORY_BANK.md) FIRST for complete project context, common issues, solutions, and best practices before making any changes.**

## Quick Overview

**Project:** Stock Trading Bot  
**Repository:** https://github.com/mlevitan96-crypto/stock-bot  
**Environment:** Ubuntu droplet, Python 3.12, deployed via `deploy_supervisor.py`

## Core Components

- **`main.py`**: Main trading logic, position management, entry/exit decisions
- **`dashboard.py`**: Web UI (port 5000) - positions, SRE monitoring, executive summary
- **`deploy_supervisor.py`**: Process manager for all services
- **`sre_monitoring.py`**: Health monitoring for signals, APIs, execution
- **`comprehensive_learning_orchestrator.py`**: ML-based parameter optimization

## Critical Information

**For complete details on any topic, see [MEMORY_BANK.md](MEMORY_BANK.md):**

- **Environment Setup**: Critical env vars, Python environment, dependencies
- **Deployment Procedures**: Standard deployment, quick restart, troubleshooting
- **Common Issues & Solutions**: 6+ documented issues with step-by-step solutions
- **Architecture Patterns**: Signal flow, trade execution, exit criteria, displacement logic
- **SRE Monitoring**: Health endpoints, signal categories, status levels
- **Diagnostic Scripts**: Complete reference of all diagnostic tools
- **Quick Reference Commands**: Common commands for checking status

## Before Making Changes

1. **Read [MEMORY_BANK.md](MEMORY_BANK.md)** - Contains all project knowledge
2. **Check Common Issues** - May already have a documented solution
3. **Review Deployment Best Practices** - Follow SDLC process
4. **Run Verification Scripts** - Use diagnostic tools before/after changes

## Key Files Reference

| File | Purpose | See Memory Bank Section |
|------|---------|------------------------|
| `main.py` | Core trading logic | Architecture Patterns |
| `dashboard.py` | Web dashboard | Project Overview |
| `deploy_supervisor.py` | Process manager | Deployment Procedures |
| `sre_monitoring.py` | Health monitoring | SRE Monitoring |
| `MEMORY_BANK.md` | **Complete knowledge base** | **ALL SECTIONS** |

## Important Notes

- **Environment Variables**: Loaded by Python via `load_dotenv()`, NOT visible in shell (this is expected)
- **Deployment**: Always use `FIX_AND_DEPLOY.sh` for standard deployments
- **Code Changes**: Dashboard must be restarted to load new Python code
- **Git Conflicts**: Use `git stash` and `git reset --hard origin/main` if needed

## Quick Links

- **[MEMORY_BANK.md](MEMORY_BANK.md)** - Complete project knowledge base
- **[DEPLOYMENT_BEST_PRACTICES.md](DEPLOYMENT_BEST_PRACTICES.md)** - SDLC process
- **[README.md](README.md)** - Quick start guide

---

**Remember: [MEMORY_BANK.md](MEMORY_BANK.md) contains the complete context. Check it first!**




