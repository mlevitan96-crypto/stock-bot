# Specialist Tier Monitoring - Deployment Guide

## Overview

The Specialist Tier Monitoring system provides comprehensive daily and weekly audit reports that analyze trading performance, regime alignment, and system efficiency. All reports are automatically committed and pushed to GitHub.

## Files Deployed

1. `daily_alpha_audit.py` - Daily performance reports (Mon-Thu)
2. `friday_eow_audit.py` - Friday EOW structural audit
3. `regime_persistence_audit.py` - Weekly regime persistence analysis
4. `specialist_tier_monitoring_orchestrator.py` - Orchestrator with Git integration

## Quick Start

### Run Daily Audit (Mon-Thu)
```bash
python3 daily_alpha_audit.py
# Output: reports/daily_alpha_audit_YYYY-MM-DD.json
```

### Run Friday EOW Audit
```bash
python3 friday_eow_audit.py
# Output: reports/EOW_structural_audit_YYYY-MM-DD.md
```

### Run Regime Persistence Audit
```bash
python3 regime_persistence_audit.py
# Output: reports/weekly_regime_persistence_YYYY-MM-DD.json
```

### Run Orchestrator (Recommended)
```bash
# Automatically runs appropriate audits based on day of week
python3 specialist_tier_monitoring_orchestrator.py

# Force Friday audits on any day
python3 specialist_tier_monitoring_orchestrator.py --force-friday

# Test without Git commit/push
python3 specialist_tier_monitoring_orchestrator.py --skip-git
```

## Scheduling

### Recommended: Cron Job (Post-Market Close)

**Daily (Mon-Thu) - 4:30 PM ET (20:30 UTC):**
```bash
30 20 * * 1-4 cd /root/stock-bot && python3 specialist_tier_monitoring_orchestrator.py
```

**Friday - 4:30 PM ET (20:30 UTC):**
```bash
30 20 * * 5 cd /root/stock-bot && python3 specialist_tier_monitoring_orchestrator.py
```

### Alternative: Systemd Timer

Create `/etc/systemd/system/specialist-monitoring.service`:
```ini
[Unit]
Description=Specialist Tier Monitoring Orchestrator
After=network.target

[Service]
Type=oneshot
User=root
WorkingDirectory=/root/stock-bot
EnvironmentFile=/root/stock-bot/.env
ExecStart=/usr/bin/python3 /root/stock-bot/specialist_tier_monitoring_orchestrator.py
```

Create `/etc/systemd/system/specialist-monitoring.timer`:
```ini
[Unit]
Description=Run Specialist Tier Monitoring daily at market close
Requires=specialist-monitoring.service

[Timer]
OnCalendar=Mon-Fri 20:30:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:
```bash
systemctl enable specialist-monitoring.timer
systemctl start specialist-monitoring.timer
```

## Report Outputs

### Daily Alpha Audit (`reports/daily_alpha_audit_YYYY-MM-DD.json`)
- Today's summary (trades, win rate, P&L)
- Regime performance (today vs weekly average)
- VWAP deviation metrics
- Momentum lead-time metrics
- Liquidity metrics

### Friday EOW Audit (`reports/EOW_structural_audit_YYYY-MM-DD.md`)
- Alpha decay curves (P&L over time)
- Stealth flow effectiveness (100% win rate target)
- Temporal liquidity gate impact
- Greeks decay analysis
- Capacity efficiency (displacement stats)
- Opportunity cost analysis
- Recommendations section

### Regime Persistence Audit (`reports/weekly_regime_persistence_YYYY-MM-DD.json`)
- Current vs dominant regime
- Regime distribution
- Transition analysis and stability score
- Weight alignment assessment
- Recommendations

## Data Requirements

The scripts require the following data files:
- `logs/attribution.jsonl` - Trade outcomes
- `logs/gate.jsonl` - Gate blocking events
- `logs/orders.jsonl` - Order execution data
- `state/blocked_trades.jsonl` - Blocked trade records
- `state/regime_detector_state.json` - Current regime state

## Git Integration

All reports are automatically committed and pushed to `origin/main` with commit messages that:
- Reference MEMORY_BANK.md
- Include report type and date
- Follow format: `"{Report Type} {Date} - MEMORY_BANK.md Specialist Tier Monitoring"`

## Verification

After deployment, verify scripts work:
```bash
# Test daily audit
python3 daily_alpha_audit.py --date 2025-12-31

# Test Friday audit
python3 friday_eow_audit.py --date 2025-12-27  # Last Friday

# Test orchestrator (without Git)
python3 specialist_tier_monitoring_orchestrator.py --skip-git
```

## Status: READY FOR DEPLOYMENT ✅

All scripts tested and verified. Ready to schedule for automated execution.
