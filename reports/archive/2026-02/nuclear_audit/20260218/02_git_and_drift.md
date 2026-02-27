# 02 Git and drift

## git rev-parse HEAD
539c5f902b2b75658e89b2b40b33ecddd7435399

## git status --short
```
M data/uw_flow_cache.json
 M profiles.json
?? reports/effectiveness_baseline_blame_v3/
?? reports/effectiveness_baseline_blame_v4/
?? reports/effectiveness_baseline_blame_v5/
?? telemetry/paper_mode_intel_state.json
```

## git log -20 --oneline
```
539c5f9 Fix: align expectancy gate to composite exec score
085537a Fix: make attribution ↔ exit_attribution join stable for blame classification
d4f694c Fix: log entry_score for blame classification
515bcf1 Add scripts/analysis: effectiveness reports and attribution loader for baseline v3
9b6c638 Fix: ensure exit_quality_metrics emitted for giveback computation
1b1a218 30-day backtest after intelligence overhaul — Wed Feb 18 04:09:33 UTC 2026
9ac7b44 30-day backtest after intelligence overhaul — Wed Feb 18 04:07:12 UTC 2026
9fe7b48 30-day backtest after intelligence overhaul — Wed Feb 18 04:06:54 UTC 2026
b19c169 30-day backtest after intelligence overhaul — Wed Feb 18 03:30:00 UTC 2026
aec48db 30-day backtest after intelligence overhaul — Wed Feb 18 03:29:54 UTC 2026
88e121c 30-day backtest after intelligence overhaul — Wed Feb 18 00:21:03 UTC 2026
5e22b85 EOD report for 2026-02-17 (auto-confirmed and pushed)
c724871 Fix EOD sync: add board/eod/out/DATE/ to git; do not block push on audit failure
7b2d444 Daily Alpha Audit 2026-02-17 - MEMORY_BANK.md Specialist Tier Monitoring
1d615db AI leverage: OpenClaw Molt synthesis, daily checklist, molt_last_run.json
c3f88ab Deploy: pkill dashboard before restart to avoid stale PID on 5000; MEMORY_BANK dashboard deploy and top-strip notes
f9564e3 Wheel: raise limits (5 concurrent, 12 max), dashboard Strategy column + Wheel tab open positions
24a7857 Entry-score: document never-enter-with-0; add comment in submit_entry gate
aa8f3e9 Entry-score fix: pending-fill persistence, recovery helper, reconciliation paths set entry_score
76c3c24 Daily Alpha Audit 2026-02-16 - MEMORY_BANK.md Specialist Tier Monitoring
```

## Local modifications (git diff name-only)
```
data/uw_flow_cache.json
profiles.json
```