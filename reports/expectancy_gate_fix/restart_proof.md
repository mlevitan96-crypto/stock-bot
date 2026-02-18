# Expectancy gate fix — Restart proof

**Date:** 2026-02-18

## Git pull
- Exit code: 0
- HEAD: 085537ab99bf
```
From https://github.com/mlevitan96-crypto/stock-bot
 * branch            main       -> FETCH_HEAD
   d4f694c..085537a  main       -> origin/main
Updating d4f694c..085537a
Fast-forward
 main.py                                            |  6 +++-
 .../20260218_baseline_v5_verification.md           | 28 +++++++++++++++
 ...0218_exit_quality_emission_proof_postrestart.md | 40 ++++++++++++++++++++++
 .../20260218_paper_restart_proof.md                | 23 +++++++++++++
 .../20260218_paper_restart_snapshot_before.md      | 25 ++++++++++++++
 .../20260218_restart_and_join_plan_review.md       | 35 +++++++++++++++++++
 .../phase9_data_integrity/20260218_signoff_v5.md   | 24 +++++++++++++
 scripts/analysis/attribution_loader.py             | 18 ++++++++--
 src/exit/exit_attribution.py                       |  7 ++++
 9 files changed, 203 insertions(+), 3 deletions(-)
 create mode 100644 reports/phase9_data_integrity/20260218_baseline_v5_verification.md
 create mode 100644 reports/phase9_data_integrity/20260218_exit_quality_emission_proof_postrestart.md
 create mode 100644 reports/phase9_data_integrity/20260218_paper_restart_proof.md
 create mode 100644 reports/phase9_data_integrity/20260218_paper_restart_snapshot_before.md
 create mode 100644 reports/phase9_data_integrity/20260218_restart_and_join_plan_review.md
 create mode 100644 reports/phase9_data_integrity/20260218_signoff_v5.md

```

## Restart (no overlay)
- Restart exit code: 0
- No GOVERNED_TUNING_CONFIG in state: **True**

## tmux ls
```
clawdbot: 1 windows (created Thu Jan 29 23:28:35 2026)
stock_bot_paper_run: 1 windows (created Wed Feb 18 19:28:15 2026)
trading: 1 windows (created Sat Dec 13 20:52:28 2025)
```

## tmux capture-pane (stock_bot_paper_run)
```
[CONFIG] Loaded theme_risk.json: ENABLE_THEME_RISK=True, MAX_THEME_NOTIONAL_USD=
$150,000
2026-02-18 19:28:19,005 [CACHE-ENRICH] INFO: Starting cache enrichment cycle
[MOCK-SIGNAL] Mock signal injection loop started (every 15 minutes)
[MAIN] Mock signal injection loop started
DEBUG: Worker loop STARTED (thread 131095070246592)
DEBUG: SIMULATE_MARKET_OPEN=False, stop_evt.is_set()=True
DEBUG: Worker loop EXITING (stop_evt was set)
======================================================================
  STARTUP CONTRACT CHECK
======================================================================
✅ Composite scoring smoke test passed (score: 2.111)
✅ V2 components present in scoring output
✅ Live cache smoke test passed (_top_net_impact: 1.646)

----------------------------------------------------------------------
⚠️   Warnings (1):
   Contract validator not available: No module named 'internal_contract_validato
r'

======================================================================
  ✅ STARTUP CHECK PASSED - READY TO TRADE
======================================================================
```

## state/live_paper_run_state.json
```
{
  "status": "live_paper_run_started",
  "timestamp": 1771442898,
  "details": {
    "trading_mode": "paper",
    "process": "python3 main.py",
    "session": "stock_bot_paper_run",
    "governed_tuning_config": ""
  }
}
```