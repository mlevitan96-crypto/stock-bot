# FULL SYSTEM AUDIT & REPAIR — 2026-01-16 (STOCK-BOT / Alpaca)

## 0) Executive summary (current state)

**Status:** The pipeline is **alive and advancing** on the droplet (**YES**: scoring + decision gating are running). **Orders are still 0 today** because the account is at **max positions (16/16)** and the top composite scores observed are **below `MIN_EXEC_SCORE=3.0`** for new entries.

**Primary remaining external dependency:** Alpaca **1Min bars are stale across symbols** (e.g., SPY last bar ~`09:04Z` while now ~`17:34Z`), which is a **data-quality risk** for any bar-derived indicators.

## 1) Trading session window (UTC + ET)

- **Date:** 2026-01-16
- **US equities regular session:** **14:30–21:00 UTC** (09:30–16:00 ET)
- **This report covers:** today’s runtime behavior and the audit/repair actions taken to restore end-to-end coherence.

## 2) Vitals snapshot (droplet)

### 2.1 Systemd / process health

Evidence shows the service is active and all subprocesses are running (dashboard, UW daemon, main engine, heartbeat).

### 2.2 Loop health (“is the bot advancing?”)

`logs/worker.jsonl` shows the worker loop iterating and calling `run_once` each cycle (e.g., `iter_start` → `market_check` → `calling_run_once`).

### 2.3 Scoring health

`logs/scoring_flow.jsonl` shows composite scoring activity today, including per-symbol `composite_calculated` events with non-constant scores (examples observed: ~2.43–2.69, varying freshness factors, component breakdown present).

### 2.4 Decision + gate health (“why no trades?”)

`logs/gate.jsonl` shows explicit, structured gate reasons today, including:

- **`max_positions_reached`** with `max=16` and `alpaca_positions=16`
- **`max_one_position_per_symbol`** for already-held symbols
- **`cycle_summary`** per cycle (market regime, considered count, top score, gate counts)

## 3) Current “no trades” root causes (today)

1. **Capacity is full:** `MAX_CONCURRENT_POSITIONS=16` and Alpaca currently reports **16 open positions**, so entries are blocked by `max_positions_reached`.
2. **Score floor is binding for new entries:** `Config.MIN_EXEC_SCORE` is **3.0**; observed top composite scores in cycles are **~2.8** (below the floor), so even with capacity, many entries would not qualify.
3. **Market data quality issue:** Alpaca **1Min bars are stale** across key symbols (SPY/AAPL/AMZN/HOOD/COIN). This can suppress/degenerate bar-derived indicators and should be treated as unsafe input until resolved at the data layer.

## 4) Repairs applied (contract-driven, minimal, no strategy expansion)

### 4.1 Import/package hardening (prevents silent pipeline suppression)

- Ensured `utils` is a package (`utils/__init__.py`) so `read_uw_cache()` doesn’t crash due to `ModuleNotFoundError`.
- Hardened `read_uw_cache()` to **never raise** on import/load failures; it logs and returns safe defaults.
- Updated `run_once()` to treat import failures as **fatal/high-severity** (visible), rather than silently swallowing them.

### 4.2 Exit reliability hardening (prevents exit abort loops)

- Fixed historical exit handler bug where the code could throw **`UnboundLocalError: time`** inside failure handling.
- Added `cancel_orders=True` (with safe fallback) to `close_position` calls to avoid “insufficient qty” due to reserved shares from open orders.

### 4.3 UW signal wiring / score variance restoration

- Fixed composite score collapse caused by missing `conviction`/`sentiment` defaults and positive defaults for missing intelligence components.
- Fixed UW daemon per-ticker polling so `option_flow` endpoints are tracked by `endpoint:ticker` (prevents “only first ticker updates”).

### 4.4 Stale bar behavior is now explicit (observability-only)

- Added a low-noise 1Min bar freshness probe (throttled) to emit a structured stale-bar event when bars are older than `BAR_STALE_MAX_AGE_MINUTES` (default 5). This is **reporting-only**; it does not change strategy intent.

## 5) Verification checklist (droplet)

After deploy/restart, confirm:

1. **Processes running:** `stock-bot.service` shows child processes for `main.py`, `uw_flow_daemon.py`, `dashboard.py`, `heartbeat_keeper.py`.
2. **Loop advancing:** `logs/worker.jsonl` continues to append `iter_start`/`calling_run_once` each minute.
3. **Scoring live:** `logs/scoring_flow.jsonl` has fresh entries (today) and scores are varied.
4. **Decision/gates visible:** `logs/gate.jsonl` has fresh entries with explicit reason codes; at least one `cycle_summary` per cycle.
5. **Exit engine not crashing:** no new `close_position_failed` entries caused by `UnboundLocalError: time`.
6. **Bar staleness is observable:** `logs/market_check.jsonl` contains `stale_1min_bars_detected` events when bars are stale.

## 6) Remaining open issues / follow-ups

- **Alpaca 1Min bars are stale across symbols.** This is an external data-quality blocker that must be resolved (feed/subscription/endpoint/SDK usage). Until this is fixed, bar-derived indicators should be treated as unsafe inputs (the system now logs this condition clearly).
- **Capacity is currently saturated (16/16 open positions).** New entries are blocked by design. If trading is expected today, exits must free capacity (or the system must be run with a different portfolio state).

