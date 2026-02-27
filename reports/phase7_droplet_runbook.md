# Phase 7 — Droplet runbook (exact commands)

**Date:** 2026-02-18

## 1. Run full 30d backtest (with effectiveness + guards + recommendation)

On droplet (SSH):

```bash
cd /root/stock-bot
git fetch --all && git checkout main && git pull --rebase origin main
export OUT_DIR_PREFIX=30d_after_signal_engine_block3g
export BACKTEST_DAYS=7
bash board/eod/run_30d_backtest_on_droplet.sh
```

Runs backtest, effectiveness, regression_guards, profitability_baseline_and_recommend, writes state/latest_backtest_dir.json, commits and pushes.

## 2. Run profitability pipeline on existing backtest dir

```bash
bash board/eod/run_profitability_on_backtest_dir.sh backtests/30d_after_signal_engine_block3g_YYYYMMDD_HHMMSS
```

## 3. Generate extended recommendation

```bash
python3 scripts/governance/generate_recommendation.py --effectiveness-dir backtests/30d_xxx/effectiveness --out backtests/30d_xxx
```

## 4. Compare baseline vs proposed

```bash
bash board/eod/run_profitability_compare_on_droplet.sh --baseline backtests/baseline_dir --proposed backtests/proposed_dir
```

Output: reports/governance_comparison/comparison.json and comparison.md.

## 5. Regression guards only

```bash
python3 scripts/governance/regression_guards.py
```

## 6. Trigger from local (SSH to droplet)

```bash
BACKTEST_DAYS=7 python scripts/run_backtest_on_droplet_and_push.py
```
