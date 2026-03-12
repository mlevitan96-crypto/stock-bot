# Quantified Decision Spine — Alpaca Experiment #1

**Experiment:** ALPACA_BASELINE_VALIDATION_AND_METRICS_TRUTH  
**Date:** 2026-03-12  
**Mode:** Analysis-only. No live execution changes.

---

## 1. Data sources

All metrics use **droplet/runtime artifacts only**; no synthetic data.

| Source | Path (repo-relative) | Use |
|--------|----------------------|-----|
| Closed-trade attribution | `logs/attribution.jsonl` | PnL, context per closed trade |
| Exit attribution | `logs/exit_attribution.jsonl` | Exit reason, PnL, components |
| Master trade log | `logs/master_trade_log.jsonl` | Trade IDs, symbol, entry_ts, exit_ts |
| Blocked trades | `state/blocked_trades.jsonl` | Block reason, score, symbol |
| Session baseline | `state/daily_start_equity.json` | Session baseline equity |
| Peak equity | `state/peak_equity.json` | Peak equity for drawdown |
| Executive summary / PnL | Dashboard `/api/executive_summary`, `/api/rolling_pnl_5d` | 24h/7d PnL (when run on droplet) |

---

## 2. Baseline metrics to compute

| Metric | Description | N/A policy |
|--------|-------------|------------|
| **Closed-trade count** | Count of closed trades in window (from attribution or master_trade_log). | Required. If logs missing, report gap and do not claim count. |
| **Total PnL** | Sum of realized PnL over the window. | Required. If attribution/exit_attribution missing, state "N/A — logs missing" and why. |
| **Expectancy per trade** | (Total PnL / closed-trade count) or win-rate–based formula per MEMORY_BANK. | Required when count > 0. If count = 0, report 0 and note "no trades in window". |
| **PnL per session/day** | PnL attributed by calendar day or session (daily_start_equity deltas or attribution by date). | Required when data present. If daily_start_equity or date buckets missing, state "N/A — session boundaries not available" and why. |
| **Slippage summary** | Fill vs signal price and/or time-to-fill from execution/order logs if available. | N/A if no execution logs with fill price and signal price; must state "Slippage N/A — no fill vs signal data in logs". |
| **Drawdown summary** | Peak-to-trough from peak_equity and equity curve. | N/A if peak_equity or equity series missing; must state "Drawdown N/A — peak_equity or equity series missing". |

---

## 3. CSA_REVIEW

- **What “baseline truth” enables later:** A validated baseline (expectancy, PnL/day, slippage, drawdown) is the prerequisite for any profit-impact experiment. Without it, we cannot distinguish strategy effect from data gaps or metric bugs. Opportunity cost of skipping: later experiments become uninterpretable; we may iterate on noise or miss real degradation.
- **What would invalidate conclusions:** Selection bias (e.g. only counting a subset of closed trades), missing trades (attribution or master_trade_log gaps), or mixing time windows. Evidence must cover the full validation window (7 sessions or 500 trades) without silent drops.
- **Evidence required before any profit-impact experiment:** (1) Ledger health PASS (validator exit 0). (2) Metrics computed without gaps for the full window. (3) No silent failures (break alerts = 0). (4) Explicit N/A for any metric that is truly not computable, with reason documented.

---

## 4. SRE_REVIEW

- **Failure modes:** (1) Missing files — attribution.jsonl, exit_attribution.jsonl, or master_trade_log.jsonl truncated/missing. (2) Partial writes — JSONL mid-write on crash. (3) Disk pressure — logs/ or state/ full. (4) Time skew — server time vs exchange/session boundaries. Mitigations: run validators and daily checks; alert on break; do not overwrite ledger; read-only analysis only.
- **Observability (daily):** Run `python scripts/run_alpaca_experiment_1_daily_checks.py`. Watch for break Telegram (invalid or stale ledger). Check that ledger validator exits 0 and that report artifacts (this Decision Spine, batch outputs) exist when expected.
- **Rollback confidence:** High. This experiment is analysis-only; there is no deployment or trading logic to roll back. "Rollback" = stop running completion/break scripts or re-run with corrected data; no live system state changed.

---

## 5. References

- **Experiment definition:** MEMORY_BANK.md — Governance Experiments → Experiment #1
- **Framework:** `docs/QUANTIFIED_GOVERNANCE_EXPERIMENT_FRAMEWORK_ALPACA.md`
- **Ledger:** `state/governance_experiment_1_hypothesis_ledger_alpaca.json`
- **Daily checks:** `python scripts/run_alpaca_experiment_1_daily_checks.py`
- **Completion (when window satisfied):** `python scripts/notify_governance_experiment_alpaca_complete.py --sessions-elapsed N --trades-count M`
