# MEMORY_BANK.md
# Master Operating Manual for Cursor + Trading Bot
# Version: 2026-01-12 (SSH Deployment Verified)

---
# ⚠️ MEMORY BANK — DO NOT OVERWRITE ⚠️
# Cursor MUST load this file before ANY code changes.
# Cursor MUST update this file when ANY new system behavior is added.
# This file is the single source of truth for all system architecture and behavior.
---

---

# 0. CURSOR BEHAVIOR CONTRACT (TOP‑LEVEL GOVERNING RULE)
**Cursor MUST read and follow this section BEFORE doing anything else.  
This section overrides all other rules.**

## 0.1 THE GOLDEN WORKFLOW RULE  
**Every task MUST follow this exact cycle:**

### **USER → CURSOR → GITHUB → DROPLET → GITHUB → CURSOR → USER**

Cursor MUST:
- push all code changes to GitHub  
- trigger droplet deployment immediately  
- wait for deployment + verification to finish  
- pull results back from GitHub  
- analyze results  
- only then respond to the user  

Cursor MUST NOT:
- skip GitHub  
- skip droplet  
- skip verification  
- respond early  
- ask the user to run commands manually  
- assume the droplet is up to date  
- assume GitHub has the latest code  

**NO TASK IS COMPLETE UNTIL THE FULL CYCLE IS COMPLETE.**

---

## 0.2 MANDATORY CURSOR RESPONSIBILITIES  
Cursor MUST:
- ALWAYS push code to GitHub before deployment  
- ALWAYS trigger droplet deployment via SSH  
- ALWAYS wait for verification results  
- ALWAYS pull results from GitHub  
- ALWAYS analyze verification output  
- ALWAYS complete the entire workflow before responding  

Cursor MUST NOT:
- ask the user to run commands  
- ask the user to copy/paste output  
- skip any step  
- report partial completion  
- rely on local files for production data  
- mask errors or hide failures  

---

## 0.3 FAILURE MODE RULE  
If any step fails, Cursor MUST:
1. Stop immediately  
2. Report the failure  
3. Diagnose the cause  
4. Fix the issue  
5. Restart the full workflow  

Cursor MUST NOT:
- continue after a failed step  
- ignore verification failures  
- assume success  

---

# 1. PURPOSE & SCOPE
This document defines:
- how Cursor MUST behave  
- how the trading bot MUST operate  
- how deployments MUST occur  
- how data MUST be sourced  
- how signals MUST be processed  
- how reports MUST be generated  

Cursor MUST treat this document as the **authoritative rule set** for all actions.

---

# 2. PROJECT ARCHITECTURE OVERVIEW

## 2.1 ENTRY POINTS (PRIMARY)
- `deploy_supervisor.py` — orchestrates all services  
- `main.py` — core trading engine  
- `uw_flow_daemon.py` — UW API ingestion  
- `dashboard.py` — monitoring dashboard  
- `heartbeat_keeper.py` — health monitor  

## 2.2 SECONDARY MODULES
- `startup_contract_check.py`  
- `position_reconciliation_loop.py`  
- `risk_management.py`  
- `momentum_ignition_filter.py`  
- `comprehensive_learning_scheduler.py`  
- `v2_nightly_orchestration_with_auto_promotion.py`  

## 2.2.1 MULTI-STRATEGY ARCHITECTURE (ADDITIVE - 2026-01)
- **equity** — Existing UW-driven equity strategy (unchanged logic). `strategies/equity_strategy.py`.
- **wheel** — Options wheel (CSP → CC). `strategies/wheel_strategy.py`.
- Single droplet, single Alpaca paper, single UW, single EOD review. All orders/telemetry tagged with `strategy_id`.
- Config: `config/strategies.yaml`, `config/universe_wheel.yaml`. See `docs/stock-bot_overview.md`, `docs/stock-bot_wheel_strategy.md`, `docs/stock-bot_governance.md`.

## 2.2.2 STRUCTURAL UPGRADE MODULES (ADDITIVE - 2026-01-20)
- `structural_intelligence/market_context_v2.py` — market context snapshot (premarket/overnight + vol term proxy)
- `structural_intelligence/symbol_risk_features.py` — realized vol + beta feature store (per-symbol)
- `structural_intelligence/regime_posture_v2.py` — regime label + posture (log-only context layer)
- (REMOVED) Shadow A/B modules — shadow trading is not supported in v2-only mode.

## 2.3 CONFIG FILES
- `config/registry.py` — **single source of truth**  
- `config/theme_risk.json`  
- `config/execution_router.json`  
- `config/startup_safety_suite_v2.json`  
- `config/uw_signal_contracts.py`  

## 2.4 RUNTIME DIRECTORIES
- `logs/`  
- `state/`  
- `data/`  
- `signals/`  
- `structural_intelligence/`  
- `learning/`  
- `telemetry/`  
- `xai/`  
- `self_healing/`  

---

# 3. GLOBAL RULES (MUST / MUST NOT)

## 3.1 ROOT CAUSE RULE
Cursor MUST:
- fix underlying issues  
- investigate missing data  
- validate assumptions  
- ensure real signals flow end‑to‑end  

Cursor MUST NOT:
- mask errors  
- clear data to hide failures  
- create empty structures to fake health  
- bypass validation  

---

## 3.2 DATA SOURCE RULE (UPDATED)
**Reports MUST always use production data from the droplet.**

Cursor MUST:
- use `ReportDataFetcher`  
- validate data source  
- reject reports with invalid or empty data  
- include data source metadata  

Cursor MUST NOT:
- read local logs  
- read local state files  
- assume local data is production data  

---

## 3.3 SAFETY RULES
Cursor MUST:
- enforce trading arm checks  
- enforce LIVE mode acknowledgment  
- validate notional, price, and buying power  
- prevent division by zero  
- clamp invalid ranges  

Cursor MUST NOT:
- bypass safety checks  
- modify safety logic without explicit instruction  

---

# 4. SIGNAL INTEGRITY CONTRACT

## 4.1 NORMALIZATION RULES
Cursor MUST:
- extract all metadata fields  
- validate structure before processing  
- ensure no missing keys  

Required fields:
- `flow_conv`  
- `flow_magnitude`  
- `signal_type`  
- `direction`  
- `flow_type`  

---

## 4.2 CLUSTERING RULES
Cursor MUST:
- preserve `signal_type`  
- preserve metadata  
- ensure clusters contain real data  

Cursor MUST NOT:
- drop metadata  
- create empty clusters  

---

## 4.3 GATE EVENT RULES
Cursor MUST:
- include `gate_type`  
- include `signal_type`  
- include full context  

Cursor MUST NOT:
- log "unknown" unless truly unknown  

---

## 4.4 COMPOSITE SCORING RULES

See Section 7 (Scoring Pipeline Contract) for detailed scoring rules.

---

# 7. SCORING PIPELINE CONTRACT (SYSTEM HARDENING - 2026-01-10)

## 7.1 SCORING PIPELINE FIXES (PRIORITY 1-4)

### Priority 1: Freshness Decay Configuration
- **Location:** `uw_enrichment_v2.py:234`
- **Constant:** `DECAY_MINUTES = 180` (changed from 45)
- **Rationale:** Reduces score decay from 50% after 45min to 50% after 180min
- **Impact:** Prevents aggressive score reduction for stale data
- **Reference:** See `SIGNAL_SCORE_PIPELINE_AUDIT.md` for full analysis

### Priority 2: Flow Conviction Default
- **Location:** `uw_composite_v2.py:552`
- **Change:** Default `flow_conv` from `0.0` to `0.5` (neutral)
- **Rationale:** Ensures primary component (weight 2.4) contributes 1.2 instead of 0.0 when conviction is missing
- **Impact:** Prevents loss of primary scoring component

### Priority 3: Core Features Always Computed
- **Location:** `main.py:7390-7434`
- **Requirement:** `iv_term_skew`, `smile_slope`, `event_alignment` must always exist
- **Fallback:** If computation fails, default to `0.0` (neutral)
- **Telemetry:** Logs missing core features for monitoring
- **Impact:** Prevents 3 components from contributing 0.0 (potential 1.35 points lost)

### Priority 4: Expanded Intel Neutral Defaults
- **Location:** `uw_composite_v2.py` component functions
- **Requirement:** All V3 expanded components return neutral default (0.2x weight) instead of 0.0 when data missing
- **Components:** congress, shorts_squeeze, institutional, market_tide, calendar, greeks_gamma, ftd_pressure, oi_change, etf_flow, squeeze_score
- **Impact:** Prevents 11 components from contributing 0.0 (potential 4.0 points lost)

## 7.2 SCORE CALCULATION FORMULA

```
composite_raw = (
    flow_component +           # 2.4 * flow_conv (defaults to 0.5 if missing)
    dp_component +             # 1.3 * dp_strength
    insider_component +        # 0.5 * (0.25-0.75)
    iv_component +             # 0.6 * abs(iv_skew) (defaults to 0.0 if missing)
    smile_component +          # 0.35 * abs(smile_slope) (defaults to 0.0 if missing)
    whale_score +              # 0.7 * avg_conv (if detected)
    event_component +          # 0.4 * event_align (defaults to 0.0 if missing)
    motif_bonus +              # 0.6 * motif_strength
    toxicity_component +       # -0.9 * (toxicity - 0.5) (if > 0.5)
    regime_component +         # 0.3 * (regime_factor - 1.0) * 2.0
    # V3 expanded (11 components, neutral default 0.2x weight if missing)
    congress_component +       # 0.9 * strength (or 0.18 if missing)
    shorts_component +         # 0.7 * strength (or 0.14 if missing)
    inst_component +          # 0.5 * strength (or 0.10 if missing)
    tide_component +           # 0.4 * strength (or 0.08 if missing)
    calendar_component +       # 0.45 * strength (or 0.09 if missing)
    greeks_gamma_component +   # 0.4 * strength (or 0.08 if missing)
    ftd_pressure_component +   # 0.3 * strength (or 0.06 if missing)
    iv_rank_component +        # 0.2 * strength (or 0.04 if missing)
    oi_change_component +      # 0.35 * strength (or 0.07 if missing)
    etf_flow_component +       # 0.3 * strength (or 0.06 if missing)
    squeeze_score_component    # 0.2 * strength (or 0.04 if missing)
)

composite_score = composite_raw * freshness  # freshness decays over 180min (not 45min)
composite_score += whale_conviction_boost   # +0.5 if whale detected
composite_score = max(0.0, min(8.0, composite_score))  # Clamp to 0-8
```

## 7.3 SCORE TELEMETRY REQUIREMENTS

- **Module:** `telemetry/score_telemetry.py`
- **State File:** `state/score_telemetry.json`
- **Recording:** After each composite score calculation in `main.py:7565`
- **Tracks:**
  - Score distribution (min, max, mean, median, percentiles, histogram)
  - Component contributions (avg, zero percentage)
  - Missing intel counts (per component)
  - Defaulted conviction count
  - Decay factor distribution
  - Neutral defaults count (per component)
  - Core features missing count

## 7.4 SCORE MONITORING DASHBOARD

- **Endpoints:**
  - `/api/scores/distribution` - Score distribution statistics
  - `/api/scores/components` - Component health statistics
  - `/api/scores/telemetry` - Complete telemetry summary
- **Panel:** "Score Health" (to be added to dashboard UI)
- **Displays:**
  - Histogram of scores
  - Component contribution breakdown
  - Missing intel counts
  - Decay factor distribution
  - % of trades using default conviction
  - % of trades using neutral-expanded-intel defaults

## 7.5 ADAPTIVE WEIGHTS & STAGNATION ALERTS (2026-01-10)

### Current Protection Status

**✅ Protected Component:**
- `options_flow` - Hardcoded to always return default weight (2.4) in `uw_composite_v2.py:83-85`
- **Reason:** Adaptive system previously learned bad weight (0.612 instead of 2.4), killing all scores

**⚠️ Unprotected Components:**
- All other 21 components can have adaptive multipliers applied (0.25x to 2.5x)
- If multiple components are reduced to 0.25x, this can cause significant score reduction

### Stagnation Alert Causes

**Common Causes:**
1. **Adaptive weights reducing multiple components** - If 5+ components reduced to 0.25x → 3-4 point score reduction
2. **Zero score threshold** - 20+ consecutive signals with score=0.00 triggers alert
3. **Funnel stagnation** - >50 alerts but 0 trades in 30min during RISK_ON regimes

### Diagnostic Steps

**When stagnation alerts occur:**
1. Check adaptive weight state: `state/signal_weights.json`
2. Verify component multipliers: Run `comprehensive_score_diagnostic.py`
3. Review weight reductions: Components with multiplier < 1.0
4. Calculate impact: `effective_weight = base_weight * multiplier`

### Recommended Actions

**Immediate:**
- Review `SCORE_STAGNATION_ANALYSIS.md` for full analysis
- Run diagnostics to check current weight state
- Verify if weights need reset or protection

**Long-term:**
- Consider adding safety floors for critical components (similar to `options_flow`)
- Review adaptive learning data to ensure weights learned from correct behavior
- Add component contribution monitoring to track weight impacts

---

## 7.6 STRUCTURAL UPGRADE: COMPOSITE V2 + SHADOW A/B (2026-01-20)

### Composite versioning (contract)
- **v2 is the only composite**:
  - The system exposes a single composite scorer in `uw_composite_v2.py` (v2-only).
  - v1 composite functions and version flags are removed and MUST NOT be reintroduced.

### Feature inputs added (log-only until promotion)
- Per-symbol risk features attached in enrichment:
  - `realized_vol_5d`, `realized_vol_20d`, `beta_vs_spy`
- Market context snapshot:
  - `state/market_context_v2.json`
- Regime/posture snapshot:
  - `state/regime_posture_state.json`

### Trading mode (contract)
- Trading is **paper-only** for now.
- The engine MUST refuse entries if `ALPACA_BASE_URL` is not the Alpaca paper endpoint.

### Daily review
- Daily review artifacts are derived from **v2 live paper logs/state only** (no shadow comparisons).

---

## 7.7 COMPOSITE V2 WEIGHT TUNING (SHADOW-ONLY) (2026-01-20)

### Contract (do not break)
- **v2-only**: weights affect the only engine.
- **Paper-only**: tuning is validated in paper trading; no live deployment without explicit approval.
- **Logging preserved**: tuning never bypasses safety/guards; observability remains append-only.

### Config-driven weights
- **Location**: `config/registry.py` → `COMPOSITE_WEIGHTS_V2`
- **Versioning**: `COMPOSITE_WEIGHTS_V2["version"]` (e.g., `2026-01-20_wt1`)
- **New knobs (v2-only adjustment layer)**:
  - vol/beta: `vol_*`, `beta_*`, `*_bonus_max`, `low_vol_penalty_*`
  - UW strength: `uw_*`, `uw_bonus_max` (uses conviction + trade_count; no reward when trade_count==0)
  - premarket alignment: `premarket_align_bonus`, `premarket_misalign_penalty` (SPY/QQQ overnight proxy)
  - regime/posture: `regime_align_bonus`, `regime_misalign_penalty`, `posture_conf_strong`
  - alignment dampening: `misalign_dampen`, `neutral_dampen`

### Score-shaping (optional, OFF by default)
- **Gate**: only applied when explicitly enabled (env/config), and MUST be regression-covered.
- **Params**: `shape_*` keys in `COMPOSITE_WEIGHTS_V2`
- **Purpose**: nonlinear volatility reward, extra regime-aligned boost, and weak-UW penalties under heavy print counts.

### Observability additions (additive)
- `logs/system_events.jsonl`:
  - `subsystem="scoring" event_type="composite_version_used"` includes `v2_weights_version`

### Diagnostics + reports (droplet-source-of-truth)
- **Weight impact**:
  - generator: `diagnostics/weight_impact_report.py` (runs on droplet)
  - runner: `reports/_daily_review_tools/run_droplet_weight_impact.py`
  - output: `reports/WEIGHT_IMPACT_YYYY-MM-DD.md`
- **Weight tuning summary**:
  - generator: `reports/_daily_review_tools/droplet_weight_tuning_summary_payload.py` (runs on droplet)
  - runner: `reports/_daily_review_tools/run_droplet_weight_tuning_summary.py`
  - output: `reports/WEIGHT_TUNING_SUMMARY_YYYY-MM-DD.md`
- **Fetch helper** (for exporting droplet-generated files):
  - `reports/_daily_review_tools/fetch_from_droplet.py`

### Operational note: refreshing vol/beta when market is closed
- Worker may skip the vol/beta refresh when `market_open=false`.
- Use the droplet-native refresh tool to repopulate `state/symbol_risk_features.json` on-demand:
  - `reports/_daily_review_tools/run_droplet_refresh_symbol_risk_features.py`

## 7.8 UW INTELLIGENCE LAYER (CENTRAL CLIENT + UNIVERSE + INTEL PASSES) (2026-01-20)

### Invariants (non-negotiable)
- **All UW HTTP calls must route through** `src/uw/uw_client.py` (rate-limited, cached, logged).
- **All UW endpoints must be validated** against the official OpenAPI spec at `unusual_whales_api/api_spec.yaml`.
- **Invalid UW endpoints must be blocked at runtime** by `uw_client` before any caching/rate limiting/network, and must log `uw_invalid_endpoint_attempt`.
- **UW daily usage must be persisted** to `state/uw_usage_state.json` (self-healing; never crashes engine).
- **UW response cache (v2 intelligence) lives under** `state/uw_cache/` (TTL enforced per endpoint policy).
- **Symbol-level UW calls are allowed only for** `daily_universe ∪ core_universe`.
- **Universe build must happen before market open** (or the intel passes fall back and log).
- **Pre/post intel must be generated daily**:
  - `state/premarket_intel.json`
  - `state/postmarket_intel.json`
- **Composite scoring is v2-only**; there is no composite version flag.

### UW endpoint validation (anti-404 contract) (2026-01-20)
- **Official spec location**: `unusual_whales_api/api_spec.yaml` (downloaded from UW and committed).
- **Spec loader**: `src/uw/uw_spec_loader.py` (extracts OpenAPI `paths` without YAML dependencies).
- **Static auditing**: `scripts/audit_uw_endpoints.py` (used by regression; fails if any UW endpoint used in code is not in spec).
- **Runtime blocking**: `src/uw/uw_client.py` rejects invalid endpoints and logs `uw_invalid_endpoint_attempt`.

### Components
- **Endpoint policies**: `config/uw_endpoint_policies.py`
- **Central UW client**: `src/uw/uw_client.py`
- **Universe builder**: `scripts/build_daily_universe.py` → `state/daily_universe.json`, `state/core_universe.json`
- **Pre-market pass**: `scripts/run_premarket_intel.py` → `state/premarket_intel.json`
- **Post-market pass**: `scripts/run_postmarket_intel.py` → `state/postmarket_intel.json`
- **Regression runner**: `scripts/run_regression_checks.py`

### Droplet execution + state sync (operational phase) (2026-01-20)

#### Invariants (non-negotiable)
- **Droplet execution must be runnable end-to-end**:
  - `scripts/build_daily_universe.py`
  - `scripts/run_premarket_intel.py`
  - `scripts/run_postmarket_intel.py`
  - `scripts/run_regression_checks.py`
- **Order of operations is binding**:
  - Universe build → premarket intel → postmarket intel → regression
- **State is synced locally for review**:
  - All synced artifacts MUST be written under: `droplet_sync/YYYY-MM-DD/`
  - Each sync MUST append to: `droplet_sync/YYYY-MM-DD/sync_log.jsonl`
- **Safety on failure**:
  - If droplet regression fails, sync MUST abort (no partial “success”).
  - Sync failures MUST be logged and MUST NOT break trading.
- **Shadow-only enforcement**:
  - v2 composite MUST consume UW intel only from `state/premarket_intel.json` / `state/postmarket_intel.json` (no live UW calls in scoring).
- **UW polling must be single-instance (quota safety)**:
  - `uw_flow_daemon.py` MUST NOT run more than once on the droplet.
  - Systemd service `uw-flow-daemon.service` is the canonical runner.
  - The daemon enforces a file lock at `state/uw_flow_daemon.lock` to prevent duplicates.

#### Operator scripts
- **Full run + sync**: `scripts/run_uw_intel_on_droplet.py`
  - Fetches: `state/daily_universe.json`, `state/core_universe.json`, `state/premarket_intel.json`, `state/postmarket_intel.json`, `state/uw_usage_state.json`
  - Fetches tails: `logs/system_events.jsonl` (last 500 lines), `logs/master_trade_log.jsonl` (tail), `logs/exit_attribution.jsonl` (tail)
- **Premarket trigger**: `scripts/run_premarket_on_droplet.py`
- **Postmarket trigger**: `scripts/run_postmarket_on_droplet.py`

### Observability
- `logs/system_events.jsonl` (subsystem=`uw`):
  - `uw_call`
  - `uw_rate_limit_block`
  - `daily_universe_built`
  - `premarket_intel_ready`
  - `postmarket_intel_ready`

## 7.9 INTELLIGENCE & PROFITABILITY LAYER (ATTRIBUTION + P&L + SECTOR/REGIME + UNIVERSE v2 + DASHBOARD + HEALTH) (2026-01-20)

### Invariants (non-negotiable)
- **v2-only engine**: v1 code paths are removed and MUST NOT be reintroduced.
- **No shadow trading**: shadow A/B artifacts are not produced in v2-only mode.
- **Attribution/P&L/dashboard are sourced from v2 live paper logs + state only**.
- **Attribution is append-only and non-blocking**:
  - Writer: `src/uw/uw_attribution.py`
  - Output: `logs/uw_attribution.jsonl`
  - Attribution MUST NEVER raise inside scoring.
- **Sector profiles are config-driven**:
  - Config: `config/sector_profiles.json`
  - Resolver: `src/intel/sector_intel.py` (safe defaults to `UNKNOWN`)
- **Regime state is a stable snapshot**:
  - Engine: `src/intel/regime_detector.py`
  - Output: `state/regime_state.json`
- **Universe scoring v2 is active (v2-only)**:
  - Config: `DAILY_UNIVERSE_SCORING_V2` in `config/registry.py`
  - Output: `state/daily_universe_v2.json`
- **Daily Intel P&L is best-effort and additive**:
  - Script: `scripts/run_daily_intel_pnl.py`
  - Outputs: `reports/UW_INTEL_PNL_YYYY-MM-DD.md`, `state/uw_intel_pnl_summary.json`
- **Intel dashboard is generated from state + logs**:
  - Generator: `reports/_dashboard/intel_dashboard_generator.py`
  - Output: `reports/INTEL_DASHBOARD_YYYY-MM-DD.md`
- **Intel health checks are required for visibility (self-heal optional)**:
  - Script: `scripts/run_intel_health_checks.py`
  - Output: `state/intel_health_state.json`
  - Self-heal attempts MUST be logged in the health state under `self_heal` and MUST NOT impact trading.

## 7.10 UW FLOW DAEMON HEALTH SENTINEL (WATCHDOG) (2026-01-20)

### Invariants (non-negotiable)
- **Daemon must be single-instance** (systemd + file lock): `uw-flow-daemon.service` + `state/uw_flow_daemon.lock`.
- **PID must be valid**:
  - systemd `ExecMainPID` must exist and must be present in `/proc` on the droplet.
- **Lock must be consistent**:
  - `state/uw_flow_daemon.lock` must exist
  - lock must be held (advisory lock)
  - lock file `pid=` should match `ExecMainPID` (best-effort verification)
- **Polling output must be fresh**:
  - Canonical output is `data/uw_flow_cache.json`
  - If stale beyond threshold, sentinel logs a warning/critical health event.
- **Crash loops must be detected**:
  - Crash loop is considered **current instability** (failed/auto-restart/non-active), not historical `NRestarts` alone.
- **Endpoint error spikes must be detected**:
  - Sentinel scans `logs/system_events.jsonl` for `uw_rate_limit_block` and `uw_invalid_endpoint_attempt`.
- **Sentinel must write a health state file**:
  - `state/uw_daemon_health_state.json`
- **Restart-storm detection (observability-only)**:
  - Sentinel may surface `restart_storm_detected` when journal shows repeated “Another instance is already running” patterns.
- **Dashboard must display daemon health**:
  - Intel dashboard includes “UW Flow Daemon Health” section sourced from `state/uw_daemon_health_state.json`.
- **Self-healing is optional and conservative**:
  - Script may attempt `systemctl restart uw-flow-daemon.service` only when enabled (`--heal`)
  - All attempts/results must be logged as system events.

### Operator script
- `scripts/run_daemon_health_check.py`

## 7.11 v2 SHADOW TRADING READINESS + TUNING PIPELINE (2026-01-21)

### Invariants (non-negotiable)
- (UPDATED) v2 LIVE READINESS (paper-only):
  - v2 MUST consume intel from state files only (no live UW calls in scoring).
  - v2 MUST enforce paper endpoint configuration (misconfig => block entries).
  - v2 MUST log all trade lifecycle events for audit/telemetry (master trade log + attribution).
  - Pre-open readiness MUST pass before session:
    - Script: `scripts/run_preopen_readiness_check.py`
    - Must validate freshness of universe + premarket intel + regime + daemon health.
    - Must fail if daemon health is `critical`.
  - Tuning suggestions are advisory only:
    - Helper: `src/intel/v2_tuning_helper.py` → `reports/V2_TUNING_SUGGESTIONS_YYYY-MM-DD.md`
    - No auto-application of weight changes.
  - Dashboard must expose v2 activity via v2 live logs/state (no shadow).

## 7.12 v2 EXIT INTELLIGENCE LAYER (PAPER LIVE) (2026-01-21)

### Invariants (non-negotiable)
- **v2 exit intelligence is live (paper)**:
  - MUST submit paper exit orders when required.
  - MUST log every v2 exit decision and attribution.
- **Exit attribution must be logged for every v2 exit**:
  - Engine: `src/exit/exit_attribution.py`
  - Output: `logs/exit_attribution.jsonl`
- **Exit score must be intel-driven (multi-factor)**:
  - Engine: `src/exit/exit_score_v2.py`
  - Includes UW/sector/regime + score deterioration + thesis flags.
- **Dynamic targets and stops are required** (best-effort when prices are available):
  - Targets: `src/exit/profit_targets_v2.py`
  - Stops: `src/exit/stops_v2.py`
- **Replacement logic is conservative and logged**:
  - Engine: `src/exit/replacement_logic_v2.py`
- **Pre/post-market exit intel must be generated**:
  - `scripts/run_premarket_exit_intel.py` → `state/premarket_exit_intel.json`
  - `scripts/run_postmarket_exit_intel.py` → `state/postmarket_exit_intel.json`
- **Exit analytics must be produced daily**:
  - `scripts/run_exit_intel_pnl.py` → `state/exit_intel_pnl_summary.json`, `reports/EXIT_INTEL_PNL_YYYY-MM-DD.md`
  - `scripts/run_exit_day_summary.py` → `reports/EXIT_DAY_SUMMARY_YYYY-MM-DD.md`
- **Dashboard must expose exit intel**:
  - Intel dashboard includes “Exit Intelligence Snapshot (v2)”.

## 7.13 POST-CLOSE ANALYSIS PACK (DAILY REVIEW BUNDLE) (2026-01-21)

### Invariants (non-negotiable)
- **Additive (no orders)**: pack generation must never submit orders or affect trading behavior.
- **Canonical location**:
  - `analysis_packs/YYYY-MM-DD/`
- **Pack generator**:
  - `scripts/run_postclose_analysis_pack.py`
  - Produces: `analysis_packs/YYYY-MM-DD/MASTER_SUMMARY_YYYY-MM-DD.md`
  - Includes best-effort copies of key `state/`, key `reports/`, and log tails under `analysis_packs/YYYY-MM-DD/{state, reports, logs}/`
- **Droplet integration**:
  - `scripts/run_uw_intel_on_droplet.py --postclose-pack` runs the pack on droplet and syncs it under `droplet_sync/YYYY-MM-DD/analysis_packs/YYYY-MM-DD/`

# 8. TELEMETRY CONTRACT (SYSTEM HARDENING - 2026-01-10)

## 8.1 SCORE TELEMETRY MODULE

- **File:** `telemetry/score_telemetry.py`
- **Purpose:** Track score distribution, component health, and missing data patterns
- **State File:** `state/score_telemetry.json`
- **Functions:**
  - `record(symbol, score, components, metadata)` - Record a score calculation
  - `get_score_distribution(symbol, lookback_hours)` - Get score statistics
  - `get_component_health(lookback_hours)` - Get component contribution stats
  - `get_missing_intel_stats(lookback_hours)` - Get missing data statistics
  - `get_telemetry_summary()` - Get complete telemetry summary

## 8.2 TELEMETRY INTEGRATION

- **Location:** `main.py:7565` (after all boosts applied)
- **Metadata Captured:**
  - `freshness`: Freshness factor applied
  - `conviction_defaulted`: Whether conviction was defaulted to 0.5
  - `missing_intel`: List of missing expanded intel components
  - `neutral_defaults`: List of components using neutral defaults
  - `core_features_missing`: List of missing core features

## 8.3 DASHBOARD TELEMETRY ENDPOINTS

- **Endpoint:** `/api/scores/distribution`
  - Returns: Score min, max, mean, median, percentiles, histogram
  - Parameters: `symbol` (optional), `lookback_hours` (default: 24)
  
- **Endpoint:** `/api/scores/components`
  - Returns: Per-component stats (avg contribution, zero percentage, total count)
  - Parameters: `lookback_hours` (default: 24)
  
- **Endpoint:** `/api/scores/telemetry`
  - Returns: Complete telemetry summary (all statistics)
  - Parameters: None

## 8.4 STRUCTURAL UPGRADE DASHBOARD ENDPOINTS (2026-01-20)
- **Endpoint:** `/api/regime-and-posture`
  - Returns:
    - `state/market_context_v2.json` snapshot
    - `state/regime_posture_state.json` snapshot
    - `composite_version: "v2"` (static)

---

## 8.5 [TELEMETRY_EQUALIZER_CONTRACT] (v2-only, additive) (2026-01-22)

Goal:
- Produce **equalizer-ready** telemetry that maps **per-feature contributions → realized PnL**, without modifying any trading logic.

Invariants (non-negotiable):
- **Read-only**: telemetry builders MUST read from logs/state only and MUST NOT write anywhere except `telemetry/YYYY-MM-DD/`.
- **Trading-safe**: MUST NOT affect trading/scoring/exit behavior (observability only).
- **Idempotent**: running multiple times for the same date must produce the same files given the same inputs.
- **Best-effort**: missing logs/fields are recorded as missing; bundle still generates.

Canonical outputs (generated by `scripts/run_full_telemetry_extract.py`):
- Folder: `telemetry/YYYY-MM-DD/`
- Equalizer artifacts under: `telemetry/YYYY-MM-DD/computed/`
  - `feature_equalizer_builder.json`
  - `feature_value_curves.json`
  - `regime_sector_feature_matrix.json`

### Daily Required Artifacts List (computed/)
The following computed artifacts are considered **daily-required** for a full telemetry bundle:
- `feature_equalizer_builder.json`
- `long_short_analysis.json`
- `exit_intel_completeness.json`
- `feature_value_curves.json`
- `regime_sector_feature_matrix.json`
- `score_distribution_curves.json`
- `regime_timeline.json`
- `replacement_telemetry_expanded.json`
- `pnl_windows.json`
- `signal_performance.json`
- `signal_weight_recommendations.json`

### Master Trade Log (append-only)
Path:
- `logs/master_trade_log.jsonl`

Purpose:
- A single, append-only stream of v2 live (paper) trade lifecycle records for long-term learning and auditing.

Rules:
- Append-only (never rewrite history).
- MUST NOT change trading/scoring/exit behavior; this is a passive “tap” off existing live logging.

### Feature Families (definition)
“Feature families” are **telemetry-only groupings** used to summarize score behavior and parity deltas without changing any trading logic.
- Families are used in:
  - `score_distribution_curves.json`
- (Optional) future dashboards/analysis pack summaries
- Canonical family set (coarse, stable): `flow`, `darkpool`, `sentiment`, `earnings`, `alignment`, `greeks`, `volatility`, `regime`, `event`, `short_interest`, `etf_flow`, `calendar`, `toxicity`, plus `other/unknown` fallbacks.

### Equalizer Knob Families (definition)
“Equalizer knob families” are the **operator-facing** counterparts of feature families:
- They define the buckets you would tune in a future equalizer UI (analysis-only).
- They MUST be derived only from telemetry artifacts (no live weight changes).

Required contents (minimum):
- **Per-feature PnL mapping**: total/avg PnL, win-rate, count (overall + by long/short).
- **Per-feature exit impact** (best-effort): exit score distributions + deterioration/RS/vol-expansion summaries for trades where the feature is active.
- **Equalizer-ready structures**: value curves (binned/quantiles) suitable for converting feature strength into a suggested weight/curve without touching live logic.

---

## 8.6 [LONG_SHORT_ASYMMETRY_CONTRACT] (v2-only, additive) (2026-01-22)

Goal:
- Track long vs short asymmetry using v2 live (paper) realized exits.

Required metrics (minimum):
- **Win rate**, **avg PnL**, **avg win**, **avg loss**, **expectancy** for:
  - overall
  - long-only
  - short-only

Output:
- `telemetry/YYYY-MM-DD/computed/long_short_analysis.json`

---

## 8.7 [EXIT_INTEL_COMPLETENESS_CONTRACT] (v2-only, additive) (2026-01-22)

Goal:
- Ensure exit-intel telemetry contains the full set of **required deterioration components** for debugging and promotion decisions.

Required exit-intel components (minimum keys in `exit_attribution.v2_exit_components`):
- `vol_expansion`
- `regime_shift`
- `sector_shift`
- `relative_strength_deterioration` (top-level in attribution record)
- `score_deterioration` (top-level + component-level where applicable)
- `flow_deterioration`
- `darkpool_deterioration`
- `sentiment_deterioration`

Output:
- `telemetry/YYYY-MM-DD/computed/exit_intel_completeness.json`

Rule:
- If keys are missing, bundle MUST still be produced and must report missing-key counts.

---

## 8.8 [FEATURE_VALUE_CURVES_CONTRACT] (v2-only, additive) (2026-01-22)

Goal:
- Produce per-feature “value curves” suitable for a future **feature equalizer** (shadow-only analysis).

Requirements:
- Curves MUST be derived from realized v2 shadow exits only.
- Curves MUST be computed separately for long/short when side is known.
- Curves MUST include counts per bin and average realized PnL per bin.

Output:
- `telemetry/YYYY-MM-DD/computed/feature_value_curves.json`

---

## 8.9 [REGIME_SECTOR_MATRIX_CONTRACT] (v2-only, additive) (2026-01-22)

Goal:
- Provide diagnostics for regime-aware and sector-aware feature weighting.

Requirements:
- For each (regime, sector) cell, compute per-feature counts and realized PnL summaries (best-effort).
- Must include a top-level summary for sparse cells (low sample sizes).

Output:
- `telemetry/YYYY-MM-DD/computed/regime_sector_feature_matrix.json`

---

## 8.10 [REPLACEMENT_LOGIC_TELEMETRY_CONTRACT] (v2-only, additive) (2026-01-22)

Requirements:
- Telemetry MUST count replacement exits and include replacement metadata when present:
  - `replacement_candidate`
  - `replacement_reasoning` (best-effort)
- Output MUST include:
  - count of replacement exits
  - realized PnL summary for replacement vs non-replacement exits (when PnL exists)

Where captured:
- `logs/master_trade_log.jsonl` (replacement fields when present)
- `logs/exit_attribution.jsonl` (`replacement_candidate`, `replacement_reasoning`)
- summarized into `telemetry/YYYY-MM-DD/FULL_TELEMETRY_YYYY-MM-DD.md` and `telemetry_manifest.json`.

---

# 9. CURSOR BEHAVIOR CONTRACT (ENHANCED - 2026-01-10)

## 9.1 MEMORY BANK LOADING RULE

Cursor MUST:
- **ALWAYS** load `MEMORY_BANK.md` at the start of every session
- **ALWAYS** read Section 0 (Cursor Behavior Contract) first
- **ALWAYS** reference `MEMORY_BANK.md` before making ANY code changes
- **ALWAYS** update `MEMORY_BANK.md` when adding new system behavior

Cursor MUST NOT:
- Skip loading `MEMORY_BANK.md`
- Overwrite `MEMORY_BANK.md` unless explicitly instructed
- Make changes without checking `MEMORY_BANK.md` first

## 9.2 MEMORY BANK UPDATE RULES

Cursor MUST update `MEMORY_BANK.md` when:
- New modules are added
- New telemetry is added
- New scoring logic is added
- New dashboard panels are added
- New operational rules are added
- New contracts are established

## 9.3 MEMORY BANK AS SINGLE SOURCE OF TRUTH

`MEMORY_BANK.md` is the authoritative source for:
- Architecture (Section 2)
- Signal integrity (Section 4)
- Scoring pipeline (Section 7)
- Telemetry (Section 8)
- Cursor behavior (Section 0, 9)
- Deployment workflow (Section 6)
- Report generation (Section 5)

## 9.4 SACRED LOGIC PROTECTION

Cursor MUST NOT modify without explicit permission:
- Core strategy logic (signal generation, model logic)
- Wallet/P&L/risk math (unless explicitly required)
- `.env` secrets or their loading path
- Systemd service configuration
- Fundamental process structure (`deploy_supervisor.py` + children)

All changes MUST be:
- Additive (not replacing existing logic)
- Defensive (fail-safe, not fail-dangerous)
- Reversible (can be undone if needed)
- Documented (in `MEMORY_BANK.md`)

---

## 4.4 COMPOSITE SCORING RULES
Cursor MUST:
- count only symbol keys (exclude metadata keys)  
- validate cache contents  
- ensure scoring only runs with real data  

---

# 5. REPORT GENERATION CONTRACT

## 5.1 REQUIRED STEPS
Cursor MUST:
1. Use `ReportDataFetcher(date="YYYY-MM-DD")`  
2. Fetch trades, blocked trades, signals, orders, gates  
3. Validate with `validate_report_data()`  
4. Validate data source  
5. Include data source metadata  
6. Reject invalid reports  

## 5.4 END-OF-DAY TRADE REVIEW (EOD)
- **Droplet-native generator**:
  - Payload: `reports/_daily_review_tools/droplet_end_of_day_review_payload.py`
  - Runner: `reports/_daily_review_tools/run_droplet_end_of_day_review.py`
- **Output**:
  - `reports/END_OF_DAY_REVIEW_YYYY-MM-DD.md`
- **Contract**:
  - MUST use droplet logs/state as source-of-truth
  - MUST be brutally honest (explicit YES/NO verdicts)
  - MUST review v2 live paper trades (no shadow comparison) and include buy-and-hold benchmark (best-effort)

---

## 5.5 EOD Data Pipeline (Canonical)

Canonical 8-file bundle paths (relative to repo root; **do not move/rename**):
- `logs/attribution.jsonl`, `logs/exit_attribution.jsonl`, `logs/master_trade_log.jsonl`
- `state/blocked_trades.jsonl`, `state/daily_start_equity.json`, `state/peak_equity.json`, `state/signal_weights.json`, `state/daily_universe_v2.json`

**Runner:** `board/eod/run_stock_quant_officer_eod.py` — uses `REPO_ROOT` + canonical paths with `(REPO_ROOT / rel).resolve()`; defensive checks (missing → log.error, data[name]=None; empty → log.warning, [] or None); prompt prepended with "Ignore any prior context. Use ONLY the EOD bundle summary below."; Linux: no truncation; Windows: MAX_PROMPT_LEN truncation; date-scoped session `CLAWDBOT_SESSION_ID="stock_quant_eod_$(date -u +%Y-%m-%d)"`.

**Contract:** `board/quant_officer_contract.md` (fallback: `board/stock_quant_officer_contract.md`).

**Outputs:** `board/eod/out/quant_officer_eod_<DATE>.json`, `board/eod/out/quant_officer_eod_<DATE>.md`. On parse failure: `board/eod/out/<DATE>_raw_response.txt`, exit 1.

**Cron:** EOD at 21:30 UTC weekdays; installed via `board/eod/install_eod_cron_on_droplet.py`. Audit+sync: `scripts/run_droplet_audit_and_sync.sh` (21:32 UTC weekdays) — runs `run_stockbot_daily_reports.py` for the date, then audit, then commits EOD + droplet_audit + stockbot pack and pushes. Local fetch (repeatable): `scripts/pull_eod_to_local.ps1` (Windows) or `scripts/pull_eod_to_local.sh` (Git Bash/Linux) — run weekdays after 21:35 UTC to get latest EOD without conflicts. Direct: `scripts/local_sync_from_droplet.sh`, `scripts/fetch_eod_to_local.py` → `board/eod/out/` and `EOD--OUT/`.

**Docs:** `docs/EOD_DATA_PIPELINE.md`, `docs/CRON_STRATEGIC_REVIEW.md`; summary: `reports/EOD_TARGETED_REPAIR_SUMMARY.md`.

**Extended canonical (vNext):** `state/symbol_risk_snapshot.json` — optional daily per-symbol risk snapshot; produced by `scripts/generate_symbol_risk_snapshot.py`; EOD runner loads defensively and includes "Symbol risk intelligence" subsection in memo when present; copies to `board/eod/out/symbol_risk_snapshot_<DATE>.json` and `.md`. See docs/EOD_DATA_PIPELINE.md.

**EOD data hardening (observability):** `scripts/eod_bundle_manifest.py` — validates canonical 8-file bundle (exists, non-empty, sha256); outputs `reports/eod_manifests/EOD_MANIFEST_<DATE>.json|.md`; exits non-zero if any required file missing/empty. `scripts/generate_signal_weight_exit_inventory.py` — signal/weight/exit inventory (COMPOSITE_WEIGHTS_V2, adaptive state/signal_weights.json, exit usage); output `reports/STOCK_SIGNAL_WEIGHT_EXIT_INVENTORY_<DATE>.md`. Droplet runner: `scripts/run_stock_eod_integrity_on_droplet.sh` (path-agnostic: REPO_DIR defaults to script's parent directory); manifest → EOD quant officer → inventory → commit + push. §3.2 (reports use droplet production data).

**Unified daily intelligence pack:** `scripts/run_stockbot_daily_reports.py` — creates `reports/stockbot/YYYY-MM-DD/` with 9 files: STOCK_EOD_SUMMARY.md/.json, STOCK_EQUITY_ATTRIBUTION.jsonl, STOCK_WHEEL_ATTRIBUTION.jsonl, STOCK_BLOCKED_TRADES.jsonl, STOCK_PROFITABILITY_DIAGNOSTICS.md/.json, STOCK_REGIME_AND_UNIVERSE.json, MEMORY_BANK_SNAPSHOT.md. Canonical wheel fields: strategy_id, phase, option_type, strike, expiry, dte, delta_at_entry, premium, assigned, called_away. Moltbot expansion: `scripts/run_molt_intelligence_expansion.py` loads pack via load_equity_attribution(), load_wheel_attribution(), load_profitability_diagnostics(), load_blocked_trades(), load_regime_universe(). Pack integrated into EOD flow via run_stock_eod_integrity_on_droplet.sh.

**Cron + Git diagnostic:** `scripts/diagnose_cron_and_git.py` — full Cron + Git + execution diagnostic and repair (path-agnostic). Auto-detects stock-bot root (/root/stock-bot-current, /root/stock-bot); diagnoses cron, verifies scripts, EOD dry-run, git push; repairs cron if needed; updates Memory Bank; outputs `reports/STOCKBOT_CRON_AND_GIT_DIAGNOSTIC_<DATE>.md`. Usage: `python3 scripts/diagnose_cron_and_git.py` on droplet; `--local` for Windows; `--remote` to run via DropletClient; `--dry-run` for report only. **Remote runner:** `python scripts/run_diagnose_on_droplet_via_ssh.py` — pulls latest on droplet, runs diagnostic, from local machine. **Verified 2026-02-01:** EOD 21:30 UTC, sync 21:32 UTC Mon–Fri; droplet push OK.

### Signal Snapshot Mapping Layer (observability-only)
- **Log:** `logs/signal_snapshots.jsonl` — append-only, one JSON record per lifecycle moment.
- **Schema:** timestamp_utc, symbol, lifecycle_event (ENTRY_DECISION | ENTRY_FILL | EXIT_DECISION | EXIT_FILL), mode (LIVE | PAPER | SHADOW), trade_id, regime_label, composite_score_v2, freshness_factor, components (present/defaulted/contrib), uw_artifacts_used, notes.
- **Writer:** `telemetry/signal_snapshot_writer.py` — write_snapshot_safe(); never raises.
- **Hooks:** main.py at entry decision (pre-submit), entry fill (log_attribution), exit decision (pre-close), exit fill (log_exit_attribution). SHADOW mode: counterfactual components; non-mutating.
- **Report:** `reports/SIGNAL_MAP_<DATE>.md` — daily per-symbol snapshot summary; generator `scripts/generate_daily_signal_map_report.py`; droplet runner `scripts/run_daily_signal_map_on_droplet.py`.
- **Snapshot harness verification (pre-market required):**
  - **Runner:** `scripts/run_snapshot_harness_on_droplet.py` (DropletClient); shell `scripts/run_snapshot_harness_on_droplet.sh`.
  - **Success criteria:** logs/signal_snapshots_harness_<DATE>.jsonl exists with >0 lines; reports/SNAPSHOT_HARNESS_VERIFICATION_<DATE>.md passes schema checks; reports/SIGNAL_MAP_<DATE>.md non-empty and labeled HARNESS.
  - **NO ORDERS PLACED:** Harness produces snapshots from master_trade_log; never places orders.

### Snapshot→Outcome Attribution
- **Join keys contract:** `telemetry/snapshot_join_keys.py` — canonical join_key and join_key_fields for snapshots↔master_trade_log↔exit_attribution↔blocked_trades. Prefer trade_id; surrogate: symbol|rounded_ts_bucket|side|lifecycle_event.
- **Report:** `reports/SNAPSHOT_OUTCOME_ATTRIBUTION_<DATE>.md` — join quality, outcome buckets (WIN/LOSS/FLAT/blocked), signal separability, marginal value (informative/neutral/misleading), shadow comparisons.
- **Shadow snapshot profiles (NO-APPLY):** `config/shadow_snapshot_profiles.yaml` — baseline, emphasize_dark_pool, emphasize_congress, emphasize_regime, disable_toxicity, etc. `telemetry/snapshot_builder.py` recomputes composite with profile multipliers; writes to `logs/signal_snapshots_shadow_<DATE>.jsonl`.
- **Shadow snapshots do NOT change decisions.** They are counterfactual analysis only.
- **Runner:** `scripts/run_snapshot_outcome_attribution_on_droplet.py` — harness → shadow snapshots → attribution report → commit + push.

### Exit Join Canonicalization
- **Join key precedence (deterministic exit joins):** `telemetry/snapshot_join_keys.py` — a) position_id (preferred); b) trade_id (live:SYMBOL:entry_ts); c) surrogate: symbol + side + entry_ts_bucket + intent_id.
- **Exit join fields:** EXIT_DECISION and EXIT_FILL snapshots emit `exit_join_key`, `exit_join_key_fields`, `entry_timestamp_utc` for auditability.
- **Reconciliation:** `telemetry/exit_join_reconciler.py` — resolves delayed exits, partial fills, regime-driven exits by time-window tolerance (default 5 min).
- **Report:** `reports/EXIT_JOIN_HEALTH_<DATE>.md` — snapshot→exit match rate, unmatched reasons, sources.

### Blocked-Trade Intelligence Attribution
- **Linkage:** `telemetry/blocked_snapshot_linker.py` — links state/blocked_trades.jsonl to nearest ENTRY_DECISION snapshot by symbol + time window (10 min).
- **Output:** `logs/blocked_trade_snapshots.jsonl` — append-only; each record: blocked_reason, snapshot components present/defaulted/missing, regime_label, notes.
- **Report:** `reports/BLOCKED_TRADE_INTEL_<DATE>.md` — blocked counts by reason, intelligence at block time, shadow profile deltas (hypothetical; NO-APPLY).
- **Runner:** `scripts/run_exit_join_and_blocked_attribution_on_droplet.py` — intel producers → UW audit → harness (if needed) → exit join health → blocked intel report → commit + push.

### Molt.bot — Learning & Engineering Governor
- **Role:** Molt is the orchestration and governance layer. Cursor implements all workflows. Molt produces artifacts and proposals ONLY; never applies changes.
- **NO-APPLY guarantee:** Molt MUST NEVER change weights, gates, or decisions. Artifact-only consumption. No live UW calls. No orders.
- **Workflows:**
  - **Learning Orchestrator** (`moltbot/orchestrator.py`): Verifies Memory Bank version, learning pipeline artifacts, NO-APPLY compliance. Output: `reports/LEARNING_STATUS_<DATE>.md`
  - **Engineering Sentinel** (`moltbot/sentinel.py`): Reads cron logs, EXIT_JOIN_HEALTH, BLOCKED_TRADE_INTEL, SNAPSHOT_OUTCOME_ATTRIBUTION. Output: `reports/ENGINEERING_HEALTH_<DATE>.md`. No code changes.
  - **Multi-Agent Learning Board** (`moltbot/board.py`): signal_advocate, risk_auditor, counterfactual_analyst, governance_chair. Output: `reports/PROMOTION_PROPOSAL_<DATE>.md` or `reports/REJECTION_WITH_REASON_<DATE>.md`
  - **Promotion Discipline** (`moltbot/promotion_discipline.py`): Multi-day stability, regime consistency, blocked-trade impact, shadow persistence. No automatic promotion. Output: `reports/PROMOTION_DISCIPLINE_<DATE>.md`
  - **Memory Bank Evolution** (`moltbot/memory_evolution.py`): Detects patterns, proposes Memory Bank updates. Output: `reports/MEMORY_BANK_CHANGE_PROPOSAL_<DATE>.md`. Never writes MEMORY_BANK directly.
- **Automation:** `scripts/run_molt_workflow.py` — runs full Molt pipeline. `scripts/run_molt_on_droplet.sh` — droplet runner. Cron: 21:35 UTC weekdays (post-market) via `scripts/install_molt_cron_on_droplet.py`
- **Promotion:** Human approval required. Molt proposes; Cursor/human approves and applies.

### UW canonical rules
- **Docs:** `docs/uw/README.md`, `docs/uw/ENDPOINT_POLICY.md` — canonical reference.
- **No hallucinated endpoints:** all must exist in `unusual_whales_api/api_spec.yaml`; static audit `scripts/audit_uw_endpoints.py` fails CI if unknown endpoints referenced.
- **Single-instance ingestion:** uw_flow_daemon only; file lock + systemd; scoring reads only from cached artifacts (uw_flow_cache, premarket_intel, postmarket_intel, uw_expanded_intel).

---

## 5.2 PROHIBITED PRACTICES
Cursor MUST NOT:
- read local logs  
- generate reports with 0 trades (unless market closed)  
- skip validation  
- commit incorrect reports  

---

## 5.3 REPORT CHECKLIST
Cursor MUST verify:
- Data source = "Droplet"  
- Trade count > 0 (or documented reason)  
- Timestamp < 1 hour old  
- Validation passed  

---

# 6. DEPLOYMENT WORKFLOW (FULL SOP)

## 6.1 REQUIRED STEPS
Cursor MUST:
1. Commit + push to GitHub  
2. SSH into droplet using `droplet_client.py` (via `deploy_dashboard_via_ssh.py` or similar)  
3. Pull latest code: `git pull origin main`  
4. Restart services (dashboard, trading bot, etc.)  
5. Wait for verification (check health endpoints)  
6. Verify deployment success  
7. Report to user

**VERIFIED WORKFLOW (2026-01-12):**
- ✅ SSH connection via `droplet_client.py` works (paramiko installed)
- ✅ Deployment script `deploy_dashboard_via_ssh.py` successfully deploys
- ✅ Dashboard can be started with: `nohup python3 dashboard.py > logs/dashboard.log 2>&1 &`
- ✅ Health check endpoint responds (Basic Auth required):
  - `set -a && source /root/stock-bot/.env && set +a && curl -u "$DASHBOARD_USER:$DASHBOARD_PASS" http://localhost:5000/health`  

---

## 6.2 PROHIBITED ACTIONS
Cursor MUST NOT:
- skip GitHub push  
- skip droplet deployment  
- ask user to run commands  
- assume droplet is updated  
- report early  

---

## 6.3 SSH CONFIG
**DEPLOY_TARGET: 104.236.102.57 (stock-bot)**

**VERIFIED (2026-01-12):** SSH deployment works via `droplet_client.py` with paramiko.

Droplet config (`droplet_config.json`):
```json
{
  "host": "104.236.102.57",
  "port": 22,
  "username": "root",
  "use_ssh_config": false,
  "key_file": "C:/Users/markl/.ssh/id_ed25519",
  "project_dir": "/root/stock-bot"
}
```

**Alternative:** Can use SSH config alias "alpaca" with `"use_ssh_config": true` and `"host": "alpaca"`.

**CRITICAL:** 
- All deployments MUST target `104.236.102.57` (stock-bot) — use `droplet_config.json` or DropletClient.
- **NEVER use `147.182.255.165`** — that IP is for a different droplet/bot. This repo uses `104.236.102.57` only.
- SSH alias "alpaca" resolves to this IP
- **REQUIRED:** `paramiko` library must be installed: `python -m pip install paramiko`
- SSH key must be authorized on droplet (user fixed key mismatch on 2026-01-12)

### STOCK-BOT ISOLATION
- **Repository identity:** stock-bot (equities only). Do NOT reference trading-bot paths, IPs, or repos.
- **Droplet binding:** `droplet_config.json` is the single source for host/key; DropletClient MUST use it.
- **Forbidden IP:** `147.182.255.165` — never use for stock-bot. That IP is for a different bot.
- **Canonical droplet:** `104.236.102.57` or SSH alias `alpaca`; project dir `/root/stock-bot` or `/root/trading-bot-current` per deployment.

---

## 6.4 CREDENTIALS & ENVIRONMENT

### Credentials Location
**CRITICAL:** Alpaca API credentials are stored in:
- `/root/stock-bot/.env`

The `.env` file contains:
- `ALPACA_KEY=...` - Alpaca API key
- `ALPACA_SECRET=...` - Alpaca API secret
- `ALPACA_BASE_URL=...` - Alpaca API base URL (default: https://paper-api.alpaca.markets)
- `UW_API_KEY=...` - Unusual Whales API key
- `DASHBOARD_USER=...` - Dashboard HTTP Basic Auth username (email)
- `DASHBOARD_PASS=...` - Dashboard HTTP Basic Auth password (rotate as needed)

### Credential Loading
- The systemd service (`stock-bot.service`) automatically loads credentials via `EnvironmentFile=/root/stock-bot/.env`
- `deploy_supervisor.py` uses `load_dotenv()` to load `.env` file
- All services inherit environment variables from the supervisor

### Important Notes
- **DO NOT** commit `.env` file to git (it's in `.gitignore`)
- **DO NOT** modify `.env` file contents during migrations
- Credentials are loaded automatically by systemd service

---

## 6.5 SYSTEMD SERVICE MANAGEMENT

### Service Details
**NOTE (2026-01-12):** Systemd service `trading-bot.service` may not exist. Dashboard can be started manually.

**If systemd service exists:**
- **SERVICE_NAME:** `trading-bot.service` or `stock-bot.service`
- **Service file location:** `/etc/systemd/system/trading-bot.service` or `/etc/systemd/system/stock-bot.service`
- **Service configuration:**
  - **WorkingDirectory:** `/root/stock-bot`
  - **EnvironmentFile:** `/root/stock-bot/.env`
  - **ExecStart:** `/root/stock-bot/venv/bin/python /root/stock-bot/deploy_supervisor.py`
  - **Restart:** `always` (with 5 second delay)
  - **User:** `root`
  - **Start on boot:** `enabled`

**Manual Dashboard Start (VERIFIED WORKING):**
```bash
cd /root/stock-bot
nohup python3 dashboard.py > logs/dashboard.log 2>&1 &
```

**Dashboard Health Check:**
```bash
set -a && source /root/stock-bot/.env && set +a
curl -u "$DASHBOARD_USER:$DASHBOARD_PASS" http://localhost:5000/health
# Should return: {"status":"degraded"|"healthy",...}
```

### Service Management Commands
```bash
# Start/Stop/Restart
sudo systemctl start stock-bot
sudo systemctl stop stock-bot
sudo systemctl restart stock-bot

# Check status
sudo systemctl status stock-bot

# View logs
journalctl -u stock-bot -f          # Follow logs
journalctl -u stock-bot -n 100      # Last 100 lines
journalctl -u stock-bot -b          # Since boot
```

### Service Architecture
- **Entry Point:** `deploy_supervisor.py` (NOT modified during systemd migration)
- **Supervisor manages:**
  - `dashboard.py` (port 5000)
  - `uw_flow_daemon.py` (UW API ingestion)
  - `main.py` (core trading engine)

### Migration Notes
The bot was migrated from manual supervisor execution to systemd management:
- ✅ Preserved all trading logic
- ✅ Preserved supervisor architecture (`deploy_supervisor.py`)
- ✅ Added automatic restart on failure
- ✅ Added automatic start on boot
- ✅ Centralized logging via journalctl
- ❌ Did NOT modify trading logic
- ❌ Did NOT modify `deploy_supervisor.py` logic
- ❌ Did NOT modify `.env` file contents

### Troubleshooting
If service won't start:
1. Verify `.env` file exists: `ls -la /root/stock-bot/.env`
2. Check service status: `sudo systemctl status stock-bot`
3. Check logs: `journalctl -u stock-bot -n 50`
4. Verify credentials format in `.env` file (no spaces around `=`)

---

## 6.6 DASHBOARD DEPLOYMENT (VERIFIED 2026-01-12)

### Deployment Process
**VERIFIED WORKING:** SSH deployment via `droplet_client.py` works correctly.

**Deployment Script:** `deploy_dashboard_via_ssh.py`

**Required Dependencies:**
- `paramiko` library: `python -m pip install paramiko`
- `droplet_config.json` configured with correct SSH key path
- SSH key authorized on droplet (user fixed key mismatch on 2026-01-12)

### Deployment Steps (VERIFIED)
1. **Code Push:** Commit and push to GitHub
2. **SSH Connection:** Use `DropletClient()` from `droplet_client.py`
3. **Pull Code:** `git pull origin main` on droplet
4. **Restart Dashboard:** 
   - Kill existing: `pkill -f 'python.*dashboard.py'`
   - Start new: `nohup python3 dashboard.py > logs/dashboard.log 2>&1 &`
5. **Verify (Basic Auth required):** `set -a && source /root/stock-bot/.env && set +a && curl -u "$DASHBOARD_USER:$DASHBOARD_PASS" http://localhost:5000/health`

### Dashboard Startup
**VERIFIED METHOD (2026-01-12):**
```bash
cd /root/stock-bot
nohup python3 dashboard.py > logs/dashboard.log 2>&1 &
```

**Health Check:**
```bash
set -a && source /root/stock-bot/.env && set +a
curl -u "$DASHBOARD_USER:$DASHBOARD_PASS" http://localhost:5000/health
# Expected: {"status":"degraded"|"healthy","alpaca_connected":true,...}
```

### Dashboard Endpoints
- **Main:** http://104.236.102.57:5000/
- **Health:** http://104.236.102.57:5000/health
- **Positions:** http://104.236.102.57:5000/api/positions
- **Health Status:** http://104.236.102.57:5000/api/health_status

### Recent Fixes (2026-01-12)
- ✅ Fixed blocking file read operations (`readlines()` → chunk-based reading)
- ✅ Optimized large file processing (10,000 line limit, efficient reading)
- ✅ All endpoints return valid JSON even on errors
- ✅ Memory-efficient file operations

### Troubleshooting Dashboard
If dashboard not responding:
1. Check if running: `ps aux | grep dashboard.py | grep -v grep`
2. Check logs: `tail -50 /root/stock-bot/logs/dashboard.log`
3. Start manually: `cd /root/stock-bot && nohup python3 dashboard.py > logs/dashboard.log 2>&1 &`
4. Verify port: `netstat -tlnp | grep 5000` or `ss -tlnp | grep 5000`

---

## 6.7 FAILURE POINT MONITORING + SELF-HEALING SYSTEM (UPDATED 2026-01-14)

### System Overview
The failure point monitoring system tracks all critical system components and provides self-healing for recoverable issues. It answers "Why am I not trading?" with explicit, accurate explanations.

### Failure Point Categories

**FP-1.x: Data & Signal Generation**
- **FP-1.1:** UW Daemon Running - Checks if `uw_flow_daemon.py` process is active
- **FP-1.2:** Cache File Exists - Verifies `data/uw_flow_cache.json` exists and has data
- **FP-1.3:** Cache Fresh - Checks cache file age (< 10 min = OK, < 30 min = WARN, > 30 min = ERROR)
- **FP-1.4:** Cache Has Symbols - Verifies cache contains symbol data
- **FP-1.5:** UW API Authentication - Checks for recent 401/403 errors in daemon logs

**FP-2.x: Scoring & Evaluation**
- **FP-2.1:** Adaptive Weights Initialized - Verifies `state/signal_weights.json` has 21 components

**FP-3.x: Gates & Filters**
- **FP-3.1:** Freeze State - Checks `check_performance_freeze()` and `state/governor_freezes.json`
  - **Single Source of Truth:** Matches `monitoring_guards.py:check_freeze_state()` exactly
  - **Files Checked:** `state/governor_freezes.json` (active freezes where value == True)
  - **Performance Freeze:** Automatically set by `check_performance_freeze()` in LIVE mode only
- **FP-3.2:** Max Positions Reached - Checks Alpaca positions vs `MAX_CONCURRENT_POSITIONS` (16)
- **FP-3.3:** Concentration Gate - Calculates `net_delta_pct` and checks if > 70% (blocking bullish entries)
  - **Matches:** `main.py:5794` - Blocks when `net_delta_pct > 70.0` and `direction == "bullish"`

**FP-4.x: Execution & Broker**
- **FP-4.1:** Alpaca Connection - Tests `api.get_account()` connectivity
- **FP-4.2:** Alpaca API Authentication - Checks for 401/403 errors
- **FP-4.3:** Insufficient Buying Power - Warns if buying power < $100

**FP-6.x: System & Infrastructure**
- **FP-6.1:** Bot Running - Checks if `main.py` process is active (multiple pattern matching + port 8081 check)

### Freeze State Contract

**Single Source of Truth:** `monitoring_guards.py:check_freeze_state()`

**Logic:**
1. First checks `check_performance_freeze()` (only in LIVE mode, freezes on extreme losses)
2. Then checks `state/governor_freezes.json` for any active freezes (value == True)

**Files:**
- ✅ `state/governor_freezes.json` - ACTIVE (single source of truth)
- ❌ `state/pre_market_freeze.flag` - REMOVED (stale mechanism, cleaned up 2026-01-14)

**How Bot Uses It:**
- `main.py:7430` - Early exit if frozen: `if not check_freeze_state(): return {"clusters": 0, "orders": 0}`
- `main.py:6050` - Passed to expectancy gate: `freeze_active = check_freeze_state() == False`

**How Panel Reads It:**
- `failure_point_monitor.py:check_fp_3_1_freeze_state()` - Matches main.py logic exactly

**Self-Healing:**
- ❌ **NO self-healing for freezes** - Must be manually cleared (correct behavior)

### Trading Blockers Function

**Function:** `get_trading_blockers()` in `failure_point_monitor.py`

**Purpose:** Provides explicit answer to "Why am I not trading?"

**Returns:**
```python
{
    "blocked": bool,
    "blockers": [
        {
            "type": "freeze_state" | "max_positions" | "concentration_gate" | "system_error",
            "active": bool,
            "reason": str,
            "source": str,
            "can_self_heal": bool,
            "requires_manual_action": bool,
            "fp_id": str
        }
    ],
    "summary": str
}
```

**Usage:**
- Dashboard `/api/failure_points` endpoint includes blockers
- Dashboard UI shows "Why am I not trading?" panel when blocked
- `get_trading_readiness()` includes blockers in response

### Self-Healing System

**Routines:**
1. **`_heal_uw_daemon()`** - Restarts UW daemon (kills process, supervisor restarts; fallback: systemd)
2. **`_heal_weights_init()`** - Initializes weights file via `fix_adaptive_weights_init.py`
3. **`_heal_bot_restart()`** - Restarts bot service via systemd

**Logging:**
- ✅ All self-healing actions logged to `logs/self_healing.jsonl` (structured JSONL)
- ✅ Includes: timestamp, FP ID, action, message, success status
- ✅ Also prints to console for immediate visibility

**Safety:**
- ✅ All routines are safe operational repairs
- ✅ No modifications to sacred logic
- ✅ No deletion of important state
- ✅ No masking of real problems

### Dashboard Integration

**Endpoint:** `/api/failure_points`
- Returns trading readiness status
- Includes all failure point details
- Includes blockers explanation

**UI Tab:** "⚠️ Trading Readiness"
- Shows overall readiness (READY/DEGRADED/BLOCKED)
- Lists all failure points with status
- Shows "Why am I not trading?" panel when blocked
- Auto-refreshes every 30 seconds

### Usage

**Check Trading Readiness:**
```bash
python3 -c "from failure_point_monitor import get_failure_point_monitor; m = get_failure_point_monitor(); r = m.get_trading_readiness(); print(r['readiness'])"
```

**Get Trading Blockers:**
```bash
python3 -c "from failure_point_monitor import get_failure_point_monitor; m = get_failure_point_monitor(); b = m.get_trading_blockers(); print(b['summary'])"
```

**View Self-Healing Logs:**
```bash
tail -20 logs/self_healing.jsonl | jq '.'
```

---

## 6.8 TRADING BLOCKERS EXPLANATION (NEW 2026-01-14)

### Common Blockers

1. **Freeze State (FP-3.1)**
   - **Reason:** Trading frozen by operator or performance freeze
   - **Source:** `state/governor_freezes.json` or `check_performance_freeze()`
   - **Action Required:** Manual - Clear freeze flags in `governor_freezes.json`

2. **Max Positions (FP-3.2)**
   - **Reason:** At capacity (16/16 positions)
   - **Source:** Alpaca API position count
   - **Action Required:** None - Wait for natural exits or manually close positions

3. **Concentration Gate (FP-3.3)**
   - **Reason:** Portfolio >70% long-delta, blocking bullish entries
   - **Source:** Portfolio calculation (net_delta / account_equity)
   - **Action Required:** None - Wait for exits, bearish signals, or manually close positions

4. **System Errors (FP-1.x, FP-4.x, FP-6.x)**
   - **Reason:** Critical system component failed
   - **Source:** Various (daemon, cache, API, bot process)
   - **Action Required:** Check self-healing status, may require manual intervention

---

## 6.9 ALPHA UPGRADE (Displacement Policy, Shorts, EOD) — 2026-01-26

### New Config Keys (env)

- **`DISPLACEMENT_ENABLED`** (default `true`): Master switch for displacement policy.
- **`DISPLACEMENT_MIN_HOLD_SECONDS`** (default `1200`, 20 min): Min hold before displacement unless emergency (score &lt; 3 or pnl &lt; -0.5%).
- **`DISPLACEMENT_MIN_DELTA_SCORE`** (default `0.75`): Challenger must beat current by at least this.
- **`DISPLACEMENT_REQUIRE_THESIS_DOMINANCE`** (default `true`): Require at least one of flow/regime/dark_pool win.
- **`DISPLACEMENT_THESIS_DOMINANCE_MODE`** (default `flow_or_regime`): Mode for thesis dominance.
- **`DISPLACEMENT_LOG_EVERY_DECISION`** (default `true`): Log every displacement evaluate to system_events.

### New Logs / Events

- **`logs/system_events.jsonl`**: `subsystem=displacement`, `event_type=displacement_evaluated`, `severity=INFO`, `details={allowed, reason, ...}`.
- **`close_reason`** for displacement exits: `displaced_by_<SYMBOL>|delta=<x>|age_s=<y>|thesis=<reason>` (when policy diagnostics present).

### Toggle-Back (Revert Displacement Tuning)

Do **not** remove code; revert by config:

- `DISPLACEMENT_MIN_HOLD_SECONDS=0`
- `DISPLACEMENT_MIN_DELTA_SCORE=0`
- `DISPLACEMENT_REQUIRE_THESIS_DOMINANCE=false`

### Verification

```bash
python scripts/verify_alpha_upgrade.py
```

Exits non-zero on any FAIL. Checks: displacement policy present, displacement logging, shorts sanity, feature snapshot, shadow experiments (if enabled), EOD report.

### EOD Alpha Diagnostic

```bash
python reports/_daily_review_tools/generate_eod_alpha_diagnostic.py --date YYYY-MM-DD
```

Output: `reports/EOD_ALPHA_DIAGNOSTIC_<DATE>.md`. Headline PnL, win rate, top/bottom symbols, displacement summary, data availability.

### Displacement Logs / Variant Scoreboard

- **Displacement:** Filter `logs/system_events.jsonl` for `subsystem=displacement`, `event_type=displacement_evaluated`. Use `details.allowed`, `details.reason`, `details.delta_score`, `details.age_seconds` for audit.
- **Shadows / variants:** When shadow experiments enabled, see `logs/shadow.jsonl` for `event_type=shadow_variant_decision` and `shadow_variant_summary`.

---

## 6.10 ALPHA DISCOVERY (Thesis Tags, Directional Gate, Shadow Matrix) — 2026-01-27

### Thesis Tags

- **Module:** `telemetry/thesis_tags.py` — `derive_thesis_tags(snapshot) -> dict`
- **Tags:** `thesis_flow_continuation`, `thesis_flow_reversal`, `thesis_dark_pool_accumulation`, `thesis_dark_pool_distribution`, `thesis_premarket_gap_continuation`, `thesis_event_earnings_drift`, `thesis_congress_tailwind`, `thesis_insider_tailwind`, `thesis_regime_alignment_score` (0–1), `thesis_vol_expansion`, `thesis_vol_compression`
- **Contract:** Missing data => `None` (never silently `False`).

### Directional Gate (HIGH_VOL)

- **HIGH_VOL:** Top quartile `realized_vol_20d`. For HIGH_VOL only:
  - **Longs:** Require at least one of `thesis_flow_continuation`, `thesis_dark_pool_accumulation`, `thesis_regime_alignment_score >= 0.6`.
  - **Shorts:** Require at least one of `thesis_flow_reversal`, `thesis_dark_pool_distribution`, `thesis_regime_alignment_score <= 0.4`.
- **Logging:** `subsystem=directional_gate`, `event_type=blocked_high_vol_no_alignment`, `feature_snapshot`, `thesis_tags` in `logs/system_events.jsonl`. Does **not** reduce vol exposure; prevents directional guessing in volatile names.

### Shadow Experiment Matrix

- **Config:** `SHADOW_EXPERIMENTS_ENABLED`, `SHADOW_EXPERIMENTS` (list of variants), `SHADOW_MAX_VARIANTS_PER_CYCLE` (default 4).
- **Module:** `telemetry/shadow_experiments.py` — `run_shadow_variants(live_context, candidates, positions)`. Writes **only** to `logs/shadow.jsonl`; **no** live orders.
- **Events:** `shadow_variant_decision` (per symbol/variant), `shadow_variant_summary` (per variant/cycle).

### Trade / Exit Intent (Run Log)

- **`logs/run.jsonl`:** `event_type=trade_intent` (feature_snapshot, thesis_tags, displacement_context) at entry; `event_type=exit_intent` (feature_snapshot_at_exit, thesis_tags_at_exit, thesis_break_reason) at exit. Additive only.

### How to Interpret EOD Alpha Tables

- **Headline:** Total PnL, win rate, top/bottom symbols — same as before.
- **Winners vs Losers:** Counts; use for feature effect-size (mean winners vs mean losers) when you have trade-level snapshots.
- **Telemetry:** `trade_intent` / `exit_intent` counts and `directional_gate` blocks — confirm live decisions are explained.
- **Shadow scoreboard:** Per-variant `would_enter` / `would_exit` / blocked — use to see **what to turn up** (variants that would have traded more) and **what to turn down** (variants that block more).
- **Data availability:** PASS/FAIL per dataset; use substitutes when documented.

---

## 6.11 Phase-2 Activation (Log Sinks, Heartbeat, Verification) — 2026-01-27

### Config (env)

- **`PHASE2_TELEMETRY_ENABLED`** (default `true`): Gate trade_intent/exit_intent emission.
- **`PHASE2_HEARTBEAT_ENABLED`** (default `true`): Emit phase2_heartbeat once per cycle.
- **`PHASE2_REQUIRE_SYMBOL_RISK_FEATURES`** (default `true`): If symbol_risk missing, emit CRITICAL and set high_vol_count=0.

### Canonical Log Sinks

- **Startup:** `_phase2_confirm_log_sinks()` runs when bot starts (`__main__`). Ensures `logs/run.jsonl`, `logs/system_events.jsonl`, `logs/shadow.jsonl`, `logs/orders.jsonl` are writable.
- **Event:** `subsystem=phase2`, `event_type=log_sink_confirmed`, `details={resolved_paths, writable}`. If any not writable → CRITICAL + fail fast (exit 1).

### Phase-2 Heartbeat

- **Once per cycle** (after run_once + evaluate_exits): `subsystem=phase2`, `event_type=phase2_heartbeat`, `details={ts, cycle_id, telemetry_enabled, shadow_enabled, wrote_trade_intent_count_this_cycle, wrote_exit_intent_count_this_cycle, wrote_shadow_decision_count_this_cycle, symbol_risk_feature_count, high_vol_threshold, high_vol_symbol_count}`.
- If **`PHASE2_REQUIRE_SYMBOL_RISK_FEATURES`** and symbol_risk empty → `event_type=symbol_risk_missing_required`, `severity=CRITICAL` before heartbeat.

### Trade / Exit Intent (Extended)

- **trade_intent:** Emitted for **every** entry attempt (blocked or entered). Includes `decision_outcome` (`entered`|`blocked`), `blocked_reason` when blocked.
- **exit_intent:** `thesis_break_reason` required; use `unknown` + `thesis_break_unknown_reason` when indeterminable.

### Shadow

- After `run_shadow_variants`: `subsystem=phase2`, `event_type=shadow_variants_rotated`, `details={variants_run_this_cycle}`.
- Shadow **never** places orders; only writes to `logs/shadow.jsonl`.

### EOD Diagnostic

- **Sections:** Winners vs Losers, High-Volatility Alpha, Shadow Scoreboard, Data availability, **Section presence and FAIL reasons**.
- If a section cannot be populated (e.g. symbol_risk missing), report **explicit FAIL** reasons; do not silently omit.

### Verification (run on droplet)

1. **Restart** service safely; **wait 5 minutes** of runtime.
2. **Runtime identity:** `python3 scripts/phase2_runtime_identity.py` → `reports/PHASE2_RUNTIME_IDENTITY.md` (systemd units, WorkingDirectory, git rev, python path).
3. **Activation proof:** `python3 scripts/phase2_activation_proof.py --date YYYY-MM-DD` → `reports/PHASE2_ACTIVATION_PROOF_<DATE>.md` (heartbeats, trade_intent, shadow, symbol_risk, EOD, PASS/FAIL).
4. **Audit:** `python3 scripts/phase2_forensic_audit.py --date YYYY-MM-DD --local` → `reports/PHASE2_VERIFICATION_SUMMARY_<DATE>.md` + `exports/VERIFY_*.csv`.

**From local (fetch from droplet):**

```bash
python scripts/run_phase2_audit_on_droplet.py --date YYYY-MM-DD
```

Uploads audit/proof/runtime-identity scripts, runs them on droplet, fetches reports and CSVs.

**Success criteria:** phase2_heartbeat present; trade_intent present; shadow_variant_decision present (when enabled); symbol_risk_features.json exists and >0 symbols; EOD has all required sections.

---

# 10. DECISION INTELLIGENCE TRACE CONTRACT (2026-01)

Every trade or block decision MUST be explained by a **multi-layer intelligence trace**. There must never be a single opaque reason. Every decision must show: which signals fired, which opposed, how they combined, and why the final decision was made.

## 10.1 Schema: DecisionIntelligenceTrace

```text
DecisionIntelligenceTrace {
  intent_id          : str (UUID)
  symbol             : str
  side_intended      : str ("buy" | "sell")
  ts                 : str (ISO)
  cycle_id           : int | null

  signal_layers: {
    alpha_signals    : [{ name, value, score, direction, confidence }]
    flow_signals     : [{ name, value, score, direction, confidence }]
    regime_signals   : [{ name, value, score, direction, confidence }]
    volatility_signals : [{ name, value, score, direction, confidence }]
    dark_pool_signals  : [{ name, value, score, direction, confidence }]
  }

  opposing_signals   : [{ name, layer, reason, magnitude }]

  aggregation: {
    raw_score, normalized_score, direction_confidence, score_components
  }

  gates: {
    directional_gate : { passed, reason }
    risk_gate        : { passed, reason }
    capacity_gate    : { passed, reason }
    displacement_gate: { evaluated, passed, incumbent_symbol, challenger_delta, min_hold_remaining }
  }

  final_decision: {
    outcome          : "entered" | "blocked"
    primary_reason    : str
    secondary_reasons : [str]
  }
}
```

Object MUST be serializable and logged verbatim with every trade_intent.

## 10.2 Invariants

- **All trade_intent emits MUST include intelligence_trace.** Every emit (entered or blocked) must carry a populated trace; there are no exceptions once this contract is in force.
- **Coverage rule:** No block site may emit without a trace. Every call to `_emit_trade_intent` / `_emit_trade_intent_blocked` must pass `intelligence_trace`.
- **At least 2 signal layers** must contribute; otherwise the decision is INVALID.
- **Incremental build only:** use `build_initial_trace`, then `append_gate_result` per gate, then `set_final_decision` before emit. Gates and `final_decision` must always be present before emit.
- **Size cap:** serialized trace MUST be &lt; 500KB per trace.
- If **blocked**, `primary_reason` MUST map to a gate OR opposing signal.
- **No module overwrites another** when appending to the trace; each gate/signal appends only its own slice.

### 10.2.1 Missing-trace behavior

If a trade_intent is emitted with `decision_outcome` in `{entered, blocked}` and `intelligence_trace` is missing, the runtime MUST emit a **CRITICAL** system_event: `subsystem="telemetry"`, `event_type="missing_intelligence_trace"`, with `symbol`, `decision_outcome`, `blocked_reason` (if any). The trade_intent is still written (no crash); the CRITICAL event makes omissions impossible to ignore in production.

## 10.3 Blocked reason codes (enum)

Replace opaque `blocked_reason` strings with:

- `blocked_reason_code` — one of: `capacity_full`, `displacement_min_hold`, `displacement_no_dominance`, `displacement_blocked`, `displacement_failed`, `directional_conflict`, `blocked_high_vol_no_alignment`, `risk_exceeded`, `symbol_exposure_limit`, `sector_exposure_limit`, `opposing_signal_override`, `score_below_min`, `max_positions_reached`, `symbol_on_cooldown`, `momentum_ignition_filter`, `market_closed`, `long_only_blocked_short_entry`, `regime_blocked`, `concentration_gate`, `theme_exposure_blocked`, `other`.
- `blocked_reason_details` — structured: `{ primary_reason, gates }`. Each MUST reference the trace.

## 10.4 trade_intent extensions (additive only)

- `intent_id`
- `intelligence_trace` (full object)
- `active_signal_names[]`
- `opposing_signal_names[]`
- `gate_summary`
- `final_decision_primary_reason`
- When blocked: `blocked_reason_code`, `blocked_reason_details`

**DO NOT** remove existing fields (`blocked_reason` retained for backward compat).

## 10.5 Rules for future contributors

1. Every call to `_emit_trade_intent` / `_emit_trade_intent_blocked` MUST pass a populated `intelligence_trace` when telemetry is enabled.
2. Build the trace incrementally: `build_initial_trace` at decision start, `append_gate_result` at each gate, `set_final_decision` before emit.
3. Validate with `validate_trace()` before emit; if invalid, log and do not treat the decision as explained.
4. Dry-run validation: `python3 scripts/validate_intelligence_trace_dryrun.py` MUST pass (trace exists, ≥2 layers, gates populated, final_decision coherent, size &lt; 500KB).## WHEEL STRATEGY DASHBOARD INTEGRATION (2026-02-02)
- **strategy_id and wheel-specific fields** surfaced in stock-bot dashboard and API; no trade engine changes.
- **Dashboard:** Closed Trades tab shows strategy_id (Equity/Wheel), filter (All / Equity only / Wheel only), and wheel columns when strategy_id = wheel: wheel_phase, option_type, strike, expiry, dte, premium, assigned, called_away.
- **API:** `GET /api/stockbot/closed_trades` returns `closed_trades` (list) and `count`; each record has `strategy_id`, `wheel_phase`, `option_type`, `strike`, `expiry`, `dte`, `delta_at_entry`, `premium`, `assigned`, `called_away` (nullable for equity). `GET /api/stockbot/wheel_analytics` returns wheel-only metrics: premium_collected, assignment_rate_pct, call_away_rate_pct, expectancy_per_trade_usd, realized_pnl_sum.
- **Loader:** `dashboard._load_stock_closed_trades()` reads attribution.jsonl (closed trades with strategy_id from context) and telemetry.jsonl (strategy_id=wheel events); combines and sorts by timestamp.
- **Wheel Strategy tab:** Dedicated analytics panel (premium, assignment, call-away, expectancy); read-only.
- **Diagnostics:** `scripts/audit_stock_bot_readiness.py` check `stockbot_closed_trades_wheel_fields` verifies strategy_id and wheel phase/option metadata; `scripts/verify_dashboard_contracts.py` includes `/api/stockbot/closed_trades` and `/api/stockbot/wheel_analytics`. Full-integration dashboard check validates both endpoints.
- **Canonical field names:** Per wheel_strategy and MEMORY_BANK §2.2.1: strategy_id, phase (exposed as wheel_phase in API/UI), option_type, strike, expiry, dte, delta_at_entry, premium, assigned, called_away.
- **Deployment (live):** Pushed to GitHub; deployed to droplet via `deploy_dashboard_via_ssh.py` (git pull + dashboard restart only; no trade engine restart). Droplet at 104.236.102.57; dashboard at http://104.236.102.57:5000/. Post-deploy verification: `/api/stockbot/closed_trades` and `/api/stockbot/wheel_analytics` return 200 (verified 2026-02-02). To re-verify: `python scripts/verify_wheel_endpoints_on_droplet.py`.- **Dashboard endpoint map:** `reports/DASHBOARD_ENDPOINT_MAP.md` — canonical mapping of all API routes to data locations. All paths resolved against `_DASHBOARD_ROOT` (cwd-independent). Perf: XAI auditor max 3k lines; system_events tail-only read (~200KB); no engine data modified.

### Dashboard Data Mapping Audit (2026-02-05)
- **Closed trades:** `_load_stock_closed_trades` now reads `logs/attribution.jsonl`, `logs/exit_attribution.jsonl` (v2 equity exits), `logs/telemetry.jsonl`. Deduped by (symbol, timestamp). Paths resolved via `(_DASHBOARD_ROOT / LogFiles.*).resolve()`.
- **Wheel analytics:** Primary from closed_trades (strategy_id=wheel); fallback `reports/*_stock-bot_wheel.json`, `state/wheel_state.json` when logs empty.
- **Wheel universe health:** Primary `state/wheel_universe_health.json`; when missing, derives from `config/universe_wheel.yaml` and `state/daily_universe_v2.json` (no external script required).
- **Strategy comparison:** `reports/{date}_stock-bot_combined.json` from `scripts/generate_daily_strategy_reports.py`.
- **Regime/posture:** `state/market_context_v2.json`, `state/regime_posture_state.json`; paths resolved via _DASHBOARD_ROOT.
- **Rule:** Dashboard connects to logs/state/config only; NEVER modifies trading engine. See `reports/DASHBOARD_ENDPOINT_MAP.md`.

### Dashboard Rationalization Pass (2026-02-09)
- **Canonical layout:** See `docs/TRADING_DASHBOARD.md` for tab layout, data sources, and where to find Health, P&L, Wheel, and scoring.
- **Core cockpit (top-level):** Positions, Closed Trades, Executive Summary, SRE Monitoring. Health and P&L remain always visible via Top Strip and Executive Summary.
- **Strategy:** Wheel Strategy (includes Wheel Universe Health as sub-panel), Strategy Comparison.
- **Advanced (under “More” dropdown):** Signal Review, Natural Language Auditor, Trading Readiness, Telemetry.
- **Merged/removed from main bar:** Wheel Universe Health merged into Wheel Strategy tab (no data source removed).
- **Scoring labels:** UI shows “Entry Signal Strength” and “Current Signal Strength” (backend still `entry_score` / `current_score` from position metadata and live composite). Real values from engine; no legacy placeholders.
- **Top Strip:** Health (SRE), P&L today, P&L 7d, Last signal, Last update. Populated by `loadTopStrip()` (SRE health + executive summary 24h/7d).
- **Executive Summary:** Now includes Health & Wheel at a glance (from `/api/sre/health`, `/api/stockbot/wheel_analytics`).
- **Where to look:** Health → Executive Summary + SRE tab + Top Strip. P&L → Executive Summary + Positions + Closed Trades + Top Strip. Wheel → Wheel Strategy tab + Executive Summary + Closed Trades (filter). Scoring → Positions table columns (Entry/Current Signal Strength).

### Wheel Strategy Execution & Dashboard Data Activation (2026-02-09)
- **What was addressed:** Wheel had no explicit lifecycle logging; premium was not recorded on fill; dashboard could show zeros when wheel had not yet executed or when telemetry lacked premium.
- **Fixes:** (1) Explicit wheel lifecycle events in `logs/system_events.jsonl` (subsystem=wheel): wheel_run_started, wheel_csp_skipped (with reason), wheel_order_submitted, wheel_order_filled (with premium). (2) After each CSP order submit, wheel strategy polls Alpaca for fill (up to 5×2s); when filled, records **premium** (filled_avg_price × 100) in the same telemetry record. (3) Fallback DTE window: if no contracts in config DTE range, try up to 21 DTE once to allow one trade. (4) Regime is modifier-only; wheel is not gated by regime (comment in main.py and docs/REGIME_DETECTION.md).
- **How to validate:** (1) Run bot during market hours; check `logs/system_events.jsonl` for subsystem=wheel. (2) If a wheel order fills, check `logs/telemetry.jsonl` for strategy_id=wheel and non-null premium. (3) Dashboard Wheel Strategy tab and `/api/stockbot/wheel_analytics` show total_trades and premium_collected from telemetry + attribution. (4) Run `python scripts/generate_daily_strategy_reports.py`; confirm `reports/*_stock-bot_wheel.json` and combined report. (5) Scoring: Positions table uses entry_score from metadata and current_score from live composite (no static placeholders).

### Wheel root cause & verification playbook (2026-02-09)
- **Definitive outcome (ran on droplet 2026-02-09):** **A — Wheel NOT RUNNING.** Evidence: wheel_run_started = 0 in logs/system_events.jsonl; config had wheel.enabled = True. Root cause: **trading bot process had been running since Feb 07 and was never restarted after wheel-enabled code was deployed**; in-memory code never reached the wheel block. Full report: `reports/WHEEL_ROOT_CAUSE_REPORT_2026-02-09.md`.
- **Fix applied on droplet:** `sudo systemctl restart stock-bot` (new process 20:23 UTC 2026-02-09). **Deployment rule:** After pushing wheel or main-loop changes, restart stock-bot on droplet so the process loads new code.
- **Outcomes (for future runs):** Run `python3 scripts/wheel_root_cause_report.py --days 5` on droplet to get A/B/C/D.
- **Outcomes:** A = Wheel NOT RUNNING (scheduling/config/dispatch); B = RUNNING but ALWAYS SKIPPING (eligibility/universe/contracts); C = SUBMITTING but NOT FILLING (broker/liquidity/pricing); D = Pipeline/counting bug (dashboard or strategy_id/filter).
- **Fixes applied (minimum safe):** (1) Wheel now runs whenever `wheel.enabled` is true even if `strategy_context` fails to import (main.py: run wheel with or without context manager so dispatch is not blocked). (2) Wheel analytics contract test: `python3 scripts/test_wheel_analytics_contract.py` — given fixture with strategy_id=wheel and premium, analytics aggregation must report total_trades ≥ 1 and premium_collected ≥ 0 (for CI/regression). (3) Regime remains modifier-only; no gating.
- **Verification (next cycle):** (1) On droplet, run `wheel_root_cause_report.py --days 5` and open the generated report. (2) If A: confirm strategies.yaml wheel.enabled and that no exception prevents wheel invocation. (3) If B: use report’s skip-reason table; address top reasons (universe/DTE/limits) without relaxing risk limits broadly. (4) If C: inspect last submitted orders; improve order type/price within policy; add “not filled because …” logs. (5) If D: ensure _load_stock_closed_trades and wheel_analytics filter include strategy_id=wheel; run contract test. (6) Truth checks: wheel_run_started each cycle; skip reasons logged if skipping; order_submitted/order_filled with order_id/premium when applicable; telemetry and dashboard analytics consistent.
- **Docs:** `docs/TRADING_DASHBOARD.md` §8 — Wheel troubleshooting (where to look: system_events, telemetry, state, endpoint; how to interpret A/B/C/D; diagnostic script; regime = modifier-only).

### Droplet wheel check (2026-02-10)
- **Ran via SSH:** `python scripts/run_wheel_check_on_droplet.py` (uses DropletClient; full output in `reports/droplet_wheel_check_YYYY-MM-DD.txt`).
- **Result:** **Outcome B — Wheel RUNNING but ALWAYS SKIPPING.** wheel_run_started = 30 (last 7 days), wheel_order_submitted = 0, wheel_order_filled = 0. **Blocking reason: no_spot (840 skips).** Every candidate is skipped because `api.get_quote(symbol)` returns no valid bid/ask (spot <= 0 or exception) in `strategies/wheel_strategy.py` _run_csp_phase().
- **Root cause:** Alpaca quote API (paper) shape mismatch — quote object may use different attribute names or return None/partial; narrow spot extraction (ap/ask_price only) failed for all symbols.

### Wheel spot resolution — Alpaca contract and verification (2026-02-10)
- **Alpaca quote contract (definitive):** `normalize_alpaca_quote(raw_quote)` in `strategies/wheel_strategy.py` — accepts raw `api.get_quote()` return; never raises; returns None only if raw_quote is None. Normalized dict: `ask`, `bid`, `last_trade` (float | None), `source_fields_present` (list of field names found). Handles object and dict; extracts ap/ask_price/askprice, bp/bid_price/bidprice, last_trade.price|p.
- **Single spot resolution:** `resolve_spot_from_market_data(normalized_quote, bar_close)` — only place spot is resolved. Order: ask > bid > last_trade > bar_close; returns (spot_price, spot_source) or (None, None). CSP and CC both use `_resolve_spot(api, symbol)` which gets quote → normalize → get bar close → resolve_spot_from_market_data → emit telemetry.
- **Telemetry (mandatory):** Every attempt emits either **wheel_spot_resolved** (symbol, spot_price, spot_source, quote_fields_present, bar_used) or **wheel_spot_unavailable** (symbol, quote_fields_present, bar_attempted). no_spot skip occurs only when wheel_spot_unavailable was emitted.
- **Verification report:** `python3 scripts/wheel_spot_resolution_verification.py --days 7` → `reports/wheel_spot_resolution_verification_<date>.md` (counts resolved vs unavailable, spot_source distribution, first option-chain reach, wheel_order_submitted/filled, next blocker with evidence).
- **Droplet check assertion:** `scripts/run_wheel_check_on_droplet.py` runs the verification script and **fails with exit 1** if wheel_spot_resolved == 0 and wheel_spot_unavailable > 0 (no spot resolved during market hours).
- **Verification commands:** After deploy + restart: `python3 scripts/run_wheel_check_on_droplet.py`; inspect `reports/wheel_spot_resolution_verification_*.md` and `grep '"event_type": "wheel_spot_resolved"' logs/system_events.jsonl | tail -5`.

---
## Profitability Push (2026-02-09)
- **LIVE (deployed):** (1) **Exit logic:** No "unknown" exit reasons; every exit maps to concrete reason (signal_decay, stop, regime_shift, risk, etc.). Fallback is "risk". Regime-aware exit timing (BEAR: cut losers faster -0.8% stop, let winners run longer 1.0% target; modifiers only, no gating). Telemetry: exit_reason_recorded per close in system_events (subsystem=exit). (2) **Displacement:** BEAR + high-confidence (score >= 7): relaxed score advantage and PnL band for displacement. Log when displacement blocks: displacement_blocked_no_candidate (symbol, new_signal_score, regime) in system_events. (3) **Wheel:** Runs every cycle when enabled; lifecycle events (wheel_run_started, wheel_csp_skipped, wheel_order_submitted, wheel_order_filled). Restart stock-bot after deploy so wheel runs.
- **Board:** Customer Advocate, Innovation Officer, SRE roles in config/ai_board_roles.json. Board output must include: top_3_root_causes_pnl_degradation, top_3_concrete_actions_next, expected_impact_per_action, success_failure_measured_in_3_5_days. Contract: board/stock_quant_officer_contract.md — prescription mandatory; Customer Advocate must disagree when results poor.
- **Wheel as profit engine:** Role: income stabilizer and drawdown reducer. Track: premium collected per day, expectancy per wheel trade (dashboard /api/stockbot/wheel_analytics: expectancy_per_trade_usd, premium_collected), correlation with equity P&L. Compare wheel vs equity contribution weekly (reports, dashboard).
- **Multi-day expectancy:** Board must answer "Is expectancy improving?" over 3, 5, 7 days. If not after 5–7 days: change strategy, reduce frequency, re-evaluate edge.
- **Regime:** Modifier-only; never gates trading.

---
## Wheel Strategy Audit — PATH B (2026-02-09)
- **Decision:** PATH B. Wheel was **not** using UW intelligence: selector used only Alpaca volume/OI/spread and stub IV; no UW cache or composite score.
- **Evidence:** `strategies/wheel_universe_selector.py` had no reads of `uw_flow_cache` or `uw_composite_v2`; ranking was by `wheel_suitability_score` (liquidity*0.4 + iv*0.3 + spread*0.3). Hard filters (spot, contracts) ran per-ticker in order of that list.
- **Fix applied:** (1) **UW-first ranking:** In `wheel_universe_selector`, added `_rank_by_uw_intelligence()` — reads `CacheFiles.UW_FLOW_CACHE`, gets regime from state, calls `uw_composite_v2.compute_composite_score_v2(symbol, enriched, regime)` per symbol; sorts by UW score descending; top N become the candidate list. (2) **Order of operations:** Sector/earnings/count filter → UW rank → take top `universe_max_candidates` → hard filters (spot, contracts) only in `_run_csp_phase` per-ticker. (3) **Explainability:** Every cycle emits `wheel_candidate_ranked` (subsystem=wheel) with top_5_symbols, top_5_uw_scores, chosen or reason_none.
- **Wheel intelligence contract:** Primary driver = UW composite score from `data/uw_flow_cache.json` + `uw_composite_v2.compute_composite_score_v2`. Secondary = liquidity/OI/spread (for telemetry). Spot and contract availability are hard filters applied only to the UW-ranked list. Regime is modifier-only (used in composite call).
- **Verification:** On droplet, `grep wheel_candidate_ranked logs/system_events.jsonl` and `wheel_root_cause_report.py --days 1`; expect wheel_run_started, wheel_candidate_ranked, and wheel_csp_skipped with reasons. See `docs/TRADING_DASHBOARD.md` §6.1.

---
## Wheel Dry-Run Validation (Market-Closed) (2026-02-09)
- **Purpose:** Prove UW-first ranking and `wheel_candidate_ranked` emission without live quotes, options chains, or market hours. No broker calls; deterministic test.
- **Command (run from repo root, e.g. on droplet):**  
  `python3 scripts/wheel_dry_run_rank.py`
- **Expected stdout:** Ranked candidates (symbol, uw_score) then final line: `wheel_candidate_ranked emitted successfully`.
- **Verify event:**  
  `grep '"event_type": "wheel_candidate_ranked"' logs/system_events.jsonl | tail -1`  
  Expect: non-empty `top_5_symbols`, UW scores present, `chosen` = null, `reason_none` = `"dry_run_rank_only"`.
- **Interpretation:** If dry-run emits correctly → ranking path is wired; zero count during market-closed hours is expected; live wheel will emit during market hours. If dry-run does NOT emit → systemic wiring issue; fix before market open.
- **Docs:** See `docs/TRADING_DASHBOARD.md` §6.1 (validate wheel intelligence without market hours).

---
## CRON + GIT DIAGNOSTIC (2026-02-04)
- **Detected path:** /root/stock-bot
- **Cron:** crontab has EOD entry with correct path (21:30 UTC); audit+sync 21:32 UTC via run_droplet_audit_and_sync.sh
- **Git push:** push OK (if transient ref-lock on remote, retry or push from local)
- **Report generation:** EOD dry-run OK
- **Operational readiness audit (droplet):** All CRITICAL checks passed (2026-02-04). MEDIUM unified_daily_intelligence_pack: **addressed** — run_droplet_audit_and_sync.sh now runs run_stockbot_daily_reports.py for $DATE before the audit and adds reports/stockbot/$DATE to the sync commit.
- **Repairs applied:** (parity: config/strategies, universe_wheel, universe_wheel_expanded, strategies/, main.py duplicate composite_meta removed; audit+sync generates daily pack before audit)

---
## Strategy Sovereignty (2026-02-05)
- Wheel and Equity are independent institutions.
- No cross-strategy displacement.
- Separate capital, exits, promotion metrics.
- Dashboard and AI board are strategy-aware.
- **Config:** `config/strategy_governance.json` — position caps, capital fractions, displacement rules, exit policies, promotion metrics per strategy.
- **Exit policies:** `src/exit/wheel_exit_v1.py` (wheel: time + premium decay); equity uses equity_exit_v2.
- **Analytics:** `scripts/aggregate_strategy_pnl.py` → `artifacts/strategy_pnl.json` (EQUITY/WHEEL segmented PnL).
- **AI Board:** `config/ai_board_roles.json` — adversarial review roles (Equity Skeptic, Wheel Advocate, Risk Officer, Promotion Judge); require_disagreement and require_synthesis.

---
## Mode divergence contract (2026-02-05)
- LIVE, PAPER, SHADOW must not be symmetric.
- LIVE changes are small and controlled; PAPER changes are meaningful; SHADOW changes are aggressive.
- Mode governance lives in `config/mode_governance.json` and must be resolved per-trade to avoid bleed.
- Analytics must include mode+strategy rollups (`artifacts/mode_strategy_pnl.json`) for promotion decisions.
- **Script:** `scripts/aggregate_mode_strategy_pnl.py` — produces mode:strategy buckets (LIVE:EQUITY, PAPER:WHEEL, etc.).
- **Contract:** non_interference (mode settings resolved at decision-time per trade); promotion only from PAPER/SHADOW into LIVE after evidence.

---
## Exit timing + scenario replay initiative (2026-02-07)
- Added config/exit_timing_scenarios.json to explore multi-hour to multi-day hold floors and reduced decay/displacement sensitivity.
- Implemented src/governance/governance_loader.py to load/resolve (strategy_governance, mode_governance, exit_timing_scenarios) into a per-decision policy blob.
- Added scripts/replay_week_multi_scenario.py to generate a scenario replay report from droplet-captured artifacts; defaults to diagnostics-only unless a canonical counterfactual replay engine is present.
- Added config/ai_board_exit_research_addendum.json requiring hold-time expectancy analysis, exit-reason expectancy, and explicit data demands for unbiased counterfactual replays.

## Exit timing enforcement shim (2026-02-07)
- Added src/governance/apply_exit_timing_policy.py as a non-breaking enforcement shim.
- Runtime must call apply_exit_timing_to_exit_config(...) during exit evaluation to enforce scenario params.
- If not called, behavior remains unchanged (safe by default).

## Alpaca market data capture + counterfactual exit replay (2026-02-07)
- Added src/exit/exit_attribution_enrich.py and patched src/exit/exit_attribution.py to enrich exit rows with mode, strategy, regime_label, and entry/exit fields when available.
- Added scripts/fetch_alpaca_bars.py to pull historical bars from Alpaca Market Data API for recent traded symbols.
- Added scripts/replay_exit_timing_counterfactuals.py to run exit-only counterfactual replays for hold-floor scenarios (no forward-looking entry optimization).
- Governance requirement: exit_attribution rows must include mode+strategy (and ideally entry_ts/entry_price/qty) to enable mode:strategy bucketing and unbiased exit timing research.

## Pre-Monday instrumentation and Cursor governance (2026-02-07)
- Added replay-readiness sanity check to ensure exits are replayable.
- Locked AI Board mandate to exit timing and hold-duration analysis.
- Wrote explicit promotion and rollback criteria before results.
- Introduced .cursorrules to encode governance invariants and prevent drift.

## Board output packaging and AI Board workflow upgrade (2026-02-07)
- Added `scripts/board_daily_packager.py` to create dated folders under `board/eod/out/YYYY-MM-DD/` with:
  - `daily_board_review.md` (combined markdown artifacts).
  - `daily_board_review.json` (combined JSON artifacts).
- Updated `.cursorrules` with:
  - AI Board Charter and Invocation Protocol.
  - Automatic (cron) and manual Board Review triggers.
  - Multi-model, multi-agent execution guidance.
  - Conflict handling and multi-idea requirements.
  - Innovation Officer "What else?" mandate.
  - Customer Profit Advocate escalation.
- Added `docs/BOARD_REVIEW.md` documenting the daily Board Review workflow and how to test it.

## Board Upgrade V2 (2026-02-07)
- Strengthened all agents with adversarial, multi-option, and evidence-based mandates.
- Added yesterday's commitments tracking.
- Added multi-model execution requirement.
- Added deeper Innovation Officer and SRE Officer mandates.
- Updated .cursorrules with V2 governance rules.

## Board Upgrade V3 — Multi-Day Intelligence (2026-02-08)
- **Multi-Day Analysis Module:** `scripts/run_multi_day_analysis.py` — runs automatically after daily EOD pipeline; computes rolling 3-day, 5-day, 7-day windows; outputs `board/eod/out/YYYY-MM-DD/multi_day_analysis.json` and `.md`. Metrics: regime persistence/transition, volatility trend, sector rotation, attribution vs exit, churn, hold-time, exit-reason distribution, blocked trades (displacement/max positions/capacity), displacement sensitivity, capacity utilization, expectancy, MAE/MFE.
- **Regime Review Officer:** New agent (`.cursor/agents/regime_review_officer.json`) — analyzes 3/5/7-day regime behavior, detects transitions, identifies misalignment, produces 2–3 regime-aware options. Must participate in every Board Review.
- **Updated Agents:** All agents now read multi-day analysis, incorporate multi-day trends, produce multi-day options, track multi-day commitments (1/3/5-day).
- **Multi-Day Board Review Sections:** Daily Board Review includes multi-day regime summary, multi-day P&L & risk, multi-day exit & churn, multi-day blocked trades, multi-day innovation opportunities, multi-day promotion review.
- **Multi-Day Commitments:** Extended from yesterday's commitments to 1-day, 3-day, 5-day commitments. Board reports: Completed, Not completed, Blocked, Needs escalation. Customer Profit Advocate challenges incomplete commitments.
- **Board Packager:** `scripts/board_daily_packager.py` now includes `multi_day_analysis.json` and `.md` in combined outputs.
- **Cron Integration:** After EOD pipeline: run multi-day analysis → run V3 Board Review → package → commit → push → deploy.
- **Governance:** `.cursorrules` updated with V3 mandates: multi-day analysis required, Regime Review Officer participation, multi-day evidence required for LIVE/PAPER changes, multi-day scenario replay for exit timing.
- **Documentation:** `docs/BOARD_REVIEW.md` updated, `docs/BOARD_UPGRADE_V2.md` references V3, `docs/BOARD_UPGRADE_V3.md` created.

## Remediation Pass: Regime, Exit Timing, Displacement, Attribution (2026-02-08)
- **Regime detection fix:** Stockbot daily pack was reading regime from top level of `daily_universe_v2.json`; regime is under `_meta`. Fixed in `scripts/run_stockbot_daily_reports.py` to read `(v2.get("_meta") or {}).get("regime_label")` with fallback `"NEUTRAL"` so multi-day analysis no longer shows UNKNOWN for all days.
- **Regime never a gate:** `ENABLE_REGIME_GATING` default changed from `true` to `false` in `main.py`. Regime is a modifier only (sizing, filters, preferences); it must never fully block trading. See `docs/REGIME_DETECTION.md`.
- **Exit timing shim wired:** `apply_exit_timing_to_exit_config` is now called at the start of `evaluate_exits()`; policy is applied from `config/exit_timing_scenarios.json` (mode/strategy/regime/scenario). Min-hold floor is enforced before adding a position to the close list; skips logged as `hold_floor_skipped`. Scenario set via `EXIT_TIMING_SCENARIO` (default `baseline_current`).
- **Diagnostics added:** `scripts/regime_detection_diagnostic.py`, `scripts/exit_timing_diagnostic.py`, `scripts/displacement_capacity_diagnostic.py`, `scripts/attribution_exit_reconciliation.py` for regime, exit timing by reason/mode:strategy, displacement/capacity blocked counts, and attribution vs exit PnL reconciliation.
- **Displacement/capacity:** Documented in `docs/CAPACITY_AND_DISPLACEMENT.md`. Regime can influence policy but never set capacity to zero or fully block. Displacement decisions already logged to `logs/system_events.jsonl` (subsystem=displacement).
- **Board reasoning:** Board agents should treat regime as modifier-only; ask explicitly about regime health, exit timing health, displacement/capacity health, and attribution vs exit alignment. See `docs/BOARD_REVIEW.md` interpretation notes.
---

