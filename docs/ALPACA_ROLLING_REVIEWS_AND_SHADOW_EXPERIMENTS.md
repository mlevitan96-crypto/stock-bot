# Alpaca Rolling Reviews & Shadow Experiments — Inventory & Map

**Purpose:** Code-level inventory of (1) rolling reviews of trades, (2) shadow experiments / shadow policies, and (3) their wiring into governance, CSA, and SRE. **Discovery and documentation only** — no behavior changes, no new cron, no new promotion logic. Alpaca US equities only.

---

## 1. Overview

- **Rolling reviews:** Alpaca has several mechanisms that compute performance or activity over **rolling or windowed** trade/exit data:
  - **EOD Board rolling windows** (1/3/5/7 day) in `board/eod/rolling_windows.py`, used by the 30d/last-N comprehensive review and optionally by the Board.
  - **5-day rolling PnL** in `scripts/performance/update_rolling_pnl_5d.py`, cron every 10 min on droplet; outputs append-only JSONL and audit artifacts.
  - **30-day or last-N-exits comprehensive review** in `scripts/build_30d_comprehensive_review.py` (and droplet runner `run_30d_board_review_on_droplet.py`), which can use either a 30-day calendar window or "last N exits" (e.g. last387) and optionally pulls in a 30-day rolling aggregate from `rolling_windows`.
  - **Trade visibility review** with configurable since-date/since-hours window; **Fast-lane 25-trade cycles** (shadow-only) for rolling PnL per cycle.
  - **Daily intelligence pack** is date-scoped (single day), not multi-day rolling; **weekly** ledger and CSA weekly review consume weekly evidence.

- **Shadow experiments:** Multiple shadow mechanisms exist:
  - **Telemetry shadow variants** (`telemetry/shadow_experiments.py`): writes `logs/shadow.jsonl` with `shadow_variant_decision`; used by post-market analysis; no live orders.
  - **State/shadow cohort shadows (A1, A2, A3, B1, B2, C2):** Scripts under `scripts/shadow/` write `state/shadow/*.json`; `build_shadow_comparison_last387.py` synthesizes `reports/board/SHADOW_COMPARISON_LAST387.json`, which CSA and profitability cockpit consume.
  - **Fast-lane 25-trade shadow:** `run_fast_lane_shadow_cycle.py` / `run_fast_lane_supervisor.py`; rolling 25-trade windows; writes only to `state/fast_lane_experiment/` and logs; dashboard tab "Alpaca Fast-Lane 25-Trade PnL."
  - **Shadow snapshot profiles** (NO-APPLY): `config/shadow_snapshot_profiles.yaml`; snapshot builder writes `logs/signal_snapshots_shadow_<DATE>.jsonl`; outcome attribution and blocked-trade intel can reference shadow deltas.
  - **Intraday shadow exit / exit-lag shadow:** `run_intraday_shadow_exit_surgical.py`, `run_exit_lag_shadow_replay.py` produce exit-lag shadow results per date; used in experiments and backfill.
  - **Self-healing ShadowTradeLogger** logs rejected signals to `data/shadow_trades.jsonl` (shadow-only analysis).
  - **Droplet daily shadow confirmation** reads `logs/shadow.jsonl`, writes `reports/SHADOW_TRADING_CONFIRMATION_YYYY-MM-DD.md`.

- **Governance wiring:** Rolling reviews and shadow outputs feed **CSA** (Chief Strategy Auditor) and **SRE** as follows:
  - **CSA** is invoked every 100 trades (`run_csa_every_100_trades.py`) and optionally for weekly review (`run_csa_weekly_review.py`). It consumes: board review JSON (e.g. `last387_comprehensive_review.json`), **shadow comparison** (`SHADOW_COMPARISON_LAST387.json`), SRE status/events, and automation evidence. If shadow comparison is missing, CSA adds a finding to produce it before promotion.
  - **SRE** produces `SRE_STATUS.json` and `SRE_EVENTS.jsonl`; CSA reads these for escalation and anomaly context. Governance Integrity automation writes `GOVERNANCE_AUTOMATION_STATUS.json`; SRE consumes it for correlation.
  - **Profitability cockpit** (`update_profitability_cockpit.py`) and dashboard load board review and shadow comparison; cockpit and dashboard show "top promotable" from shadow comparison when present.
  - **Daily/weekly reviews:** Daily pack (`run_stockbot_daily_reports.py`) is single-day; weekly board audit runs ledger build, CSA weekly review, persona memos, cockpit update. **Parallel reviews** on droplet build 7d/14d/30d and last100/last387/last750 comprehensive reviews plus A3 shadow per scope, then run CSA once with last387.

---

## 2. Rolling Reviews Inventory

### 2.1 EOD Board rolling windows (1/3/5/7 day)

| Field | Detail |
|-------|--------|
| **Name** | `build_rolling_windows`, `get_rolling_windows_for_date`, `build_signal_survivorship` |
| **File** | `board/eod/rolling_windows.py` |
| **Window(s)** | 1, 3, 5, 7 days (configurable); signal survivorship default 7 days |
| **Inputs** | `logs/attribution.jsonl`, `logs/exit_attribution.jsonl`, `state/blocked_trades.jsonl`, `logs/system_events.jsonl` (signal events) |
| **Outputs** | In-memory dict (win_rate_by_window, pnl_by_window, exit_reason_counts_by_window, blocked_trade_counts_by_window, signal_decay_exit_rate_by_window, windows detail). `build_signal_survivorship` writes `state/signal_survivorship_<date>.json` |
| **Usage** | Called by `build_30d_comprehensive_review.py` (optional 30-day rolling key); used by EOD Board flow when present |
| **Purpose** | Short-horizon PnL, win rate, exit/blocked reason distribution, signal decay exit rate for Board context |

### 2.2 5-day rolling PnL update

| Field | Detail |
|-------|--------|
| **Name** | `update_rolling_pnl_5d.py` (main) |
| **File** | `scripts/performance/update_rolling_pnl_5d.py` |
| **Window(s)** | Last 5 days (unified exits) |
| **Inputs** | `logs/exit_attribution.jsonl`, `logs/attribution.jsonl` (fallback), `state/daily_start_equity.json` (baseline) |
| **Outputs** | `reports/state/rolling_pnl_5d.jsonl` (append-only, pruned by age); `reports/audit/ROLLING_PNL_5D_UPDATE_<timestamp>.json` |
| **Usage** | Cron on droplet: `*/10 * * * *` (deploy via `scripts/performance/deploy_rolling_pnl_on_droplet.py`) |
| **Purpose** | Rolling 5d equity/PnL for charts and CSA-auditable state; no backfill, no smoothing |

### 2.3 30-day / last-N-exits comprehensive review

| Field | Detail |
|-------|--------|
| **Name** | `build_30d_comprehensive_review.py` |
| **File** | `scripts/build_30d_comprehensive_review.py` |
| **Window(s)** | Either 30-day calendar window (configurable days) or **last N exits** (e.g. 387, 5000) from `exit_attribution.jsonl` |
| **Inputs** | `logs/attribution.jsonl`, `logs/exit_attribution.jsonl`, `state/blocked_trades.jsonl`; optional `board.eod.rolling_windows.build_rolling_windows` for 30d key |
| **Outputs** | `reports/board/<basename>.json` and `.md` (e.g. `30d_comprehensive_review`, `last387_comprehensive_review`) — PnL, win rate, exit/blocked distribution, counter-intelligence, learning telemetry, how_to_proceed |
| **Usage** | Droplet: `scripts/run_30d_board_review_on_droplet.py` (pushes script + rolling_windows, runs build, fetches bundle). Also used by `run_parallel_reviews_on_droplet.py` for 7d/14d/30d and last100/last387/last750 |
| **Purpose** | Board input bundle; align learning and board review to same exit cohort; counter-intel and replay readiness |

### 2.4 Trade visibility review

| Field | Detail |
|-------|--------|
| **Name** | `trade_visibility_review.py` |
| **File** | `scripts/trade_visibility_review.py` |
| **Window(s)** | Configurable: `--since-hours` (e.g. 48) or `--since-date YYYY-MM-DD` |
| **Inputs** | `logs/attribution.jsonl` (closed trades), `logs/exit_attribution.jsonl` (telemetry-backed count), `state/direction_readiness.json` |
| **Outputs** | Markdown report (default stdout or `--out`); JSON summary with executed_in_window, telemetry counts |
| **Usage** | Manual / scripted; not cron |
| **Purpose** | Executed trades in window, 100-trade baseline progress, entries/exits/sizing summary |

### 2.5 Fast-lane 25-trade cycles (shadow-only rolling)

| Field | Detail |
|-------|--------|
| **Name** | `run_fast_lane_shadow_cycle.py` |
| **File** | `scripts/run_fast_lane_shadow_cycle.py` |
| **Window(s)** | **25 trades per cycle**; go-forward only (epoch from config, e.g. 2026-03-17) |
| **Inputs** | `logs/exit_attribution.jsonl` (or `logs/alpaca_unified_events.jsonl`); reads from `state/fast_lane_experiment/config.json` |
| **Outputs** | `state/fast_lane_experiment/fast_lane_ledger.json`, `fast_lane_state.json`, `cycles/`; `logs/fast_lane_shadow.log`; optional Telegram via `notify_fast_lane_summary.py` |
| **Usage** | Cron on droplet: cycle every 15 min, supervisor every 4h (`scripts/install_fast_lane_cron_on_droplet.py`) |
| **Purpose** | Rolling 25-trade PnL per cycle; promote single best dimension per cycle (shadow-only); dashboard "Alpaca Fast-Lane 25-Trade PnL" |

### 2.6 Daily intelligence pack (date-scoped, not multi-day rolling)

| Field | Detail |
|-------|--------|
| **Name** | `run_stockbot_daily_reports.py` |
| **File** | `scripts/run_stockbot_daily_reports.py` |
| **Window(s)** | **Single calendar day** (--date YYYY-MM-DD) |
| **Inputs** | attribution, exit_attribution, telemetry, blocked_trades, profitability, regime/universe paths |
| **Outputs** | `reports/stockbot/YYYY-MM-DD/` (STOCK_EOD_SUMMARY, STOCK_*_ATTRIBUTION, STOCK_PROFITABILITY_DIAGNOSTICS, etc.) |
| **Usage** | Cron on droplet (e.g. via `run_cron_for_date_on_droplet.py`); also used by `run_molt_intelligence_expansion` |
| **Purpose** | Unified daily pack for EOD and learning; not a rolling window over multiple days |

### 2.7 Weekly trade decision ledger and summary

| Field | Detail |
|-------|--------|
| **Name** | `build_weekly_trade_decision_ledger.py`; weekly evidence collection |
| **File** | `scripts/audit/build_weekly_trade_decision_ledger.py`; `scripts/audit/collect_weekly_droplet_evidence.py` |
| **Window(s)** | **7 days** (weekly); evidence stage can fetch last N lines for logs |
| **Inputs** | Ledger from exits/attribution/blocked; droplet evidence paths (board review, shadow comparison, governance, SRE) |
| **Outputs** | `reports/audit/WEEKLY_TRADE_DECISION_LEDGER_*.json`, summary; evidence stage fetches artifacts to weekly_evidence_stage |
| **Usage** | Weekly board audit on droplet (`run_weekly_board_audit_on_droplet.py`); collect_weekly_droplet_evidence for evidence bundle |
| **Purpose** | Weekly ledger for CSA weekly review; evidence for governance |

### 2.8 Rolling promotion review (CSA + Board)

| Field | Detail |
|-------|--------|
| **Name** | `run_rolling_promotion_review.py` |
| **File** | `scripts/board/run_rolling_promotion_review.py` |
| **Window(s)** | Defined by input stability and cluster-risk files (date-scoped) |
| **Inputs** | `STABILITY_ANALYSIS_${END_DATE}.json`, `CLUSTER_RISK_OVER_TIME_${END_DATE}.json` |
| **Outputs** | `CSA_BOARD_REVIEW_${END_DATE}.json` (ranked configs, shadow_only scope, no gating) |
| **Usage** | Downstream of stability and cluster risk; read by tools that need top-N promotable ideas |
| **Purpose** | Combine stability and cluster risk for CSA/Board; shadow-only, no auto-promotion |

---

## 3. Shadow Experiments Inventory

### 3.1 Telemetry shadow variants (shadow_variant_decision)

| Field | Detail |
|-------|--------|
| **Name** | `run_shadow_variants` |
| **File** | `telemetry/shadow_experiments.py` |
| **Type** | Shadow variant decisions (would_enter / would_exit / blocked by reason per variant) |
| **Inputs** | live_context, candidates, positions; Config.SHADOW_EXPERIMENTS, SHADOW_MAX_VARIANTS_PER_CYCLE |
| **Outputs** | `logs/shadow.jsonl` (shadow_variant_decision, shadow_variant_summary) |
| **Usage** | Called from engine when SHADOW_EXPERIMENTS_ENABLED; post-market analysis (§7) reads shadow.jsonl → POSTMARKET_SHADOW_ANALYSIS.md, POSTMARKET_shadow_scoreboard.csv |
| **Coupling** | Post-market verdict and "what worked" include shadow decision count; no tuning/promotion logic reads this directly |

### 3.2 State/shadow cohort (A1, A2, A3, B1, B2, C2)

| Field | Detail |
|-------|--------|
| **Name** | `run_a1_shadow.py`, `run_a2_shadow.py`, `run_a3_expectancy_floor_shadow.py`, `run_b1_shadow.py`, `run_b2_shadow.py`, `run_c2_shadow.py`; `run_all_shadows_last387.py` |
| **File** | `scripts/shadow/run_*_shadow.py`; `scripts/shadow/run_all_shadows_last387.py` |
| **Type** | Shadow policy experiments: A1 displacement relax, A2 max positions, A3 expectancy floor, B1/B2 exit timing, C2 good vetoes vs missed winners |
| **Inputs** | Board review / last387 exits, attribution, blocked_trades; A3 uses --since-hours |
| **Outputs** | `state/shadow/A1_shadow.json`, `A2_shadow.json`, `a3_expectancy_floor_shadow.json` (or A3_shadow.json), `B1_shadow.json`, `B2_shadow.json`, `C2_shadow.json`; audit MD in `reports/audit/` (e.g. A1_SHADOW_RESULTS.md) |
| **Usage** | Manual or droplet; `run_all_shadows_last387.py` runs all for last-387; `run_parallel_reviews_on_droplet.py` runs A3 per scope (7d/14d/30d/last100/last387/last750) |
| **Coupling** | **build_shadow_comparison_last387.py** reads state/shadow/* → SHADOW_COMPARISON_LAST387.json; **CSA** and **profitability cockpit** consume shadow comparison; CSA adds finding if shadow comparison missing |

### 3.3 Shadow comparison (last-387)

| Field | Detail |
|-------|--------|
| **Name** | `build_shadow_comparison_last387.py` |
| **File** | `scripts/board/build_shadow_comparison_last387.py` |
| **Type** | Synthesis of all state/shadow/*.json into ranked comparison and nomination (Advance / Hold / Discard) |
| **Inputs** | `state/shadow/*.json` (A1, A2, A3, B1, B2, C2), `reports/board/last387_comprehensive_review.json` (baseline) |
| **Outputs** | `reports/board/SHADOW_COMPARISON_LAST387.json`, `SHADOW_COMPARISON_LAST387.md` |
| **Usage** | Run before CSA when promotion is in scope; run_csa_every_100_trades and run_csa_weekly_review pass it to run_chief_strategy_auditor if present; update_profitability_cockpit and dashboard read it |
| **Coupling** | **CSA** uses it for advance/hold/discard and missing-data findings; **cockpit** and dashboard show top promotable from ranking |

### 3.4 Fast-lane 25-trade shadow (see §2.5)

| Field | Detail |
|-------|--------|
| **Name** | `run_fast_lane_shadow_cycle.py`, `run_fast_lane_supervisor.py` |
| **File** | `scripts/run_fast_lane_shadow_cycle.py`, `scripts/run_fast_lane_supervisor.py` |
| **Type** | Shadow strategy: rolling 25-trade windows, promote best dimension per cycle; 500-trade supervisor summary |
| **Inputs** | exit_attribution / alpaca_unified_events (go-forward from epoch) |
| **Outputs** | state/fast_lane_experiment/; dashboard API `/api/stockbot/fast_lane_ledger` |
| **Usage** | Cron (15 min cycle, 4h supervisor); dashboard tab |
| **Coupling** | Dashboard and cockpit display only; no tuning or promotion logic reads fast_lane_ledger for gating |

### 3.5 Shadow snapshot profiles (NO-APPLY)

| Field | Detail |
|-------|--------|
| **Name** | Snapshot builder with shadow profiles; outcome attribution |
| **File** | `config/shadow_snapshot_profiles.yaml`; `telemetry/snapshot_builder.py`; snapshot outcome attribution report |
| **Type** | Shadow snapshot variants (baseline, emphasize_dark_pool, emphasize_congress, etc.) for composite recompute |
| **Inputs** | Profile multipliers; signal snapshots |
| **Outputs** | `logs/signal_snapshots_shadow_<DATE>.jsonl`; reports such as SNAPSHOT_OUTCOME_ATTRIBUTION_<DATE>.md, BLOCKED_TRADE_INTEL_<DATE>.md (shadow profile deltas) |
| **Usage** | Run via run_snapshot_outcome_attribution_on_droplet; moltbot orchestrator checks NO-APPLY disclaimer |
| **Coupling** | Diagnostic and report-only; no execution gating |

### 3.6 Intraday shadow exit / exit-lag shadow replay

| Field | Detail |
|-------|--------|
| **Name** | `run_intraday_shadow_exit_surgical.py`, `run_exit_lag_shadow_replay.py` |
| **File** | `scripts/audit/run_intraday_shadow_exit_surgical.py`; `scripts/experiments/run_exit_lag_shadow_replay.py` |
| **Type** | Shadow exit timing: surgical exit analysis and exit-lag replay per date |
| **Inputs** | Staged evidence / exit attribution by date |
| **Outputs** | EXIT_LAG_SHADOW_RESULTS_<date>.json and related artifacts; used by run_exit_lag_backfill_days, run_why_we_didnt_win_on_droplet |
| **Usage** | Experiments and backfill; run_exit_lag_from_staged_evidence |
| **Coupling** | Exit-lag multi-day validation produces CSA_EXIT_LAG_MULTI_DAY_VERDICT.json and board packet; SRE note that no live exit logic is modified |

### 3.7 Self-healing ShadowTradeLogger

| Field | Detail |
|-------|--------|
| **Name** | `ShadowTradeLogger`, `get_shadow_logger` |
| **File** | `self_healing/shadow_trade_logger.py` |
| **Type** | Log rejected signals for shadow tracking; analyze_shadow_performance (lookback_days) |
| **Inputs** | Rejected signals (gate_name, signal_score, etc.) |
| **Outputs** | `data/shadow_trades.jsonl`; analyze_shadow_performance returns gate analysis, shadow_trades_count |
| **Usage** | Called when signals are rejected (if used); optional threshold adjustments (apply_threshold_adjustments) — shadow-only |
| **Coupling** | Read-only analysis; no automatic tuning in production path documented here |

### 3.8 Droplet daily shadow confirmation

| Field | Detail |
|-------|--------|
| **Name** | `droplet_shadow_confirmation_payload.py` (report generator) |
| **File** | `reports/_daily_review_tools/droplet_shadow_confirmation_payload.py` |
| **Type** | Daily report: real vs shadow symbol overlap, shadow_executed counts |
| **Inputs** | `logs/shadow.jsonl`, real executed trades (from attribution or equivalent) |
| **Outputs** | `reports/SHADOW_TRADING_CONFIRMATION_YYYY-MM-DD.md` |
| **Usage** | Run via run_droplet_shadow_confirmation (payload runner) |
| **Coupling** | Human/daily review; confirms v2 hypothetical order-intent path and shadow trade enrichment |

### 3.9 Other shadow-related scripts (diagnostics / no gating)

- **scripts/shadow/backfill_replay_artifacts.py** — Backfill ledgers with replay artifacts (shadow-only).
- **scripts/shadow/classify_signal_gates.py**, **inventory_signal_gates.py**, **emit_cluster_recommendations.py**, **emit_promotion_shortlist.py** — Diagnostics/shortlist; no gating.
- **scripts/shadow/run_true_replay_rescore.py** — Decision-grade rescore when true replay is possible (shadow).
- **scripts/verify_alpha_upgrade.py** — Check SHADOW_EXPERIMENTS_ENABLED and shadow.jsonl for shadow_variant_decision.
- **scripts/audit/write_a3_shadow_proof.py** — Writes A3_SHADOW_PROOF.md from state/shadow/a3_expectancy_floor_shadow.json.

---

## 4. Governance Wiring

### 4.1 CSA (Chief Strategy Auditor)

**Persona (canonical detail):** `docs/ALPACA_TIERED_BOARD_REVIEW_DESIGN.md` §8.1 — **Chief Strategy Auditor — Economic Truth Guardian (Alpaca)**. Session-based, low-frequency-aware: durable edges vs lucky sparse wins; certify learning from **live entry/exit intent + realized outcome**; no portfolio, allocation, or execution-timing ownership. **Learning-layer narrative verdicts:** `CSA_LEARNING_UNBLOCKED_LIVE_TRUTH_CONFIRMED`, `CSA_LEARNING_BLOCKED` (with `trade_ids` + missing decision truth), `CSA_PASS_WEAK` (time-weighted risk note). **Hard gates unchanged:** `CSA_VERDICT_*.json` still uses **PROCEED | HOLD | ESCALATE | ROLLBACK** for `enforce_csa_gate.py` and related tooling (see §8.3 of the tiered design doc).

| Input | Source | Used for |
|-------|--------|----------|
| Board review JSON | `reports/board/last387_comprehensive_review.json` (or 30d) | PnL, counter-intel, learning telemetry, how_to_proceed; assumption and missing-data audit |
| Shadow comparison JSON | `reports/board/SHADOW_COMPARISON_LAST387.json` | Advance/hold/discard nomination; risk asymmetry; finding if missing: "Produce shadow comparison before any promotion" |
| SRE status / events | `reports/audit/SRE_STATUS.json`, `SRE_EVENTS.jsonl` | Escalation triggers, anomaly context |
| Automation evidence | `csa_automation_evidence` (GOVERNANCE_AUTOMATION_STATUS, etc.) | Evidence section in findings |
| Context JSON | Optional (e.g. CSA_WEEKLY_CONTEXT_<date>.json for weekly) | Mission-specific context |

**Entry points:**  
- **Every 100 trades:** `run_csa_every_100_trades.py` (called by trading engine via `src/infra/csa_trade_state.py` when trade count hits 100) → `run_chief_strategy_auditor.py` with board review + shadow comparison if present.  
- **Weekly:** `run_csa_weekly_review.py` → same auditor with weekly context, board review, shadow comparison.  
- **Parallel reviews (droplet):** `run_parallel_reviews_on_droplet.py` builds 7d/14d/30d and last100/last387/last750 reviews + A3 shadow per scope, then runs CSA once with last387 board review (no shadow comparison in that single CSA call unless built separately).  
- **Integration verify:** `run_csa_integration_verify_on_droplet.py` runs CSA on droplet with board + shadow comparison paths.

**Outputs:**  
`reports/audit/CSA_FINDINGS_<mission-id>.md`, `CSA_VERDICT_<mission-id>.json`, `CSA_SUMMARY_LATEST.md`, `CSA_VERDICT_LATEST.json`; board report `reports/board/CSA_TRADE_100_<date>.md` for 100-trade runs. Enforce gate: `enforce_csa_gate.py` (blocks on HOLD/ESCALATE/ROLLBACK without risk acceptance).

### 4.2 SRE

**Persona (canonical detail):** `docs/ALPACA_TIERED_BOARD_REVIEW_DESIGN.md` §8.2 — **Site Reliability Engineer — Operational Integrity Sentinel (Alpaca)**. Session-aware telemetry, open/close transitions, overnight state; no strategy or learning-decision ownership. **Learning-pipeline narrative verdicts:** `SRE_LEARNING_PIPELINE_HEALTHY`, `SRE_PIPELINE_DEGRADED` (non-blocking), `SRE_PIPELINE_UNHEALTHY` (blocking). **Machine layer unchanged:** `SRE_STATUS.json`, `SRE_EVENTS.jsonl`, and existing anomaly consumption are still authoritative for automation (see §8.3 of the tiered design doc).

| Input | Source | Used for |
|-------|--------|----------|
| Runtime / service health | Scripts and engine | SRE_STATUS.json, SRE_EVENTS.jsonl |
| GOVERNANCE_AUTOMATION_STATUS.json | Governance Integrity automation | Correlation; SRE writes SRE_AUTOMATION_ANOMALY_<date>.md when anomalies |

**Entry points:**  
- **Anomaly scan:** `scripts/sre/run_sre_anomaly_scan.py` writes SRE_STATUS, SRE_EVENTS; can write SRE_AUTOMATION_ANOMALY when governance status is anomalous.  
- **Day health:** `scripts/sre/run_day_health_audit.py` (SRE_DAY_HEALTH).  
- **CSA** reads SRE status/events for escalation and interpretation; SRE does not run rolling reviews or shadow experiments itself.

### 4.3 Tuning / promotion

- **No automatic promotion:** Governance is review-only; no code path automatically promotes a shadow to live based on rolling reviews or shadow comparison.  
- **Profitability cockpit** (`update_profitability_cockpit.py`) and dashboard display shadow comparison and "top promotable" for human decision.  
- **Rolling promotion review** (`run_rolling_promotion_review.py`) produces CSA_BOARD_REVIEW_${END_DATE}.json (shadow_only scope); consumed by tools that rank promotable ideas, not by auto-promotion.  
- **Fast-lane** is shadow-only; 25-trade PnL and supervisor summary inform human/governance, not live execution.

### 4.4 Daily / weekly review scheduling

| Review | Schedule | Scripts / artifacts |
|--------|----------|---------------------|
| Daily intelligence pack | Cron (date-based) | `run_stockbot_daily_reports.py` → reports/stockbot/YYYY-MM-DD/ |
| Daily review (shadow synthesis) | Manual / scripted | `scripts/daily/synthesize_daily_review.py` → DAILY_REVIEW_<date>.md from artifact index |
| Board actions (EOD) | Manual / droplet | `board/eod/run_stock_quant_officer_eod.py` → board_actions_<date>.json |
| Post-market analysis | Manual / droplet | `run_postmarket_analysis.py` → POSTMARKET_*.md/csv including §7 Shadow |
| Weekly board audit | Manual / scheduled | `run_weekly_board_audit_on_droplet.py`: ledger → CSA weekly → persona memos → cockpit |
| Weekly evidence | Manual / scheduled | `collect_weekly_droplet_evidence.py` fetches board review, shadow comparison, governance, SRE |
| Validate daily governance artifacts | Manual / CI | `validate_daily_governance_artifacts.py` (run window: date + 12h) |

---

## 5. Gaps / Observations (Descriptive Only)

- **Rolling reviews:**  
  - **5d rolling PnL** is written and pruned but not referenced in CSA or Board narrative by default; dashboard may show it if an endpoint is wired.  
  - **1/3/5/7 day rolling windows** are computed inside the 30d/last-N build only when optional `rolling_30_day` is requested (single 30d key in current build); the full 1/3/5/7 set is available from `rolling_windows.py` but not always passed into the board bundle.  
  - **Trade visibility review** and **fast-lane 25-trade** are rolling in nature but not fed into CSA as first-class inputs; fast-lane is dashboard-only for visibility.

- **Shadow experiments:**  
  - **logs/shadow.jsonl** (telemetry shadow variants) is used by post-market analysis and droplet shadow confirmation; it is **not** an input to SHADOW_COMPARISON_LAST387 (which uses state/shadow/*.json from A1–C2). So two separate shadow surfaces: (1) live-cycle variant decisions in shadow.jsonl, (2) cohort shadows A1–C2 in state/shadow and their comparison.  
  - **Shadow comparison** is optional for CSA; when missing, CSA adds a finding but still produces a verdict. So governance can run without any shadow comparison.  
  - **Fast-lane** and **shadow snapshot profiles** are not part of the CSA shadow comparison ranking; they are separate diagnostic/shadow surfaces.

- **Governance:**  
  - **CSA** uses a **static or long-horizon** view when given last387 (or 30d) board review; it does not consume 5d rolling PnL or 1/3/5/7 day rolling windows directly.  
  - **Weekly review** consumes weekly ledger summary and same board/shadow artifacts as 100-trade run; no distinct "rolling weekly metric" beyond the 7-day evidence bundle.  
  - **Parallel reviews** produce multiple scopes (7d/14d/30d, last100/last387/last750) and A3 shadow per scope, but the single CSA run in that flow uses only last387 board review; other scopes are available for manual or future use.

No recommendations in this document — inventory and mapping only.
