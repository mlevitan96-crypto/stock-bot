# Stock-Bot — External Review Brief

**Purpose:** Single-document orientation for reviewers who need the real architecture: signals, strategies, entries, exits, integrations, data, and governance.  
**Authority:** This brief synthesizes **`MEMORY_BANK_ALPACA.md`** (master operating manual), **`config/registry.py`** (thresholds and paths), key engine modules, and a **live droplet snapshot** (2026-03-27). Where the local repo and production diverge, **production on the droplet wins**.

**Not in scope here:** API secrets, exact account balances, proprietary third-party contract text, or legal/compliance sign-off.

---

## 1. Production snapshot (droplet)

Captured via SSH to the Alpaca droplet (`/root/stock-bot`):

| Item | Value |
|------|--------|
| **Git HEAD** | `39d98ac38b72ba33a7194fb51934222de2f1b362` |
| **`stock-bot.service`** | `active` |
| **`uw-flow-daemon.service`** | `active` |
| **`config/strategies.yaml` (production)** | Multi-strategy: **wheel 25%** + **equity 75%** capital partition; both `enabled: true`; wheel uses `config/universe_wheel_expanded.yaml`, universe caps/liquidity filters |

**Important:** A checkout of this repo on a laptop may show a **different** `config/strategies.yaml` (e.g. equity-only). Treat the **droplet file** as the trading configuration actually loaded in production unless you have verified a fresh deploy.

---

## 2. System architecture (high level)

### 2.1 Golden operational workflow (from MEMORY_BANK)

Operations expect: **USER → CURSOR → GITHUB → DROPLET → GITHUB → CURSOR → USER**. Production data for audits and reports is expected to come from the **droplet**, not a developer laptop.

### 2.2 Primary runtime processes

| Component | Role |
|-----------|------|
| **`deploy_supervisor.py`** | Orchestrates dashboard, UW daemon, and trading engine |
| **`main.py`** | Core trading loop: ingest signals, score, gate, enter, manage positions, exit |
| **`uw_flow_daemon.py`** | Polls Unusual Whales (UW) data into **`data/uw_flow_cache.json`** (single-instance; systemd + lock file per MEMORY_BANK) |
| **`dashboard.py`** | Monitoring UI and JSON APIs (e.g. health, PnL, integrity, scores) |
| **`heartbeat_keeper.py`** | Health / liveness support |

### 2.3 Supporting systems (non-exhaustive)

- **Risk / safety:** `risk_management.py`, `config/startup_safety_suite_v2.json`, `config/theme_risk.json`, `config/execution_router.json`
- **Reconciliation:** `position_reconciliation_loop.py` (bot vs broker)
- **Structural context (log-first):** `structural_intelligence/*`, `state/market_context_v2.json`, `state/regime_posture_state.json`
- **Governance / learning:** multiple scripts under `scripts/governance/`, `scripts/audit/`, board packs under `reports/` / `board/`
- **Post-close & alerts:** `scripts/alpaca_postclose_deepdive.py`, Telegram via `scripts/alpaca_telegram.py`, **failure paging:** `scripts/governance/telegram_failure_detector.py` + systemd timer (every 5 minutes on droplet)

---

## 3. Strategies and capital

### 3.1 What “strategy” means here

The bot can run **multiple strategy lanes** with **`strategy_id`** tagging on orders and telemetry. Production (droplet) currently allocates capital in **fixed** mode:

- **Equity (~75%)** — primary UW-driven equity flow (see §4–§6).
- **Wheel (~25%)** — options wheel lane (CSP/CC style; universe from `config/universe_wheel_expanded.yaml` with liquidity / candidate caps on droplet).

`MEMORY_BANK_ALPACA.md` still documents historical layout; the **authoritative runtime split** is whatever is in **`config/strategies.yaml` on the deployed host**.

### 3.2 Promotion / governance (config file)

`config/strategies.yaml` also carries **promotion** thresholds (e.g. minimum score to promote, weeks of data, drawdown limits). These govern **research / promotion** style gates, not every intraday tick.

---

## 4. Signal sources and integrations

### 4.1 Unusual Whales (UW)

- **Ingestion:** `uw_flow_daemon.py` → **`data/uw_flow_cache.json`** (+ related logs under `data/` and `logs/`).
- **Contract:** MEMORY_BANK requires all UW HTTP to go through **`src/uw/uw_client.py`**, validated against committed OpenAPI spec **`unusual_whales_api/api_spec.yaml`**, with usage tracked in **`state/uw_usage_state.json`** and caching under **`state/uw_cache/`**.
- **Intel passes (scheduled / state files):** Universe build and pre/post market intel scripts write **`state/daily_universe.json`**, **`state/premarket_intel.json`**, **`state/postmarket_intel.json`**, etc. Scoring is designed to consume **state-file intel** in v2 live readiness mode (no live UW HTTP inside the hot scoring path per MEMORY_BANK §7.11).

### 4.2 Alpaca

- **Broker API** via `alpaca_trade_api` in **`main.py`** (`AlpacaExecutor`).
- **Paper enforcement:** MEMORY_BANK states the engine must refuse entries if `ALPACA_BASE_URL` is not the **paper** endpoint (policy: paper-only until explicitly changed).
- **Orders / positions:** Standard REST order flow; guarded submission path with optional audit dry-run hooks (`src/audit_guard.py`).

### 4.3 Dashboard & operators

- **Dashboard** exposes health, scores, regime/posture, PnL, closed trades, integrity panels, etc. (see `docs/ARCHITECTURE_AND_OPERATIONS.md` for endpoint map references).
- **Telegram:** governance / daily summaries use **`TELEGRAM_BOT_TOKEN`** and **`TELEGRAM_CHAT_ID`** (from `.env` / systemd environment). Env detection: `scripts/alpaca_telegram_env_detect.py`.

### 4.4 Scope (Alpaca-only live path)

Live trading, governance, and certification paths in this repository target **US equities via Alpaca** only. Historical evidence packs under `reports/daily/` may mention older tooling names; operators should rely on current scripts and `docs/ARCHITECTURE_AND_OPERATIONS.md` for what runs in production.

---

## 5. How signals become trades (entry path)

### 5.1 End-to-end narrative

1. **UW flow data** lands in **`data/uw_flow_cache.json`** (daemon).
2. **`main.py`** reads the cache (`read_uw_cache`), normalizes and **clusters** flow events while preserving metadata (MEMORY_BANK §4).
3. **Composite scoring v2** (`uw_composite_v2.py` and related enrichment) turns cluster + intel features into a **numeric score** in **[0, 8]** with **freshness decay** (default half-life **180 minutes** per MEMORY_BANK §7.1).
4. **Regime / posture / vol / beta** adjustments come from **`config/registry.py`** → **`COMPOSITE_WEIGHTS_V2`** and structural state files.
5. **`StrategyEngine.decide_and_execute`** (in **`main.py`**) walks ranked clusters through **gates** (capacity, theme risk, expectancy floors, duplicates, market stage, etc.).
6. **Hard entry floor:** composite score must be **`>= MIN_EXEC_SCORE`** (default **2.5**, overridable via env; defined in **`config/registry.py`** / `Config` in `main.py`).
7. **Sizing:** baseline **~`POSITION_SIZE_USD` = $500** per position (env override); caps such as **`MAX_CONCURRENT_POSITIONS`** (default **16**), **`MAX_NEW_POSITIONS_PER_CYCLE`** (**6**), and **theme notional** limits apply.
8. **Order submission** via Alpaca (market/limit as implemented); lifecycle logged to **`logs/run.jsonl`** (`trade_intent`, etc.), **`logs/orders.jsonl`**, **`logs/signal_context.jsonl`**, and related streams.

### 5.2 Scoring formula (summary)

MEMORY_BANK §7.2 documents the **composite_raw** sum (flow, dark pool, insider, IV/smile, whale, event, motif, toxicity, regime, and **eleven expanded V3-style components**), then:

- Multiply by **freshness** (time decay).
- Apply **whale conviction boost** when applicable.
- **Clamp** to **[0, 8]**.

Adaptive multipliers may scale many components (**options_flow** weight is specially protected — MEMORY_BANK §7.5).

### 5.3 Displacement (replacing a held idea)

When at capacity, the engine may **displace** a weak/old position for a stronger signal if displacement rules pass (defaults in **`Thresholds`**: min age **4h**, max PnL **1%**, score advantage **2.0**, cooldown **6h** — all env-overridable).

---

## 6. How exits work

Exits combine **rule-based** mechanics and **v2 exit intelligence**.

### 6.1 Mechanical / risk exits (registry defaults)

From **`config/registry.py`** (`Thresholds`):

- **Trailing stop:** `TRAILING_STOP_PCT` (default **1.5%**).
- **Profit scaling / take-profit style behavior:** `PROFIT_SCALE_PCT` (default **2%**).
- **Time stop:** `TIME_EXIT_MINUTES` (default **240** minutes) — gives intraday positions room vs very short holds.
- **Stale exit:** `TIME_EXIT_DAYS_STALE` (default **12** days) with `TIME_EXIT_STALE_PNL_THRESH_PCT` (default **3%**).

Exact wiring is in the engine / exit pipeline inside **`main.py`** and associated helpers (search `TIME_EXIT`, trailing, autoexit).

### 6.2 v2 exit intelligence (intel-driven)

MEMORY_BANK §7.12 mandates:

| Piece | Module | Output / role |
|-------|--------|----------------|
| **Exit score** | `src/exit/exit_score_v2.py` | Weighted **0–1** score from deterioration + shifts + thesis flags |
| **Attribution** | `src/exit/exit_attribution.py` | **`logs/exit_attribution.jsonl`** per closed trade |
| **Targets / stops (dynamic)** | `src/exit/profit_targets_v2.py`, `src/exit/stops_v2.py` | Best-effort price-aware levels |
| **Replacement** | `src/exit/replacement_logic_v2.py` | Conservative replacement rules |
| **Exit intel state** | pre/post scripts | `state/premarket_exit_intel.json`, `state/postmarket_exit_intel.json` |

**Default exit weights** (merged with optional tuning overlays via `config/tuning` loader) include strong emphasis on **score deterioration** and **flow/darkpool/sentiment deterioration**, plus regime/sector shift, vol expansion, thesis invalidation, etc. — see **`compute_exit_score_v2`** in `exit_score_v2.py`.

### 6.3 Telemetry and audit

- **`exit_intent`** events go to **`logs/run.jsonl`** (`_emit_exit_intent` in **`main.py`**).
- Exit **components** for analytics must use `signal_id` values prefixed with **`exit_`** per MEMORY_BANK (e.g. `exit_flow_deterioration`).

---

## 7. Data, logs, and “strict” learning era (Alpaca)

### 7.1 Canonical log streams (illustrative)

| Path | Use |
|------|-----|
| `logs/run.jsonl` | Intents, cycle summaries |
| `logs/orders.jsonl` | Orders / fills |
| `logs/exit_attribution.jsonl` | Exit economics + v2 components |
| `logs/signal_context.jsonl` | Signal state at decisions |
| `logs/system_events.jsonl` | Cross-subsystem events |
| `logs/master_trade_log.jsonl` | Lifecycle audit stream (MEMORY_BANK §8.5) |
| `state/*.json` | Regime, weights, health, universe, intel snapshots |

### 7.2 Strict completeness gate

- **Code:** `telemetry/alpaca_strict_completeness_gate.py`
- **Forward era floor:** **`STRICT_EPOCH_START = 1774458080`** ( **`2026-03-25T17:01:20Z`** ) per MEMORY_BANK §1.1.
- **Purpose:** Deterministic join checks across **exit attribution**, **unified events**, **orders**, **run.jsonl** intents — used for **learning / dashboard / certification** without relaxing truth.

Reviewers evaluating “are stats decision-grade?” should ask whether reports use **strict-complete** cohorts vs raw log counts.

---

## 8. Risk controls and operational safety

- **Trading arm / mode:** Environment and startup safety suite gate whether the bot may trade; halts and flags live under `state/` (e.g. freeze flags, health safe mode — see `StateFiles` in registry).
- **Theme concentration:** `config/theme_risk.json` + `MAX_THEME_NOTIONAL_USD` / per-theme caps.
- **Self-healing:** Logged, conservative; must not mask missing data (MEMORY_BANK §3).
- **Failure paging:** `telegram_failure_detector.py` pages on missing/failed **expected** Telegram (Alpaca post-close, milestones) and **direction-readiness integrity** (`state/direction_readiness.json` freshness) with dedupe.

---

## 9. What this brief does **not** prove

- **Past performance** or **future profitability** — only describes mechanism.
- **Completeness of every branch** in **`main.py`** — the file is large; reviewers should grep for `decide_and_execute`, `MIN_EXEC_SCORE`, `exit`, and read surrounding blocks for edge cases.
- **Regulatory classification** (advisor, dealer, etc.) — not addressed.
- **Third-party SLAs** (UW, Alpaca) — subject to their terms and outage behavior.

---

## 10. Suggested reviewer deep-dives

1. **`MEMORY_BANK_ALPACA.md`** §4 (signals), §7 (scoring), §7.11–7.13 (v2 live + exits + post-close), §8 (telemetry).
2. **`config/registry.py`** — all of `Thresholds` and `COMPOSITE_WEIGHTS_V2`.
3. **`main.py`** — `read_uw_cache`, `StrategyEngine.decide_and_execute`, exit sections near `exit_intent` / score v2 usage.
4. **`src/exit/exit_score_v2.py`** + **`src/exit/exit_attribution.py`**.
5. **Production** `config/strategies.yaml` and wheel universe YAML **on the droplet**.
6. **Dashboard** JSON contracts referenced from `docs/ARCHITECTURE_AND_OPERATIONS.md` / `reports/DASHBOARD_ENDPOINT_MAP.md` (if present in tree).

---

## 11. Document metadata

| Field | Value |
|-------|--------|
| **Generated** | 2026-03-27 (America/New_York calendar date aligned with mission context) |
| **Primary sources** | `MEMORY_BANK_ALPACA.md`, `config/registry.py`, `config/strategies.yaml` (local + droplet note), `main.py`, `src/exit/*.py`, `uw_flow_daemon.py`, droplet systemd status + git HEAD above |
| **Maintainer expectation** | Update this file when strategy mix, entry floor, or exit contract changes materially |

---

*End of external review brief.*
