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

