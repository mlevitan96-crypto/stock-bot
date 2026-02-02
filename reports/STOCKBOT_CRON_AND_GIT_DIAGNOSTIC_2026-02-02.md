# Stock-bot Cron + Git + Execution Diagnostic Report

**Date:** 2026-02-02
**Generated:** 2026-02-02T23:34:54.781937+00:00

## 1. Detected Path
- `/root/stock-bot`

## 2. Cron State
```
0 * * * * cd ~/stock-bot && ./report_status_to_git.sh >> /tmp/git_sync.log 2>&1
30 20 * * 1-5 cd /root/stock-bot && venv/bin/python specialist_tier_monitoring_orchestrator.py >> logs/orchestrator.log 2>&1
30 20 * * * cd /root/stock-bot && /root/stock-bot/venv/bin/python3 scripts/run_full_telemetry_extract.py >> logs/telemetry_extract.log 2>&1
31 21 * * 1-5 cd /root/stock-bot && /usr/bin/python3 scripts/run_exit_join_and_blocked_attribution_on_droplet.py --date $(date -u +\%Y-\%m-\%d) >> logs/learning_pipeline.log 2>&1
32 21 * * 1-5 cd /root/stock-bot && bash scripts/droplet_sync_to_github.sh >> /root/stock-bot/logs/cron_sync.log 2>&1
30 21 * * 1-5 cd /root/stock-bot && CLAWDBOT_SESSION_ID="stock_quant_eod_$(date -u +\%Y-\%m-\%d)" /usr/bin/python3 board/eod/run_stock_quant_officer_eod.py >> /root/stock-bot/logs/cron_eod.log 2>&1

```

## 3. Script Verification
- board/eod/run_stock_quant_officer_eod.py: not executable (chmod +x board/eod/run_stock_quant_officer_eod.py)
- scripts/run_stock_bot_workflow.py: missing: scripts/run_stock_bot_workflow.py
- scripts/run_wheel_strategy.py: missing: scripts/run_wheel_strategy.py

## 4. Report Generation (EOD --dry-run)
- Exit code: 0
- Stdout: (see below)

```
INFO Calling Clawdbot agent (TODO: model/provider Gemini)...
INFO Dry-run: skipping clawdbot call.
INFO Wrote /root/stock-bot/board/eod/out/stock_quant_officer_eod_2026-02-02.json
INFO Wrote /root/stock-bot/board/eod/out/stock_quant_officer_eod_2026-02-02.md

```

## 5. Git State
- Branch: main

```
On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   board/eod/out/stock_quant_officer_eod_2026-02-02.json
	modified:   board/eod/out/stock_quant_officer_eod_2026-02-02.md
	modified:   data/uw_flow_cache.json
	modified:   profiles.json

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	reports/dashboard_audits/2026-02-02/
	reports/report_2026-02-02.html
	reports/report_2026-02-02.json

no changes added to commit (use "git add" and/or "git commit -a")

```

## 6. Fixes Applied
Fix SSH/key for root; check known_hosts, remote URL

## 7. Next Steps
- Verify cron fires at scheduled times
- Monitor logs/ directory
