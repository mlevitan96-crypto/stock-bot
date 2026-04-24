# Gemini Quant Audit — Stock Bot (Alpaca Paper)

**Purpose:** Single reference for a quant strategist diagnosing paper-trading P&L. **Secrets redacted:** no API keys, tokens, or server IPs appear in this document. **Operational note:** Production behavior is expected to match the **droplet-deployed** revision of this repository; treat live `state/`, `logs/`, and `.env` on the host as the runtime source of truth for thresholds and flags.

---

## 1. Strategy & Logic Overview:

### Core thesis

The bot is a **US equities** system (via **Alpaca**) that leans on **Unusual Whales (UW)**-style flow and alternative data (options flow, dark pool notionals, insider/congress/shorts/calendar/tide, greeks-related features, etc.) cached per symbol. A **composite score** (roughly 0–8 after clamping) ranks symbols; entries require passing **score, toxicity, freshness**, and optional **ATR/EMA exhaustion** and **gamma wall** checks. **Adaptive weights** (`adaptive_signal_optimizer`) can scale component contributions from trade outcomes.

### Indicators & features (non-exhaustive)

- **Options flow:** conviction, trade count, sweep detection (premium > $100k in recent window), sentiment (BULLISH/BEARISH/NEUTRAL).
- **Dark pool:** 1h / total notional scaled into a strength term.
- **Insider, IV term skew, smile slope, whale/motif** (staircase, sweep block, burst), **toxicity** (penalty), **regime_modifier**, **congress, shorts/squeeze, institutional, market_tide, calendar**, **greeks, FTD, IV rank, OI change, ETF flow, squeeze_score** (from enrichment + `data/uw_expanded_intel.json`).
- **Post-composite v2 layer:** realized vol 20d, beta vs SPY, overnight SPY/QQQ proxy, posture/regime alignment, optional pre/postmarket intel files (`state/premarket_intel.json`, `state/postmarket_intel.json`).
- **Runtime boosts in `run_once`:** cross-asset confirmation (when enabled), sector tide tracker, persistence tracker, alpha signature (e.g. RVOL).

### Timeframes

- **Signal freshness:** composite carries a `freshness` factor; `should_enter_v2` rejects if `freshness < 0.25`.
- **Bars for gates:** `should_enter_v2` uses **1-minute** bars (25 bars) for 20-period EMA; ATR via `compute_atr` (configurable lookback, often 14–20).
- **Cycle time:** `Config.RUN_INTERVAL_SEC` default **60s** between worker iterations when healthy.
- **Exits:** mix of **time-based** (`TIME_EXIT_MINUTES`, stale trade exits), **trailing** (`TRAILING_STOP_PCT`), **profit targets** (`PROFIT_TARGETS` / `SCALE_OUT_FRACTIONS`), **signal decay** (composite vs entry score, regime-specific thresholds from `board.eod.exit_regimes`), **exit_score_v2** (UW/intel deterioration), displacement (rotate into stronger signals), and **AlpacaExecutor.evaluate_exits** orchestration in `main.py`.

### Entry logic (summary)

1. `uw_flow_daemon` fills `data/uw_flow_cache.json` (and related paths via `CacheFiles`).
2. `run_once` reads cache, **enriches** per symbol, calls `uw_composite_v2.compute_composite_score_v2`, then **`should_enter_v2`** (with Alpaca `api` for exhaustion/wall checks when available).
3. Accepted symbols become **synthetic clusters** with `source` marking composite origin.
4. **`StrategyEngine.decide_and_execute`** applies portfolio gates (concentration, theme, expectancy/V3.2, momentum, spread, cooldown, max positions per cycle, kill switch, live safety caps), sizing, then **`AlpacaExecutor.submit_entry`**.

### Exit logic (summary)

- **`evaluate_exits`** on `AlpacaExecutor` uses position metadata, current quotes, composite re-evaluation, **exit_score_v2**, decay, min-hold guards, stop/profit tiers, and broker **`close_position`** with retry logging. Exact precedence is branchy; see `main.py` in the `evaluate_exits` implementation and `src/exit/exit_score_v2.py` for the deterioration score.

---

## 2. Environment specifics:

### Venue

**This bot trades on Alpaca** (US equities via Alpaca’s REST API — paper or live per configuration). This codebase’s **primary trading venue is Alpaca** (REST API, paper or live controlled by `TRADING_MODE` and `ALPACA_BASE_URL`). **Kraken-related runtime paths have been removed or are legacy documentation only** in the current tree; do not assume crypto spot trading from this repo.

### Exchange-specific handling

| Topic | Behavior in code |
|--------|-------------------|
| **Maker/taker fees** | No explicit per-fill fee model in strategy P&L; **Alpaca’s paper account** models fills. Code focuses on **limit-first** execution and spread watchdog, not fee arithmetic. |
| **Slippage** | **`predict_slippage_bps`** / **`choose_entry_route`** in `main.py` support **routing hints** (maker vs midpoint). **Telemetry** records slippage vs limit on fills. **Market fallback** can increase realized slippage vs limit quotes. |
| **Rate limits** | **UW:** centralized in **`uw_flow_daemon.py`** with comments targeting ~30 req/min; main loop is **cache-first** to avoid duplicate UW polling. **Alpaca:** `SmartPoller`-style backoff for API endpoints, `ExponentialBackoff` wrappers on critical broker calls, idempotent `client_order_id` patterns. |
| **Market hours** | **`is_market_open_now`**, **`is_after_close_now`** (Eastern), `SmartPoller._is_market_hours` for **9:30–16:00 ET**. Entries use **`extended_hours=False`** on submitted orders. Worker still runs outside RTH but gates behavior (documentation in `ALPACA_TRADING_BOT_WORKFLOW.md`: signals may continue, entries may be restricted by design). |
| **Paper safety** | **`enforce_paper_only_or_die`**, **`trading_is_armed()`** checks mode vs base URL mismatch, **`AUDIT_MODE` / `AUDIT_DRY_RUN`** blocks real submits. |

---

## 3. Data Pipeline & Integrity:

### Live / operational data

- **UW:** `uw_flow_daemon.py` → **`data/uw_flow_cache.json`** (path may be overridden via `config.registry.CacheFiles`).
- **Enrichment:** `run_once` merges cache rows with defaults for missing dicts; can **write back** normalized fields to cache (`atomic_write_json`).
- **Alpaca:** quotes, last trade, bars, positions, account — via `alpaca_trade_api` REST in `AlpacaExecutor` and helpers (`fetch_bars_safe`, `compute_atr`).
- **Intel overlays:** `state/premarket_intel.json`, `state/postmarket_intel.json`, `state/daily_universe*.json`, `data/uw_expanded_intel.json`.

### Historical / research

- **Backtests & replay:** `backtests/`, `historical_replay_engine.py`, scripts under `scripts/` (e.g. Alpaca bar discovery, 30d backtest drivers). **Bars cache** may live under `data/bars_cache/` when populated.
- **Artifacts:** JSON summaries under `artifacts/`, `reports/` for audits.

### Lookahead / latency risks (for the quant to test)

- **Cache timestamps vs wall clock:** Stale UW data may still score if freshness floor is low; conversely **boosts** (persistence, sector tide) use **in-memory windows** that may not match strict exchange-time ordering.
- **Same-bar decisions:** Composite uses **current** enrichment and, for exhaustion, **recent 1Min bars** including the latest bar — **minimal lookahead** if bars are aligned to closed bars only; confirm `get_bars` usage is not mixing incomplete bars (Alpaca behavior is version-dependent).
- **Adaptive weights** trained on **labeled outcomes** can **overfit** if labels leak future information — review `adaptive_signal_optimizer` and learning logs.
- **Paper fills ≠ live:** Paper liquidity and fill model can **understate** slippage vs live.
- **Reconciliation:** Position metadata vs broker can drift briefly; **reconciliation loop** and `ensure_reconciled` gate entries when inconsistent.

---

## 4. Risk Management:

### Position sizing

- **Base notional:** `SIZE_BASE_USD` / **`POSITION_SIZE_USD`** (env-driven; defaults in `Config` around **$500** base).
- **Minimum notional:** `MIN_NOTIONAL_USD` (default **$100**); **fractional shares** attempted when price > cap.
- **Adaptive overlays:** composite `sizing_overlay` from IV skew / whale / toxicity / congress / squeeze (see `_compute_composite_score_core`); `apply_sizing_overlay` in `uw_composite_v2.py`.
- **Concurrency:** `MAX_CONCURRENT_POSITIONS` (default **16**), **`MAX_NEW_POSITIONS_PER_CYCLE`** (env / live caps).
- **Cooldown:** `COOLDOWN_MINUTES_PER_TICKER` (default **15**).

### Stops / take-profit / time exits

- **ATR-related:** `ATR_LOOKBACK`, `ATR_MIN_PCT`, stop action space for bandit (`STOP_ACTIONS`).
- **Trailing:** `TRAILING_STOP_PCT` (default ~**1.5%**).
- **Profit tiers:** `PROFIT_TARGETS` (e.g. 2%, 5%, 10%) with `SCALE_OUT_FRACTIONS`.
- **Time stops:** `TIME_EXIT_MINUTES` (~**150** min), `STALE_TRADE_EXIT_MINUTES`, `TIME_EXIT_DAYS_STALE` with P&amp;L threshold.
- **Displacement:** closes weaker positions for stronger candidates subject to min hold, score delta, thesis dominance (`DISPLACEMENT_*`).

### Order types

- **Primary:** **Limit** with **`ENTRY_POST_ONLY`** default true, **`MAKER_BIAS`** pricing from NBBO (`compute_entry_price`), retries with refreshed limits.
- **Fallback:** **Market** order path when limits fail (`submit_market_fallback`).
- **Regime override:** `REGIME_EXECUTION_MAP` can force more aggressive (market-style) or passive (maker) behavior.

### Account-level circuit breakers

- **`risk_management.run_risk_checks`:** daily loss ($ and %), drawdown vs peak equity, equity floor; can trigger freeze via governor state.
- **`trade_guard.evaluate_order`:** pre-submit sanity on exposure and buying power.
- **Concentration:** skip new **bullish** entries if **net long delta > 70%** of equity (approximation via position market values).

---

## 5. Codebase Structure:

High-level tree (depth-limited; large/evidence folders summarized):

```text
stock-bot/
├── main.py                 # Alpaca executor, StrategyEngine, run_once, worker, API routes
├── uw_composite_v2.py      # Composite score v2 + entry gate should_enter_v2
├── uw_flow_daemon.py       # UW API poller → flow cache
├── risk_management.py      # Limits, peak equity, order validation helpers
├── adaptive_signal_optimizer.py
├── position_reconciliation_loop.py
├── config/                 # registry, strategies.yaml, governance JSON, overlays, tuning
├── src/                    # exit scores, intel, audit, paper experiments, uw attribution
├── strategies/             # strategy modules (equity cohort via strategies.yaml)
├── board/                  # EOD bundles, exit regimes, live entry adjustments
├── scripts/                # audits, backtests, droplet ops, reports
├── backtests/              # configs + summaries
├── data/                   # caches (uw_flow, bars_cache, etc.)
├── state/                  # runtime JSON (freezes, universe, intel, risk)
├── logs/                   # jsonl telemetry
├── docs/                   # architecture & workflow references
├── tests/
├── deploy/                 # systemd units
└── telemetry/
```

---

## 6. Core Logic Code:

**Sources:** Line numbers refer to the repository at audit generation time.

- **Signal stack:** `uw_composite_v2.py` — `WEIGHTS_V3`, `ENTRY_THRESHOLDS`, `_compute_composite_score_core` (730–1371), `compute_composite_score_v2` (1382–1769), `should_enter_v2` (2010–2162). Alias: `compute_composite_score_v3 = compute_composite_score_v2`.
- **Execution stack:** `main.py` — `run_all_strategies` (11148–11186) calls `run_once`; `Watchdog._worker_loop` (~13095–13195) calls `run_all_strategies`; full **`run_once`** spans **11193–12803** (not all pasted below); **`AlpacaExecutor.submit_entry`** 4804–5560+ (excerpt includes `compute_entry_price` 4765+ for context).

The following blocks are **verbatim** extracts from the codebase.

### 6.1 Weights and thresholds (`uw_composite_v2.py`)


## compute_composite_score_v2

```python
@global_failure_wrapper("scoring")
def compute_composite_score_v2(
    symbol: str,
    enriched_data: Dict,
    regime: str = "NEUTRAL",
    *,
    market_context: Optional[Dict[str, Any]] = None,
    posture_state: Optional[Dict[str, Any]] = None,
    expanded_intel: Dict = None,
    use_adaptive_weights: bool = True,
    v2_params: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Composite V2 (v2-only engine):
    - Uses the core composite as a base
    - Applies explicit, parameterized adjustments for:
      - realized volatility
      - beta vs SPY
      - regime/posture alignment

    IMPORTANT:
    - This function is the single composite scorer for the engine (paper-only).
    - It is designed to be safe-by-default and fully observable.
    """
    if market_context is None:
        market_context = {}
    if posture_state is None:
        posture_state = {}
    if v2_params is None:
        # Default to config-driven params when available (shadow-safe).
        try:
            from config.registry import COMPOSITE_WEIGHTS_V2 as _CWV2  # type: ignore
            v2_params = dict(_CWV2) if isinstance(_CWV2, dict) else {}
        except Exception:
            v2_params = {}
        if not v2_params:
            v2_params = {
                "version": "fallback_defaults",
                "vol_center": 0.20,
                "vol_scale": 0.25,
                "vol_bonus_max": 0.6,
                "low_vol_penalty_center": 0.15,
                "low_vol_penalty_max": -0.10,
                "beta_center": 1.00,
                "beta_scale": 1.00,
                "beta_bonus_max": 0.4,
                "uw_center": 0.55,
                "uw_scale": 0.45,
                "uw_bonus_max": 0.20,
                "premarket_align_bonus": 0.10,
                "premarket_misalign_penalty": -0.10,
                "regime_align_bonus": 0.5,
                "regime_misalign_penalty": -0.25,
                "posture_conf_strong": 0.65,
                "high_vol_multiplier": 1.15,
                "low_vol_multiplier": 0.90,
                "mid_vol_multiplier": 1.00,
                "misalign_dampen": 0.25,
                "neutral_dampen": 0.60,
            }

    # Base score source: compute from scratch using the core composite.
    base = _compute_composite_score_core(
        symbol,
        enriched_data,
        regime=regime,
        expanded_intel=expanded_intel,
        use_adaptive_weights=use_adaptive_weights,
    ) or {}

    base_score = _to_num(base.get("score", 0.0))

    # Inputs (from enrichment feature store)
    vol_20d = _to_num(enriched_data.get("realized_vol_20d", 0.0))
    beta = _to_num(enriched_data.get("beta_vs_spy", 0.0))
    flow_conv = _to_num(enriched_data.get("conviction", enriched_data.get("flow_conv", 0.0)))
    trade_count = int(_to_num(enriched_data.get("trade_count", 0)) or 0)

    # Context
    vol_regime = str(market_context.get("volatility_regime", "mid") or "mid").lower()
    posture = str(posture_state.get("posture", "neutral") or "neutral").lower()
    posture_conf = _to_num(posture_state.get("regime_confidence", posture_state.get("regime_confidence", 0.0)))

    # Direction from sentiment
    sent = enriched_data.get("sentiment") or "NEUTRAL"
    direction = "bullish" if sent == "BULLISH" else ("bearish" if sent == "BEARISH" else "neutral")

    # Multipliers by vol regime
    if vol_regime == "high":
        vol_mult = float(v2_params.get("high_vol_multiplier", 1.30))
    elif vol_regime == "low":
        vol_mult = float(v2_params.get("low_vol_multiplier", 0.85))
    else:
        vol_mult = float(v2_params.get("mid_vol_multiplier", 1.00))

    # Alignment dampening (avoid boosting misaligned directions).
    align = (posture == "long" and direction == "bullish") or (posture == "short" and direction == "bearish")
    misalign = (posture == "long" and direction == "bearish") or (posture == "short" and direction == "bullish")
    if misalign:
        align_mult = float(v2_params.get("misalign_dampen", 0.25))
    elif direction == "neutral" or posture == "neutral":
        align_mult = float(v2_params.get("neutral_dampen", 0.60))
    else:
        align_mult = 1.0

    # Volatility preference: reward higher realized vol (and optionally penalize low-vol in high-vol regimes).
    vol_center = float(v2_params.get("vol_center", 0.20))
    vol_scale = float(v2_params.get("vol_scale", 0.25)) or 0.25
    vol_strength = _clamp((vol_20d - vol_center) / vol_scale, 0.0, 1.0)
    vol_bonus = float(v2_params.get("vol_bonus_max", 0.6)) * vol_strength * vol_mult * align_mult
    low_vol_pen = 0.0
    if vol_regime == "high":
        low_center = float(v2_params.get("low_vol_penalty_center", 0.15))
        low_strength = _clamp((low_center - vol_20d) / max(1e-9, low_center), 0.0, 1.0)
        low_vol_pen = float(v2_params.get("low_vol_penalty_max", -0.10)) * low_strength * align_mult

    # Beta preference: prefer beta > 1 when otherwise comparable.
    beta_center = float(v2_params.get("beta_center", 1.0))
    beta_scale = float(v2_params.get("beta_scale", 1.0)) or 1.0
    beta_strength = _clamp((beta - beta_center) / beta_scale, 0.0, 1.0)
    beta_bonus = float(v2_params.get("beta_bonus_max", 0.4)) * beta_strength * vol_mult * align_mult

    # UW strength proxy: conviction + trade_count (only reward when there is actual flow data).
    uw_strength = _clamp(flow_conv, 0.0, 1.0) if trade_count > 0 else 0.0
    uw_center = float(v2_params.get("uw_center", 0.55))
    uw_scale = float(v2_params.get("uw_scale", 0.45)) or 0.45
    uw_norm = _clamp((uw_strength - uw_center) / uw_scale, 0.0, 1.0)
    uw_bonus = float(v2_params.get("uw_bonus_max", 0.2)) * uw_norm * align_mult

    # Premarket / futures proxy alignment (SPY/QQQ overnight direction).
    spy_ov = _to_num(market_context.get("spy_overnight_ret", 0.0))
    qqq_ov = _to_num(market_context.get("qqq_overnight_ret", 0.0))
    mkt_trend = str(market_context.get("market_trend", "") or "")
    fut_dir = "up" if (spy_ov + qqq_ov) > 0.005 else ("down" if (spy_ov + qqq_ov) < -0.005 else "flat")
    pre_bonus = 0.0
    if direction in ("bullish", "bearish"):
        aligned = (direction == "bullish" and fut_dir == "up") or (direction == "bearish" and fut_dir == "down")
        if aligned:
            pre_bonus = float(v2_params.get("premarket_align_bonus", 0.10)) * align_mult
        elif fut_dir in ("up", "down"):
            pre_bonus = float(v2_params.get("premarket_misalign_penalty", -0.10)) * align_mult

    # Regime/posture alignment (directional).
    conf_mult = 1.0 if posture_conf >= float(v2_params.get("posture_conf_strong", 0.65)) else 0.6
    regime_bonus = float(v2_params.get("regime_align_bonus", 0.5)) * (conf_mult if align else 0.0)
    regime_pen = float(v2_params.get("regime_misalign_penalty", -0.25)) * (conf_mult if misalign else 0.0)

    # Optional nonlinear shaping (strictly gated; disabled by default).
    shaping_adj = 0.0
    shaping_on = str(os.getenv("V2_SHAPING_ENABLED", "") or "").strip().lower() in ("1", "true", "yes", "on")
    if shaping_on:
        try:
            # Nonlinear volatility reward
            gamma = float(v2_params.get("shape_vol_gamma", 1.8))
            shape_vol = float(v2_params.get("shape_vol_bonus_max", 0.15)) * (vol_strength ** max(0.5, gamma)) * vol_mult * align_mult
            shaping_adj += shape_vol
            # Extra regime-aligned directional boost
            shaping_adj += float(v2_params.get("shape_regime_align_bonus", 0.10)) * (conf_mult if align else 0.0)
            # Penalty for weak UW flow even when many prints exist
            if trade_count >= int(v2_params.get("shape_trade_count_strong", 15)):
                if uw_strength <= float(v2_params.get("shape_uw_weak_threshold", 0.35)):
                    shaping_adj += float(v2_params.get("shape_uw_weak_penalty_max", -0.10)) * align_mult
        except Exception:
            shaping_adj = 0.0

    total_adj = vol_bonus + low_vol_pen + beta_bonus + uw_bonus + pre_bonus + regime_bonus + regime_pen + shaping_adj
    score_v2 = _clamp(base_score + total_adj, 0.0, 8.0)

    # UW intelligence layer (optional additive inputs for v2 only; shadow-safe).
    # Reads state written by scripts/run_premarket_intel.py and scripts/run_postmarket_intel.py.
    uw_inputs: Dict[str, Any] = {}
    uw_adj = {
        "flow_strength": 0.0,
        "darkpool_bias": 0.0,
        "sentiment": 0.0,
        "earnings_proximity": 0.0,
        "sector_alignment": 0.0,
        "regime_alignment": 0.0,
        "total": 0.0,
    }
    uw_intel_version = ""
    v2_uw_sector_profile: Dict[str, Any] = {}
    v2_uw_regime_profile: Dict[str, Any] = {}
    universe_scoring_version = ""
    universe_source = ""
    in_universe = None
    try:
        uw_cfg = v2_params.get("uw", {}) if isinstance(v2_params, dict) else {}
        if isinstance(uw_cfg, dict) and uw_cfg:
            from utils.state_io import read_json_self_heal
            # Universe v2 metadata
            try:
                u2 = read_json_self_heal("state/daily_universe_v2.json", default={}, heal=True, mkdir=True)
                if isinstance(u2, dict) and isinstance(u2.get("_meta"), dict) and u2.get("symbols") is not None:
                    universe_scoring_version = str((u2.get("_meta") or {}).get("version") or "")
                    universe_source = "daily_universe_v2"
                    try:
                        syms = u2.get("symbols") or []
                        sset = {str(r.get("symbol")).upper() for r in syms if isinstance(r, dict) and r.get("symbol")}
                        in_universe = str(symbol).upper() in sset if sset else None
                    except Exception:
                        in_universe = None
            except Exception:
                pass
            # Fallback: universe v1 metadata
            if not universe_scoring_version:
                try:
                    u1 = read_json_self_heal("state/daily_universe.json", default={}, heal=True, mkdir=True)
                    if isinstance(u1, dict) and isinstance(u1.get("_meta"), dict):
                        universe_scoring_version = str((u1.get("_meta") or {}).get("version") or "")
                        universe_source = "daily_universe_v1"
                except Exception:
                    pass

            # Sector/regime context (safe defaults)
            try:
                from src.intel.sector_intel import get_sector_multipliers, get_sector_profile_version
                sector, sm = get_sector_multipliers(symbol)
                v2_uw_sector_profile = {
                    "sector": sector,
                    "version": str(uw_cfg.get("sector_profile_version") or get_sector_profile_version() or ""),
                    "multipliers": dict(sm),
                }
            except Exception:
                sector, sm = "UNKNOWN", {"flow_weight": 1.0, "darkpool_weight": 1.0, "earnings_weight": 1.0, "short_interest_weight": 1.0}
                v2_uw_sector_profile = {"sector": sector, "version": str(uw_cfg.get("sector_profile_version") or ""), "multipliers": dict(sm)}
            try:
                from src.intel.regime_detector import read_regime_state, regime_alignment_score
                rs = read_regime_state()
                r_label = str(rs.get("regime_label", "NEUTRAL") or "NEUTRAL")
                r_ver = str(((rs.get("_meta", {}) if isinstance(rs, dict) else {}) or {}).get("version") or uw_cfg.get("regime_profile_version") or "")
                r_align = float(regime_alignment_score(r_label, direction))
                v2_uw_regime_profile = {"regime_label": r_label, "version": r_ver, "alignment": r_align}
            except Exception:
                r_label, r_ver, r_align = "NEUTRAL", str(uw_cfg.get("regime_profile_version") or ""), 0.0
                v2_uw_regime_profile = {"regime_label": r_label, "version": r_ver, "alignment": r_align}

            pm = read_json_self_heal("state/premarket_intel.json", default={}, heal=True, mkdir=True)
            post = read_json_self_heal("state/postmarket_intel.json", default={}, heal=True, mkdir=True)

            sym = str(symbol).upper()
            pm_syms = pm.get("symbols", {}) if isinstance(pm, dict) else {}
            post_syms = post.get("symbols", {}) if isinstance(post, dict) else {}
            srec = (pm_syms.get(sym) if isinstance(pm_syms, dict) else None) or (post_syms.get(sym) if isinstance(post_syms, dict) else None) or {}
            if isinstance(srec, dict) and srec:
                uw_intel_version = str((pm.get("_meta", {}) if isinstance(pm, dict) else {}).get("uw_intel_version") or (post.get("_meta", {}) if isinstance(post, dict) else {}).get("uw_intel_version") or uw_cfg.get("version") or "")

                flow_strength = _clamp(_to_num(srec.get("flow_strength", 0.0)), 0.0, 1.0)
                darkpool_bias = _clamp(_to_num(srec.get("darkpool_bias", 0.0)), -1.0, 1.0)
                sector_alignment = _clamp(_to_num(srec.get("sector_alignment", 0.0)), -1.0, 1.0)
                sentiment_s = str(srec.get("sentiment", "NEUTRAL") or "NEUTRAL").upper()
                earnings_prox = srec.get("earnings_proximity")
                try:
                    earnings_days = int(earnings_prox) if earnings_prox is not None else None
                except Exception:
                    earnings_days = None

                # Apply bounded adjustments
                # Tuning weights (multipliers; default 1.0)
                w_flow = float(uw_cfg.get("flow_strength_weight", 1.0))
                w_dp = float(uw_cfg.get("darkpool_bias_weight", 1.0))
                w_sent = float(uw_cfg.get("sentiment_weight", 1.0))
                w_earn = float(uw_cfg.get("earnings_proximity_weight", 1.0))
                w_sector = float(uw_cfg.get("sector_alignment_weight", 1.0))
                w_regime = float(uw_cfg.get("regime_alignment_weight", 1.0))

                uw_adj["flow_strength"] = float(uw_cfg.get("flow_strength_bonus_max", 0.20)) * float(flow_strength) * float(align_mult) * float(sm.get("flow_weight", 1.0)) * w_flow
                uw_adj["darkpool_bias"] = float(uw_cfg.get("darkpool_bias_bonus_max", 0.12)) * float(abs(darkpool_bias)) * float(align_mult) * float(sm.get("darkpool_weight", 1.0)) * w_dp
                if sentiment_s == "BULLISH" and direction == "bullish":
                    uw_adj["sentiment"] = float(uw_cfg.get("sentiment_bonus_max", 0.10)) * float(align_mult) * w_sent
                elif sentiment_s == "BEARISH" and direction == "bearish":
                    uw_adj["sentiment"] = float(uw_cfg.get("sentiment_bonus_max", 0.10)) * float(align_mult) * w_sent

                # Earnings proximity penalty (risk reduction)
                pen_days = int(uw_cfg.get("earnings_penalty_days", 3) or 3)
                if earnings_days is not None and earnings_days <= pen_days:
                    uw_adj["earnings_proximity"] = float(uw_cfg.get("earnings_proximity_penalty_max", -0.12)) * float(align_mult) * float(sm.get("earnings_weight", 1.0)) * w_earn

                uw_adj["sector_alignment"] = float(uw_cfg.get("sector_alignment_bonus_max", 0.12)) * float(max(0.0, sector_alignment)) * float(align_mult) * w_sector
                uw_adj["regime_alignment"] = float(uw_cfg.get("regime_alignment_bonus_max", 0.08)) * float(max(0.0, r_align)) * float(align_mult) * w_regime

                uw_adj["total"] = float(sum(float(v) for k, v in uw_adj.items() if k != "total"))
                uw_inputs = {
                    "flow_strength": float(flow_strength),
                    "darkpool_bias": float(darkpool_bias),
                    "sentiment": sentiment_s,
                    "earnings_proximity": earnings_days,
                    "sector_alignment": float(sector_alignment),
                    "regime_alignment": float(r_align),
                    "uw_intel_version": uw_intel_version,
                }
                # Apply to score
                score_v2 = _clamp(score_v2 + float(uw_adj["total"]), 0.0, 8.0)
    except Exception:
        uw_inputs = {}
        uw_adj = {
            "flow_strength": 0.0,
            "darkpool_bias": 0.0,
            "sentiment": 0.0,
            "earnings_proximity": 0.0,
            "sector_alignment": 0.0,
            "regime_alignment": 0.0,
            "total": 0.0,
        }
        uw_intel_version = ""
        v2_uw_sector_profile = {}
        v2_uw_regime_profile = {}

    # Annotate
    try:
        base["score"] = round(float(score_v2), 3)
        base["composite_version"] = "v2"
        base["base_score"] = round(float(base_score), 3)
        base["v2_adjustments"] = {
            "vol_bonus": round(float(vol_bonus), 4),
            "low_vol_penalty": round(float(low_vol_pen), 4),
            "beta_bonus": round(float(beta_bonus), 4),
            "uw_bonus": round(float(uw_bonus), 4),
            "premarket_bonus": round(float(pre_bonus), 4),
            "regime_align_bonus": round(float(regime_bonus), 4),
            "regime_misalign_penalty": round(float(regime_pen), 4),
            "shaping_adj": round(float(shaping_adj), 4),
            "total": round(float(total_adj), 4),
        }
        base["v2_inputs"] = {
            "realized_vol_20d": round(float(vol_20d), 6),
            "beta_vs_spy": round(float(beta), 6),
            "uw_conviction": round(float(flow_conv), 6),
            "trade_count": int(trade_count),
            "volatility_regime": vol_regime,
            "market_trend": str(mkt_trend),
            "futures_direction": str(fut_dir),
            "spy_overnight_ret": round(float(spy_ov), 6),
            "qqq_overnight_ret": round(float(qqq_ov), 6),
            "posture": posture,
            "direction": direction,
            "posture_confidence": round(float(posture_conf), 4),
            "weights_version": str(v2_params.get("version", "")),
        }
        if uw_inputs:
            base["v2_uw_inputs"] = uw_inputs
            base["v2_uw_adjustments"] = {k: round(float(v), 4) for k, v in (uw_adj or {}).items()}
            base["uw_intel_version"] = str(uw_intel_version)
            if v2_uw_sector_profile:
                base["v2_uw_sector_profile"] = v2_uw_sector_profile
            if v2_uw_regime_profile:
                base["v2_uw_regime_profile"] = v2_uw_regime_profile
        if universe_scoring_version:
            base["universe_scoring_version"] = str(universe_scoring_version)
            base["universe_source"] = str(universe_source or "")
            if in_universe is not None:
                base["in_universe"] = bool(in_universe)
        # Preserve existing notes while making adjustments explicit.
        base["notes"] = (str(base.get("notes", "") or "") + f"; v2_adj={round(float(total_adj), 3)}").strip("; ").strip()
        base["version"] = "V2"
    except Exception:
        pass

    # Attribution (append-only, never raises).
    try:
        # Emit when there is meaningful v2 evaluation context (trade_count>0) OR UW intel exists.
        if (int(trade_count) > 0 or bool(uw_inputs)) and isinstance(uw_adj, dict):
            from src.uw.uw_attribution import emit_uw_attribution
            emit_uw_attribution(
                symbol=str(symbol),
                direction=str(direction),
                composite_version="v2",
                uw_intel_version=str(uw_intel_version or ""),
                uw_features={
                    "flow_strength": (uw_inputs.get("flow_strength", 0.0) if isinstance(uw_inputs, dict) else 0.0),
                    "darkpool_bias": (uw_inputs.get("darkpool_bias", 0.0) if isinstance(uw_inputs, dict) else 0.0),
                    "sentiment": (uw_inputs.get("sentiment", "NEUTRAL") if isinstance(uw_inputs, dict) else "NEUTRAL"),
                    "earnings_proximity": (uw_inputs.get("earnings_proximity") if isinstance(uw_inputs, dict) else None),
                    "sector_alignment": (uw_inputs.get("sector_alignment", 0.0) if isinstance(uw_inputs, dict) else 0.0),
                    "regime_alignment": (uw_inputs.get("regime_alignment", (v2_uw_regime_profile or {}).get("alignment", 0.0)) if isinstance(uw_inputs, dict) else (v2_uw_regime_profile or {}).get("alignment", 0.0)),
                },
                uw_contribution={
                    "score_delta": float(uw_adj.get("total", 0.0) or 0.0),
                    "weight_profile": {
                        "uw_version": str((v2_params or {}).get("uw", {}).get("version", "")) if isinstance(v2_params, dict) else "",
                        "sector_profile": v2_uw_sector_profile,
                        "regime_profile": v2_uw_regime_profile,
                    },
                },
            )
    except Exception:
        pass

    return base
```

## should_enter_v2

```python
def should_enter_v2(composite: Dict, symbol: str, mode: str = "base", api=None) -> bool:
    """
    V3.0 Predatory Entry Filter: V2 entry decision with hierarchical thresholds + Exhaustion Check
    
    Industrial Upgrade:
    - MIN_EXEC_SCORE increased to 3.0 (quality gate)
    - Exhaustion Check: Block entries where price > 2.5 ATRs from 20-period EMA
      (avoids buying the 'top' of a spike)
    """
    if not composite:
        # DIAGNOSTIC: Log composite None
        _log_gate_failure(symbol, "composite_none", {"reason": "composite is None or empty"})
        return False
    
    score = composite.get("score", 0.0)
    threshold = get_threshold(symbol, mode)
    
    # V3.0: Score must be >= 3.0 (MIN_EXEC_SCORE from config)
    if score < threshold:
        # DIAGNOSTIC: Log score gate failure
        _log_gate_failure(symbol, "score_gate", {
            "score": score,
            "threshold": threshold,
            "gap": threshold - score,
            "reason": f"Score {score:.2f} < threshold {threshold:.2f}"
        })
        return False
    
    # Additional gating: don't enter if toxicity too high
    toxicity = composite.get("toxicity", 0.0)
    if toxicity > 0.90:
        # DIAGNOSTIC: Log toxicity gate failure
        _log_gate_failure(symbol, "toxicity_gate", {
            "toxicity": toxicity,
            "threshold": 0.90,
            "reason": f"Toxicity {toxicity:.2f} > 0.90"
        })
        return False
    
    # Don't enter if freshness too low (stale data)
    # CRITICAL FIX: Allow freshness as low as 0.25 if score is good
    # The freshness floor in main.py sets minimum to 0.9, so this should rarely trigger
    freshness = composite.get("freshness", 1.0)
    if freshness < 0.25:  # Lowered from 0.30 to 0.25 to match freshness floor fix
        # DIAGNOSTIC: Log freshness gate failure
        _log_gate_failure(symbol, "freshness_gate", {
            "freshness": freshness,
            "threshold": 0.25,
            "reason": f"Freshness {freshness:.2f} < 0.25"
        })
        return False
    
    # V3.0 EXHAUSTION CHECK: Block entries where price is > 2.5 ATRs from 20-period EMA
    # Purpose: Filter out noise and avoid buying the 'top' of a spike
    if api is not None:
        try:
            from main import compute_atr
            import pandas as pd
            
            # Get current price
            try:
                current_price = float(api.get_last_trade(symbol).price) if hasattr(api.get_last_trade(symbol), 'price') else None
                if not current_price:
                    last_trade = api.get_last_trade(symbol)
                    current_price = float(last_trade) if isinstance(last_trade, (int, float)) else None
            except:
                # Fallback: try getting quote
                try:
                    quote = api.get_quote(symbol)
                    current_price = (float(quote.bid) + float(quote.ask)) / 2.0
                except:
                    current_price = None
            
            if current_price and current_price > 0:
                # Compute ATR (14-period is standard, but we'll use what's available)
                atr = compute_atr(api, symbol, lookback=20)
                
                # Compute 20-period EMA
                try:
                    bars = api.get_bars(symbol, "1Min", limit=25).df
                    if len(bars) >= 20:
                        # Calculate EMA
                        ema_20 = bars['close'].ewm(span=20, adjust=False).mean().iloc[-1]
                        
                        if atr > 0 and ema_20 > 0:
                            # Check if price is > 2.5 ATRs above EMA
                            distance_from_ema = current_price - ema_20
                            atr_distance = distance_from_ema / atr if atr > 0 else 0
                            
                            if atr_distance > 2.5:
                                # EXHAUSTION DETECTED: Price too extended from EMA
                                # DIAGNOSTIC: Log exhaustion gate failure
                                _log_gate_failure(symbol, "atr_exhaustion_gate", {
                                    "current_price": current_price,
                                    "ema_20": float(ema_20),
                                    "atr": atr,
                                    "atr_distance": round(atr_distance, 2),
                                    "threshold": 2.5,
                                    "signal_score": score,
                                    "reason": f"Price {current_price:.2f} is {atr_distance:.2f} ATRs above EMA {float(ema_20):.2f} (threshold: 2.5)"
                                })
                                return False  # Block exhausted entry
                except Exception as e:
                    # If EMA calculation fails, fail open (allow trade)
                    # Log error but don't block
                    pass
        except Exception as e:
            # If exhaustion check fails, fail open (allow trade)
            # This ensures we don't block trades due to technical indicator errors
            pass

    # Phase 5: Gamma wall awareness — block trades into resistance walls
    try:
        levels = composite.get("gamma_resistance_levels") or []
        if api is not None and levels:
            # Reuse current price best-effort (as above); fall back to last trade.
            try:
                current_price = float(api.get_last_trade(symbol).price) if hasattr(api.get_last_trade(symbol), 'price') else None
            except Exception:
                current_price = None
            if not current_price or current_price <= 0:
                try:
                    quote = api.get_quote(symbol)
                    current_price = (float(quote.bid) + float(quote.ask)) / 2.0
                except Exception:
                    current_price = None

            if current_price and current_price > 0:
                nearest = None
                nearest_dist = None
                for lv in levels:
                    lvf = _to_num(lv, 0.0)
                    if lvf <= 0:
                        continue
                    dist = abs(current_price - lvf) / lvf
                    if nearest_dist is None or dist < nearest_dist:
                        nearest_dist = dist
                        nearest = lvf
                if nearest is not None and nearest_dist is not None and nearest_dist <= 0.002:
                    composite["gate_msg"] = "resistance_wall_detected"
                    composite["notes"] = (composite.get("notes", "") + "; gate:resistance_wall_detected").strip("; ").strip()
                    _log_gate_failure(symbol, "resistance_wall_detected", {
                        "current_price": float(current_price),
                        "nearest_level": float(nearest),
                        "distance_pct": round(nearest_dist * 100, 4),
                        "threshold_pct": 0.2,
                        "reason": "Entry price within 0.2% of gamma resistance level"
                    })
                    return False
    except Exception:
        pass
    
    return score >= threshold
```

## WEIGHTS_V3 and ENTRY_THRESHOLDS

```python
# V3 Weights - Full Intelligence Integration (V2 Pipeline)
WEIGHTS_V3 = {
    # Core flow signals (original)
    "options_flow": 2.4,           # Slightly reduced to make room for new signals
    "dark_pool": 1.3,
    "insider": 0.5,
    
    # V2 features (retained)
    "iv_term_skew": 0.6,
    "smile_slope": 0.35,
    "whale_persistence": 0.7,
    "event_alignment": 0.4,
    "toxicity_penalty": -0.9,
    "temporal_motif": 0.6,  # Increased to favor staircase patterns showing early success
    "regime_modifier": 0.3,
    
    # V3 NEW: Expanded Intelligence Signals
    "congress": 0.9,               # Politician trading (user says "very valuable")
    "shorts_squeeze": 0.7,         # Short interest & squeeze potential
    "institutional": 0.5,          # 13F filings & institutional activity
    "market_tide": 0.4,            # Options market sentiment
    "calendar_catalyst": 0.45,     # Earnings/FDA/Economic events
    "etf_flow": 0.3,               # ETF in/outflows
    
    # V2 NEW: Full Intelligence Pipeline (must match SIGNAL_COMPONENTS in main.py)
    "greeks_gamma": 0.4,           # Gamma/delta exposure for squeeze detection
    "ftd_pressure": 0.3,           # Fails-to-deliver for squeeze signals
    "iv_rank": 0.2,                # IV rank for options timing (can be negative)
    "oi_change": 0.35,             # Open interest changes - institutional positioning
    "squeeze_score": 0.2,          # Combined squeeze indicator bonus
}

# NOTE: legacy v1/v2 weight tables have been removed (v2-only engine).

# V2 Thresholds
# ROOT CAUSE FIX: Thresholds were raised to 3.5/3.8/4.2 which blocked ALL trading
# Restored to original reasonable thresholds to allow signals to trade
# Thresholds can be adjusted via hierarchical threshold file if needed
ENTRY_THRESHOLDS = {
    "base": 2.7,      # RESTORED to quality level - orders show scores 2.26-3.00 (avg 2.89)
    "canary": 2.9,    # RESTORED to quality level
    "champion": 3.2   # RESTORED to quality level
}
```

## core

```python
def _compute_composite_score_core(symbol: str, enriched_data: Dict, regime: str = "NEUTRAL",
                                  expanded_intel: Dict = None,
                                  use_adaptive_weights: bool = True) -> Dict[str, Any]:
    """
    Core composite scoring used by the v2-only engine.
    
    Incorporates ALL expanded endpoints:
    - Congress/politician trading
    - Short interest & squeeze potential
    - Institutional activity
    - Market tide
    - Calendar catalysts
    - ETF flows
    
    V3.1: Uses adaptive weight multipliers (0.25x-2.5x) learned from trade outcomes.
    Weights are continuously tuned based on which signals prove most predictive.
    
    Returns comprehensive result with all components for learning
    """
    
    # V3.1: Get adaptive weights if available (V2.0: regime-specific)
    weights = WEIGHTS_V3.copy()
    # Reversible config: signal weight multipliers from win/loss profile (env, default 1.0)
    for env_key, weight_keys in (
        ("FLOW_WEIGHT_MULTIPLIER", ["options_flow"]),
        ("UW_WEIGHT_MULTIPLIER", ["dark_pool", "insider", "whale_persistence", "event_alignment"]),
        ("REGIME_WEIGHT_MULTIPLIER", ["regime_modifier", "market_tide", "calendar_catalyst", "temporal_motif"]),
    ):
        try:
            mult = float(os.environ.get(env_key, "1.0"))
            if mult == 1.0:
                continue
            for k in weight_keys:
                if k in weights:
                    weights[k] = weights[k] * mult
        except Exception:
            pass
    adaptive_active = False
    if use_adaptive_weights:
        # V2.0: Get regime-specific adaptive weights
        adaptive_weights = get_adaptive_weights(regime)
        if adaptive_weights:
            weights.update(adaptive_weights)
            adaptive_active = True
    
    # Load expanded intel if not provided
    if expanded_intel is None:
        expanded_intel = _load_expanded_intel()
    
    symbol_intel = expanded_intel.get(symbol, {})
    
    # Base flow components (from enriched_data / cache)
    # Contract: missing/None sentiment must behave as NEUTRAL.
    flow_sent = enriched_data.get("sentiment") or "NEUTRAL"
    # Conviction: 0 when missing (no inflation). Enrichment/daemon must provide value when there is flow.
    conv_raw = enriched_data.get("conviction", None)
    flow_conv = _to_num(conv_raw) if conv_raw is not None else 0.0
    flow_sign = _sign_from_sentiment(flow_sent)
    
    # Dark pool (Phase 5: use 1h notional, not neutral constant)
    dp = enriched_data.get("dark_pool", {}) or {}
    dp_sent = dp.get("sentiment", "NEUTRAL")
    dp_notional_1h = _to_num(dp.get("total_notional_1h", 0.0) or dp.get("notional_1h", 0.0) or 0.0)
    dp_notional_total = _to_num(dp.get("total_notional", 0.0) or dp.get("total_premium", 0.0) or 0.0)
    dp_prem = dp_notional_1h if dp_notional_1h > 0 else dp_notional_total  # backward compat name
    
    # Insider (also used for institutional)
    ins = enriched_data.get("insider", {}) or {}
    
    # V2 features
    iv_skew = _to_num(enriched_data.get("iv_term_skew", 0.0))
    smile_slope = _to_num(enriched_data.get("smile_slope", 0.0))
    toxicity = _to_num(enriched_data.get("toxicity", 0.0))
    event_align = _to_num(enriched_data.get("event_alignment", 0.0))
    freshness = _to_num(enriched_data.get("freshness", 1.0))
    
    # V3 NEW: Expanded intelligence from cache
    congress_data = enriched_data.get("congress", {}) or symbol_intel.get("congress", {})
    shorts_data = enriched_data.get("shorts", {}) or symbol_intel.get("shorts", {})
    # FIXED: Market tide is stored per-ticker in cache, check enriched_data first
    tide_data = enriched_data.get("market_tide", {}) or symbol_intel.get("market_tide", {})
    calendar_data = enriched_data.get("calendar", {}) or symbol_intel.get("calendar", {})
    
    # Motif data
    motif_staircase = enriched_data.get("motif_staircase", {})
    motif_sweep = enriched_data.get("motif_sweep_block", {})
    motif_burst = enriched_data.get("motif_burst", {})
    motif_whale = enriched_data.get("motif_whale", {})
    
    # ============ COMPONENT CALCULATIONS (using adaptive weights) ============
    all_notes = []
    if adaptive_active:
        all_notes.append("adaptive_weights_active")
    if conv_raw is None:
        all_notes.append("conviction_missing")
    
    # 1. Options flow (primary)
    # CAUSAL INSIGHT: Low Magnitude Flow (Stealth Flow) has 100% win rate
    # Apply +0.2 points base conviction boost for LOW flow magnitude (< 0.3)
    # Contract: DO NOT boost when there is *no* flow data (trade_count == 0), otherwise
    # missing data becomes a positive constant and collapses scores across the universe.
    flow_trade_count = int(_to_num(enriched_data.get("trade_count", 0)) or 0)
    flow_magnitude = "LOW" if flow_conv < 0.3 else ("MEDIUM" if flow_conv < 0.7 else "HIGH")
    stealth_flow_boost = 0.2 if (flow_trade_count > 0 and flow_magnitude == "LOW") else 0.0
    flow_conv_adjusted = min(1.0, flow_conv + stealth_flow_boost)  # Cap at 1.0
    
    # Use regime-aware weight for options_flow component
    flow_weight = get_weight("options_flow", regime)
    flow_component = flow_weight * flow_conv_adjusted

    # Phase 5: Sweep urgency multiplier (>=3 sweeps with premium > $100k in recent flow)
    urgency_multiplier = 1.0
    try:
        sweeps_hi = 0
        now_ts = int(time.time())
        for tr in (enriched_data.get("flow_trades") or []):
            if not isinstance(tr, dict):
                continue
            if not _is_sweep_trade(tr):
                continue
            prem = _trade_premium_usd(tr)
            if prem < 100_000:
                continue
            tts = _parse_trade_ts(tr)
            if tts is not None and (now_ts - tts) > 3600:
                continue  # focus on last hour if timestamps exist
            sweeps_hi += 1
        if sweeps_hi >= 3:
            urgency_multiplier = 1.2
            flow_component *= urgency_multiplier
            all_notes.append(f"sweep_urgency({urgency_multiplier}x,{sweeps_hi} sweeps>$100k)")
    except Exception:
        pass
    
    # Track if stealth flow boost was applied (for logging)
    if stealth_flow_boost > 0:
        all_notes.append(f"stealth_flow_boost(+{stealth_flow_boost:.1f})")
    
    # 2. Dark pool (use regime-aware weight) - proportional to 1h notional
    # Proportional scaling: 0 -> 0.2 baseline, 50M -> ~1.0 strength
    dp_strength = 0.2
    try:
        scale = max(0.0, dp_prem)
        dp_strength = 0.2 + 0.8 * min(1.0, scale / 50_000_000.0)
    except Exception:
        dp_strength = 0.2
    dp_weight = get_weight("dark_pool", regime)
    dp_component = dp_weight * dp_strength
    
    # 3. Insider (use regime-aware weight)
    ins_sent = ins.get("sentiment", "NEUTRAL")
    ins_mod = _to_num(ins.get("conviction_modifier", 0.0))
    insider_weight = get_weight("insider", regime)
    if ins_sent == "BULLISH":
        insider_component = insider_weight * (0.50 + ins_mod)
    elif ins_sent == "BEARISH":
        insider_component = insider_weight * (0.50 - abs(ins_mod))
    else:
        insider_component = insider_weight * 0.25
    
    # 4. IV term skew (use regime-aware weight)
    iv_aligned = (iv_skew > 0 and flow_sign == +1) or (iv_skew < 0 and flow_sign == -1)
    iv_weight = get_weight("iv_term_skew", regime)
    iv_component = iv_weight * abs(iv_skew) * (1.3 if iv_aligned else 0.7)
    
    # 5. Smile slope (use regime-aware weight)
    smile_weight = get_weight("smile_slope", regime)
    smile_component = smile_weight * abs(smile_slope)
    
    # 6. Whale persistence (use regime-aware weight); 0 when not detected so scoring is data-driven only.
    whale_detected = motif_whale.get("detected", False)
    whale_weight = get_weight("whale_persistence", regime)
    whale_score = 0.0 if not whale_detected else whale_weight * _to_num(motif_whale.get("avg_conviction", 0.0))
    
    # 7. Event alignment (use regime-aware weight)
    event_weight = get_weight("event_alignment", regime)
    event_component = event_weight * event_align
    
    # 8. Temporal motif bonus (use regime-aware weight); 0 when no motif so scoring is data-driven only.
    motif_weight = get_weight("temporal_motif", regime)
    motif_bonus = 0.0
    if motif_staircase.get("detected"):
        motif_bonus += motif_weight * motif_staircase.get("slope", 0.0) * 3.0
        all_notes.append(f"staircase({motif_staircase.get('steps', 0)} steps)")
    if motif_burst.get("detected"):
        intensity = motif_burst.get("intensity", 0.0)
        motif_bonus += motif_weight * min(1.0, intensity / 2.0)
        all_notes.append(f"burst({motif_burst.get('count', 0)} updates)")
    
    # 9. Toxicity penalty - FIXED: Apply penalty starting at 0.5 (was 0.85)
    # CRITICAL: Ensure toxicity weight is NEGATIVE (it's a penalty, not a boost)
    # Use regime-aware weight
    raw_tox_weight = get_weight("toxicity_penalty", regime)
    tox_weight = raw_tox_weight if raw_tox_weight < 0 else -abs(raw_tox_weight)  # Force negative
    toxicity_component = 0.0
    if toxicity > 0.5:
        toxicity_component = tox_weight * (toxicity - 0.5) * 1.5
        all_notes.append(f"toxicity_penalty({toxicity:.2f})")
    elif toxicity > 0.3:
        toxicity_component = tox_weight * (toxicity - 0.3) * 0.5
        all_notes.append(f"mild_toxicity({toxicity:.2f})")
    
    # 10. Regime modifier
    # FIXED: Handle "mixed" regime case
    aligned_regime = (regime == "RISK_ON" and flow_sign == +1) or (regime == "RISK_OFF" and flow_sign == -1)
    opposite_regime = (regime == "RISK_ON" and flow_sign == -1) or (regime == "RISK_OFF" and flow_sign == +1)
    regime_factor = 1.0
    if regime == "RISK_ON":
        regime_factor = 1.15 if aligned_regime else 0.95
    elif regime == "RISK_OFF":
        regime_factor = 1.10 if opposite_regime else 0.90
    elif regime == "mixed" or regime == "NEUTRAL":
        # FIXED: Mixed/neutral regime - slight positive contribution for balanced conditions
        regime_factor = 1.02  # Small boost for neutral/mixed conditions
    regime_weight = get_weight("regime_modifier", regime)
    regime_component = regime_weight * (regime_factor - 1.0) * 2.0
    
    # ============ V3 NEW COMPONENTS ============
    
    # 11. Congress/Politician trading
    congress_component, congress_notes = compute_congress_component(congress_data, flow_sign)
    if congress_notes:
        all_notes.append(congress_notes)
    
    # 12. Short interest & squeeze
    shorts_component, shorts_notes = compute_shorts_component(shorts_data, flow_sign, regime)
    if shorts_notes:
        all_notes.append(shorts_notes)
    
    # 13. Institutional activity (enhanced from insider)
    institutional_payload = enriched_data.get("institutional", {}) or symbol_intel.get("institutional", {})
    inst_component, inst_notes = compute_institutional_component(ins, institutional_payload, flow_sign, regime)
    if inst_notes:
        all_notes.append(inst_notes)
    
    # 14. Market tide
    tide_component, tide_notes = compute_market_tide_component(tide_data, flow_sign, regime)
    if tide_notes:
        all_notes.append(tide_notes)
    
    # 15. Calendar catalysts (component function uses get_weight internally with regime)
    calendar_component, calendar_notes = compute_calendar_component(calendar_data, symbol, regime)
    if calendar_notes:
        all_notes.append(calendar_notes)
    
    # ============ V2 NEW COMPONENTS (Full Intelligence Pipeline) ============
    
    # 16. Greeks/Gamma (squeeze detection)
    greeks_data = enriched_data.get("greeks", {})
    gamma_resistance_levels = _extract_gamma_resistance_levels(greeks_data if isinstance(greeks_data, dict) else {})
    # REAL SCORES: No placeholder. When greeks data missing use 0.0 (see SIGNAL_INTEGRITY_REAL_SCORES_PATH.md).
    if not greeks_data:
        greeks_gamma_component = 0.0
        all_notes.append("greeks_missing")
    else:
        # FIXED: Calculate gamma_exposure from call_gamma and put_gamma if not directly available
        gamma_exposure = _to_num(greeks_data.get("gamma_exposure", 0))
        if gamma_exposure == 0:
            # Calculate from call_gamma and put_gamma (net gamma exposure)
            call_gamma = _to_num(greeks_data.get("call_gamma", 0))
            put_gamma = _to_num(greeks_data.get("put_gamma", 0))
            gamma_exposure = call_gamma - put_gamma  # Net gamma exposure
        
        gamma_squeeze = greeks_data.get("gamma_squeeze_setup", False)
        greeks_weight = get_weight("greeks_gamma", regime)
        if gamma_squeeze:
            greeks_gamma_component = greeks_weight * 1.0
            all_notes.append("gamma_squeeze_setup")
        elif abs(gamma_exposure) > 500000:
            greeks_gamma_component = greeks_weight * 0.5
        elif abs(gamma_exposure) > 100000:
            greeks_gamma_component = greeks_weight * 0.25
        elif abs(gamma_exposure) > 10000:  # Lower threshold for smaller contributions
            greeks_gamma_component = greeks_weight * 0.1
        else:
            greeks_gamma_component = greeks_weight * 0.2  # Neutral default instead of 0.0
    
    # 17. FTD Pressure (squeeze signals)
    # FIXED: Check both 'ftd' and 'shorts' keys (FTD data may be in shorts)
    ftd_data = enriched_data.get("ftd", {}) or enriched_data.get("shorts", {})
    # SCORING PIPELINE FIX (Priority 4): Provide neutral default if data missing
    if not ftd_data:
        ftd_weight = get_weight("ftd_pressure", regime)
        ftd_pressure_component = ftd_weight * 0.2  # Neutral default
        all_notes.append("ftd_neutral_default")
    else:
        ftd_count = _to_num(ftd_data.get("ftd_count", 0))
        ftd_squeeze = ftd_data.get("squeeze_pressure", False) or ftd_data.get("squeeze_risk", False)
        ftd_weight = get_weight("ftd_pressure", regime)
        if ftd_squeeze or ftd_count > 200000:
            ftd_pressure_component = ftd_weight * 1.0
            all_notes.append("high_ftd_pressure")
        elif ftd_count > 100000:
            ftd_pressure_component = ftd_weight * 0.67
        elif ftd_count > 50000:
            ftd_pressure_component = ftd_weight * 0.33
        elif ftd_count > 10000:  # FIXED: Lower threshold for smaller contributions
            ftd_pressure_component = ftd_weight * 0.1
        else:
            ftd_pressure_component = ftd_weight * 0.2  # Neutral default instead of 0.0
    
    # 18. IV Rank (volatility regime)
    # FIXED: Check both 'iv' and 'iv_rank' keys, and handle iv_rank_1y field
    iv_data = enriched_data.get("iv", {}) or enriched_data.get("iv_rank", {})
    iv_rank_val = _to_num(iv_data.get("iv_rank", iv_data.get("iv_rank_1y", 50)))
    
    iv_rank_weight = get_weight("iv_rank", regime)
    if iv_rank_val < 20:  # Low IV = opportunity
        iv_rank_component = iv_rank_weight * 1.0
        all_notes.append("low_iv_opportunity")
    elif iv_rank_val < 30:
        iv_rank_component = iv_rank_weight * 0.5
    elif iv_rank_val > 80:  # High IV = caution
        iv_rank_component = -iv_rank_weight * 1.0
        all_notes.append("high_iv_caution")
    elif iv_rank_val > 70:
        iv_rank_component = -iv_rank_weight * 0.5
    elif 30 <= iv_rank_val <= 70:  # FIXED: Add contribution for middle range
        # Moderate IV - slight positive contribution for balanced conditions
        iv_rank_component = iv_rank_weight * 0.15
    else:
        iv_rank_component = 0.0
    
    # 19. OI Change (institutional positioning)
    # FIXED: Check both 'oi' and 'oi_change' keys
    oi_data = enriched_data.get("oi_change", {}) or enriched_data.get("oi", {})
    # SCORING PIPELINE FIX (Priority 4): Provide neutral default if data missing
    if not oi_data:
        oi_weight = get_weight("oi_change", regime)
        oi_change_component = oi_weight * 0.2  # Neutral default
        all_notes.append("oi_change_neutral_default")
    else:
        # Calculate net_oi from available fields if net_oi_change doesn't exist
        net_oi = _to_num(oi_data.get("net_oi_change", 0))
        if net_oi == 0:
            # Try to calculate from curr_oi and prev_oi or other fields
            curr_oi = _to_num(oi_data.get("curr_oi", 0))
            # If we have volume data, use that as proxy
            if curr_oi == 0:
                volume = _to_num(oi_data.get("volume", 0))
                if volume > 0:
                    net_oi = volume * 0.1  # Estimate OI change from volume
        
        oi_sentiment = oi_data.get("oi_sentiment", "NEUTRAL")
        # If sentiment not available, infer from net_oi
        if oi_sentiment == "NEUTRAL" and net_oi != 0:
            oi_sentiment = "BULLISH" if net_oi > 0 else "BEARISH"
        
        oi_weight = get_weight("oi_change", regime)
        if net_oi > 50000 and oi_sentiment == "BULLISH" and flow_sign > 0:
            oi_change_component = oi_weight * 1.0
            all_notes.append("strong_call_positioning")
        elif net_oi > 20000 and oi_sentiment == "BULLISH":
            oi_change_component = oi_weight * 0.57
        elif abs(net_oi) > 10000:
            oi_change_component = oi_weight * 0.29
        elif abs(net_oi) > 1000:  # FIXED: Lower threshold for smaller contributions
            oi_change_component = oi_weight * 0.1
        else:
            oi_change_component = oi_weight * 0.2  # Neutral default instead of 0.0
    
    # 20. ETF Flow (market sentiment) - REDUCED weight due to negative contribution in analysis
    etf_data = enriched_data.get("etf_flow", {})
    # SCORING PIPELINE FIX (Priority 4): Provide neutral default if data missing
    if not etf_data:
        etf_weight = get_weight("etf_flow", regime)
        etf_flow_component = etf_weight * 0.2  # Neutral default
        all_notes.append("etf_flow_neutral_default")
    else:
        etf_sentiment = etf_data.get("overall_sentiment", "NEUTRAL")
        risk_on = etf_data.get("market_risk_on", False)
        etf_weight = get_weight("etf_flow", regime)
        if etf_sentiment == "BULLISH" and risk_on:
            etf_flow_component = etf_weight * 1.0  # Reduced from 0.2 to 0.05
            all_notes.append("risk_on_environment")
        elif etf_sentiment == "BULLISH":
            etf_flow_component = etf_weight * 0.5
        elif etf_sentiment == "BEARISH":
            etf_flow_component = -etf_weight * 0.3  # Reduced negative impact too
        else:
            etf_flow_component = etf_weight * 0.2  # Neutral default instead of 0.0
    
    # 21. Squeeze Score (combined FTD + SI + gamma)
    squeeze_data = enriched_data.get("squeeze_score", {})
    # SCORING PIPELINE FIX (Priority 4): Provide neutral default if data missing
    if not squeeze_data:
        squeeze_weight = get_weight("squeeze_score", regime)
        squeeze_score_component = squeeze_weight * 0.2  # Neutral default
        all_notes.append("squeeze_score_neutral_default")
    else:
        squeeze_signals = _to_num(squeeze_data.get("signals", 0))
        high_squeeze = squeeze_data.get("high_squeeze_potential", False)
        squeeze_weight = get_weight("squeeze_score", regime)
        if high_squeeze:
            squeeze_score_component = squeeze_weight * 1.0
            all_notes.append("high_squeeze_potential")
        elif squeeze_signals >= 1:
            squeeze_score_component = squeeze_weight * 0.5
        else:
            squeeze_score_component = squeeze_weight * 0.2  # Neutral default instead of 0.0
    
    # ============ FINAL SCORE ============
    
    # Sum all components (including V2)
    composite_raw = (
        flow_component +
        dp_component +
        insider_component +
        iv_component +
        smile_component +
        whale_score +
        event_component +
        motif_bonus +
        toxicity_component +
        regime_component +
        # V3 new components
        congress_component +
        shorts_component +
        inst_component +
        tide_component +
        calendar_component +
        # V2 new components
        greeks_gamma_component +
        ftd_pressure_component +
        iv_rank_component +
        oi_change_component +
        etf_flow_component +
        squeeze_score_component
    )
    
    # Apply freshness decay
    composite_score = composite_raw * freshness
    
    # ALPHA REPAIR: Whale Conviction Normalization
    # If whale_persistence or sweep_block motifs are detected, apply +0.5 Conviction Boost
    # This ensures actual Whales can clear the 3.0 gate even when 'Noise' scores are suppressed
    whale_conviction_boost = 0.0
    if whale_detected or motif_sweep.get("detected", False):
        whale_conviction_boost = 0.5
        composite_score += whale_conviction_boost
        all_notes.append(f"whale_conviction_boost(+{whale_conviction_boost})")
    
    # Pre-clamp score for attribution (multi-model signal edge discovery)
    composite_pre_clamp = composite_score
    # Clamp to 0-8 (higher max due to new components)
    composite_score = max(0.0, min(8.0, composite_score))

    # ============ SIZING OVERLAY ============
    sizing_overlay = 0.0
    
    # IV skew alignment boost
    if iv_aligned and abs(iv_skew) > 0.08:
        sizing_overlay += SIZING_OVERLAYS["iv_skew_align_boost"]
    
    # Whale persistence boost
    if whale_detected:
        sizing_overlay += SIZING_OVERLAYS["whale_persistence_boost"]
    
    # V3: Congress confirmation boost
    if congress_component > 0.3:
        sizing_overlay += 0.15
    
    # V3: Squeeze setup boost
    if shorts_component > 0.3:
        sizing_overlay += 0.20
    
    # Skew conflict penalty
    if not iv_aligned and abs(iv_skew) > 0.08:
        sizing_overlay += SIZING_OVERLAYS["skew_conflict_penalty"]
    
    # Toxicity penalty
    if toxicity > 0.85:
        sizing_overlay += SIZING_OVERLAYS["toxicity_penalty"]
    
    # ============ ENTRY DELAY ============
    entry_delay_sec = 0
    if motif_staircase.get("detected") and motif_staircase.get("steps", 0) < 4:
        entry_delay_sec = 120
    if motif_sweep.get("detected") and motif_sweep.get("immediate"):
        entry_delay_sec = 0
    if motif_burst.get("detected") and motif_burst.get("intensity", 0) > 2.0:
        entry_delay_sec = 180
    
    # ============ BUILD RESULT ============
    components = {
        # Core
        "flow": round(flow_component, 3),
        "dark_pool": round(dp_component, 3),
        "insider": round(insider_component, 3),
        # V2
        "iv_skew": round(iv_component, 3),
        "smile": round(smile_component, 3),
        "whale": round(whale_score, 3),
        "event": round(event_component, 3),
        "motif_bonus": round(motif_bonus, 3),
        "toxicity_penalty": round(toxicity_component, 3),
        "regime": round(regime_component, 3),
        # V3 NEW
        "congress": round(congress_component, 3),
        "shorts_squeeze": round(shorts_component, 3),
        "institutional": round(inst_component, 3),
        "market_tide": round(tide_component, 3),
        "calendar": round(calendar_component, 3),
        # V2 NEW (Full Intelligence Pipeline) - must match SIGNAL_COMPONENTS in main.py
        "greeks_gamma": round(greeks_gamma_component, 3),
        "ftd_pressure": round(ftd_pressure_component, 3),
        "iv_rank": round(iv_rank_component, 3),
        "oi_change": round(oi_change_component, 3),
        "etf_flow": round(etf_flow_component, 3),
        "squeeze_score": round(squeeze_score_component, 3),
        # Meta
        "freshness_factor": round(freshness, 3)
    }

    # Component sources for audit/telemetry
    # WHY: Stop treating neutral defaults as "real" signal; make it explicit which components were defaulted/missing.
    # HOW TO VERIFY: position metadata and attribution logs include component_sources; defaults correlate with *_neutral_default notes.
    default_note_by_component = {
        "congress": "congress_neutral_default",
        "shorts_squeeze": "shorts_neutral_default",
        "institutional": "institutional_neutral_default",
        "market_tide": "tide_neutral_default",
        "calendar": "calendar_neutral_default",
        "greeks_gamma": "greeks_neutral_default",
        "ftd_pressure": "ftd_neutral_default",
        "oi_change": "oi_change_neutral_default",
        "etf_flow": "etf_flow_neutral_default",
        "squeeze_score": "squeeze_score_neutral_default",
    }
    component_sources = {}
    missing_components = []
    for name in components.keys():
        source = "real"
        note_marker = default_note_by_component.get(name)
        if note_marker and note_marker in all_notes:
            source = "default"
        # Dark pool "0 notional + NEUTRAL" should be treated as missing signal.
        if name == "dark_pool" and dp_sent not in ("BULLISH", "BEARISH") and dp_prem <= 0:
            source = "missing"
        # Whale/motif are legitimately absent when no motif detected.
        if name == "whale" and not whale_detected:
            source = "missing"
        if name == "motif_bonus" and not (motif_staircase.get("detected") or motif_burst.get("detected")):
            source = "missing"
        component_sources[name] = source
        if source == "missing":
            missing_components.append(name)

    # Group sums for signal-strength / edge discovery (multi-model attribution)
    _uw_keys = ("flow", "dark_pool", "insider", "whale", "event")
    _regime_keys = ("regime", "market_tide", "calendar", "motif_bonus")
    group_sums = {
        "uw": round(sum(components.get(k, 0) or 0 for k in _uw_keys), 4),
        "regime_macro": round(sum(components.get(k, 0) or 0 for k in _regime_keys), 4),
        "other_components": round(
            sum(v or 0 for k, v in components.items() if k not in _uw_keys and k not in _regime_keys and k != "freshness_factor"),
            4,
        ),
    }

    # Attribution: list of {signal_id, name, contribution_to_score} for effectiveness/signal_effectiveness (Phase 5 join).
    attribution_components = [
        {"signal_id": k, "name": k, "contribution_to_score": round(float(v), 4)}
        for k, v in components.items()
        if k != "freshness_factor" and isinstance(v, (int, float))
    ]

    return {
        "symbol": symbol,
        "score": round(composite_score, 3),
        "composite_pre_clamp": round(composite_pre_clamp, 4),
        "group_sums": group_sums,
        "version": "V3.1" if adaptive_active else "V3",
        "adaptive_weights_active": adaptive_active,
        "gamma_resistance_levels": gamma_resistance_levels,
        "components": components,
        "attribution_components": attribution_components,
        "component_sources": component_sources,
        "missing_components": missing_components,
        "motifs": {
            "staircase": motif_staircase.get("detected", False),
            "sweep_block": motif_sweep.get("detected", False),
            "burst": motif_burst.get("detected", False),
            "whale_persistence": whale_detected
        },
        "expanded_intel": {
            # V1 intelligence
            "congress_active": bool(congress_data),
            "shorts_active": bool(shorts_data),
            "tide_active": bool(tide_data),
            "calendar_active": bool(calendar_data),
            # V2 NEW intelligence
            "greeks_active": bool(enriched_data.get("greeks", {}).get("gamma_exposure", 0)),
            "ftd_active": bool(enriched_data.get("ftd", {}).get("ftd_count", 0)),
            "iv_active": bool(enriched_data.get("iv", {}).get("iv_rank", 0)),
            "oi_active": bool(enriched_data.get("oi", {}).get("net_oi_change", 0)),
            "etf_active": bool(enriched_data.get("etf_flow", {}).get("overall_sentiment")),
            "squeeze_active": bool(enriched_data.get("squeeze_score", {}).get("signals", 0))
        },
        "sizing_overlay": round(sizing_overlay, 3),
        "entry_delay_sec": entry_delay_sec,
        "toxicity": round(toxicity, 3),
        "freshness": round(freshness, 3),
        "whale_conviction_boost": round(whale_conviction_boost, 3),  # ALPHA REPAIR: Track whale boost applied
        "notes": "; ".join(all_notes) if all_notes else "clean",
        # For learning - all raw inputs (V2 Full Intelligence Pipeline)
        "features_for_learning": {
            # Original features
            "flow_conviction": flow_conv,
            "flow_sign": flow_sign,
            "dp_premium": dp_prem,
            "dp_notional_1h": dp_notional_1h,
            "sweep_urgency_multiplier": urgency_multiplier,
            "iv_skew": iv_skew,
            "smile_slope": smile_slope,
            "toxicity": toxicity,
            "congress_buys": congress_data.get("buys", 0) if congress_data else 0,
            "congress_sells": congress_data.get("sells", 0) if congress_data else 0,
            "short_interest_pct": shorts_data.get("interest_pct", 0) if shorts_data else 0,
            "days_to_cover": shorts_data.get("days_to_cover", 0) if shorts_data else 0,
            "squeeze_risk": shorts_data.get("squeeze_risk", False) if shorts_data else False,
            "regime": regime,
            # V2 NEW: Full intelligence pipeline features
            "greeks_gamma": _to_num(enriched_data.get("greeks", {}).get("gamma_exposure", 0)),
            "greeks_delta": _to_num(enriched_data.get("greeks", {}).get("delta_exposure", 0)),
            "gamma_squeeze_setup": enriched_data.get("greeks", {}).get("gamma_squeeze_setup", False),
            "ftd_count": _to_num(enriched_data.get("ftd", {}).get("ftd_count", 0)),
            "ftd_pressure": enriched_data.get("ftd", {}).get("squeeze_pressure", False),
            "iv_rank": _to_num(enriched_data.get("iv", {}).get("iv_rank", 0)),
            "iv_percentile": _to_num(enriched_data.get("iv", {}).get("iv_percentile", 0)),
            "high_iv_caution": enriched_data.get("iv", {}).get("high_iv_caution", False),
            "low_iv_opportunity": enriched_data.get("iv", {}).get("low_iv_opportunity", False),
            "oi_net_change": _to_num(enriched_data.get("oi", {}).get("net_oi_change", 0)),
            "oi_sentiment": enriched_data.get("oi", {}).get("oi_sentiment", "NEUTRAL"),
            "etf_overall_sentiment": enriched_data.get("etf_flow", {}).get("overall_sentiment", "NEUTRAL"),
            "market_risk_on": enriched_data.get("etf_flow", {}).get("market_risk_on", False),
            "squeeze_signals": _to_num(enriched_data.get("squeeze_score", {}).get("signals", 0)),
            "high_squeeze_potential": enriched_data.get("squeeze_score", {}).get("high_squeeze_potential", False),
            "squeeze_setup_type": enriched_data.get("squeeze_score", {}).get("setup", "NONE"),
            "max_pain": _to_num(enriched_data.get("max_pain", {}).get("max_pain", 0))
        }
    }
```

## submit_entry

```python
    def compute_entry_price(self, symbol: str, side: str):
        bid, ask = self.get_nbbo(symbol)
        if bid <= 0 or ask <= 0:
            return None
        mid = (bid + ask) / 2.0
        tol = mid * (Config.ENTRY_TOLERANCE_BPS / 10000.0)

        mode = Config.ENTRY_MODE.upper()
        if mode == "MAKER_BIAS":
            if side == "buy":
                target = min(ask - tol, max(bid, mid - tol))
            else:
                target = min(ask, max(bid + tol, mid - tol))
            return normalize_equity_limit_price(target)

        if mode == "MIDPOINT":
            if side == "buy":
                return normalize_equity_limit_price(min(mid, ask - tol))
            else:
                return normalize_equity_limit_price(max(mid, bid + tol))

        if mode == "BID_PLUS":
            if side == "buy":
                return normalize_equity_limit_price(min(ask - tol, bid + tol))
            else:
                return normalize_equity_limit_price(max(bid + tol, ask - tol))

        spread = ask - bid
        if spread / mid <= (Config.ENTRY_TOLERANCE_BPS / 10000.0):
            return normalize_equity_limit_price(mid)
        return None

    def _get_order_by_client_order_id(self, client_order_id: str):
        fn = getattr(self.api, "get_order_by_client_order_id", None)
        if callable(fn):
            return fn(client_order_id)
        return None

    @global_failure_wrapper("order")
    def submit_entry(
        self,
        symbol: str,
        qty: int,
        side: str,
        regime: str = "unknown",
        client_order_id_base: str = None,
        *,
        entry_score: float = None,
        market_regime: str = None,
    ):
        """
        Submit entry order with spread watchdog and regime-aware execution.
        
        Per Audit Recommendations (Dec 2025):
        - Spread Watchdog: Block trades when spread > MAX_SPREAD_BPS
        - Regime-Aware Execution: Adjust aggressiveness based on market regime
        
        Self-healing: All orders must pass trade_guard before submission.
        """
        # Logging upgrade: mandatory metadata integrity
        # We never enter a new position without a positive score (scoring exists to only enter when we have edge).
        # - entry_score must exist and be positive
        # - market_regime must be explicitly known (not "unknown")
        if entry_score is None or not isinstance(entry_score, (int, float)) or float(entry_score) <= 0.0:
            log_event("orders", "CRITICAL_missing_entry_score_abort",
                      symbol=symbol, side=side, qty=qty, entry_score=entry_score)
            return None, None, "metadata_missing", 0, "missing_entry_score"

        effective_regime = market_regime if market_regime is not None else regime
        if effective_regime is None or str(effective_regime).strip().lower() in ("", "unknown", "none"):
            log_event("orders", "CRITICAL_missing_market_regime_abort",
                      symbol=symbol, side=side, qty=qty, market_regime=market_regime, regime=regime)
            return None, None, "metadata_missing", 0, "missing_market_regime"

        # Phase 2: prevent broker rejections for short entries (LCID-style)
        # Only applies to entry path; exits may legitimately submit sell orders to close longs.
        if side == "sell":
            try:
                asset = self.api.get_asset(symbol)
                is_shortable = bool(getattr(asset, "shortable", False))
            except Exception as e:
                log_event("submit_entry", "asset_lookup_failed", symbol=symbol, error=str(e))
                is_shortable = False
            if not is_shortable:
                log_event("submit_entry", "asset_not_shortable_blocked", symbol=symbol)
                return None, None, "asset_not_shortable", 0, "asset_not_shortable"

        ref_price = self.get_last_trade(symbol)
        if ref_price <= 0:
            log_event("submit_entry", "bad_ref_price", symbol=symbol, ref_price=ref_price)
            return None, None, "error", 0, "bad_ref_price"
        
        # === TRADE GUARD: Mandatory sanity check (Risk #15) ===
        try:
            from trade_guard import evaluate_order
            from state_manager import StateManager
            
            # Get current positions from state manager
            state_manager = getattr(self, '_state_manager', None)
            if state_manager is None:
                # Initialize state manager if not already done
                state_manager = StateManager(self.api)
                state_manager.load_state()
                self._state_manager = state_manager
            
            current_state = state_manager.get_state()
            current_positions = current_state.get("open_positions", {})
            
            # Get account info for exposure checks
            try:
                account = self.api.get_account()
                account_equity = float(getattr(account, "equity", 0.0))
                account_buying_power = float(getattr(account, "buying_power", 0.0))
            except Exception:
                account_equity = 0.0
                account_buying_power = 0.0
            
            # Build order context for trade guard
            order_context = {
                "symbol": symbol,
                "side": side,
                "qty": qty,
                "intended_price": ref_price,
                "last_known_price": ref_price,
                "current_positions": current_positions,
                "account_equity": account_equity,
                "account_buying_power": account_buying_power,
                "last_trade_timestamp": current_state.get("last_trade_per_symbol", {}).get(symbol),
                "risk_config": {}  # Can be extended with custom risk config
            }
            
            # Evaluate order
            approved, reason = evaluate_order(order_context)
            if not approved:
                log_event("submit_entry", "trade_guard_blocked", 
                         symbol=symbol, side=side, qty=qty, reason=reason)
                # Log rejection
                from trade_guard import get_guard
                guard = get_guard()
                guard.log_rejection(symbol, side, qty, reason, order_context)
                return None, None, "trade_guard_blocked", 0, reason
        except ImportError:
            # Trade guard not available - log warning but continue (fail open for backward compatibility)
            log_event("submit_entry", "trade_guard_unavailable", symbol=symbol, warning="Trade guard module not found")
        except Exception as e:
            # Trade guard error - log but don't block (fail open)
            log_event("submit_entry", "trade_guard_error", symbol=symbol, error=str(e))
        
        # === SPREAD WATCHDOG (Audit Recommendation) ===
        if Config.ENABLE_SPREAD_WATCHDOG:
            bid, ask = self.get_nbbo(symbol)
            if bid > 0 and ask > 0:
                mid = (bid + ask) / 2.0
                # BULLETPROOF: Validate mid > 0 before division
                spread_bps = ((ask - bid) / mid * 10000) if mid > 0 else 0
                # Clamp to reasonable range
                spread_bps = max(0.0, min(10000.0, spread_bps))
                if spread_bps > Config.MAX_SPREAD_BPS:
                    log_event("submit_entry", "spread_watchdog_blocked", 
                             symbol=symbol, spread_bps=round(spread_bps, 1),
                             max_spread_bps=Config.MAX_SPREAD_BPS,
                             bid=bid, ask=ask)
                    return None, None, "spread_too_wide", 0, "spread_too_wide"
        
        notional = qty * ref_price
        if notional < Config.MIN_NOTIONAL_USD:
            log_event("submit_entry", "min_notional_blocked", 
                     symbol=symbol, qty=qty, ref_price=ref_price, 
                     notional=notional, min_required=Config.MIN_NOTIONAL_USD)
            return None, None, "min_notional_blocked", 0, "min_notional_blocked"
        
        # V3.0 FORENSIC FIX: Handle symbols > $825 (GS, COST, etc.)
        # If price exceeds position size, attempt fractional shares or log Price_Exceeds_Cap event
        position_size_usd = Config.POSITION_SIZE_USD if hasattr(Config, 'POSITION_SIZE_USD') else Config.SIZE_BASE_USD
        if ref_price > position_size_usd:
            # Try fractional shares if supported (Alpaca paper trading may support this)
            try:
                # Calculate fractional qty to match position size
                fractional_qty = position_size_usd / ref_price
                if fractional_qty >= 0.001:  # Minimum fractional share (0.001)
                    qty = fractional_qty
                    log_event("submit_entry", "fractional_share_used",
                             symbol=symbol, price=ref_price, position_size=position_size_usd,
                             fractional_qty=round(fractional_qty, 4), notional=round(notional, 2))
                else:
                    # Price too high even for fractional - log and block
                    log_event("submit_entry", "price_exceeds_cap",
                             symbol=symbol, price=ref_price, position_size=position_size_usd,
                             required_notional=ref_price, max_allowed=position_size_usd)
                    # Log to dedicated Price_Exceeds_Cap log file
                    try:
                        from pathlib import Path
                        import json
                        from datetime import datetime, timezone
                        log_file = Path("logs/price_exceeds_cap.jsonl")
                        log_file.parent.mkdir(exist_ok=True)
                        log_rec = {
                            "ts": datetime.now(timezone.utc).isoformat(),
                            "symbol": symbol,
                            "price": ref_price,
                            "position_size_usd": position_size_usd,
                            "required_notional": ref_price,
                            "fractional_qty": fractional_qty,
                            "status": "blocked",
                            "reason": "Price_Exceeds_Cap"
                        }
                        with log_file.open("a") as f:
                            f.write(json.dumps(log_rec) + "\n")
                    except:
                        pass
                    return None, None, "price_exceeds_cap", 0, "Price_Exceeds_Cap"
            except Exception as e:
                # If fractional shares not supported or error, log and block
                log_event("submit_entry", "price_exceeds_cap_fallback",
                         symbol=symbol, price=ref_price, position_size=position_size_usd,
                         error=str(e))
                try:
                    from pathlib import Path
                    import json
                    from datetime import datetime, timezone
                    log_file = Path("logs/price_exceeds_cap.jsonl")
                    log_file.parent.mkdir(exist_ok=True)
                    log_rec = {
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "symbol": symbol,
                        "price": ref_price,
                        "position_size_usd": position_size_usd,
                        "error": str(e),
                        "status": "blocked",
                        "reason": "Price_Exceeds_Cap"
                    }
                    with log_file.open("a") as f:
                        f.write(json.dumps(log_rec) + "\n")
                except:
                    pass
                return None, None, "price_exceeds_cap", 0, "Price_Exceeds_Cap"
        
        # RISK MANAGEMENT: Order size validation (enhanced version of existing check)
        try:
            # V4.0: Apply API resilience with exponential backoff
            from api_resilience import ExponentialBackoff
            backoff = ExponentialBackoff(max_retries=3, base_delay=0.5, max_delay=5.0)
            
            def get_account():
                return self.api.get_account()
            
            acct = backoff(get_account)()
            # BULLETPROOF: Safe attribute access with defaults
            dtbp = float(getattr(acct, "daytrading_buying_power", 0.0))
            bp = float(getattr(acct, "buying_power", 0.0))
            
            # BULLETPROOF: Validate buying power is positive
            if bp <= 0:
                log_event("submit_entry", "invalid_buying_power", symbol=symbol, bp=bp, dtbp=dtbp)
                # Fail open - allow trade to proceed if can't validate (will fail at broker if truly insufficient)
                bp = 1000000.0  # Large default to not block trade
            
            required_margin = notional * 1.5 if side == "sell" else notional
            # Use regular buying_power for paper trading (dtbp is unreliable in paper accounts)
            available_bp = bp
            
            # Enhanced validation using risk management module
            try:
                from risk_management import validate_order_size
                order_valid, order_error = validate_order_size(symbol, qty, side, ref_price, available_bp)
                if not order_valid:
                    log_event("submit_entry", "risk_validation_blocked",
                             symbol=symbol, side=side, qty=qty, notional=notional,
                             error=order_error)
                    return None, None, "risk_validation_failed", 0, order_error
            except ImportError:
                # Risk management not available - use existing check
                pass
            
            # Existing buying power check (keep for backward compatibility)
            if required_margin > available_bp:
                log_event("submit_entry", "insufficient_buying_power",
                         symbol=symbol, side=side, qty=qty, notional=notional,
                         required_margin=round(required_margin, 2),
                         available_dtbp=round(dtbp, 2),
                         available_bp=round(bp, 2))
                return None, None, "insufficient_buying_power", 0, "insufficient_buying_power"
        except Exception as e:
            log_event("submit_entry", "margin_check_failed", symbol=symbol, error=str(e))
        
        # === REGIME-AWARE EXECUTION (Audit Recommendation) ===
        execution_urgency = Config.REGIME_EXECUTION_MAP.get(regime, "NEUTRAL")
        original_mode = Config.ENTRY_MODE
        
        if execution_urgency == "AGGRESSIVE":
            # Cross the spread immediately for volatile conditions
            Config.ENTRY_MODE = "MARKET_FALLBACK"
            log_event("submit_entry", "regime_aggressive_mode", 
                     symbol=symbol, regime=regime, urgency=execution_urgency)
        elif execution_urgency == "PASSIVE":
            # Join NBBO to capture spread in calm conditions
            Config.ENTRY_MODE = "MAKER_BIAS"
            log_event("submit_entry", "regime_passive_mode",
                     symbol=symbol, regime=regime, urgency=execution_urgency)
        # else: NEUTRAL uses default Config.ENTRY_MODE
        
        limit_price = self.compute_entry_price(symbol, side)

        # AUDIT_MODE: Safety check - no live orders in audit mode
        audit_mode = os.getenv("AUDIT_MODE", "").strip().lower() in ("1", "true", "yes")
        if audit_mode:
            assert os.getenv("AUDIT_DRY_RUN", "").strip().lower() in ("1", "true", "yes"), "AUDIT_MODE requires AUDIT_DRY_RUN=1"
            try:
                log_system_event("audit", "audit_mode_enabled", "INFO", details={"symbol": symbol, "side": side, "qty": qty})
            except Exception:
                pass

        # AUDIT_DRY_RUN: Check early and return mock if enabled
        # This check is redundant with _submit_order_guarded, but provides early exit
        # and explicit logging for audit verification
        if self._audit_guard and self._should_use_dry_run():
            import uuid
            fake_id = f"AUDIT-DRYRUN-{uuid.uuid4().hex[:12]}"
            try:
                log_order({
                    "action": "audit_dry_run",
                    "symbol": symbol,
                    "side": side,
                    "qty": qty,
                    "limit_price": limit_price or ref_price,
                    "order_id": fake_id,
                    "dry_run": True,
                    "entry_score": entry_score,
                    "market_regime": effective_regime,
                })
                # Log explicit audit check
                try:
                    from src.audit_guard import is_audit_mode
                    log_system_event("audit", "audit_dry_run_check", "INFO", details={
                        "audit_mode": is_audit_mode(),
                        "audit_dry_run": self._is_audit_dry_run(),
                        "branch_taken": "mock_return",
                        "symbol": symbol,
                        "caller": "submit_entry:early_check",
                    })
                except Exception:
                    pass
            except Exception as e:
                log_event("submit_entry", "audit_dry_run_log_failed", symbol=symbol, error=str(e))
            _mock = self._create_mock_order(fake_id, symbol, qty, side, "limit", limit_price or ref_price) if self._create_mock_order else type("_MockOrder", (), {"id": fake_id})()
            return _mock, ref_price, "limit", qty, "dry_run"

        # Paper-only A/B execution promo (PASSIVE_THEN_CROSS vs baseline); gated by env + universe. Never arms for live.
        try:
            from src.paper.paper_exec_mode_runtime import try_paper_exec_ab_entry

            _pe_res = try_paper_exec_ab_entry(
                self,
                symbol,
                qty,
                side,
                ref_price,
                client_order_id_base=client_order_id_base,
                entry_score=entry_score,
                effective_regime=effective_regime,
            )
            if _pe_res is not None:
                return _pe_res
        except Exception as _pe_ex:
            try:
                log_event("paper_exec_promo", "hook_error", symbol=symbol, error=str(_pe_ex)[:300])
            except Exception:
                pass

        if limit_price is not None and Config.ENTRY_POST_ONLY:
            for attempt in range(1, Config.ENTRY_MAX_RETRIES + 1):
                try:
                    # Use idempotency key from risk management if available
                    if client_order_id_base and len(client_order_id_base) > 0:
                        client_order_id = f"{client_order_id_base}-lpo-a{attempt}"
                    else:
                        # Fallback: generate new idempotency key
                        try:
                            from risk_management import generate_idempotency_key
                            client_order_id = generate_idempotency_key(symbol, side, qty)
                        except ImportError:
                            client_order_id = None
                    
                    # V4.0: Apply API resilience with exponential backoff
                    # CRITICAL FIX: Generate unique client_order_id for each backoff retry
                    from api_resilience import ExponentialBackoff
                    backoff = ExponentialBackoff(max_retries=3, base_delay=0.5, max_delay=10.0)
                    
                    backoff_attempt = [0]  # Counter for backoff retries
                    def submit_order():
                        backoff_attempt[0] += 1
                        # Generate unique client_order_id for each backoff retry to avoid "must be unique" error
                        if backoff_attempt[0] > 1:
                            unique_client_order_id = f"{client_order_id}-retry{backoff_attempt[0]}"
                        else:
                            unique_client_order_id = client_order_id
                        return self._submit_order_guarded(
                            symbol=symbol,
                            qty=qty,
                            side=side,
                            order_type="limit",
                            time_in_force="day",
                            limit_price=limit_price,
                            client_order_id=unique_client_order_id,
                            caller="submit_entry:backoff_retry",
                            extended_hours=False
                        )
                    
                    o = backoff(submit_order)()
                    order_id = getattr(o, "id", None)
                    # CRITICAL: Log if order was submitted but has no ID (API rejection)
                    if not order_id and o is not None:
                        try:
                            from pathlib import Path
                            import json
                            log_file = Path("logs/critical_api_failure.log")
                            log_file.parent.mkdir(exist_ok=True)
                            error_details = {
                                "symbol": symbol,
                                "qty": qty,
                                "side": side,
                                "limit_price": limit_price,
                                "client_order_id": client_order_id,
                                "order_object_type": type(o).__name__,
                                "order_object_str": str(o),
                                "order_object_dict": o.__dict__ if hasattr(o, '__dict__') else None,
                                "error": "submit_order_returned_no_id"
                            }
                            with log_file.open("a") as lf:
                                lf.write(f"{datetime.now(timezone.utc).isoformat()} | submit_order_no_id | {json.dumps(error_details, default=str)}\\n")
                            log_event("critical_api_failure", "submit_order_no_id", **error_details)
                        except Exception:
                            pass  # Don't fail on logging error
                    if order_id:
                        filled, filled_qty, filled_price = self.check_order_filled(order_id)
                        if filled and filled_qty > 0:
                            # If partial fill, cancel remainder and proceed with filled_qty only.
                            if filled_qty < qty:
                                try:
                                    self.api.cancel_order(order_id)
                                except Exception:
                                    pass
                            log_order({"action": "submit_limit_filled", "symbol": symbol, "side": side,
                                       "limit_price": limit_price, "filled_price": filled_price, "attempt": attempt})
                            telemetry.log_order_event(
                                event_type="LIMIT_FILLED",
                                symbol=symbol,
                                side=side,
                                qty=filled_qty,
                                order_type="limit",
                                limit_price=limit_price,
                                fill_price=filled_price,
                                slippage_bps=abs(filled_price - limit_price) / limit_price * 10000 if limit_price > 0 else 0,
                                attempt=attempt,
                                status="filled"
                            )
                            return o, filled_price, "limit", filled_qty, "filled"
                        try:
                            self.api.cancel_order(order_id)
                        except Exception:
                            pass
                    log_order({"action": "limit_not_filled", "symbol": symbol, "side": side,
                               "limit_price": limit_price, "attempt": attempt})
                except Exception as e:
                    # CRITICAL: Log RAW API error response for forensic analysis
                    error_details = {
                        "symbol": symbol,
                        "qty": qty,
                        "side": side,
                        "limit_price": limit_price,
                        "client_order_id": client_order_id if 'client_order_id' in locals() else None,
                        "attempt": attempt,
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "error_args": e.args if hasattr(e, 'args') else None
                    }
                    # Capture HTTP error details if available
                    if hasattr(e, 'status_code'):
                        error_details["status_code"] = e.status_code
                    if hasattr(e, 'response'):
                        try:
                            error_details["response_body"] = e.response.text if hasattr(e.response, 'text') else str(e.response)
                            if hasattr(e.response, 'json'):
                                try:
                                    error_details["response_json"] = e.response.json()
                                except:
                                    error_details["response_json"] = None
                        except:
                            pass
                    # Log to dedicated critical API failure log
                    try:
                        from pathlib import Path
                        log_file = Path("logs/critical_api_failure.log")
                        log_file.parent.mkdir(exist_ok=True)
                        import json
                        with log_file.open("a") as lf:
                            lf.write(f"{datetime.now(timezone.utc).isoformat()} | limit_retry_failed | {json.dumps(error_details, default=str)}\\n")
                    except Exception as log_err:
                        pass  # Don't fail on logging error
                    
                    log_event("critical_api_failure", "limit_retry_failed", **error_details)
                    log_order({"action": "limit_retry_failed", "symbol": symbol, "side": side,
                               "limit_price": limit_price, "attempt": attempt, "error": str(e), "error_details": error_details})
                    
                    # Idempotency: if the client_order_id already exists, fetch the existing order.
                    if client_order_id_base:
                        try:
                            existing = self._get_order_by_client_order_id(f"{client_order_id_base}-lpo-a{attempt}")
                            if existing is not None:
                                existing_id = getattr(existing, "id", None)
                                if existing_id:
                                    filled, filled_qty, filled_price = self.check_order_filled(existing_id)
                                    if filled and filled_qty > 0:
                                        return existing, filled_price, "limit", filled_qty, "filled"
                        except Exception:
                            pass
                    # Track execution failure for learning
                    try:
                        from tca_data_manager import track_execution_failure
                        track_execution_failure(symbol, "limit_retry_failed", {"attempt": attempt, "error": str(e)})
                    except ImportError:
                        pass
                
                if attempt < Config.ENTRY_MAX_RETRIES:
                    time.sleep(Config.ENTRY_RETRY_SLEEP_SEC)
                    bid, ask = self.get_nbbo(symbol)
                    if bid > 0 and ask > 0:
                        mid = (bid + ask) / 2.0
                        tol = mid * (Config.ENTRY_TOLERANCE_BPS / 10000.0)
                        if side == "buy":
                            # Use normalized 2-decimal limit prices to eliminate sub-penny leakage
                            # WHY: Audit found retry logic still produced 4-decimal prices.
                            # HOW TO VERIFY: logs/orders.jsonl shows zero 'sub-penny increment' errors.
                            raw_price = min(ask - tol, max(bid, limit_price + tol))
                            limit_price = normalize_equity_limit_price(raw_price)
                        else:
                            # Use normalized 2-decimal limit prices to eliminate sub-penny leakage
                            # WHY: Audit found retry logic still produced 4-decimal prices.
                            # HOW TO VERIFY: logs/orders.jsonl shows zero 'sub-penny increment' errors.
                            raw_price = min(ask, max(bid + tol, limit_price - tol))
                            limit_price = normalize_equity_limit_price(raw_price)

        if limit_price is not None:
            try:
                # Use idempotency key from risk management if available
                if client_order_id_base and len(client_order_id_base) > 0:
                    client_order_id = f"{client_order_id_base}-lpfinal"
                else:
                    # Fallback: generate new idempotency key
                    try:
                        from risk_management import generate_idempotency_key
                        client_order_id = generate_idempotency_key(symbol, side, qty)
                    except ImportError:
                        client_order_id = None
                
                o = self._submit_order_guarded(
                    symbol=symbol,
                    qty=qty,
                    side=side,
                    order_type="limit",
                    time_in_force="day",
                    limit_price=limit_price,
                    client_order_id=client_order_id,
                    caller="submit_entry:limit_fallback",
                    extended_hours=False
                )
                order_id = getattr(o, "id", None)
                # CRITICAL: Log if order was submitted but has no ID (API rejection)
                if not order_id and o is not None:
                    try:
                        from pathlib import Path
                        import json
                        log_file = Path("logs/critical_api_failure.log")
                        log_file.parent.mkdir(exist_ok=True)
                        error_details = {
                            "symbol": symbol,
                            "qty": qty,
                            "side": side,
                            "limit_price": limit_price,
                            "client_order_id": client_order_id if 'client_order_id' in locals() else None,
                            "order_object_type": type(o).__name__,
                            "order_object_str": str(o),
                            "order_object_dict": o.__dict__ if hasattr(o, '__dict__') else None,
                            "error": "submit_order_returned_no_id"
                        }
                        with log_file.open("a") as lf:
                            lf.write(f"{datetime.now(timezone.utc).isoformat()} | submit_order_final_no_id | {json.dumps(error_details, default=str)}\\n")
                        log_event("critical_api_failure", "submit_order_final_no_id", **error_details)
                    except Exception:
                        pass  # Don't fail on logging error
                if order_id:
                    filled, filled_qty, filled_price = self.check_order_filled(order_id)
                    if filled and filled_qty > 0:
                        if filled_qty < qty:
                            try:
                                self.api.cancel_order(order_id)
                            except Exception:
                                pass
                        log_order({"action": "submit_limit_final_filled", "symbol": symbol, "side": side,
                                   "limit_price": limit_price, "filled_price": filled_price})
                        telemetry.log_order_event(
                            event_type="LIMIT_FINAL_FILLED",
                            symbol=symbol,
                            side=side,
                            qty=filled_qty,
                            order_type="limit",
                            limit_price=limit_price,
                            fill_price=filled_price,
                            slippage_bps=abs(filled_price - limit_price) / limit_price * 10000 if limit_price > 0 else 0,
                            attempt="final",
                            status="filled"
                        )
                        return o, filled_price, "limit", filled_qty, "filled"
                    try:
                        self.api.cancel_order(order_id)
                    except Exception:
                        pass
                log_order({"action": "limit_final_not_filled", "symbol": symbol, "side": side,
                           "limit_price": limit_price})
            except Exception as e:
                # CRITICAL: Log RAW API error response for forensic analysis
                error_details = {
                    "symbol": symbol,
                    "qty": qty,
                    "side": side,
                    "limit_price": limit_price,
                    "client_order_id": client_order_id if 'client_order_id' in locals() else None,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "error_args": e.args if hasattr(e, 'args') else None
                }
                # Capture HTTP error details if available
                if hasattr(e, 'status_code'):
                    error_details["status_code"] = e.status_code
                if hasattr(e, 'response'):
                    try:
                        error_details["response_body"] = e.response.text if hasattr(e.response, 'text') else str(e.response)
                        if hasattr(e.response, 'json'):
                            try:
                                error_details["response_json"] = e.response.json()
                            except:
                                error_details["response_json"] = None
                    except:
                        pass
                # Log to dedicated critical API failure log
                try:
                    from pathlib import Path
                    log_file = Path("logs/critical_api_failure.log")
                    log_file.parent.mkdir(exist_ok=True)
                    import json
                    with log_file.open("a") as lf:
                        lf.write(f"{datetime.now(timezone.utc).isoformat()} | limit_final_failed | {json.dumps(error_details, default=str)}\\n")
                except Exception as log_err:
                    pass  # Don't fail on logging error
                
                log_event("critical_api_failure", "limit_final_failed", **error_details)
                
                if client_order_id_base:
                    try:
                        existing = self._get_order_by_client_order_id(f"{client_order_id_base}-lpfinal")
                        if existing is not None:
                            existing_id = getattr(existing, "id", None)
                            if existing_id:
                                filled, filled_qty, filled_price = self.check_order_filled(existing_id)
                                if filled and filled_qty > 0:
                                    return existing, filled_price, "limit", filled_qty, "filled"
                    except Exception:
                        pass
                log_order({"action": "limit_final_failed", "symbol": symbol, "side": side,
                           "limit_price": limit_price, "error": str(e), "error_details": error_details})
                # Track execution failure for learning
                try:
                    from tca_data_manager import track_execution_failure
                    track_execution_failure(symbol, "limit_final_failed", {"error": str(e)})
                except ImportError:
                    pass

        try:
            # Use idempotency key from risk management if available
            if client_order_id_base and len(client_order_id_base) > 0:
                client_order_id = f"{client_order_id_base}-mkt"
            else:
                # Fallback: generate new idempotency key
                try:
                    from risk_management import generate_idempotency_key
                    client_order_id = generate_idempotency_key(symbol, side, qty)
                except ImportError:
                    client_order_id = None
            
            # V4.0: Apply API resilience with exponential backoff
            # CRITICAL FIX: Generate unique client_order_id for each backoff retry
            from api_resilience import ExponentialBackoff
            backoff = ExponentialBackoff(max_retries=3, base_delay=0.5, max_delay=10.0)
            
            backoff_attempt = [0]  # Counter for backoff retries
            def submit_market_order():
                backoff_attempt[0] += 1
                # Generate unique client_order_id for each backoff retry to avoid "must be unique" error
                if backoff_attempt[0] > 1:
                    unique_client_order_id = f"{client_order_id}-retry{backoff_attempt[0]}" if client_order_id else None
                else:
                    unique_client_order_id = client_order_id
                return self._submit_order_guarded(
                    symbol=symbol,
                    qty=qty,
                    side=side,
                    order_type="market",
                    time_in_force="day",
                    client_order_id=unique_client_order_id,
                    caller="submit_entry:market_backoff_retry",
                    extended_hours=False
                )
            
            o = backoff(submit_market_order)()
            log_order({"action": "submit_market_fallback", "symbol": symbol, "side": side})
            order_id = getattr(o, "id", None)
            # CRITICAL: Log if order was submitted but has no ID (API rejection)
            if not order_id and o is not None:
                try:
                    from pathlib import Path
                    import json
                    log_file = Path("logs/critical_api_failure.log")
                    log_file.parent.mkdir(exist_ok=True)
                    error_details = {
                        "symbol": symbol,
                        "qty": qty,
                        "side": side,
                        "client_order_id": client_order_id if 'client_order_id' in locals() else None,
                        "order_object_type": type(o).__name__,
                        "order_object_str": str(o),
                        "order_object_dict": o.__dict__ if hasattr(o, '__dict__') else None,
                        "error": "submit_order_market_returned_no_id"
                    }
                    with log_file.open("a") as lf:
                        lf.write(f"{datetime.now(timezone.utc).isoformat()} | submit_order_market_no_id | {json.dumps(error_details, default=str)}\\n")
                    log_event("critical_api_failure", "submit_order_market_no_id", **error_details)
                except Exception:
                    pass  # Don't fail on logging error
            if order_id:
                filled, filled_qty, filled_price = self.check_order_filled(order_id, max_wait_sec=1.0)
                if filled and filled_qty > 0:
                    telemetry.log_order_event(
                        event_type="MARKET_FILLED",
                        symbol=symbol,
                        side=side,
                        qty=filled_qty,
                        order_type="market",
                        limit_price=None,
                        fill_price=filled_price,
                        slippage_bps=0,
                        attempt="market_fallback",
                        status="filled"
                    )
                    return o, filled_price, "market", filled_qty, "filled"
            # Live-safety: if not confirmed filled, do NOT mark position open. Reconciliation will pick it up.
            return o, None, "market", 0, "submitted_unfilled"
        except Exception as e:
            if client_order_id_base:
                try:
                    existing = self._get_order_by_client_order_id(f"{client_order_id_base}-mkt")
                    if existing is not None:
                        existing_id = getattr(existing, "id", None)
                        if existing_id:
                            filled, filled_qty, filled_price = self.check_order_filled(existing_id, max_wait_sec=1.0)
                            if filled and filled_qty > 0:
                                return existing, filled_price, "market", filled_qty, "filled"
                except Exception:
                    pass
            # CRITICAL: Log RAW API error response for forensic analysis
            error_details = {
                "symbol": symbol,
                "qty": qty,
                "side": side,
                "client_order_id": client_order_id if 'client_order_id' in locals() else None,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "error_args": e.args if hasattr(e, 'args') else None
            }
            # Capture HTTP error details if available
            if hasattr(e, 'status_code'):
                error_details["status_code"] = e.status_code
            if hasattr(e, 'response'):
                try:
                    error_details["response_body"] = e.response.text if hasattr(e.response, 'text') else str(e.response)
                    if hasattr(e.response, 'json'):
                        try:
                            error_details["response_json"] = e.response.json()
                        except:
                            error_details["response_json"] = None
                except:
                    pass
            # Log to dedicated critical API failure log
            try:
                from pathlib import Path
                log_file = Path("logs/critical_api_failure.log")
                log_file.parent.mkdir(exist_ok=True)
                import json
                with log_file.open("a") as lf:
                    lf.write(f"{datetime.now(timezone.utc).isoformat()} | market_fail | {json.dumps(error_details, default=str)}\\n")
            except Exception as log_err:
                pass  # Don't fail on logging error
            
            log_event("critical_api_failure", "market_fail", **error_details)
            log_order({"action": "market_fail", "symbol": symbol, "side": side, "error": str(e), "error_details": error_details})
            # Track execution failure for learning
            try:
                from tca_data_manager import track_execution_failure
                track_execution_failure(symbol, "market_fail", {"error": str(e)})
            except ImportError:
                pass
            return None, None, "error", 0, str(e)
```

## run_once_head

```python
def run_once():
    # CRITICAL FIX: Log entry to run_once()
    try:
        with open("logs/worker_debug.log", "a") as f:
            f.write(f"[{datetime.now(timezone.utc).isoformat()}] run_once() ENTRY\n")
            f.flush()
    except:
        pass
    print("DEBUG: run_once() ENTRY", flush=True)
    _pipeline_heartbeat_maybe()

    # Hard safety gate: v2-only engine is paper-only.
    enforce_paper_only_or_die()
    
    # CRITICAL FIX: Ensure StateFiles is available - re-import if needed
    global StateFiles
    try:
        _ = StateFiles  # Check if available
    except NameError:
        # StateFiles not available - re-import it
        from config.registry import StateFiles
        print("DEBUG: Re-imported StateFiles in run_once()", flush=True)
        try:
            with open("logs/worker_debug.log", "a") as f:
                f.write(f"[{datetime.now(timezone.utc).isoformat()}] Re-imported StateFiles in run_once()\n")
                f.flush()
        except:
            pass
    
    # Update logic heartbeat for SRE monitoring
    try:
        from sre_diagnostics import update_sre_metrics
        update_sre_metrics({"logic_heartbeat": time.time()})
    except:
        pass
    
    # StateFiles is already imported at module level (line 30-32)
    # No redundant import needed
    try:
        # CRITICAL FIX: Log after try block entry
        try:
            with open("logs/worker_debug.log", "a") as f:
                f.write(f"[{datetime.now(timezone.utc).isoformat()}] run_once() inside try block\n")
                f.flush()
        except:
            pass
        
        global ZERO_ORDER_CYCLE_COUNT
        alerts_this_cycle = []
        fixes_applied_list = []  # V3.0: Track auto-fixes
        
        audit_seg("run_once", "START")
        
        # MONITORING GUARD 1: Check freeze state (governor_freezes.json only, no pre_market_freeze.flag)
        # NOTE: pre_market_freeze.flag mechanism removed - it was causing more problems than it solved
        if not check_freeze_state():
            alerts_this_cycle.append("freeze_active")
            print("🛑 FREEZE ACTIVE - Trading halted by monitoring guard", flush=True)
            log_event("run", "halted_freeze", alerts=alerts_this_cycle)
            
            # Still track zero-order cycles and generate monitoring summary on freeze path
            ZERO_ORDER_CYCLE_COUNT += 1
            
            # Check rollback conditions even when frozen
            check_rollback_conditions(
                composite_scores_avg=0.0,
                zero_order_cycles=ZERO_ORDER_CYCLE_COUNT,
                freeze_active=True,
                heartbeat_stale=False,
                trading_mode=Config.TRADING_MODE
            )
            
            # Generate monitoring summary for freeze cycle
            summary = generate_cycle_monitoring_summary(
                clusters=[],
                orders_placed=0,
                positions_count=0,
                alerts_triggered=alerts_this_cycle,
                zero_order_cycles=ZERO_ORDER_CYCLE_COUNT,
                fixes_applied=[],
                optimizations_applied=[]
            )
            
            # HALT: Return early - trading will NOT resume until freeze flags manually cleared
            # CRITICAL FIX: Log cycle even when frozen
            jsonl_write("run", {
                "ts": datetime.now(timezone.utc).isoformat(),
                "_ts": int(time.time()),
                "msg": "complete",
                "clusters": 0,
                "orders": 0,
                "freeze_active": True,
                "metrics": summary
            })
            return {"clusters": 0, "orders": 0, **summary}
        
        # CRITICAL FIX: Log before creating UWClient and engine
        try:
            with open("logs/worker_debug.log", "a") as f:
                f.write(f"[{datetime.now(timezone.utc).isoformat()}] run_once() creating UWClient and engine\n")
                f.flush()
        except:
            pass
        
        uw = UWClient()
        engine = StrategyEngine()
        degraded_mode = False  # Reduce-only when broker is unreachable

        # STRUCTURAL UPGRADE (additive): Market context snapshot (premarket/overnight + vol term proxy).
        # Contract:
        # - Must never block trading (best-effort, wrapped, logs to system_events).
        # - Provides inputs for regime/posture and shadow A/B (does not change decisions by itself).
        try:
            if hasattr(engine, "executor") and hasattr(engine.executor, "api") and engine.executor.api is not None:
                from structural_intelligence.market_context_v2 import update_market_context_v2
                mc = update_market_context_v2(engine.executor.api)
                try:
                    engine.market_context_v2 = mc  # type: ignore[attr-defined]
                except Exception:
                    pass
        except Exception:
            # Never block trading on context ingest errors.
            pass

        # STRUCTURAL UPGRADE (additive): Per-symbol vol/beta features store.
        # Contract: log-only enrichment fields; no scoring weight changes here.
        try:
            if hasattr(engine, "executor") and hasattr(engine.executor, "api") and engine.executor.api is not None:
                from structural_intelligence.symbol_risk_features import update_symbol_risk_features
                try:
                    symbols = list(getattr(Config, "TICKERS", []) or [])
                except Exception:
                    symbols = []
                if "SPY" not in [str(s).upper() for s in symbols]:
                    symbols.append("SPY")
                rf = update_symbol_risk_features(engine.executor.api, symbols=symbols, benchmark="SPY")
                try:
                    engine.symbol_risk_features = rf  # type: ignore[attr-defined]
                except Exception:
                    pass
        except Exception:
            pass

        # STRUCTURAL UPGRADE (additive): Regime + posture V2 (log-only; no gating changes).
        try:
            if hasattr(engine, "executor") and hasattr(engine.executor, "api") and engine.executor.api is not None:
                from structural_intelligence.regime_posture_v2 import update_regime_posture_v2
                mc = getattr(engine, "market_context_v2", None)
                if not isinstance(mc, dict):
                    mc = {}
                rp = update_regime_posture_v2(engine.executor.api, market_context=mc)
                try:
                    engine.regime_posture_v2 = rp  # type: ignore[attr-defined]
                except Exception:
                    pass
        except Exception:
            pass

        all_trades = []
        gex_map = {}
        dp_map = {}
        vol_map = {}
        net_map = {}
        ovl_map = {}
        
        audit_seg("run_once", "cache_read")
        uw_cache = read_uw_cache()
        uw_cache_path = str(CacheFiles.UW_FLOW_CACHE)
        
        # SIGNAL FUNNEL TRACKER: Count incoming UW alerts (symbols in cache = alerts received)
        try:
            from signal_funnel_tracker import get_funnel_tracker
            funnel = get_funnel_tracker()
            # Count each symbol in cache as an incoming UW alert
            cache_symbols = [k for k in uw_cache.keys() if not k.startswith("_")]
            for symbol in cache_symbols:
                cache_data = uw_cache.get(symbol, {})
                # Count alerts based on cache updates (each symbol with data = alert)
                if cache_data and not cache_data.get("simulated"):
                    funnel.record_uw_alert(symbol, "cache_update")
        except ImportError:
            pass
        except Exception as e:
            log_event("funnel", "record_alerts_error", error=str(e))
        
        adaptive_gate = AdaptiveGate()
        # ROOT CAUSE FIX: Check for actual symbol keys (not metadata keys starting with "_")
        # Only enable composite scoring if cache has real symbol data, not just metadata
        cache_symbol_count = len([k for k in uw_cache.keys() if not k.startswith("_")])
        use_composite = cache_symbol_count > 0

        # VISIBILITY: If UW cache has no symbols, make it explicit (reason for 0 clusters).
        # This should not crash or freeze trading; it only improves observability.
        if cache_symbol_count == 0:
            log_event(
                "uw_cache",
                "uw_cache_empty_no_signals",
                cache_symbol_count=cache_symbol_count,
                uw_cache_path=uw_cache_path,
                cache_total_keys=len(uw_cache) if isinstance(uw_cache, dict) else None,
            )
        
        log_event("run_once", "started", use_composite=use_composite, cache_symbols=cache_symbol_count, cache_total_keys=len(uw_cache))
        audit_seg("run_once", "init_complete", {"cache_symbols": cache_symbol_count, "cache_total_keys": len(uw_cache)})
        
        # POSITION RECONCILIATION LOOP V2: Autonomous self-healing sync
        print("DEBUG: Running autonomous position reconciliation V2...", flush=True)
        try:
```

## run_once_decide_exits

```python
        
        print(f"DEBUG: About to call decide_and_execute with {len(clusters)} clusters, regime={market_regime}", flush=True)
        if len(clusters) == 0:
            print("⚠️  WARNING: No clusters to execute - check composite scoring logs above", flush=True)
            log_event("execution", "no_clusters", cache_symbols=len(uw_cache) if use_composite else 0)
        audit_seg("run_once", "before_decide_execute", {"cluster_count": len(clusters)})
        # Live-safety gates before placing NEW entries:
        # - Broker degraded => reduce-only
        # - Not armed / endpoint mismatch => skip entries
        # - Executor not reconciled => skip entries (until it can sync positions cleanly)
        armed = trading_is_armed()
        reconciled_ok = False
        try:
            reconciled_ok = bool(engine.executor.ensure_reconciled())
        except Exception:
            reconciled_ok = False

        if degraded_mode:
            # Reduce-only safety: do not open new positions when broker connectivity is degraded.
            # Still allow exit logic and monitoring to run.
            log_event("run_once", "reduce_only_broker_degraded", action="skip_entries")
            orders = []
        elif not armed:
            log_event("run_once", "not_armed_skip_entries",
                      trading_mode=Config.TRADING_MODE, base_url=Config.ALPACA_BASE_URL)
            orders = []
        elif not reconciled_ok:
            log_event("run_once", "not_reconciled_skip_entries", action="skip_entries")
            orders = []
        else:
            if Config.ENABLE_PER_TICKER_LEARNING:
                decisions_map = build_symbol_decisions(clusters, gex_map, dp_map, net_map, vol_map, ovl_map)
                _pipeline_touch("decision")
                orders = engine.decide_and_execute(clusters, confirm_map, gex_map, decisions_map, market_regime)
            else:
                _pipeline_touch("decision")
                orders = engine.decide_and_execute(clusters, confirm_map, gex_map, None, market_regime)
        print(f"DEBUG: decide_and_execute returned {len(orders)} orders", flush=True)
        audit_seg("run_once", "after_decide_execute", {"order_count": len(orders)})
        
        # CRITICAL FIX: Log to file BEFORE self-healing code
        try:
            with open("logs/worker_debug.log", "a") as f:
                f.write(f"[{datetime.now(timezone.utc).isoformat()}] decide_and_execute returned {len(orders)} orders\n")
                f.flush()
        except:
            pass
        
        # SELF-HEALING: Clear freeze flag and reset fail counter on successful cycle
        if watchdog and hasattr(watchdog, 'state'):
            if watchdog.state.fail_count > 0:
                watchdog.state.fail_count = 0
                log_event("self_healing", "fail_counter_reset", reason="successful_cycle")
            # Clear freeze flag if it exists (was set due to previous failures)
            freeze_path = StateFiles.PRE_MARKET_FREEZE
            if freeze_path.exists():
                try:
                    freeze_path.unlink()
                    log_event("self_healing", "freeze_flag_cleared", reason="successful_cycle")
                    print("✅ SELF-HEALING: Cleared freeze flag after successful cycle", flush=True)
                except Exception as e:
                    log_event("self_healing", "freeze_clear_failed", error=str(e))
        
        # CRITICAL FIX: Log to file BEFORE calling evaluate_exits
        try:
            with open("logs/worker_debug.log", "a") as f:
                f.write(f"[{datetime.now(timezone.utc).isoformat()}] About to call evaluate_exits() - orders={len(orders)}\n")
                f.flush()
        except:
            pass
        
        print("DEBUG: Calling evaluate_exits", flush=True)
        
        # CRITICAL FIX: Log exit evaluation to file
        try:
            with open("logs/worker_debug.log", "a") as f:
                f.write(f"[{datetime.now(timezone.utc).isoformat()}] Calling evaluate_exits()\n")
                f.flush()
        except:
            pass
        
        # CRITICAL FIX: Ensure evaluate_exits is ALWAYS called, even if there's an exception
        try:
            # CRITICAL: Force evaluate_exits to run - this MUST happen
            print(f"DEBUG: FORCING evaluate_exits() call - engine.executor exists: {hasattr(engine, 'executor')}", flush=True)
            if hasattr(engine, 'executor') and hasattr(engine.executor, 'evaluate_exits'):
                engine.executor.evaluate_exits()
                print("DEBUG: evaluate_exits() completed", flush=True)
                try:
                    with open("logs/worker_debug.log", "a") as f:
                        f.write(f"[{datetime.now(timezone.utc).isoformat()}] evaluate_exits() completed\n")
                        f.flush()
                except:
                    pass
            else:
                print("ERROR: engine.executor.evaluate_exits() not available!", flush=True)
                try:
                    with open("logs/worker_debug.log", "a") as f:
                        f.write(f"[{datetime.now(timezone.utc).isoformat()}] ERROR: evaluate_exits() not available!\n")
                        f.flush()
                except:
                    pass
        except Exception as exit_err:
            print(f"ERROR: evaluate_exits() raised exception: {exit_err}", flush=True)
            traceback.print_exc()
            log_event("exit", "evaluate_exits_exception", error=str(exit_err))
            try:
                with open("logs/worker_debug.log", "a") as f:
                    f.write(f"[{datetime.now(timezone.utc).isoformat()}] ERROR: evaluate_exits() exception: {exit_err}\n")
                    f.flush()
            except:
                pass
        
        # CRITICAL FIX: Log after evaluate_exits
        try:
            with open("logs/worker_debug.log", "a") as f:
                f.write(f"[{datetime.now(timezone.utc).isoformat()}] evaluate_exits() completed\n")
                f.flush()
        except:
            pass
        
        audit_seg("run_once", "after_exits")
```

## run_all_strategies

```python
def run_all_strategies():
    """
    Run enabled strategies from config/strategies.yaml (equity cohort only).
    Returns combined metrics for run.jsonl.
    """
    strategies_cfg = {}
    try:
        path = Path("config") / "strategies.yaml"
        if path.exists():
            import yaml
            with path.open() as f:
                strategies_cfg = yaml.safe_load(f) or {}
    except Exception as e:
        log_event("strategies", "config_load_failed", error=str(e))
    strat = strategies_cfg.get("strategies", {})
    equity_cfg = strat.get("equity", {})
    equity_enabled = equity_cfg.get("enabled", True)
    total_orders = 0
    combined_metrics = {"clusters": 0, "orders": 0, "equity_orders": 0}
    try:
        from strategies.context import strategy_context
    except ImportError:
        strategy_context = None
    if equity_enabled:
        try:
            if strategy_context:
                with strategy_context("equity"):
                    metrics = run_once()
            else:
                metrics = run_once()
            if isinstance(metrics, dict):
                total_orders += metrics.get("orders", 0)
                combined_metrics["equity_orders"] = metrics.get("orders", 0)
                combined_metrics["clusters"] = metrics.get("clusters", 0)
                combined_metrics.update(metrics)
        except Exception as e:
            log_event("strategies", "equity_run_failed", error=str(e))
    combined_metrics["orders"] = total_orders
    return combined_metrics
```

## watchdog_worker

```python
                
                if market_open:
                    print(f"DEBUG: Market is OPEN - calling run_once()", flush=True)
                    log_event("worker", "calling_run_once", iter=self.state.iter_count + 1)
                    
                    # CRITICAL FIX: Write before calling run_once
                    try:
                        with open("logs/worker_debug.log", "a") as f:
                            f.write(f"[{datetime.now(timezone.utc).isoformat()}] About to call run_once()\n")
                            f.flush()
                    except:
                        pass
                    
                    # CRITICAL FIX: Create engine BEFORE run_once() so we can call evaluate_exits() even if run_once() hangs
                    worker_engine = None
                    try:
                        worker_engine = StrategyEngine()
                        try:
                            with open("logs/worker_debug.log", "a") as f:
                                f.write(f"[{datetime.now(timezone.utc).isoformat()}] Created worker_engine for evaluate_exits()\n")
                                f.flush()
                        except:
                            pass
                    except Exception as engine_err:
                        print(f"ERROR: Failed to create worker_engine: {engine_err}", flush=True)
                    
                    try:
                        # CRITICAL FIX: Add timeout protection and ensure evaluate_exits is ALWAYS called
                        print("DEBUG: About to call run_once() - entering try block", flush=True)
                        try:
                            with open("logs/worker_debug.log", "a") as f:
                                f.write(f"[{datetime.now(timezone.utc).isoformat()}] Entering run_once() try block\n")
                                f.flush()
                        except:
                            pass
                        
                        metrics = run_all_strategies()
                        if not isinstance(metrics, dict):
                            metrics = {"clusters": 0, "orders": 0, "engine_status": "degraded", "errors_this_cycle": ["run_once_returned_non_dict"]}
                        # Ensure a consistent health signal for downstream monitoring.
                        metrics.setdefault("engine_status", "ok")
                        metrics.setdefault("errors_this_cycle", [])
                        
                        # CRITICAL FIX: Write after run_once completes
                        try:
                            with open("logs/worker_debug.log", "a") as f:
                                f.write(f"[{datetime.now(timezone.utc).isoformat()}] run_once() completed: clusters={metrics.get('clusters', 0)}, orders={metrics.get('orders', 0)}\n")
                                f.flush()
                        except:
                            pass
                        print(f"DEBUG: run_once() returned: clusters={metrics.get('clusters', 0)}, orders={metrics.get('orders', 0)}", flush=True)
                        
                        # CRITICAL FIX: ALWAYS call evaluate_exits() after run_once(), regardless of run_once() result
                        # This ensures V position is evaluated and closed even if run_once() hangs or fails
                        try:
                            if worker_engine and hasattr(worker_engine, 'executor') and hasattr(worker_engine.executor, 'evaluate_exits'):
                                print("DEBUG: Calling evaluate_exits() after run_once()", flush=True)
                                try:
                                    with open("logs/worker_debug.log", "a") as f:
                                        f.write(f"[{datetime.now(timezone.utc).isoformat()}] Calling evaluate_exits() after run_once()\n")
                                        f.flush()
                                except:
                                    pass
                                worker_engine.executor.evaluate_exits()
                                print("DEBUG: evaluate_exits() completed", flush=True)
                                try:
                                    with open("logs/worker_debug.log", "a") as f:
                                        f.write(f"[{datetime.now(timezone.utc).isoformat()}] evaluate_exits() completed\n")
                                        f.flush()
                                except:
                                    pass
                            else:
                                print("ERROR: worker_engine.executor.evaluate_exits() not available", flush=True)
                                try:
                                    with open("logs/worker_debug.log", "a") as f:
                                        f.write(f"[{datetime.now(timezone.utc).isoformat()}] ERROR: worker_engine.executor.evaluate_exits() not available\n")
                                        f.flush()
                                except:
                                    pass
                        except Exception as safety_err:
                            print(f"ERROR: evaluate_exits() failed: {safety_err}", flush=True)
                            try:
                                with open("logs/worker_debug.log", "a") as f:
                                    f.write(f"[{datetime.now(timezone.utc).isoformat()}] ERROR: evaluate_exits() failed: {safety_err}\n")
                                    f.write(f"[{datetime.now(timezone.utc).isoformat()}] Traceback: {traceback.format_exc()}\n")
                                    f.flush()
                            except:
                                pass
                        # CRITICAL: Ensure run.jsonl is written even for successful cycles
                        jsonl_write("run", {
                            "ts": datetime.now(timezone.utc).isoformat(),
                            "_ts": int(time.time()),
                            "msg": "complete",
                            "clusters": metrics.get("clusters", 0),
                            "orders": metrics.get("orders", 0),
                            "market_open": True,
                            "engine_status": metrics.get("engine_status", "ok"),
                            "errors_this_cycle": metrics.get("errors_this_cycle", []),
                            "metrics": metrics
                        })
                    except Exception as run_err:
                        print(f"ERROR: run_once() raised exception: {run_err}", flush=True)
                        traceback.print_exc()

                        # CRITICAL FIX: Log exception to file
                        try:
                            with open("logs/worker_debug.log", "a") as f:
                                f.write(f"[{datetime.now(timezone.utc).isoformat()}] ERROR: run_once() exception: {run_err}\n")
                                f.write(f"[{datetime.now(timezone.utc).isoformat()}] Traceback: {traceback.format_exc()}\n")
                                f.flush()
                        except:
                            pass
                        
                        metrics = {"clusters": 0, "orders": 0, "error": str(run_err)}
                        metrics["engine_status"] = "degraded"
                        metrics["errors_this_cycle"] = [f"{type(run_err).__name__}: {str(run_err)}"]
                        jsonl_write("run", {
                            "ts": datetime.now(timezone.utc).isoformat(),
                            "_ts": int(time.time()),
                            "msg": "complete",
                            "clusters": 0,
                            "orders": 0,
                            "market_open": True,
                            "engine_status": "degraded",
                            "errors_this_cycle": metrics.get("errors_this_cycle", []),
                            "error": str(run_err)[:200],
                            "metrics": metrics
                        })
                        
                        # CRITICAL FIX: Still call evaluate_exits() even if run_once() failed
                        try:
                            if worker_engine and hasattr(worker_engine, 'executor') and hasattr(worker_engine.executor, 'evaluate_exits'):
                                print("DEBUG: Calling evaluate_exits() after run_once() exception", flush=True)
                                try:
                                    with open("logs/worker_debug.log", "a") as f:
                                        f.write(f"[{datetime.now(timezone.utc).isoformat()}] Calling evaluate_exits() after run_once() exception\n")
                                        f.flush()
                                except:
                                    pass
                                worker_engine.executor.evaluate_exits()
                                print("DEBUG: evaluate_exits() completed after exception", flush=True)
                                try:
                                    with open("logs/worker_debug.log", "a") as f:
                                        f.write(f"[{datetime.now(timezone.utc).isoformat()}] evaluate_exits() completed after exception\n")
                                        f.flush()
                                except:
                                    pass
                            else:
                                print("ERROR: worker_engine.executor.evaluate_exits() not available after exception", flush=True)
                        except Exception as exit_err:
                            print(f"ERROR: evaluate_exits() failed after run_once() exception: {exit_err}", flush=True)
                            try:
                                with open("logs/worker_debug.log", "a") as f:
                                    f.write(f"[{datetime.now(timezone.utc).isoformat()}] ERROR: evaluate_exits() failed after exception: {exit_err}\n")
                                    f.write(f"[{datetime.now(timezone.utc).isoformat()}] Traceback: {traceback.format_exc()}\n")
                                    f.flush()
                            except:
                                pass
                        
                        # SAFETY: Do not re-raise. The worker loop must not die on strategy/logging exceptions.
                else:
                    # Market closed - still log cycle but skip trading
                    print(f"DEBUG: Market is CLOSED - skipping trading", flush=True)
                    metrics = {"market_open": False, "clusters": 0, "orders": 0, "engine_status": "ok", "errors_this_cycle": []}
                    jsonl_write("run", {
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "_ts": int(time.time()),
                        "msg": "cycle_complete",
                        "clusters": 0,
                        "orders": 0,
                        "market_open": False,
                        "engine_status": metrics.get("engine_status", "ok"),
                        "errors_this_cycle": metrics.get("errors_this_cycle", []),
                        "metrics": metrics
                    })
                    log_event("run", "complete", clusters=0, orders=0, metrics=metrics, market_open=False)
                
                daily_and_weekly_tasks_if_needed()
                self.state.iter_count += 1
                self.state.fail_count = 0
                self.state.save_fail_count(0)
                self.state.backoff_sec = Config.BACKOFF_BASE_SEC
                try:
                    _emit_phase2_heartbeat(self.state.iter_count)
                except Exception:
                    pass
                self.heartbeat(metrics)
                
                log_event("worker", "iter_end", iter=self.state.iter_count, success=True, market_open=market_open)
```
