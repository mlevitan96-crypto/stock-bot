# Droplet Backtest Run — Summary (Cursor)

**Run ID:** `alpaca_backtest_20260222T022321Z`  
**Source:** Droplet (canonical). Artifacts fetched via `scripts/run_alpaca_backtest_orchestration_via_droplet.py --fetch-only alpaca_backtest_20260222T022321Z`.  
**Verdict:** BACKTEST_RUN_OK | Governance: PASS | Board: ACCEPT

---

## 1. Outcome at a glance

| Metric | Value |
|--------|--------|
| **Net PnL (USD)** | 16,623.74 |
| **Trades** | 10,715 |
| **Win rate (%)** | 51.47 |
| **Min exec score (config)** | 1.8 |
| **Data** | Alpaca 1m snapshot (lab-mode) |

---

## 2. Score vs profitability (min_exec_score tuning)

- **All executed trades** fell in the **(1.5, 2.0]** score band (min_exec_score 1.8).
- That band is **profitable**: 10,715 trades, 51.47% win rate, **+$16,623.74** net PnL, **~$1.55** avg PnL per trade.
- **Recommendation (from pipeline):** Keep min_exec_score at or above the lower edge of the profitable band (e.g. ≥ 1.5); current 1.8 is consistent with that.
- Higher bands (2.0–2.5, 2.5–3.0, …) had **no trades** in this run — either no signals in those ranges or different data/snapshot; worth checking in future runs if raising the gate reduces volume too much.

**Artifacts:** `reports/backtests/alpaca_backtest_20260222T022321Z/score_analysis/score_bands.json`, `score_vs_profitability.md`.

---

## 3. Customer advocate

- **Verdict:** Run shows positive PnL.
- **Levers:** Use score band recommendation: keep min_exec_score at or above the lower edge of the profitable band (1.5–2.0).

**Artifact:** `reports/backtests/alpaca_backtest_20260222T022321Z/customer_advocate.md`.

---

## 4. Governance & multi-model

- **Governance:** PASS (provenance, config, metrics, trades, summary_md).
- **Multi-model (prosecutor / defender / SRE / board):** Board verdict ACCEPT; roles run: prosecutor, defender, sre, board.
- **Artifacts:** `reports/governance/alpaca_backtest_20260222T022321Z/backtest_governance_report.json`, `reports/backtests/.../multi_model/board_verdict.md`, prosecutor/defender/sre outputs in same dir.

---

## 5. Provenance

- **Git commit (on droplet):** `7689ac095900440be0f73fafcfea35a6353994b3`
- **Timestamp:** 2026-02-22T02:23:22Z
- **Config:** lab_mode true, min_exec_score 1.8, snapshot `alpaca_1m_snapshot_20260222T022321Z.tar.gz`

---

## 6. How to re-fetch or re-run

- **Re-fetch this run’s artifacts (no re-run):**  
  `python scripts/run_alpaca_backtest_orchestration_via_droplet.py --fetch-only alpaca_backtest_20260222T022321Z`
- **Full orchestration on droplet (new run):**  
  `python scripts/run_alpaca_backtest_orchestration_via_droplet.py`  
  or detached:  
  `python scripts/run_alpaca_backtest_orchestration_via_droplet.py --detach`

---

*Summary generated for Cursor; run completed on droplet and artifacts synced locally.*
