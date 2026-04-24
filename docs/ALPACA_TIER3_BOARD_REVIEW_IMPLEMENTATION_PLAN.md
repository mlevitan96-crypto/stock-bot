# Alpaca Tier 3 Board Review — Implementation Plan (Phase 1)

**Status:** Plan only. No code until CSA + SRE approve.  
**Scope:** Tier 3 (long-horizon) Board Review + Packet Generation. Alpaca-native; single-venue (Alpaca) scope.  
**Constraints:** No cron, no promotion logic, no convergence logic, no heartbeat, no Telegram.

---

## 1. Tier 3 Inputs

| Input | Path (repo root) | Required | Fallback / note |
|-------|------------------|----------|------------------|
| last387 comprehensive review | `reports/board/last387_comprehensive_review.json` | Preferred | If missing, try `reports/board/last750_comprehensive_review.json` or `reports/board/30d_comprehensive_review.json`; else packet marks "Tier 3 review missing" |
| Shadow comparison | `reports/board/SHADOW_COMPARISON_LAST387.json` | No | If missing: include section "Shadow comparison not run; required before promotion." |
| Weekly ledger summary | `reports/audit/WEEKLY_TRADE_DECISION_LEDGER_SUMMARY_<date>.json` | No | Optional; date = --date or today; if missing omit weekly summary |
| CSA verdict (latest) | `reports/audit/CSA_VERDICT_LATEST.json` | No | If missing: "CSA verdict not available" |
| CSA summary (latest) | `reports/audit/CSA_SUMMARY_LATEST.md` | No | If missing: omit or link to verdict only |
| SRE status | `reports/audit/SRE_STATUS.json` | No | If missing: "SRE status not available" |
| SRE events (tail) | `reports/audit/SRE_EVENTS.jsonl` | No | Read last N lines (e.g. 20) for packet appendix |
| Governance automation | `reports/audit/GOVERNANCE_AUTOMATION_STATUS.json` | No | If present, include anomalies_detected in SRE section |
| CSA_BOARD_REVIEW (promotable ideas) | `reports/board/CSA_BOARD_REVIEW_<date>.json` (glob) | No | Optional; if present include one-line summary |

All paths relative to repo root (or --base-dir). No reads from any path outside repo; no cross-repo paths.

---

## 2. Packet Structure (Tier 3 focus)

1. **Cover**
   - Title: "Alpaca Tier 3 Board Review"
   - Generated timestamp (UTC ISO8601)
   - Base directory used
   - List of inputs loaded (present/missing)

2. **Tier 3 summary**
   - Scope (e.g. last387 / last750 / 30d) and window_start, window_end
   - Total PnL, win rate, total exits, blocked_total (from comprehensive review)
   - Weekly ledger one-liner if available
   - Shadow comparison nomination (Advance/Hold/Discard) if available
   - CSA verdict summary (verdict, confidence) if available

3. **Executed trades and attribution**
   - From comprehensive review: pnl, total_trades, total_exits, win_rate, avg_hold_minutes
   - Link to canonical logs (exit_attribution, attribution) as paths only
   - by_direction (long/short) if present

4. **Blocked trades and counter-intelligence**
   - blocked_total, blocking_patterns (top N), opportunity_cost_ranked_reasons (top N) from comprehensive review
   - If no review: "No comprehensive review data."

5. **Shadow comparison**
   - ranked_by_expected_improvement, nomination, risk_flags (excerpt), persona_verdicts (excerpt)
   - If missing: "Shadow comparison not run; required before promotion."

6. **Learning and replay readiness**
   - learning_telemetry from comprehensive review (total_exits_in_scope, telemetry_backed, pct_telemetry, ready_for_replay)
   - how_to_proceed bullets
   - If no review: omit or "N/A"

7. **SRE and automation**
   - SRE_STATUS overall_status (or "not available")
   - GOVERNANCE_AUTOMATION_STATUS anomalies_detected if present
   - Link to SRE_EVENTS (path) and note "See reports/audit/SRE_EVENTS.jsonl for tail."

8. **Appendices (optional)**
   - List of optional artifact paths (e.g. POSTMARKET_*, SHADOW_TRADING_CONFIRMATION_*) — paths only, no content load to avoid scope creep in Phase 1

---

## 3. File Outputs

| Output | Path | Format |
|--------|------|--------|
| Board Review MD | `reports/ALPACA_BOARD_REVIEW_<YYYYMMDD>_<HHMM>/BOARD_REVIEW.md` | Markdown |
| Board Review JSON | `reports/ALPACA_BOARD_REVIEW_<YYYYMMDD>_<HHMM>/BOARD_REVIEW.json` | JSON (structured payload for downstream) |
| State file | `state/alpaca_board_review_state.json` | JSON: last_run_ts, last_packet_dir, last_scope, inputs_present (keys), optional run_id |

Directory name uses UTC. State file updated only on successful write of both MD and JSON. No other files created (no cron, no heartbeat file).

---

## 4. Script to Create

**Path:** `scripts/run_alpaca_board_review_tier3.py`

**Behavior:**
- Parse args: `--base-dir` (default repo root), `--date` (YYYY-MM-DD for weekly ledger lookup), `--force` (allow run even if state suggests recent run), `--dry-run` (load inputs, build payload in memory, print summary; do not write files or state).
- Resolve base_dir; ensure reports/ and state/ exist under base.
- Load all Tier 3 inputs (read-only); never write to logs/, trading config, or Alpaca API.
- Build BOARD_REVIEW.json payload (nested dict: cover, tier3_summary, executed_attribution, blocked_counterintel, shadow_comparison, learning_replay, sre_automation, appendices_paths).
- Build BOARD_REVIEW.md from same data (sections 1–8 above).
- Create directory `reports/ALPACA_BOARD_REVIEW_<ts>/`, write BOARD_REVIEW.md and BOARD_REVIEW.json.
- Update `state/alpaca_board_review_state.json` with last_run_ts, last_packet_dir, last_scope, inputs_present.
- Exit 0 on success; exit 1 on write error or missing required path when --force not used and no fallback. In dry-run: exit 0 after printing; no writes.

**Idempotency:** Each run creates a new timestamped directory; state overwritten. No cron; manual or scripted invocation only.

**Safety:** Read-only from existing Alpaca paths. No import of trading engine, no broker calls, no promotion logic.

---

## 5. Testing Plan

1. **Dry run**
   - `python3 scripts/run_alpaca_board_review_tier3.py --force --dry-run`
   - Expect: exit 0; printed summary of inputs loaded and payload keys; no new files.

2. **Full run**
   - `python3 scripts/run_alpaca_board_review_tier3.py --force`
   - Expect: new directory under reports/ALPACA_BOARD_REVIEW_*; BOARD_REVIEW.md and BOARD_REVIEW.json present; state/alpaca_board_review_state.json updated; exit 0.

3. **CSA review of packet**
   - CSA persona reviews BOARD_REVIEW.md and BOARD_REVIEW.json for completeness, correctness, and adversarial concerns (missing surfaces, misleading summary). Verdict: ACCEPT or REVISE.

4. **SRE review**
   - SRE persona validates: artifact paths under repo; no writes to live trading paths; idempotency and no side effects. Verdict: OK or FIX REQUIRED.

5. **Verification artifacts**
   - After run: list reports/ALPACA_BOARD_REVIEW_*/ and state/alpaca_board_review_state.json in a short verification note (e.g. in MEMORY_BANK or audit doc).

---

## 6. CSA + SRE Review Requirements (Pre-Implementation)

- **CSA:** Adversarial review of this plan: risks, blind spots, missing surfaces, improvements. Approve or reject. If reject → revise plan → re-run CSA.
- **SRE:** Validate file paths, artifact safety, no cross-repo contamination, no risk to live trading, idempotency. Approve or reject. If reject → revise plan → re-run SRE.
- **Cursor:** Must not proceed to code until both approve.

---

## 7. Out of Scope (Phase 1)

- Tier 1 / Tier 2 packet generation
- Convergence logic
- Heartbeat
- Cron
- Promotion gate changes
- Telegram
- Any non-Alpaca venue reference or shared state
