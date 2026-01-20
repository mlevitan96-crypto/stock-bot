# ARCHITECTURE_CONTRACTS_CURRENT.md
**Generated:** 2026-01-20  
**Scope:** Current (pre-structural-upgrade) STOCK-BOT strategy/decision contracts as implemented in code.  
**Mandate:** This document captures invariants that MUST be preserved during the structural upgrade (data → features → scores → regime → posture → decisions), including reliability wrappers and decision-surface observability.

---

## 0) Canonical entry points and runtime services

- **Supervisor / orchestration**
  - `deploy_supervisor.py` orchestrates services (per `MEMORY_BANK.md`).
- **Core trading loop**
  - `main.py` is the core trading engine. The main cycle is `run_once()` (invoked by the worker loop).
- **UW ingestion**
  - `uw_flow_daemon.py` ingests UW endpoints and writes cache to disk (single source cache consumed by the engine).
- **Dashboard**
  - `dashboard.py` reads state/logs and recomputes current scores for open positions.

---

## 1) Data → Feature → Score → Decision → Order → Exit (current pipeline map)

### 1.1 Data sources (current)

- **Alpaca (broker + market data)**
  - Used throughout `main.py` and `structural_intelligence/regime_detector.py`.
  - Typical calls:
    - `api.list_positions()`, `api.get_account()` (risk/capacity gates, sizing, health).
    - `api.get_last_trade(symbol)`, `api.get_quote(symbol)` (ref price + sizing; dashboard current scores).
    - `api.get_bars(symbol, timeframe, ...)` (ATR exhaustion gate; regime detector SPY daily bars; various indicators).

- **Unusual Whales (UW)**
  - Ingested by `uw_flow_daemon.py`.
  - Persisted cache (consumed by trading + dashboard):
    - `data/uw_flow_cache.json` (per `config/registry.py:CacheFiles.UW_FLOW_CACHE`)
    - Optional expanded intel cache:
      - `data/uw_expanded_intel.json` (per `uw_composite_v2.py:EXPANDED_INTEL_CACHE`)

### 1.2 Feature builders (current)

- **UW enrichment**
  - `uw_enrichment_v2.enrich_signal(symbol, uw_cache, market_regime)` (decorated with `@global_failure_wrapper("data")`).
  - Produces an `enriched` dict used by composite scoring and (later) exit evaluation.
  - **Invariants in enriched output** (required by downstream scoring):
    - `sentiment`: defaults to `"NEUTRAL"` if missing.
    - `conviction`: may be missing upstream; scoring contract defaults it to **0.5** when missing/None.
    - `freshness`: computed from `_last_update` / `last_update` with exponential decay.
    - Expected nested structures exist (or are defaulted) for:
      - `dark_pool`, `insider`, `market_tide`, `calendar`, `congress`, `institutional`, `shorts`/`ftd_pressure`, `greeks`, `iv_rank`, `oi_change`, `etf_flow`, `squeeze_score`.

### 1.3 Scoring functions (current)

- **Composite score**
  - `uw_composite_v2.compute_composite_score_v3(symbol, enriched_data, regime="NEUTRAL"|"mixed"|..., expanded_intel=None, use_adaptive_weights=True)`
  - Decorated with `@global_failure_wrapper("scoring")`.
  - Produces a dict containing:
    - `score` (float)
    - `components` (component contribution breakdown)
    - `freshness`, `toxicity`, `motifs`, plus expanded intel summaries.
  - **Score semantics (current)**
    - Score is a **clamped** composite signal strength (historically \([0, 8]\) clamp is applied inside scoring).
    - Score is **freshness-weighted**: freshness is applied (as a multiplicative factor) within the composite pipeline.
    - **Missing conviction contract:** if `enriched_data["conviction"] is None/missing`, the scorer defaults to **0.5**, not 0.0.
    - **Adaptive weights contract:** adaptive multipliers may apply (with explicit protection for `options_flow` weight).

- **Entry gating (composite stage)**
  - `uw_composite_v2.should_enter_v2(composite, symbol, mode="base", api=...)` (decorated with `@global_failure_wrapper("gate")`)
  - Gate checks:
    - Score threshold via `get_threshold(symbol, mode)` with fallback to `ENTRY_THRESHOLDS[mode]`.
    - Toxicity hard block when `toxicity > 0.90`.
    - Freshness hard block when `freshness < 0.25`.
    - Optional **ATR exhaustion** gate when `api` available (block if price > 2.5 ATR above 20-EMA).
    - Optional gamma resistance wall gate (block within 0.2% of a resistance level if available).
  - **Decision-surface observability contract**
    - Every gate failure is logged via `_log_gate_failure()` to:
      - `logs/gate_diagnostic.jsonl`
      - `logs/system_events.jsonl` with `subsystem="gate"`, `event_type="blocked"`.

### 1.4 Regime detection (current)

There are **two parallel regime concepts** used today:

- **Main loop “market_regime” (string)**
  - Computed in `main.py`:
    - `compute_market_regime(gex_map, net_map, vol_map)` → `classify_market_regime(...)`
  - Emits `log_event("regime", "market_regime", ...)`.
  - Common labels: `high_vol_neg_gamma`, `low_vol_uptrend`, `downtrend_flow_heavy`, `mixed`.

- **Structural intelligence regime (stateful)**
  - `structural_intelligence.regime_detector.RegimeDetector.detect_regime()` writes:
    - `state/regime_detector_state.json`
  - Labels: `RISK_ON`, `NEUTRAL`, `RISK_OFF`, `PANIC`.
  - Used for multipliers in some paths (e.g., `StrategyEngine.decide_and_execute` applies regime/macro multipliers when available).

**Contract:** Any new regime/posture layer MUST be additive and MUST NOT remove or silence existing regime logging.

### 1.5 Decision engine (current)

- **Engine**
  - `main.py:StrategyEngine.decide_and_execute(...)` (decorated `@global_failure_wrapper("decision")`)
  - Input clusters are sorted by `composite_score` descending.
  - Per-cycle gate accounting is maintained and logged (cycle summary, per-gate counts).

- **Key gates / invariants**
  - **Freeze gating** via `monitoring_guards.check_freeze_state()` (documented in `MEMORY_BANK.md`; trading must not bypass).
  - **Max 1 position per symbol** is enforced and logged as `gate/max_one_position_per_symbol`.
  - **Capacity**: `Thresholds.MAX_CONCURRENT_POSITIONS` / `Config.MAX_CONCURRENT_POSITIONS` enforced; displacement may be attempted first.
  - **Concentration gate**: blocks bullish entries when portfolio net delta exceeds ~70% long exposure.
  - **Score floor**:
    - Trading-layer score gate uses `Config.MIN_EXEC_SCORE` (env default 3.0; see `config/registry.py:Thresholds.MIN_EXEC_SCORE` and `main.py`).
    - Composite-layer gate uses `uw_composite_v2.get_threshold()` (hierarchical thresholds) prior to cluster admission.
  - **Expectancy gate** (v3.2): `v32.ExpectancyGate.should_enter(...)` blocks entries with explicit reasons; every block logs to gate streams.

### 1.6 Order submission (current)

- Orders are submitted through `AlpacaExecutor` (in `main.py`), wrapped by global failure wrapper on order paths.
- **Risk posture invariants**
  - No surprise leverage / no position-size contract changes without explicit configuration change.
  - Sizing is capped via `risk_management.get_risk_limits()` (e.g., max position dollars).

### 1.7 Exit logic (current)

- **Primary exit loop**
  - `AlpacaExecutor.evaluate_exits()` (decorated `@global_failure_wrapper("exit")`)
  - Pulls open positions from Alpaca and merges with state metadata (`state/position_metadata.json`).
  - Recomputes “current composite score” for each open position using:
    - `uw_enrichment_v2.enrich_signal(...)` then `uw_composite_v2.compute_composite_score_v3(...)`
  - Uses:
    - **signal decay** (ratio current_score / entry_score),
    - **counter-signal** (flow reversal),
    - **time-based stale exits**, and
    - structural exits (via `structural_intelligence/structural_exit.py`) when available.

**Contract:** Exit evaluation MUST remain callable every cycle and MUST keep logging attribution/exit reasons.

---

## 2) Contracts: what a “score” means today

- **Composite score** is a normalized strength of UW-driven signal confirmation, incorporating:
  - flow conviction (primary),
  - dark pool intensity,
  - insider and expanded intel features,
  - toxicity penalty,
  - regime modifier,
  - motif/whale persistence,
  - and **freshness decay**.
- **Score range and safety**
  - Composite score is clamped (prevents runaway values).
  - Missing/None data should default to **neutral**, not to hard-zero, to avoid “false stagnation”.

---

## 3) Contracts: what MIN_EXEC_SCORE represents today

- `MIN_EXEC_SCORE` is the **trade-layer score floor** for opening new positions.
  - Default is `3.0` (env override), sourced from `config/registry.py:Thresholds.MIN_EXEC_SCORE` and used in `main.py`.
- In addition, the composite scoring stage uses symbol thresholds via:
  - `uw_composite_v2.get_threshold(symbol, mode)` with `ENTRY_THRESHOLDS` fallback.

**Invariant:** Any upgrade must preserve the meaning of “score ≥ threshold means eligible to be considered for entry”, while still allowing gates to block (capacity, diversification, expectancy, etc.).

---

## 4) Observability + reliability contracts (MUST preserve)

### 4.1 Event logging (decision surface)

- `log_event(...)` is used throughout trading, gates, scoring_flow, orders, exits, etc.
- Gate decisions MUST continue to log:
  - accepted signals,
  - blocked reasons,
  - per-cycle summaries and counts.

### 4.2 Permanent system events stream

- `utils/system_events.py` provides:
  - `log_system_event(...)` → appends to `logs/system_events.jsonl` (never blocks trading)
  - `global_failure_wrapper(subsystem)` → logs exceptions + returns safe fallbacks
- Existing subsystems in active use include (non-exhaustive):
  - `"data"`, `"uw_poll"`, `"uw_cache"`, `"scoring"`, `"gate"`, `"decision"`, `"order"`, `"exit"`, `"signals"`.

### 4.3 Failure wrapper behavior (non-negotiable)

- Any new code introduced into critical paths MUST:
  - be decorated with `@global_failure_wrapper("<subsystem>")`, and
  - emit a `log_system_event(...)` on meaningful degradations (stale/missing data), not only on exceptions.

---

## 5) Non-breaking extension rule (upgrade constraint)

- New layers (market context, volatility/beta features, regime/posture, v2 composite, shadow A/B) MUST be:
  - additive,
  - configuration-gated,
  - safe by default (no new orders, no new leverage, no bypassed gates),
  - and must preserve all existing logs/streams and global failure-wrapper semantics.

