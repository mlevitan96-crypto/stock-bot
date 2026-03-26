# Dashboard Data Accuracy Audit — CSA / Board / SRE

**Scope:** Every tab, every number. Accuracy = real and consistent with source of truth; no stale-but-matching numbers.

**Audit time (UTC):** 2026-03-06T20:14:15.739845+00:00
**Today (UTC):** 2026-03-06
**Environment:** Droplet (`/root/stock-bot`)

### Verdict (accuracy and real numbers)

- **Learning & Readiness:** Numbers are **real**. `direction_readiness.json` is fresh (<24h), and `all_time_exits` (2032) matches `exit_attribution.jsonl` line count. Last-100 telemetry 100/100. No stale mismatch.
- **Profitability & Learning:** **Real.** Dashboard reads production `TRADE_CSA_STATE.json` (not test). `total_trade_events` (2404) matches `trade_events.jsonl` line count. CSA verdict and cockpit present.
- **Closed Trades / Attribution:** **Real.** `attribution.jsonl` and `exit_attribution.jsonl` exist and are written by live flows.
- **Situation strip / Strategy comparison (today):** **Gap.** `reports/2026-03-06_stock-bot_combined.json` is missing on droplet. Those surfaces may show empty or fallback for today until the daily combined report is generated (e.g. `scripts/run_stockbot_daily_reports.py` or equivalent for today).

---

## 1. Source of truth (per metric)

| Dashboard surface | Source of truth | What dashboard reads | Real? |
|-------------------|-----------------|----------------------|-------|
| Learning & Readiness (X/100, all-time exits) | `logs/exit_attribution.jsonl` (cron writes `state/direction_readiness.json`) | `state/direction_readiness.json` | Yes |
| Profitability & Learning (trade count, CSA) | `reports/state/TRADE_CSA_STATE.json` + `reports/audit/CSA_VERDICT_LATEST.json` | reports/state/TRADE_CSA_STATE.json | Yes |
| Closed Trades | `logs/attribution.jsonl` + `logs/exit_attribution.jsonl` | Same | Yes if files exist |
| Situation strip / Strategy comparison (today) | `reports/{today}_stock-bot_combined.json` | Same | No (missing today's combined) |

---

## 2. Cross-checks (consistency)

- **Direction Readiness All Time Matches Exit Attribution Lines:** ✓ Pass
- **Csa State Is Production Not Test:** ✓ Pass
- **Trade Events Log Matches Csa Total:** ✓ Pass

---

## 3. Data source details (droplet)

### `state/direction_readiness.json`
- **Exists:** True
- **Last modified (UTC):** 2026-03-06T20:10:02.045745+00:00
- **all_time_exits:** 2032
- **total_trades:** 100
- **telemetry_trades:** 100
- **Fresh within 24h:** True

### `state/direction_replay_status.json`
- **Exists:** True
- **Last modified (UTC):** 2026-03-06T19:11:33.886686+00:00

### `logs/exit_attribution.jsonl`
- **Exists:** True
- **Last modified (UTC):** 2026-03-06T20:08:00.567429+00:00
- **Line count:** 2032

### `logs/attribution.jsonl`
- **Exists:** True
- **Last modified (UTC):** 2026-03-06T19:52:01.824659+00:00
- **Line count:** 2065

### `reports/state/TRADE_CSA_STATE.json`
- **Exists:** True
- **Last modified (UTC):** 2026-03-06T20:14:14.430680+00:00
- **total_trade_events:** 2404
- **last_csa_mission_id:** CSA_TRADE_100_20260306-201404

### `reports/state/test_csa_100/TRADE_CSA_STATE.json`
- **Exists:** False

### `reports/state/trade_events.jsonl`
- **Exists:** True
- **Line count:** 2404

### `reports/audit/CSA_VERDICT_LATEST.json`
- **Exists:** True
- **Last modified (UTC):** 2026-03-06T20:14:14.120669+00:00
- **mission_id:** CSA_TRADE_100_20260306-002808
- **verdict:** PROCEED

### `reports/board/PROFITABILITY_COCKPIT.md`
- **Exists:** True
- **Last modified (UTC):** 2026-03-06T17:34:10.549094+00:00

### `reports/2026-03-06_stock-bot_combined.json`
- **Exists:** False

---

## 4. Findings (action required if any)

- **MISSING: reports/2026-03-06_stock-bot_combined.json (Situation strip / strategy comparison may be empty for today)**

---

## 5. SRE / Eng oversight checklist

- [x] direction_readiness cron installed and running (9–21 UTC Mon–Fri): verified fresh and all_time_exits matches file.
- [x] TRADE_CSA_STATE is production path (not test_csa_100) on droplet.
- [x] exit_attribution.jsonl is appended by live trading (line count 2032, mtime today).
- [ ] Today's combined report exists when strategy comparison / situation is needed: **MISSING** — run daily reports for today or accept empty/fallback for Situation/Strategy comparison.
- [x] Dashboard auth exemption list includes only read-only, non-sensitive endpoints (per prior audit).

---

## 6. Remediation (missing combined report)

To make Situation strip and Strategy comparison use **real** numbers for today on the droplet:

1. On droplet, ensure the daily combined report is generated for today, e.g.:
   - `python3 scripts/run_stockbot_daily_reports.py --date $(date -u +%Y-%m-%d)` or
   - Whatever job normally produces `reports/{date}_stock-bot_combined.json`.
2. Re-run this accuracy audit after the report exists to confirm.
