# Alpaca Tier 1 + Tier 2 Board Reviews — Implementation Plan (Phase 2)

**Status:** Plan only. No code until CSA + SRE approve.  
**Scope:** Tier 1 (short-horizon) and Tier 2 (medium-horizon) Board Review packet generation. Alpaca-native; single-venue (Alpaca) scope.  
**Constraints:** No cron, no promotion logic, no convergence logic, no heartbeat, no Telegram.

---

## 1. Tier 1 Inputs (Short Horizon)

| Input | Path / source | Required | Notes |
|-------|----------------|----------|--------|
| 1d/3d/5d rolling windows | `board.eod.rolling_windows.build_rolling_windows(base, target_date, [1,3,5])` | Yes (call) | target_date = today UTC; returns pnl_by_window, win_rate_by_window, exit_reason_counts, blocked_trade_counts, signal_decay_exit_rate, windows detail |
| 5d rolling PnL state | `reports/state/rolling_pnl_5d.jsonl` (last line) or latest `reports/audit/ROLLING_PNL_5D_UPDATE_*.json` | No | If missing: "5d rolling PnL not available" |
| Trade visibility (since-hours) | Read `logs/attribution.jsonl`, `logs/exit_attribution.jsonl` for last 48h (configurable); compute executed count, telemetry-backed count | No | Self-contained windowed read; no subprocess to trade_visibility_review |
| Fast-lane 25-trade | `state/fast_lane_experiment/fast_lane_ledger.json` | No | total_trades, cumulative_pnl, cycles (last cycle or summary) |
| Daily pack (today) | `reports/stockbot/<date>/STOCK_EOD_SUMMARY.json` or `.md` if exists | No | date = today UTC; if missing omit |
| Attribution + blocked | Already in rolling_windows output (blocked_trade_counts_by_window, windows_detail) | — | No separate load |

All paths relative to --base-dir (repo root). No writes to logs or config.

---

## 2. Tier 2 Inputs (Medium Horizon)

| Input | Path | Required | Notes |
|-------|------|----------|--------|
| 7d comprehensive review | `reports/board/7d_comprehensive_review.json` | No | If missing: use build_rolling_windows(base, today, [7]) for 7d PnL/win_rate/blocked only |
| 30d comprehensive review | `reports/board/30d_comprehensive_review.json` | No | If missing: section "30d review not found" |
| last100 comprehensive review | `reports/board/last100_comprehensive_review.json` | No | Prefer for "medium" cohort when present |
| Rolling promotion (CSA_BOARD_REVIEW) | Latest `reports/board/CSA_BOARD_REVIEW_*.json` by mtime | No | One-line summary if present |
| Attribution + blocked | Inside comprehensive review JSONs | — | No direct log read for Tier 2 |

Tier 2 script is read-only: only loads existing artifacts. It does not invoke build_30d_comprehensive_review.py (no heavy build). If 7d/30d/last100 JSONs are missing, packet still generated with available data and "missing" markers.

---

## 3. Packet Structure

### Tier 1 packet (fast, reactive)

1. **Cover** — Generated ts, base dir, inputs present (rolling_1_3_5, rolling_pnl_5d, trade_visibility, fast_lane, daily_pack).
2. **Tier 1 summary** — 1d/3d/5d PnL and win rate; 5d rolling state (last point or audit artifact); trade visibility (executed in 48h, telemetry-backed); fast-lane last cycle or cumulative; daily pack present (yes/no).
3. **Short-horizon metrics** — exit_reason_counts_by_window (1d, 3d, 5d excerpt); blocked_trade_counts_by_window (1d, 3d, 5d excerpt); signal_decay_exit_rate_by_window.
4. **Appendices** — Paths to canonical logs and 5d state.

Output: `reports/ALPACA_TIER1_REVIEW_<YYYYMMDD>_<HHMM>/TIER1_REVIEW.md`, `TIER1_REVIEW.json`.

### Tier 2 packet (stability, validation)

1. **Cover** — Generated ts, base dir, inputs present (7d_review, 30d_review, last100_review, csa_board_review).
2. **Tier 2 summary** — Scope(s) available; for each scope: window_start, window_end, total PnL, win rate, total_exits, blocked_total; learning_telemetry (if in review); how_to_proceed (if in review).
3. **Counter-intelligence** — From first available review: opportunity_cost_ranked_reasons (top N), blocking_patterns.
4. **Rolling promotion** — CSA_BOARD_REVIEW summary (ranked_configs count, scope) if present.
5. **Appendices** — Paths to board review artifacts.

Output: `reports/ALPACA_TIER2_REVIEW_<YYYYMMDD>_<HHMM>/TIER2_REVIEW.md`, `TIER2_REVIEW.json`.

Alpaca-native formatting: same style as Tier 3 (MD sections, JSON nested dict). No external non-repo references.

---

## 4. File Outputs

| Output | Path | Format |
|--------|------|--------|
| Tier 1 packet dir | `reports/ALPACA_TIER1_REVIEW_<YYYYMMDD>_<HHMM>/` | — |
| Tier 1 MD | `reports/ALPACA_TIER1_REVIEW_<YYYYMMDD>_<HHMM>/TIER1_REVIEW.md` | Markdown |
| Tier 1 JSON | `reports/ALPACA_TIER1_REVIEW_<YYYYMMDD>_<HHMM>/TIER1_REVIEW.json` | JSON |
| Tier 2 packet dir | `reports/ALPACA_TIER2_REVIEW_<YYYYMMDD>_<HHMM>/` | — |
| Tier 2 MD | `reports/ALPACA_TIER2_REVIEW_<YYYYMMDD>_<HHMM>/TIER2_REVIEW.md` | Markdown |
| Tier 2 JSON | `reports/ALPACA_TIER2_REVIEW_<YYYYMMDD>_<HHMM>/TIER2_REVIEW.json` | JSON |
| State file | `state/alpaca_board_review_state.json` | JSON: merge existing state with tier1_last_run_ts, tier1_last_packet_dir, tier2_last_run_ts, tier2_last_packet_dir |

State: read existing state (if any), add/update tier1_* and tier2_* keys, write back. Do not remove Tier 3 keys (last_run_ts, last_packet_dir, last_scope, inputs_present).

---

## 5. Scripts to Create

### scripts/run_alpaca_board_review_tier1.py

- Args: --base-dir, --date (default today UTC), --since-hours (default 48), --force, --dry-run.
- Load: build_rolling_windows(base, date, [1,3,5]) via import or subprocess. Prefer import: add repo to sys.path, `from board.eod.rolling_windows import build_rolling_windows`. Read 5d state (last line of rolling_pnl_5d.jsonl or latest ROLLING_PNL_5D_UPDATE_*.json). Read attribution/exit_attribution for since-hours window (self-contained loop). Read fast_lane_ledger.json. Check daily pack dir for date.
- Build payload (cover, tier1_summary, short_horizon_metrics, appendices_paths).
- Write TIER1_REVIEW.md and TIER1_REVIEW.json to new timestamped dir. Update state (merge). On write failure: exit 1, do not update state.

### scripts/run_alpaca_board_review_tier2.py

- Args: --base-dir, --date (default today UTC), --force, --dry-run.
- Load: 7d_comprehensive_review.json, 30d_comprehensive_review.json, last100_comprehensive_review.json (all optional). Latest CSA_BOARD_REVIEW_*.json by mtime.
- Build payload (cover, tier2_summary, counter_intelligence, rolling_promotion, appendices_paths).
- Write TIER2_REVIEW.md and TIER2_REVIEW.json to new timestamped dir. Update state (merge). On write failure: exit 1, do not update state.

Both scripts: read-only from repo paths; no broker, no config writes, no promotion logic.

---

## 6. Testing Plan

1. **Dry run**  
   `python scripts/run_alpaca_board_review_tier1.py --force --dry-run`  
   `python scripts/run_alpaca_board_review_tier2.py --force --dry-run`  
   Expect: exit 0; printed summary; no files written.

2. **Full run**  
   `python scripts/run_alpaca_board_review_tier1.py --force`  
   `python scripts/run_alpaca_board_review_tier2.py --force`  
   Expect: new dirs under reports/ALPACA_TIER1_REVIEW_* and ALPACA_TIER2_REVIEW_*; MD + JSON in each; state file updated with tier1_* and tier2_*.

3. **CSA review** — CSA persona reviews both packets; verdicts ACCEPT or REVISE.
4. **SRE review** — SRE persona validates artifact completeness and paths; verdicts OK or FIX REQUIRED.

---

## 7. CSA + SRE Review Requirements (Pre-Implementation)

- **CSA:** Adversarial review: risks, blind spots, missing surfaces, improvements. Approve or reject.
- **SRE:** File paths, artifact safety, no cross-repo, no risk to live trading, idempotency. Approve or reject.
- **Cursor:** Must not proceed to code until both approve.

---

## 8. Out of Scope (Phase 2)

- Convergence logic
- Heartbeat
- Cron
- Promotion gate changes
- Telegram
- Any non-Alpaca venue reference
