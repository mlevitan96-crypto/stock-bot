# ARCHITECTURE_CONTRACTS_DATA.md
**Generated:** 2026-01-20  
**Scope:** Data ingestion + market context contracts introduced by the structural upgrade (additive; does not change trading by itself).

---

## 1) Data ingestion surface area (new, additive)

### 1.1 Market context snapshot (V2)

- **Module:** `structural_intelligence/market_context_v2.py`
- **State file:** `state/market_context_v2.json` (see `config/registry.py:StateFiles.MARKET_CONTEXT_V2`)
- **Writer:** `update_market_context_v2(api)`
- **Failure wrapper:** `@global_failure_wrapper("data")`
- **System events:**
  - `subsystem="data"`, `event_type="market_context_updated"`, severity `INFO`
  - `subsystem="data"`, `event_type="market_context_stale"`, severity `WARN`
  - `subsystem="data"`, `event_type="premarket_context_missing_or_stale"`, severity `CRITICAL` (see contract below)

### 1.2 Proxy inputs (tradeable on Alpaca)

Because direct ES/NQ futures and VIX term structure are not guaranteed to be available in Alpaca market data in all environments, the system uses **tradeable proxies**:

- **Futures direction proxy:** SPY/QQQ overnight return and latest 1-min bar trend.
- **Volatility / term structure proxy:**
  - `VXX` (front volatility proxy)
  - `VXZ` (back/mid volatility proxy)
  - ratio \(VXX / VXZ\) as a coarse term-structure proxy.

**Contract:** These are treated as *inputs* to regime/posture/scoring layers. If missing/stale, the system must degrade safely and log (it must not “invent” data).

---

## 2) Staleness + completeness contracts

### 2.1 Stale data MUST be detected and logged

- If 1-minute bars for SPY/QQQ are missing or older than an environment-appropriate maximum age:
  - A system event MUST be emitted:
    - `subsystem="data"`
    - `event_type="market_context_stale"`
    - `severity="WARN"`
  - The market context snapshot MUST still be written (with `stale_1m=true`), so downstream consumers can see the degradation explicitly.

### 2.2 Premarket/overnight readiness contract (NEW)

**Premarket and overnight data MUST be available to the scoring pipeline before the regular session opens, or a CRITICAL system_event is logged.**

Implementation (current):
- When Alpaca clock is available, and the system is within **4 hours of next open**, if SPY/QQQ 1-min data is missing/stale:
  - Emit:
    - `subsystem="data"`
    - `event_type="premarket_context_missing_or_stale"`
    - `severity="CRITICAL"`

Rationale:
- This is an operator-facing correctness guarantee: if premarket context is unavailable, downstream regime/posture layers should treat their inputs as degraded (and the operator must be alerted).

---

## 3) Compatibility contracts (do not break existing behavior)

- Market context is **additive**:
  - It does not modify existing gates, scoring, sizing, orders, or exits unless explicitly enabled by higher-layer config.
- All ingestion code paths must:
  - be wrapped by `@global_failure_wrapper`,
  - emit `log_system_event(...)` on meaningful degradations,
  - and **never block** the core trading loop.

