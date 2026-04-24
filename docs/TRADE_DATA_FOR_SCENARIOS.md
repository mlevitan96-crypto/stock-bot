# Trade Data for Scenario and Review Runs

We **can** review trade data and run scenarios (forensic, exit-lag shadow, backfill) in several ways. The right place depends on whether you run **on the droplet** or **locally** and how much history you need.

## 1. On the droplet (authoritative, full history)

**Where the data lives:** Single append-only files on the droplet:

| Path | Purpose |
|------|--------|
| `logs/exit_attribution.jsonl` | One row per closed trade (exit timestamp, PnL, etc.) |
| `reports/state/exit_decision_trace.jsonl` | Unrealized PnL snapshots for exit-lag analysis |
| `state/blocked_trades.jsonl` | Blocked trade events |
| `logs/attribution.jsonl` | Entry/close attribution |

**How to run scenarios:** Run the scripts **on the droplet** (SSH or via the droplet runner). They read these paths and filter by `--date`:

- **Forensic:** `python3 scripts/audit/run_why_we_didnt_win_forensic.py --date YYYY-MM-DD`
- **Backfill:** `python3 scripts/experiments/run_exit_lag_backfill_days.py --days N --anchor-date YYYY-MM-DD`
- **Droplet runner (from local):** `python scripts/audit/run_why_we_didnt_win_on_droplet.py --date YYYY-MM-DD` (runs on droplet, then fetches artifacts)

**Retention:** These paths are **retention-protected** (see `docs/DATA_RETENTION_POLICY.md`). They are no longer truncated by the supervisor, so you keep enough history for multi-day backfill and forensics.

---

## 2. Local: weekly evidence stage (after collect)

**Where the data lives:** After pulling from the droplet, a **local copy** of the same layout is written under:

- `reports/audit/weekly_evidence_stage/logs/exit_attribution.jsonl` (last 10k lines)
- `reports/audit/weekly_evidence_stage/reports/state/exit_decision_trace.jsonl` (last 50k lines)
- `reports/audit/weekly_evidence_stage/state/blocked_trades.jsonl` (last 2k lines)
- `reports/audit/weekly_evidence_stage/logs/attribution.jsonl` (last 1.5k lines)

**How to get it:** Run (from repo root, with droplet reachable):

```bash
python scripts/audit/collect_weekly_droplet_evidence.py [--date YYYY-MM-DD]
```

**How to run scenarios locally:** Use `--base-dir` so the forensic reads from the staged copy:

```bash
# After collect, run forensic for any date in the pulled window (e.g. last ~2–3 weeks)
python scripts/audit/run_why_we_didnt_win_forensic.py --date 2026-03-09 --base-dir reports/audit/weekly_evidence_stage
```

Then run surgical and replay with the same `--base-dir` if they support it, or run those on the droplet and fetch artifacts. The backfill script is designed to run **on the droplet** (it needs the full files over many days); for local scenario runs, use forensic + optional surgical/replay with `--base-dir` pointing at `weekly_evidence_stage`.

---

## 3. Local: droplet_data (fetch_droplet_data)

**Where the data lives:** `fetch_droplet_data_and_generate_report.py` writes to `droplet_data/`:

- `droplet_data/attribution.jsonl`
- `droplet_data/blocked_trades.jsonl`
- `droplet_data/exit.jsonl`
- etc.

**Gap:** This script does **not** currently fetch `logs/exit_attribution.jsonl` or `reports/state/exit_decision_trace.jsonl`. So you **cannot** run the “why we didn’t win” forensic or exit-lag backfill from `droplet_data` alone. For scenario runs that need exit_attribution + trace, use **weekly evidence** (above) or run **on the droplet**.

---

## 4. Per-day summaries in the repo (EOD sync)

**Where the data lives:** After EOD and sync, the repo has per-day **summaries** (not full exit-level logs):

- `reports/stockbot/YYYY-MM-DD/` — STOCK_EOD_SUMMARY, STOCK_EQUITY_ATTRIBUTION.jsonl (from attribution, not exit_attribution), STOCK_BLOCKED_TRADES.jsonl, etc.
- `board/eod/out/YYYY-MM-DD/` — EOD board outputs

**Use case:** High-level daily review and dashboards. **Not** sufficient for forensic or exit-lag scenarios, which need full `exit_attribution` and `exit_decision_trace`.

---

## 5. 30d backtest cohort and replay

**Where the data lives:** Scripts that load from **logs on disk** (droplet or local if you have the same layout):

- `scripts/replay/load_30d_backtest_cohort.py` — reads `logs/exit_attribution.jsonl` and `logs/attribution.jsonl` (with optional `--base-dir`).
- `historical_replay_engine.py` — uses `logs/attribution.jsonl`, `data/uw_attribution.jsonl`.
- `scripts/exit_research/run_exit_replay_scenario.py` — uses exit attribution path from config.

**Use case:** Backtests and replay over a 30d (or N-day) window. They need the log files to be present at the chosen base_dir (e.g. on the droplet or in `weekly_evidence_stage` after collect).

---

## Summary: “Can we review trade data and run scenarios?”

| Question | Answer |
|----------|--------|
| On the droplet? | **Yes.** Full trade data is in the retention-protected paths; run forensic/backfill/surgical/replay there (or via the droplet runner from local). |
| Locally with pulled data? | **Yes.** Run `collect_weekly_droplet_evidence.py` to pull exit_attribution + exit_decision_trace + blocked (tail) into `weekly_evidence_stage`, then run forensic with `--base-dir reports/audit/weekly_evidence_stage` for any date in that window. |
| Using only droplet_data/? | **No.** That fetch does not include exit_attribution or exit_decision_trace; add those to the fetch if you want scenario runs from that folder. |
| Using only reports/stockbot/<date>? | **Partial.** Good for daily summaries; not for forensic or exit-lag shadow scenarios. |

**Use previous days/weeks to get a promote verdict (no need to wait):** After pulling evidence, run the full pipeline for every date in the window and then multi-day:

```bash
python scripts/audit/collect_weekly_droplet_evidence.py
python scripts/experiments/run_exit_lag_from_staged_evidence.py
```

That produces `EXIT_LAG_SHADOW_RESULTS_<date>.json` for each date with data, then runs multi-day validation and CSA verdict. Check `reports/audit/CSA_EXIT_LAG_MULTI_DAY_VERDICT.json` and the board packet for promote-or-not. Paper is paper; promote to paper when the evidence supports it.
