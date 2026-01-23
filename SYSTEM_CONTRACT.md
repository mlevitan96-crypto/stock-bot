# SYSTEM_CONTRACT.md
**Author:** Mark  
**Purpose:** Define the non‑negotiable architectural, operational, and safety invariants that govern the stock‑bot system.  
**Audience:** Cursor, developers, and any future automation touching this codebase.  
**Status:** Binding. These rules MUST be preserved unless explicitly revised by Mark.

---

# 1. Architectural Invariants

These rules define how the system is structured. They MUST NEVER be violated.

### 1.1 Engine Startup Model
- `main.py` MUST NOT start any loops, threads, or processes on import.
- The trading engine MUST ONLY start when executed directly (`python main.py`).
- The trading engine MUST be launched as a supervised subprocess by `deploy_supervisor.py`.

### 1.2 Supervisor as Single Authority
- `deploy_supervisor.py` is the ONLY component allowed to:
  - start the engine  
  - restart the engine  
  - stop the engine  
- No other module may spawn or manage the trading engine.

### 1.3 No Import‑Time Side Effects
- No module in the repo may start background work on import.
- Importing any file MUST be safe and inert.

---

# 2. Engine Resilience Guarantees

These rules ensure the trading engine cannot silently die or stall.

### 2.1 Worker Loop Must Never Die Silently
- The worker loop MUST continue running regardless of internal failures.
- All exceptions inside `run_once()` MUST be caught and converted into degraded metrics.

### 2.2 Heartbeat & Cycle Logging
Every cycle MUST update:
- `state/bot_heartbeat.json`
- `logs/run.jsonl` with:
  - `engine_status: ok | degraded`
  - `errors_this_cycle: [] or list of strings`

### 2.3 No Unhandled Exceptions
- Displacement, exit logic, reconciliation, attribution, and scoring MUST NOT raise uncaught exceptions.
- All dictionary access MUST use `.get()` with safe defaults.

---

# 3. State File Rules (Self‑Healing Required)

### 3.1 JSON Reads Must Be Self‑Healing
All state file reads MUST:
- use the self‑healing loader  
- quarantine corrupted files as `*.corrupted.<timestamp>.json`  
- recreate a minimal valid default  
- log a structured event  

### 3.2 State Files Must Never Crash the Engine
- No state file may cause the engine or supervisor to exit.
- Corruption MUST degrade gracefully.

---

# 4. UW Flow Cache Contract

### 4.1 Canonical Path
The ONLY valid UW cache path is:

```
data/uw_flow_cache.json
```

### 4.2 Single Source of Truth
- Both the daemon and the engine MUST read/write this exact file.
- No other path may be used for UW data.

### 4.5 UW Intelligence Layer (Additive, v2-only)
This section adds a *new* UW intelligence layer WITHOUT changing the v1 flow cache contract above.

Contracts:
- `data/uw_flow_cache.json` remains the canonical v1 UW flow cache (engine + daemon).
- The v2 intelligence layer MAY use additional state files under `state/` for:
  - rate limiting + usage accounting: `state/uw_usage_state.json`
  - cached UW API responses: `state/uw_cache/`
  - daily universe: `state/daily_universe.json`, `state/core_universe.json`
  - pre/post intel: `state/premarket_intel.json`, `state/postmarket_intel.json`
- All UW HTTP calls for the v2 intelligence layer MUST route through:
  - `src/uw/uw_client.py`
- Symbol-level UW calls MUST be restricted to:
  - `daily_universe ∪ core_universe`
- v2 remains shadow-only until `COMPOSITE_VERSION` is manually flipped.

### 4.8 UW Endpoint Validation Contract
To permanently prevent silent 404s and hallucinated URLs:
- The official Unusual Whales OpenAPI spec MUST be present at:
  - `unusual_whales_api/api_spec.yaml`
- The system MUST load valid UW endpoint paths from that spec (OpenAPI `paths`).
- The centralized UW client (`src/uw/uw_client.py`) MUST reject any endpoint not in the spec:
  - Must log `event_type="uw_invalid_endpoint_attempt"`
  - Must raise `ValueError` *before* rate limiting, caching, or network calls
- Regression MUST fail if:
  - the spec is missing/corrupt, or has an unexpectedly small path set
  - any UW endpoint used in code is not present in the spec (static audit)
- No code may bypass `uw_client` for UW HTTP calls.

### 4.9 UW Polling Single-Instance Contract (Droplet)
To prevent quota waste and inconsistent cache writes:
- `uw_flow_daemon.py` MUST run as a **single instance** on the droplet.
- Canonical runner is systemd unit:
  - `uw-flow-daemon.service` (repo template: `deploy/systemd/uw-flow-daemon.service`)
- The daemon MUST also enforce a process-level single-instance guard via a file lock:
  - `state/uw_flow_daemon.lock`
- Any attempted second instance MUST exit and log:
  - `subsystem="uw_poll" event_type="uw_flow_daemon_already_running"`

### 4.6 UW Intelligence Execution Contract
The UW intelligence lifecycle MUST be executed in this order:
- **Universe build (daily, before market open)**:
  - `scripts/build_daily_universe.py` → `state/daily_universe.json`, `state/core_universe.json`
- **Premarket intel (before market open)**:
  - `scripts/run_premarket_intel.py` → `state/premarket_intel.json`
- **Postmarket intel (after market close)**:
  - `scripts/run_postmarket_intel.py` → `state/postmarket_intel.json`

Additional rules:
- All UW calls MUST route through `src/uw/uw_client.py`.
- UW symbol-level calls MUST be restricted to `daily_universe ∪ core_universe`.
- v2 composite scoring MUST read UW intel from state files only (no live UW calls during scoring).

### 4.7 Droplet Execution + State Sync Contract
Droplet runners are an operational convenience and MUST NOT affect live trading behavior.

Rules:
- Droplet execution MUST run scripts in the correct order and MUST stop if regression fails.
- Droplet state files MUST persist under `state/` on the droplet.
- Local sync MUST store fetched artifacts under: `droplet_sync/YYYY-MM-DD/`
- Local sync MUST append to: `droplet_sync/YYYY-MM-DD/sync_log.jsonl`
- Sync failures MUST be logged and MUST NOT break v1.

Canonical runner:
- `scripts/run_uw_intel_on_droplet.py`

### 4.10 Intelligence Attribution & P&L Contract (v2-only, additive)
Inputs:
- v2 composite scoring outputs (shadow-only)
- UW intel state files: `state/premarket_intel.json`, `state/postmarket_intel.json`
- Exit/PnL sources (best-effort): `logs/exits.jsonl`, `logs/shadow.jsonl`

Outputs:
- Attribution stream (append-only): `logs/uw_attribution.jsonl`
- Daily Intel P&L report: `reports/UW_INTEL_PNL_YYYY-MM-DD.md`
- Daily Intel P&L summary state: `state/uw_intel_pnl_summary.json`

Rules:
- Attribution MUST be non-blocking (never crash scoring).
- Attribution + P&L MUST NOT affect v1 trading behavior.
- P&L generation may be sparse if exit logs are unavailable; it must still run safely.

### 4.11 Sector & Regime Awareness Contract (v2-only, additive)
Sector:
- Profiles live in: `config/sector_profiles.json`
- Resolver lives in: `src/intel/sector_intel.py`
- Unknown symbols MUST default to sector=`UNKNOWN` and multipliers=1.0.

Regime:
- Engine lives in: `src/intel/regime_detector.py`
- Output state lives in: `state/regime_state.json`
- Engine MUST be safe-by-default and must not require live network calls.

### 4.12 Universe Scoring v2 Contract (shadow-only)
Inputs:
- Symbol risk features: `state/symbol_risk_features.json`
- Regime snapshot: `state/regime_state.json` (if present)
- Sector profiles (optional): `config/sector_profiles.json`

Outputs:
- v1 outputs (unchanged): `state/daily_universe.json`, `state/core_universe.json`
- v2 output (additive, shadow-only): `state/daily_universe_v2.json`

Rules:
- v2 universe output MUST NOT be consumed by v1 trading without explicit promotion.
- v1 universe behavior must remain unchanged.

### 4.13 Composite v2 Tuning Contract (shadow-only)
Rules:
- v2 composite MUST read UW intel only from state files (no live UW calls in scoring).
- Sector/regime multipliers MAY shape v2 UW adjustments, but MUST NOT affect v1.
- v2 metadata MUST be logged in the v2 output dict (inputs/versions).

### 4.14 Intel Dashboard Contract (additive)
Generator:
- `reports/_dashboard/intel_dashboard_generator.py`

Output:
- `reports/INTEL_DASHBOARD_YYYY-MM-DD.md`

Rules:
- Dashboard MUST be derivable from state/logs only (no live network calls).
- Dashboard generation MUST be safe (never crashes engine).

### 4.15 Health & Self-Healing Contract (additive)
Health check runner:
- `scripts/run_intel_health_checks.py`

Output:
- `state/intel_health_state.json`

Rules:
- Health checks MUST validate freshness + schema and report status.
- Self-heal attempts (when enabled) MUST be best-effort and MUST NOT impact v1 trading.

### 4.16 UW Flow Daemon Health Contract
Sentinel:
- `scripts/run_daemon_health_check.py`

Output:
- `state/uw_daemon_health_state.json`

Rules:
- The daemon MUST run as a single instance under systemd:
  - `uw-flow-daemon.service`
- The daemon MUST hold:
  - `state/uw_flow_daemon.lock`
- The daemon MUST produce fresh polling output:
  - canonical output file is `data/uw_flow_cache.json`
- The sentinel MUST validate:
  - systemd `ExecMainPID` exists and is alive on droplet (`/proc/<pid>`)
  - lock exists, appears held, and best-effort PID match via lock file contents
  - polling output freshness
  - crash loop risk via systemd restart counters
  - endpoint error spikes via `logs/system_events.jsonl` events:
    - `uw_rate_limit_block`
    - `uw_invalid_endpoint_attempt`
- The sentinel MUST log health summary events:
  - `uw_daemon_health_ok`
  - `uw_daemon_health_warning`
  - `uw_daemon_health_critical`
- On critical failures, sentinel MAY attempt safe restart only when explicitly enabled:
  - `systemctl restart uw-flow-daemon.service`
  - Must log: `uw_daemon_self_heal_attempt` and success/failure events.
- Sentinel MUST be additive and MUST NOT modify v1 trading behavior or trading state.

### 4.17 Shadow Trading Contract (v2)
Rules:
- v1 remains the ONLY live trading path.
- v2 MUST be shadow-only:
  - MUST never submit live orders
  - MUST log decisions for review
- v2 MUST use the full intelligence layer via state files:
  - `state/daily_universe_v2.json` (fallback `state/daily_universe.json`)
  - `state/premarket_intel.json`
  - `state/postmarket_intel.json`
  - `state/regime_state.json`
  - sector profiles from `config/sector_profiles.json`
- Shadow decision log:
  - `logs/shadow_trades.jsonl`
- Shadow position state (simulator persistence):
  - `state/shadow_v2_positions.json` (atomic updates; no live orders)
- Exit attribution (shadow exits only):
  - `logs/exit_attribution.jsonl`
- Pre-open readiness MUST run on droplet before market open:
  - `scripts/run_preopen_readiness_check.py`
  - MUST fail if daemon health is `critical` or intel artifacts are stale/missing
  - MUST require `scripts/run_regression_checks.py` pass (unless explicitly skipped for regression harness)

### 4.18 Exit Intelligence Contract (v2, shadow-only)
Rules:
- v1 exit logic is sacred and MUST NOT be modified.
- v2 exit logic is shadow-only until explicitly promoted:
  - MUST never submit live exit orders
  - MUST log every exit decision and its attribution

Exit attribution:
- Engine: `src/exit/exit_attribution.py`
- Output: `logs/exit_attribution.jsonl` (append-only)

Exit score:
- Engine: `src/exit/exit_score_v2.py`
- MUST combine UW/sector/regime + deterioration metrics + thesis flags (best-effort).

Dynamic targets/stops:
- Profit targets: `src/exit/profit_targets_v2.py`
- Stops: `src/exit/stops_v2.py`
- MUST be used by v2 exit decisions when inputs are available (best-effort).

Replacement:
- Engine: `src/exit/replacement_logic_v2.py`
- Replacement MUST require exit_score above threshold AND a superior candidate per margin.

Pre/post-market exit intel:
- `scripts/run_premarket_exit_intel.py` → `state/premarket_exit_intel.json`
- `scripts/run_postmarket_exit_intel.py` → `state/postmarket_exit_intel.json`

Exit analytics:
- `scripts/run_exit_intel_pnl.py` → `state/exit_intel_pnl_summary.json`, `reports/EXIT_INTEL_PNL_YYYY-MM-DD.md`
- `scripts/run_exit_day_summary.py` → `reports/EXIT_DAY_SUMMARY_YYYY-MM-DD.md`

Dashboard:
- Intel dashboard MUST display “Exit Intelligence Snapshot (v2)” derived from exit logs/state only.

### 4.19 Post-Close Analysis Contract (additive)
Purpose:
- After each market session, the system MUST be able to generate a single, comprehensive “analysis pack” for human review and v2 promotion decisions.

Generator:
- `scripts/run_postclose_analysis_pack.py`

Outputs:
- Folder: `analysis_packs/YYYY-MM-DD/`
- Master report: `analysis_packs/YYYY-MM-DD/MASTER_SUMMARY_YYYY-MM-DD.md`
- Best-effort copies of relevant state + reports + log tails under the pack folder.

Rules:
- MUST be additive and MUST NOT affect v1 trading behavior.
- MUST be derivable from state/logs only (no required live network calls).
- MUST be safe-by-default: missing artifacts are recorded; the pack still generates.
- Droplet runner MAY sync the pack via:
  - `scripts/run_uw_intel_on_droplet.py --postclose-pack`
  - Synced location: `droplet_sync/YYYY-MM-DD/analysis_packs/YYYY-MM-DD/`

### 4.20 Telemetry Completeness + Equalizer Contracts (v2-only, additive)
These invariants define what “complete telemetry” means for v2 shadow promotion decisions.

#### 4.20.1 Read-only + v1-safe (non-negotiable)
- Telemetry builders MUST be **read-only** (no trading logic changes, no order placement, no state mutation beyond writing into `telemetry/YYYY-MM-DD/`).
- Telemetry builders MUST be **idempotent** for a given date (same inputs → same outputs).
- Telemetry builders MUST be **best-effort**: missing inputs are recorded; bundle still generates.

#### 4.20.2 Required daily telemetry bundle (droplet-source-of-truth)
Generator:
- `scripts/run_full_telemetry_extract.py --date YYYY-MM-DD`

Required output folder:
- `telemetry/YYYY-MM-DD/`

Required output files:
- `telemetry/YYYY-MM-DD/FULL_TELEMETRY_YYYY-MM-DD.md`
- `telemetry/YYYY-MM-DD/telemetry_manifest.json`
- `telemetry/YYYY-MM-DD/computed/` containing:
  - `feature_equalizer_builder.json`
  - `long_short_analysis.json`
  - `exit_intel_completeness.json`
  - `feature_value_curves.json`
  - `regime_sector_feature_matrix.json`
  - `shadow_vs_live_parity.json`
  - `entry_parity_details.json`
  - `score_distribution_curves.json`
  - `regime_timeline.json`
  - `feature_family_summary.json`
  - `replacement_telemetry_expanded.json`
  - `live_vs_shadow_pnl.json`
  - `signal_performance.json`
  - `signal_weight_recommendations.json`

#### 4.20.3 Exit-intel completeness invariants
Exit attribution records (`logs/exit_attribution.jsonl`) are considered “complete enough for debugging” when:
- Top-level keys exist (best-effort):
  - `pnl`, `pnl_pct`, `entry_price`, `exit_price`, `qty`, `time_in_trade_minutes`
  - `entry_regime`, `exit_regime`
  - `entry_sector_profile`, `exit_sector_profile`
  - `v2_exit_score`, `v2_exit_components`
- `v2_exit_components` includes the following keys (best-effort; tracked as missing when absent):
  - `vol_expansion`, `regime_shift`, `sector_shift`
  - `flow_deterioration`, `darkpool_deterioration`, `sentiment_deterioration`
  - `score_deterioration`

Rule:
- Missing fields MUST NOT crash telemetry generation; they MUST be counted and reported in `exit_intel_completeness.json`.

#### 4.20.4 Long/short asymmetry invariants
Telemetry MUST compute, at minimum:
- win-rate, avg PnL, avg win, avg loss, expectancy for:
  - overall
  - long-only
  - short-only

#### 4.20.5 Feature equalizer invariants
Telemetry MUST produce “equalizer-ready” structures mapping feature strength to realized outcomes:
- Per-feature realized PnL summaries (overall + by long/short) using v2 shadow exits only.
- Per-feature value curves (binned/quantiled) with counts per bin and avg realized PnL per bin.
- Regime-aware and sector-aware feature summaries (matrix output).

#### 4.20.6 Replacement logic telemetry invariants
Telemetry MUST capture replacement behavior (best-effort):
- replacement exit counts
- replacement candidate symbol (if present)
- replacement reasoning blob (if present)

#### 4.20.7 Shadow vs live parity invariants
Telemetry MUST attempt a daily parity check when v1 trade logs are present:
- overlap of symbols between v1 executed trades and v2 shadow entries/candidates
- if v1 logs are missing, telemetry MUST state “parity unavailable” explicitly

#### 4.20.8 Regression Enforcement Rule (binding)
**Regression MUST fail if any computed artifact or required key is missing, malformed, or empty.**

#### 4.20.9 Live vs Shadow PnL telemetry invariants (additive)
Telemetry MUST produce `telemetry/YYYY-MM-DD/computed/live_vs_shadow_pnl.json`:
- Rolling windows: `24h`, `48h`, `5d` (UTC)
- Per-window blocks: `live`, `shadow`, `delta`, each containing:
  - `pnl_usd`, `expectancy_usd`, `trade_count`, `win_rate`
- `per_symbol[]` table with:
  - `symbol`, `window`, `live_pnl_usd`, `shadow_pnl_usd`, `delta_pnl_usd`, `live_trade_count`, `shadow_trade_count`

#### 4.20.10 Signal performance telemetry invariants (additive)
Telemetry MUST produce:
- `telemetry/YYYY-MM-DD/computed/signal_performance.json`
- `telemetry/YYYY-MM-DD/computed/signal_weight_recommendations.json` (advisory only; no auto-application)

Rules:
- “Signals” MUST be derived from existing telemetry (feature families / signal groupings) and MUST NOT modify any weights/config.
- Output MUST be schema-valid even if arrays are empty (but keys must exist).

#### 4.20.11 Master trade log requirements (append-only, additive)
System MUST maintain an append-only unified trade log:
- Path: `logs/master_trade_log.jsonl`
- Each line MUST be a JSON object containing (best-effort):
  - `trade_id`, `symbol`, `side`, `is_live`, `is_shadow`, `entry_ts`, `exit_ts`
  - `entry_price`, `exit_price`, `size`, `realized_pnl_usd`
  - `signals[]`, `feature_snapshot{}`, `regime_snapshot{}`
  - `exit_reason`, `source` (`live|shadow`)

Rules:
- Append-only; never rewrites history.
- MUST be wired into both live and shadow paths without changing trading/scoring/exit logic.

### 4.21 Parity Requirements (expanded schema) (additive)
Telemetry MUST produce:

- `telemetry/YYYY-MM-DD/computed/shadow_vs_live_parity.json` with:
  - `overlap.*` symbol overlap (v1 vs shadow candidates/entries)
  - `entry_parity.allowed_classifications` including:
    - `perfect_match`, `near_match`, `divergent`, `missing_in_v1`, `missing_in_v2`
  - `entry_parity.rows[]` rows containing:
    - `symbol`
    - `v1_entry_ts`, `v2_entry_ts`
    - `entry_ts_delta_seconds`
    - `v1_score_at_entry`, `v2_score_at_entry`, `score_delta`
    - `v1_price_at_entry`, `v2_price_at_entry`, `price_delta_usd`
    - `classification` (must be one of the allowed values)
    - `missing_fields` (best-effort)
    - `feature_family` (telemetry-only grouping)
  - `aggregate_metrics` containing:
    - `mean_entry_ts_delta_seconds`, `mean_score_delta`, `mean_price_delta_usd`, `match_rate`, `matched_pairs`
  - `notes.parity_available` true/false

- `telemetry/YYYY-MM-DD/computed/entry_parity_details.json` with:
  - `rows[]` containing the same per-entry parity row schema as above (full detail rows).

Rules:
- Missing v1 logs MUST NOT crash telemetry generation.
- Parity MUST be computed from existing logs only (no schema changes to v1 attribution or v2 shadow logs).

### 4.3 Missing/Empty/Corrupt Cache Behavior
If the cache is missing, empty, or corrupted:
- engine MUST continue running  
- engine MUST log:
  - `uw_cache_missing`
  - `uw_cache_empty`
  - `uw_cache_empty_no_signals`  

### 4.4 No Silent Zero‑Signal States
- The engine MUST NOT silently produce `clusters: 0` without a corresponding UW cache event.

---

# 5. Logging & Visibility Requirements

### 5.1 No Silent Failures
Every failure MUST produce a structured log event.

### 5.2 Safe Dictionary Access
- All dict access MUST use `.get()`.
- No KeyError may occur anywhere in the trading pipeline.

### 5.3 Debug/Telemetry Safety
- Debug prints MUST NOT assume fields exist.
- Logging MUST NOT crash the engine.

---

# 6. Supervisor Responsibilities

### 6.1 Engine Lifecycle Management
Supervisor MUST:
- start `main.py` explicitly  
- restart it on unexpected exit  
- log:
  - `TRADING_ENGINE_STARTING`
  - `TRADING_ENGINE_STARTED`
  - `TRADING_ENGINE_EXITED`
  - `TRADING_ENGINE_RESTARTING`

### 6.2 Shutdown Behavior
On SIGTERM:
- supervisor MUST terminate all subprocesses cleanly  
- kill unresponsive processes after timeout  

### 6.3 No Reliance on Import‑Time Behavior
Supervisor MUST NOT depend on `main.py` starting itself.

---

# 7. Cursor Modification Rules

These rules tell Cursor what it MUST and MUST NOT do.

### 7.1 Cursor MUST NOT:
- reintroduce import‑time side effects  
- modify supervisor restart logic without explicit instruction  
- change risk rules, scoring logic, or strategy behavior unless explicitly asked  
- change the canonical UW cache path  
- remove self‑healing JSON reads  
- remove engine_status or heartbeat updates  
- remove try/except guards around displacement, exits, reconciliation, or attribution  

### 7.2 Cursor MUST:
- preserve the supervised‑subprocess architecture  
- preserve worker loop resilience guarantees  
- preserve self‑healing behavior for all state files  
- preserve explicit logging for all failure modes  
- preserve safe dictionary access (`.get()`)  
- preserve the invariant that `run_once()` never crashes the engine  

---

# 8. System Health Definition

The system is considered **healthy** when:

- Supervisor is running  
- Engine subprocess is running  
- Heartbeat is fresh  
- run.jsonl cycles are updating  
- UW cache is readable  
- No unhandled exceptions occur  
- No silent failures occur  
- Supervisor restarts engine on exit  
- State files self‑heal automatically  

If any of these conditions fail, the system MUST degrade gracefully and continue running.

---

# 9. Modification Procedure

Any change to:
- engine startup  
- supervisor behavior  
- state file handling  
- UW cache path  
- worker loop structure  
- run_once exception model  

MUST be explicitly approved by Mark and MUST include:
- rationale  
- expected impact  
- rollback plan  

---

# End of Contract
This document is binding. Cursor MUST treat all rules as non‑negotiable unless explicitly overridden by Mark.

