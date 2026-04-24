# Quant strategy export (verbatim code)

**Purpose:** External quantitative review of signal weighting, entry/exit logic, and risk gates.

**Naming note:** The runtime composite is exposed as **`score`** on the dict returned by `compute_composite_score_v2` / `_compute_composite_score_core`. Telemetry or dashboards may label a similar quantity `total_score`; the implementation below uses `score`. Component keys in `components` are `flow` (options flow), `dark_pool`, `greeks_gamma`, `ftd_pressure`, `squeeze_score` (not `component_*` prefixes).

**Droplet telemetry:** Latest 48h UTC extracts and counts live under `reports/Gemini/` (`telemetry_overview.md`, CSVs). Refresh with `python3 scripts/extract_gemini_telemetry.py` on the server and `scp` the folder locally.

---

## 1. Signal intelligence and scoring

### 1.1 `WEIGHTS_V3`, entry thresholds, sizing overlays (`uw_composite_v2.py`)

```python
# uw_composite_v2.py (excerpt)
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

ENTRY_THRESHOLDS = {
    "base": 2.7,
    "canary": 2.9,
    "champion": 3.2
}

SIZING_OVERLAYS = {
    "iv_skew_align_boost": 0.25,
    "whale_persistence_boost": 0.20,
    "skew_conflict_penalty": -0.30,
    "toxicity_penalty": -0.25
}
```

### 1.2 Regime-aware weight accessor (`uw_composite_v2.py`)

```python
def get_weight(component: str, regime: str = "neutral") -> float:
    """
    UNIFIED WEIGHT ACCESSOR - All scoring must use this function.
    ...
    """
    global _cached_weights, _weights_cache_ts

    # CRITICAL FIX: options_flow uses default weight unless governance overlay down-weights it
    effective_weight: Optional[float] = None
    if component == "options_flow":
        effective_weight = WEIGHTS_V3.get(component, 2.4)

    # Try to get regime-aware weight from optimizer (skip for options_flow, already set)
    if effective_weight is None:
        optimizer = _get_adaptive_optimizer()
        if optimizer and hasattr(optimizer, 'entry_model'):
            try:
                effective_weight = optimizer.entry_model.get_effective_weight(component, regime)
                if component == "options_flow" and effective_weight < 1.5:
                    effective_weight = WEIGHTS_V3.get(component, 2.4)
            except Exception:
                effective_weight = None

    if effective_weight is None:
        now = time.time()
        if now - _weights_cache_ts > 60:
            adaptive = get_adaptive_weights()
            if adaptive:
                _cached_weights = {**WEIGHTS_V3, **adaptive}
            else:
                _cached_weights = WEIGHTS_V3.copy()
            _weights_cache_ts = now
        effective_weight = _cached_weights.get(component, WEIGHTS_V3.get(component, 0.0))

    gov_overlay = _get_governance_signal_weight_overlay()
    if gov_overlay and component in gov_overlay:
        delta = gov_overlay[component]
        effective_weight = effective_weight * (1.0 + delta)
        effective_weight = max(0.25, min(2.5, effective_weight))

    return effective_weight
```

### 1.3 Core composite: component math, `composite_raw`, final `score` (`_compute_composite_score_core`, `uw_composite_v2.py`)

The function begins ~line 729 with adaptive/env weight merges on `weights = WEIGHTS_V3.copy()`, then loads `flow_sent`, `flow_conv`, dark pool notionals, etc. Below is the **component calculation and aggregation** (through clamp). The returned dict includes `"score": round(composite_score, 3)` and `components` with keys `flow`, `dark_pool`, `greeks_gamma`, `ftd_pressure`, `squeeze_score`, etc.

```python
    # ============ COMPONENT CALCULATIONS (using adaptive weights) ============
    all_notes = []
    if adaptive_active:
        all_notes.append("adaptive_weights_active")
    if conv_raw is None:
        all_notes.append("conviction_missing")

    flow_trade_count = int(_to_num(enriched_data.get("trade_count", 0)) or 0)
    flow_magnitude = "LOW" if flow_conv < 0.3 else ("MEDIUM" if flow_conv < 0.7 else "HIGH")
    stealth_flow_boost = 0.2 if (flow_trade_count > 0 and flow_magnitude == "LOW") else 0.0
    flow_conv_adjusted = min(1.0, flow_conv + stealth_flow_boost)

    flow_weight = get_weight("options_flow", regime)
    flow_component = flow_weight * flow_conv_adjusted

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
                continue
            sweeps_hi += 1
        if sweeps_hi >= 3:
            urgency_multiplier = 1.2
            flow_component *= urgency_multiplier
            all_notes.append(f"sweep_urgency({urgency_multiplier}x,{sweeps_hi} sweeps>$100k)")
    except Exception:
        pass

    if stealth_flow_boost > 0:
        all_notes.append(f"stealth_flow_boost(+{stealth_flow_boost:.1f})")

    dp_strength = 0.2
    try:
        scale = max(0.0, dp_prem)
        dp_strength = 0.2 + 0.8 * min(1.0, scale / 50_000_000.0)
    except Exception:
        dp_strength = 0.2
    dp_weight = get_weight("dark_pool", regime)
    dp_component = dp_weight * dp_strength

    ins_sent = ins.get("sentiment", "NEUTRAL")
    ins_mod = _to_num(ins.get("conviction_modifier", 0.0))
    insider_weight = get_weight("insider", regime)
    if ins_sent == "BULLISH":
        insider_component = insider_weight * (0.50 + ins_mod)
    elif ins_sent == "BEARISH":
        insider_component = insider_weight * (0.50 - abs(ins_mod))
    else:
        insider_component = insider_weight * 0.25

    iv_aligned = (iv_skew > 0 and flow_sign == +1) or (iv_skew < 0 and flow_sign == -1)
    iv_weight = get_weight("iv_term_skew", regime)
    iv_component = iv_weight * abs(iv_skew) * (1.3 if iv_aligned else 0.7)

    smile_weight = get_weight("smile_slope", regime)
    smile_component = smile_weight * abs(smile_slope)

    whale_detected = motif_whale.get("detected", False)
    whale_weight = get_weight("whale_persistence", regime)
    whale_score = 0.0 if not whale_detected else whale_weight * _to_num(motif_whale.get("avg_conviction", 0.0))

    event_weight = get_weight("event_alignment", regime)
    event_component = event_weight * event_align

    motif_weight = get_weight("temporal_motif", regime)
    motif_bonus = 0.0
    if motif_staircase.get("detected"):
        motif_bonus += motif_weight * motif_staircase.get("slope", 0.0) * 3.0
        all_notes.append(f"staircase({motif_staircase.get('steps', 0)} steps)")
    if motif_burst.get("detected"):
        intensity = motif_burst.get("intensity", 0.0)
        motif_bonus += motif_weight * min(1.0, intensity / 2.0)
        all_notes.append(f"burst({motif_burst.get('count', 0)} updates)")

    raw_tox_weight = get_weight("toxicity_penalty", regime)
    tox_weight = raw_tox_weight if raw_tox_weight < 0 else -abs(raw_tox_weight)
    toxicity_component = 0.0
    if toxicity > 0.5:
        toxicity_component = tox_weight * (toxicity - 0.5) * 1.5
        all_notes.append(f"toxicity_penalty({toxicity:.2f})")
    elif toxicity > 0.3:
        toxicity_component = tox_weight * (toxicity - 0.3) * 0.5
        all_notes.append(f"mild_toxicity({toxicity:.2f})")

    aligned_regime = (regime == "RISK_ON" and flow_sign == +1) or (regime == "RISK_OFF" and flow_sign == -1)
    opposite_regime = (regime == "RISK_ON" and flow_sign == -1) or (regime == "RISK_OFF" and flow_sign == +1)
    regime_factor = 1.0
    if regime == "RISK_ON":
        regime_factor = 1.15 if aligned_regime else 0.95
    elif regime == "RISK_OFF":
        regime_factor = 1.10 if opposite_regime else 0.90
    elif regime == "mixed" or regime == "NEUTRAL":
        regime_factor = 1.02
    regime_weight = get_weight("regime_modifier", regime)
    regime_component = regime_weight * (regime_factor - 1.0) * 2.0

    congress_component, congress_notes = compute_congress_component(congress_data, flow_sign)
    shorts_component, shorts_notes = compute_shorts_component(shorts_data, flow_sign, regime)
    institutional_payload = enriched_data.get("institutional", {}) or symbol_intel.get("institutional", {})
    inst_component, inst_notes = compute_institutional_component(ins, institutional_payload, flow_sign, regime)
    tide_component, tide_notes = compute_market_tide_component(tide_data, flow_sign, regime)
    calendar_component, calendar_notes = compute_calendar_component(calendar_data, symbol, regime)

    greeks_data = enriched_data.get("greeks", {})
    gamma_resistance_levels = _extract_gamma_resistance_levels(greeks_data if isinstance(greeks_data, dict) else {})
    if not greeks_data:
        greeks_gamma_component = 0.0
        all_notes.append("greeks_missing")
    else:
        gamma_exposure = _to_num(greeks_data.get("gamma_exposure", 0))
        if gamma_exposure == 0:
            call_gamma = _to_num(greeks_data.get("call_gamma", 0))
            put_gamma = _to_num(greeks_data.get("put_gamma", 0))
            gamma_exposure = call_gamma - put_gamma
        gamma_squeeze = greeks_data.get("gamma_squeeze_setup", False)
        greeks_weight = get_weight("greeks_gamma", regime)
        if gamma_squeeze:
            greeks_gamma_component = greeks_weight * 1.0
            all_notes.append("gamma_squeeze_setup")
        elif abs(gamma_exposure) > 500000:
            greeks_gamma_component = greeks_weight * 0.5
        elif abs(gamma_exposure) > 100000:
            greeks_gamma_component = greeks_weight * 0.25
        elif abs(gamma_exposure) > 10000:
            greeks_gamma_component = greeks_weight * 0.1
        else:
            greeks_gamma_component = greeks_weight * 0.2

    ftd_data = enriched_data.get("ftd", {}) or enriched_data.get("shorts", {})
    if not ftd_data:
        ftd_weight = get_weight("ftd_pressure", regime)
        ftd_pressure_component = ftd_weight * 0.2
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
        elif ftd_count > 10000:
            ftd_pressure_component = ftd_weight * 0.1
        else:
            ftd_pressure_component = ftd_weight * 0.2

    iv_data = enriched_data.get("iv", {}) or enriched_data.get("iv_rank", {})
    iv_rank_val = _to_num(iv_data.get("iv_rank", iv_data.get("iv_rank_1y", 50)))
    iv_rank_weight = get_weight("iv_rank", regime)
    if iv_rank_val < 20:
        iv_rank_component = iv_rank_weight * 1.0
        all_notes.append("low_iv_opportunity")
    elif iv_rank_val < 30:
        iv_rank_component = iv_rank_weight * 0.5
    elif iv_rank_val > 80:
        iv_rank_component = -iv_rank_weight * 1.0
        all_notes.append("high_iv_caution")
    elif iv_rank_val > 70:
        iv_rank_component = -iv_rank_weight * 0.5
    elif 30 <= iv_rank_val <= 70:
        iv_rank_component = iv_rank_weight * 0.15
    else:
        iv_rank_component = 0.0

    oi_data = enriched_data.get("oi_change", {}) or enriched_data.get("oi", {})
    if not oi_data:
        oi_weight = get_weight("oi_change", regime)
        oi_change_component = oi_weight * 0.2
        all_notes.append("oi_change_neutral_default")
    else:
        net_oi = _to_num(oi_data.get("net_oi_change", 0))
        if net_oi == 0:
            curr_oi = _to_num(oi_data.get("curr_oi", 0))
            if curr_oi == 0:
                volume = _to_num(oi_data.get("volume", 0))
                if volume > 0:
                    net_oi = volume * 0.1
        oi_sentiment = oi_data.get("oi_sentiment", "NEUTRAL")
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
        elif abs(net_oi) > 1000:
            oi_change_component = oi_weight * 0.1
        else:
            oi_change_component = oi_weight * 0.2

    etf_data = enriched_data.get("etf_flow", {})
    if not etf_data:
        etf_weight = get_weight("etf_flow", regime)
        etf_flow_component = etf_weight * 0.2
        all_notes.append("etf_flow_neutral_default")
    else:
        etf_sentiment = etf_data.get("overall_sentiment", "NEUTRAL")
        risk_on = etf_data.get("market_risk_on", False)
        etf_weight = get_weight("etf_flow", regime)
        if etf_sentiment == "BULLISH" and risk_on:
            etf_flow_component = etf_weight * 1.0
            all_notes.append("risk_on_environment")
        elif etf_sentiment == "BULLISH":
            etf_flow_component = etf_weight * 0.5
        elif etf_sentiment == "BEARISH":
            etf_flow_component = -etf_weight * 0.3
        else:
            etf_flow_component = etf_weight * 0.2

    squeeze_data = enriched_data.get("squeeze_score", {})
    if not squeeze_data:
        squeeze_weight = get_weight("squeeze_score", regime)
        squeeze_score_component = squeeze_weight * 0.2
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
            squeeze_score_component = squeeze_weight * 0.2

    composite_raw = (
        flow_component + dp_component + insider_component + iv_component + smile_component +
        whale_score + event_component + motif_bonus + toxicity_component + regime_component +
        congress_component + shorts_component + inst_component + tide_component + calendar_component +
        greeks_gamma_component + ftd_pressure_component + iv_rank_component + oi_change_component +
        etf_flow_component + squeeze_score_component
    )

    composite_score = composite_raw * freshness

    whale_conviction_boost = 0.0
    if whale_detected or motif_sweep.get("detected", False):
        whale_conviction_boost = 0.5
        composite_score += whale_conviction_boost
        all_notes.append(f"whale_conviction_boost(+{whale_conviction_boost})")

    composite_pre_clamp = composite_score
    composite_score = max(0.0, min(8.0, composite_score))
```

### 1.4 `compute_composite_score_v2`: adjustments on top of core (`uw_composite_v2.py`)

After `base = _compute_composite_score_core(...)`, `base_score = base["score"]`, then vol/beta/UW/premarket/regime bonuses, optional shaping, then:

```python
    total_adj = vol_bonus + low_vol_pen + beta_bonus + uw_bonus + pre_bonus + regime_bonus + regime_pen + shaping_adj
    score_v2 = _clamp(base_score + total_adj, 0.0, 8.0)
    # ... optional uw_intel layer adds uw_adj["total"] to score_v2 ...
    base["score"] = round(float(score_v2), 3)
    base["base_score"] = round(float(base_score), 3)
```

Full function loads `v2_params` from `config.registry.COMPOSITE_WEIGHTS_V2` when available (see section 4). Optional premarket/postmarket intel adjustments are applied in the same function (lines ~1549–1673 in repo).

---

## 2. Entry, sizing, and score gate

### 2.1 `Config` execution thresholds (`main.py` class `Config`)

```python
    MIN_EXEC_SCORE = float(get_env("MIN_EXEC_SCORE", "2.5"))
    SIZE_BASE_USD = float(get_env("SIZE_BASE_USD", "500"))
    MIN_NOTIONAL_USD = float(get_env("MIN_NOTIONAL_USD", "100"))
    DEFAULT_QTY = get_env("DEFAULT_QTY", 25, int)
    MAX_CONCURRENT_POSITIONS = get_env("MAX_CONCURRENT_POSITIONS", 16, int)
    LONG_ONLY = get_env("LONG_ONLY", "false").lower() == "true"
    ENABLE_OPPORTUNITY_DISPLACEMENT = get_env("ENABLE_OPPORTUNITY_DISPLACEMENT", "true").lower() == "true"
    DISPLACEMENT_MIN_AGE_HOURS = get_env("DISPLACEMENT_MIN_AGE_HOURS", 4, int)
    DISPLACEMENT_MAX_PNL_PCT = float(get_env("DISPLACEMENT_MAX_PNL_PCT", "0.01"))
    DISPLACEMENT_SCORE_ADVANTAGE = float(get_env("DISPLACEMENT_SCORE_ADVANTAGE", "2.0"))
    DISPLACEMENT_COOLDOWN_HOURS = get_env("DISPLACEMENT_COOLDOWN_HOURS", 6, int)
    DISPLACEMENT_ENABLED = get_env("DISPLACEMENT_ENABLED", "true").lower() == "true"
    DISPLACEMENT_MIN_HOLD_SECONDS = get_env("DISPLACEMENT_MIN_HOLD_SECONDS", 20 * 60, int)
    DISPLACEMENT_MIN_DELTA_SCORE = float(get_env("DISPLACEMENT_MIN_DELTA_SCORE", "0.75"))
    DISPLACEMENT_REQUIRE_THESIS_DOMINANCE = get_env("DISPLACEMENT_REQUIRE_THESIS_DOMINANCE", "true").lower() == "true"
    TRAILING_STOP_PCT = float(get_env("TRAILING_STOP_PCT", "0.015"))
    PROFIT_TARGETS = [float(x) for x in get_env("PROFIT_TARGETS", "0.02,0.05,0.10").split(",")]
    SCALE_OUT_FRACTIONS = [float(x) for x in get_env("SCALE_OUT_FRACTIONS", "0.3,0.3,0.4").split(",")]
    MAX_SPREAD_BPS = float(get_env("MAX_SPREAD_BPS", "50"))
    ENABLE_SPREAD_WATCHDOG = get_env("ENABLE_SPREAD_WATCHDOG", "true").lower() == "true"
```

### 2.2 Position sizing before `submit_entry` (`main.py`, `run_all_strategies` path)

```python
                try:
                    from risk_management import calculate_position_size, get_risk_limits
                    try:
                        account = self.executor.api.get_account()
                        account_equity = float(getattr(account, "equity", Config.SIZE_BASE_USD * 100))
                    except (AttributeError, ValueError, TypeError, Exception) as acct_err:
                        log_event("sizing", "account_fetch_error", symbol=symbol, error=str(acct_err))
                        account_equity = Config.SIZE_BASE_USD * 100
                    base_notional = calculate_position_size(account_equity)  # 1.5% base
                    limits = get_risk_limits()
                    if score > 4.5:
                        conviction_mult = 2.0 / 1.5
                    elif score < 3.5:
                        conviction_mult = 1.0 / 1.5
                    else:
                        conviction_mult = 1.0
                    notional_target = min(base_notional * conviction_mult, limits["max_position_dollar"])
                except (ImportError, Exception) as sizing_error:
                    log_event("sizing", "fallback_to_fixed", symbol=symbol, error=str(sizing_error))
                    notional_target = Config.SIZE_BASE_USD
                qty = max(1, int(notional_target / ref_price))
            # ...
            if uw_flow:
                uw_sentiment = uw_flow.get("sentiment", "")
                uw_conviction = float(uw_flow.get("conviction", 0.0))
                qty = uw_size_modifier(qty, uw_sentiment, uw_conviction)

            size_multiplier = v32.DynamicSizing.calculate_multiplier(
                composite_score=score,
                slippage_pct=recent_slippage_pct,
                regime=market_regime,
                stage=system_stage
            )
            qty = max(1, int(qty * size_multiplier))
            # correlation_concentration_risk_multiplier may further reduce qty
            ref_price_check = self.executor.get_last_trade(symbol)
            actual_notional = qty * ref_price_check
            if actual_notional < Config.MIN_NOTIONAL_USD:
                log_event("sizing", "min_notional_floor_reject", ...)
                continue
```

### 2.3 `uw_size_modifier` (`signals/uw.py`)

```python
def uw_size_modifier(base_contracts: int, uw_sentiment: str, conviction: float) -> int:
    sentiment = (uw_sentiment or "").upper()
    conv = float(conviction or 0.0)

    if sentiment == "BULLISH" and conv > 0.70:
        return max(1, int(round(base_contracts * 1.20)))
    elif sentiment == "BEARISH" and conv > 0.70:
        return max(1, int(round(base_contracts * 0.80)))

    return base_contracts
```

### 2.4 Risk limits and position dollar cap (`risk_management.py`)

```python
def get_risk_limits() -> Dict[str, float]:
    starting_equity = get_starting_equity()
    is_paper = is_paper_mode()
    if is_paper:
        daily_loss_pct = 0.04
        daily_loss_dollar = 2200
        min_account_equity = starting_equity * 0.85
        risk_per_trade_pct = 0.015
        max_position_dollar = 825
        max_symbol_exposure = starting_equity * 0.10
        max_sector_exposure = starting_equity * 0.30
    else:
        daily_loss_pct = 0.04
        daily_loss_dollar = 400
        min_account_equity = starting_equity * 0.85
        risk_per_trade_pct = 0.015
        max_position_dollar = 300
        max_symbol_exposure = starting_equity * 0.10
        max_sector_exposure = starting_equity * 0.30
    return {
        "starting_equity": starting_equity,
        "daily_loss_pct": daily_loss_pct,
        "daily_loss_dollar": daily_loss_dollar,
        "min_account_equity": min_account_equity,
        "max_drawdown_pct": 0.20,
        "risk_per_trade_pct": risk_per_trade_pct,
        "max_position_dollar": max_position_dollar,
        "min_position_dollar": 50.0,
        "max_symbol_exposure": max_symbol_exposure,
        "max_sector_exposure": max_sector_exposure,
    }

def calculate_position_size(account_equity: float) -> float:
    limits = get_risk_limits()
    dynamic_size = account_equity * limits["risk_per_trade_pct"]
    return max(
        limits["min_position_dollar"],
        min(dynamic_size, limits["max_position_dollar"])
    )

def validate_order_size(symbol: str, qty: int, side: str, current_price: float, buying_power: float) -> Tuple[bool, Optional[str]]:
    limits = get_risk_limits()
    order_value = qty * current_price
    if side == "buy" and order_value > buying_power * 0.95:
        return False, f"Order ${order_value:.2f} exceeds 95% of buying power ${buying_power:.2f}"
    if order_value > limits["max_position_dollar"]:
        return False, f"Order ${order_value:.2f} exceeds max position size ${limits['max_position_dollar']:.2f}"
    if order_value < limits["min_position_dollar"]:
        return False, f"Order ${order_value:.2f} below min position size ${limits['min_position_dollar']:.2f}"
    return True, None
```

### 2.5 Score gate (`main.py`)

```python
            min_score = Config.MIN_EXEC_SCORE
            if system_stage == "bootstrap":
                min_score = 1.5
            try:
                from self_healing_threshold import SelfHealingThreshold
                if not hasattr(self, '_self_healing_threshold'):
                    self._self_healing_threshold = SelfHealingThreshold(base_threshold=min_score)
                adjusted_threshold = self._self_healing_threshold.check_recent_trades()
                min_score = adjusted_threshold
            except ImportError:
                pass
            except Exception as e:
                log_event("self_healing", "error", error=str(e))

            if score < min_score:
                log_event("gate", "score_below_min", symbol=symbol, score=score, min_required=min_score, ...)
                ...
                continue
```

### 2.6 `submit_entry`: shortability, fractional qty, notional checks (`main.py`)

**Fractional short error path:** When `ref_price > position_size_usd`, the code sets `qty = fractional_qty` (float). Alpaca rejects **fractional sell (short)** with `fractional orders cannot be sold short`. `submit_entry` still types `qty: int` but may pass a float through to the API.

```python
    def submit_entry(self, symbol: str, qty: int, side: str, regime: str = "unknown", ...):
        if entry_score is None or not isinstance(entry_score, (int, float)) or float(entry_score) <= 0.0:
            return None, None, "metadata_missing", 0, "missing_entry_score"
        ...
        if side == "sell":
            try:
                asset = self.api.get_asset(symbol)
                is_shortable = bool(getattr(asset, "shortable", False))
            except Exception as e:
                is_shortable = False
            if not is_shortable:
                return None, None, "asset_not_shortable", 0, "asset_not_shortable"
        ref_price = self.get_last_trade(symbol)
        ...
        notional = qty * ref_price
        if notional < Config.MIN_NOTIONAL_USD:
            return None, None, "min_notional_blocked", 0, "min_notional_blocked"

        position_size_usd = Config.POSITION_SIZE_USD if hasattr(Config, 'POSITION_SIZE_USD') else Config.SIZE_BASE_USD
        if ref_price > position_size_usd:
            try:
                fractional_qty = position_size_usd / ref_price
                if fractional_qty >= 0.001:
                    qty = fractional_qty
                    log_event("submit_entry", "fractional_share_used", ...)
                else:
                    return None, None, "price_exceeds_cap", 0, "Price_Exceeds_Cap"
            except Exception as e:
                return None, None, "price_exceeds_cap", 0, "Price_Exceeds_Cap"
        ...
        try:
            from risk_management import validate_order_size
            order_valid, order_error = validate_order_size(symbol, qty, side, ref_price, available_bp)
            if not order_valid:
                return None, None, "risk_validation_failed", 0, order_error
        except ImportError:
            pass
```

### 2.7 Order submission call site (`main.py`)

```python
                    res, fill_price, order_type, filled_qty, entry_status = self.executor.submit_entry(
                        symbol,
                        qty,
                        side,
                        regime=market_regime,
                        client_order_id_base=client_order_id_base,
                        entry_score=score,
                        market_regime=market_regime,
                    )
```

---

## 3. Exit management

### 3.1 Full file `src/exit/exit_score_v2.py`

```python
#!/usr/bin/env python3
"""
Composite Exit Score (v2)
=========================

Computes an exit_score and recommended exit reason from:
- UW deterioration (flow/darkpool/sentiment)
- Sector/regime shifts
- Score deterioration (entry vs now)
- Relative strength deterioration (placeholder/best-effort)
- Volatility expansion (best-effort)
- Thesis invalidation flags (from pre/postmarket exit intel, optional)

Contract:
- Read-only intelligence: MUST NOT place orders.
- Safe-by-default: if inputs are missing, output should remain conservative.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from config.tuning.tuning_loader import get_merged_exit_weights

_DEFAULT_EXIT_WEIGHTS: Dict[str, float] = {
    "flow_deterioration": 0.20,
    "darkpool_deterioration": 0.10,
    "sentiment_deterioration": 0.10,
    "score_deterioration": 0.25,
    "regime_shift": 0.10,
    "sector_shift": 0.05,
    "vol_expansion": 0.10,
    "thesis_invalidated": 0.10,
    "earnings_risk": 0.0,
    "overnight_flow_risk": 0.0,
}


def _clamp(x: float, lo: float, hi: float) -> float:
    try:
        return max(float(lo), min(float(hi), float(x)))
    except Exception:
        return float(lo)


def compute_exit_score_v2(
    *,
    symbol: str,
    direction: str,
    entry_v2_score: float,
    now_v2_score: float,
    entry_uw_inputs: Dict[str, Any],
    now_uw_inputs: Dict[str, Any],
    entry_regime: str,
    now_regime: str,
    entry_sector: str,
    now_sector: str,
    realized_vol_20d: Optional[float] = None,
    thesis_flags: Optional[Dict[str, Any]] = None,
) -> Tuple[float, Dict[str, Any], str, list, str]:
    """
    Returns (exit_score [0..1], components, recommended_reason, attribution_components, reason_code).
    attribution_components: list of {"signal_id", "contribution_to_score"} for logging.
    reason_code: normalized string for exit_reason_code (same as recommended_reason).
    """
    entry_flow = float((entry_uw_inputs or {}).get("flow_strength", 0.0) or 0.0)
    now_flow = float((now_uw_inputs or {}).get("flow_strength", 0.0) or 0.0)
    entry_dp = float((entry_uw_inputs or {}).get("darkpool_bias", 0.0) or 0.0)
    now_dp = float((now_uw_inputs or {}).get("darkpool_bias", 0.0) or 0.0)
    entry_sent = str((entry_uw_inputs or {}).get("sentiment", "NEUTRAL") or "NEUTRAL").upper()
    now_sent = str((now_uw_inputs or {}).get("sentiment", "NEUTRAL") or "NEUTRAL").upper()

    # Deterioration terms are positive when things get worse.
    flow_det = _clamp(entry_flow - now_flow, 0.0, 1.0)
    dp_det = _clamp(abs(entry_dp) - abs(now_dp), 0.0, 1.0)
    sent_det = 1.0 if (entry_sent != "NEUTRAL" and now_sent == "NEUTRAL") else (1.0 if entry_sent != now_sent else 0.0)

    score_det = _clamp(float(entry_v2_score) - float(now_v2_score), 0.0, 8.0) / 8.0

    # Regime / sector shift (binary-ish)
    r_shift = 1.0 if str(entry_regime).upper() != str(now_regime).upper() else 0.0
    s_shift = 1.0 if str(entry_sector).upper() != str(now_sector).upper() else 0.0

    # Vol expansion proxy (best-effort)
    vol = float(realized_vol_20d or 0.0)
    vol_exp = _clamp((vol - 0.35) / 0.25, 0.0, 1.0) if vol > 0 else 0.0

    # Thesis flags
    tf = thesis_flags or {}
    thesis_bad = 1.0 if bool(tf.get("thesis_invalidated")) else 0.0
    earnings_risk = 1.0 if bool(tf.get("earnings_risk")) else 0.0
    overnight_risk = 1.0 if bool(tf.get("overnight_flow_risk")) else 0.0

    # Weighted combination (conservative)
    components = {
        "flow_deterioration": round(flow_det, 4),
        "darkpool_deterioration": round(dp_det, 4),
        "sentiment_deterioration": round(sent_det, 4),
        "score_deterioration": round(score_det, 4),
        "regime_shift": round(r_shift, 4),
        "sector_shift": round(s_shift, 4),
        "vol_expansion": round(vol_exp, 4),
        "thesis_invalidated": round(thesis_bad, 4),
        "earnings_risk": round(earnings_risk, 4),
        "overnight_flow_risk": round(overnight_risk, 4),
    }

    exit_w = get_merged_exit_weights(_DEFAULT_EXIT_WEIGHTS)
    score = (
        float(exit_w.get("flow_deterioration", 0.20)) * flow_det
        + float(exit_w.get("darkpool_deterioration", 0.10)) * dp_det
        + float(exit_w.get("sentiment_deterioration", 0.10)) * sent_det
        + float(exit_w.get("score_deterioration", 0.25)) * score_det
        + float(exit_w.get("regime_shift", 0.10)) * r_shift
        + float(exit_w.get("sector_shift", 0.05)) * s_shift
        + float(exit_w.get("vol_expansion", 0.10)) * vol_exp
        + float(exit_w.get("thesis_invalidated", 0.10)) * thesis_bad
        + float(exit_w.get("earnings_risk", 0.0)) * earnings_risk
        + float(exit_w.get("overnight_flow_risk", 0.0)) * overnight_risk
    )
    score = _clamp(score, 0.0, 1.0)

    # Recommended reason and reason_code (for attribution)
    reason = "hold"
    if thesis_bad >= 1.0:
        reason = "intel_deterioration"
    elif score_det >= 0.35:
        reason = "intel_deterioration"
    elif vol_exp >= 0.8 and score >= 0.6:
        reason = "stop"
    elif earnings_risk >= 1.0 and score >= 0.5:
        reason = "stop"
    elif score >= 0.75:
        reason = "replacement"
    elif score >= 0.55:
        reason = "profit"
    reason_code = str(reason or "hold").strip() or "hold"

    # Attribution: per-component contribution to exit_score (for logs/exit_attribution.jsonl).
    # Canonical naming: all exit attribution signal_ids use "exit_" prefix (e.g. exit_flow_deterioration).
    def _exit_signal_id(key: str) -> str:
        return key if key.startswith("exit_") else f"exit_{key}"

    attribution_components = [
        {
            "signal_id": _exit_signal_id(k),
            "source": "exit",
            "contribution_to_score": round(float(exit_w.get(k, 0.0)) * float(components.get(k, 0.0)), 6),
        }
        for k in components
    ]

    return float(score), components, reason, attribution_components, reason_code
```

### 3.2 Full files `src/exit/stops_v2.py` and `src/exit/profit_targets_v2.py`

```python
#!/usr/bin/env python3
"""
Dynamic Stops (v2)
==================

Best-effort stop calculator. If prices/vol inputs are missing, returns None stop.

Contract:
- Read-only helper: stop is advisory; executor decides actual orders.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple


def compute_stop_price(
    *,
    entry_price: Optional[float],
    realized_vol_20d: Optional[float],
    flow_reversal: bool,
    regime_label: str,
    sector_collapse: bool,
    direction: str,
) -> Tuple[Optional[float], Dict[str, Any]]:
    if entry_price is None or entry_price <= 0:
        return None, {"reason": "missing_entry_price"}

    vol = float(realized_vol_20d or 0.0)
    # Base stop percent: 1.5%–4% based on vol
    base_pct = 0.015 + max(0.0, min(0.025, (vol - 0.20) * 0.06))

    # Tighten on flow reversal / regime risk-off / sector collapse
    tighten = 1.0
    if flow_reversal:
        tighten *= 0.75
    if sector_collapse:
        tighten *= 0.80
    r = str(regime_label or "NEUTRAL").upper()
    if r in ("RISK_OFF", "BEAR"):
        tighten *= 0.80

    pct = base_pct * tighten
    pct = max(0.005, min(0.08, pct))

    d = str(direction or "").lower()
    if d == "bullish":
        stop = float(entry_price) * (1.0 - pct)
    elif d == "bearish":
        stop = float(entry_price) * (1.0 + pct)
    else:
        return None, {"reason": "neutral_direction"}

    return float(stop), {
        "base_pct": round(base_pct, 4),
        "pct": round(pct, 4),
        "tighten_mult": round(tighten, 4),
        "flow_reversal": bool(flow_reversal),
        "sector_collapse": bool(sector_collapse),
        "regime_label": r,
    }
```

```python
#!/usr/bin/env python3
"""
Dynamic Profit Targets (v2)
==========================

Best-effort target calculator. If prices/vol inputs are missing, returns None target.

Contract:
- Read-only helper: target is advisory; executor decides actual orders.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple


def compute_profit_target(
    *,
    entry_price: Optional[float],
    realized_vol_20d: Optional[float],
    flow_strength: float,
    regime_label: str,
    sector: str,
    direction: str,
) -> Tuple[Optional[float], Dict[str, Any]]:
    """
    Returns (profit_target_price, reasoning)
    """
    if entry_price is None or entry_price <= 0:
        return None, {"reason": "missing_entry_price"}

    vol = float(realized_vol_20d or 0.0)
    # Base target percent: 2%–6% based on realized vol (very conservative)
    base_pct = 0.02 + max(0.0, min(0.04, (vol - 0.20) * 0.10))

    # Flow adjustment: stronger flow => wider target
    flow_mult = 1.0 + max(0.0, min(0.50, float(flow_strength) * 0.50))

    # Regime adjustment
    r = str(regime_label or "NEUTRAL").upper()
    if r == "RISK_ON":
        reg_mult = 1.15
    elif r in ("RISK_OFF", "BEAR"):
        reg_mult = 0.85
    else:
        reg_mult = 1.0

    # Sector adjustment (small)
    s = str(sector or "UNKNOWN").upper()
    sec_mult = 1.05 if s in ("TECH", "BIOTECH") else 1.0

    pct = base_pct * flow_mult * reg_mult * sec_mult
    pct = max(0.01, min(0.10, pct))

    d = str(direction or "").lower()
    if d == "bullish":
        target = float(entry_price) * (1.0 + pct)
    elif d == "bearish":
        target = float(entry_price) * (1.0 - pct)
    else:
        return None, {"reason": "neutral_direction"}

    return float(target), {
        "base_pct": round(base_pct, 4),
        "pct": round(pct, 4),
        "flow_mult": round(flow_mult, 4),
        "regime_mult": round(reg_mult, 4),
        "sector_mult": round(sec_mult, 4),
        "regime_label": r,
        "sector": s,
    }
```

### 3.3 Watchdog worker: `signal_delta`, decay, stops, profit, displacement triggers (`main.py`)

`signal_delta` for exit regimes:

```python
                current_composite = current_signals.get("composite_score", 0.0) or 0.0
                signal_delta = (float(current_composite) - float(entry_score)) if (entry_score and current_composite) else None
                price_delta_pct = (float(current_price - entry_price) / float(entry_price) * 100.0) if entry_price and entry_price > 0 else None
                exit_regime, exit_regime_reason, exit_regime_context = get_exit_regime(
                    signal_delta=signal_delta,
                    price_delta_pct=price_delta_pct,
                    entry_signal_strength=float(entry_score) if entry_score else None,
                    pnl_delta_15m=None,
                    catastrophic_decay=False,
                )
```

Stop-loss, trailing, signal decay vs composite, profit target, `should_exit`:

```python
            if regime_exit == "BEAR":
                stop_loss_pct = -0.008
                profit_target_decimal = 0.01
            else:
                stop_loss_pct = -0.01
                profit_target_decimal = 0.0075
            pnl_pct_decimal = pnl_pct / 100.0
            stop_loss_hit = pnl_pct_decimal <= stop_loss_pct
            ...
            decay_threshold = get_effective_decay_threshold(exit_regime_for_decay, base=0.60)  # or 0.50 on exception
            ...
            if entry_score > 0 and position_age_sec >= min_hold_sec:
                current_composite = current_signals.get("composite_score", 0.0)
                if current_composite != 0:
                    decay_ratio = current_composite / entry_score
                    signal_decay_exit = decay_ratio < decay_threshold
            profit_target_hit = pnl_pct_decimal >= profit_target_decimal
            ...
            should_exit = stop_loss_hit or signal_decay_exit or profit_target_hit or stop_hit
```

V2 exit promotion (env `V2_EXIT_SCORE_THRESHOLD`, default `0.80`):

```python
                if float(v2_exit_score) >= _v2_exit_thr:
                    exit_signals["v2_exit_score"] = round(float(v2_exit_score), 4)
                    ...
                    if _passes_hold_floor(exit_timing_cfg, hold_seconds):
                        to_close.append(symbol)
                    continue
```

### 3.4 Displacement: portfolio candidate selection (`main.py` `find_displacement_candidate`)

Elite tier (full book + new score > 3.6): displace positions with `current_score < 3.0` or `pnl_pct < -0.5`. Competitive: new signal > 4.0 and `score_delta > 1.0`. Legacy force-close when `num_positions == 5` and new signal > 4.5. (See `main.py` ~5621–5853.)

### 3.5 Full file `trading/displacement_policy.py`

```python
"""
Displacement policy: min hold, min delta, thesis dominance.

Contract:
- evaluate_displacement(current_position, challenger_candidate, context) -> (allowed, reason, diagnostics)
- All decisions logged via caller (system_events.jsonl, subsystem=displacement).
- Config-driven; revert by DISPLACEMENT_MIN_HOLD_SECONDS=0, MIN_DELTA=0, REQUIRE_THESIS_DOMINANCE=false.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

# Config defaults (overridden by env via caller)
DISPLACEMENT_ENABLED = True
DISPLACEMENT_MIN_HOLD_SECONDS = 20 * 60  # 20 minutes
DISPLACEMENT_MIN_DELTA_SCORE = 0.75
DISPLACEMENT_REQUIRE_THESIS_DOMINANCE = True
DISPLACEMENT_THESIS_DOMINANCE_MODE = "flow_or_regime"
DISPLACEMENT_LOG_EVERY_DECISION = True
_EPSILON = 1e-6


def _ts_now() -> datetime:
    return datetime.now(timezone.utc)


def _age_seconds(entry_ts: Optional[Any]) -> float:
    if entry_ts is None:
        return 0.0
    try:
        if hasattr(entry_ts, "timestamp"):
            t = entry_ts
        elif isinstance(entry_ts, (int, float)):
            from datetime import datetime, timezone
            t = datetime.fromtimestamp(float(entry_ts), tz=timezone.utc)
        elif isinstance(entry_ts, str):
            t = datetime.fromisoformat(entry_ts.replace("Z", "+00:00"))
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
        else:
            return 0.0
        return (_ts_now() - t).total_seconds()
    except Exception:
        return 0.0


def _regime_alignment_better(challenger_regime: Any, current_regime: Any, posture: str) -> bool:
    """True if challenger aligns with posture/regime better than current (simplified)."""
    if not posture or posture.upper() == "NEUTRAL":
        return False
    p = posture.upper()
    # Placeholder: same regime = no win; different regime we don't have full logic.
    return False


def evaluate_displacement(
    current_position: Dict[str, Any],
    challenger_candidate: Dict[str, Any],
    context: Dict[str, Any],
    *,
    config_overrides: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Evaluate whether displacement is allowed.

    Args:
        current_position: {symbol, entry_ts, current_score, entry_score, uw_flow_strength, dark_pool_bias, ...}
        challenger_candidate: {symbol, score, uw_flow_strength, dark_pool_bias, ...} (new signal)
        context: {regime_label, posture, ...}
        config_overrides: optional {DISPLACEMENT_MIN_HOLD_SECONDS, DISPLACEMENT_MIN_DELTA_SCORE, ...}

    Returns:
        (allowed: bool, reason: str, diagnostics: dict)
    """
    overrides = config_overrides or {}
    min_hold = overrides.get("DISPLACEMENT_MIN_HOLD_SECONDS", DISPLACEMENT_MIN_HOLD_SECONDS)
    min_delta = overrides.get("DISPLACEMENT_MIN_DELTA_SCORE", DISPLACEMENT_MIN_DELTA_SCORE)
    require_thesis = overrides.get("DISPLACEMENT_REQUIRE_THESIS_DOMINANCE", DISPLACEMENT_REQUIRE_THESIS_DOMINANCE)
    enabled = overrides.get("DISPLACEMENT_ENABLED", DISPLACEMENT_ENABLED)

    current_symbol = current_position.get("symbol", "UNKNOWN")
    challenger_symbol = challenger_candidate.get("symbol", "UNKNOWN")
    current_score = float(current_position.get("current_score") or current_position.get("entry_score") or 0.0)
    challenger_score = float(challenger_candidate.get("score") or challenger_candidate.get("new_signal_score") or 0.0)
    delta_score = challenger_score - current_score

    entry_ts = current_position.get("entry_ts") or current_position.get("ts")
    age_seconds = _age_seconds(entry_ts)
    if age_seconds <= 0 and current_position.get("age_hours") is not None:
        age_seconds = float(current_position["age_hours"]) * 3600

    regime_label = str(context.get("regime_label") or context.get("regime") or "UNKNOWN")
    posture = str(context.get("posture") or "NEUTRAL")

    uw_current = current_position.get("uw_flow_strength")
    uw_challenger = challenger_candidate.get("uw_flow_strength")
    dp_current = current_position.get("dark_pool_bias")
    dp_challenger = challenger_candidate.get("dark_pool_bias")

    diagnostics: Dict[str, Any] = {
        "current_symbol": current_symbol,
        "challenger_symbol": challenger_symbol,
        "current_score": round(current_score, 4),
        "challenger_score": round(challenger_score, 4),
        "delta_score": round(delta_score, 4),
        "current_entry_ts": str(entry_ts) if entry_ts else None,
        "age_seconds": round(age_seconds, 1),
        "regime_label": regime_label,
        "posture": posture,
        "uw_flow_strength_current": uw_current,
        "uw_flow_strength_challenger": uw_challenger,
        "dark_pool_bias_current": dp_current,
        "dark_pool_bias_challenger": dp_challenger,
        "note_missing_fields": [],
    }
    if uw_current is None and uw_challenger is None:
        diagnostics["note_missing_fields"].append("uw_flow_strength")
    if dp_current is None and dp_challenger is None:
        diagnostics["note_missing_fields"].append("dark_pool_bias")
    if not diagnostics["note_missing_fields"]:
        diagnostics["note_missing_fields"] = None

    if not enabled:
        diagnostics["allowed"] = False
        diagnostics["reason"] = "displacement_disabled"
        return False, "displacement_disabled", diagnostics

    # Emergency bypass: elite-tier (score < 3 or pnl < -0.5%) — no min hold.
    emergency = (
        current_score < 3.0
        or (isinstance(current_position.get("pnl_pct"), (int, float)) and float(current_position["pnl_pct"]) < -0.005)
    )
    if not emergency and age_seconds < min_hold:
        diagnostics["allowed"] = False
        diagnostics["reason"] = "displacement_min_hold"
        return False, "displacement_min_hold", diagnostics

    if delta_score < min_delta:
        diagnostics["allowed"] = False
        diagnostics["reason"] = "displacement_delta_too_small"
        return False, "displacement_delta_too_small", diagnostics

    if require_thesis:
        flow_win = False
        if uw_challenger is not None:
            if uw_current is None:
                flow_win = True
            else:
                flow_win = float(uw_challenger) >= float(uw_current) + _EPSILON
        regime_win = _regime_alignment_better(
            challenger_candidate.get("regime_label"),
            current_position.get("regime_label"),
            posture,
        )
        dp_win = False
        if dp_challenger is not None and dp_current is not None:
            # Same sign and challenger stronger
            try:
                dc, dch = float(dp_current), float(dp_challenger)
                dp_win = (dc * dch > 0) and (abs(dch) > abs(dc) + _EPSILON)
            except Exception:
                pass
        elif dp_challenger is not None and dp_current is None:
            dp_win = True
        if not (flow_win or regime_win or dp_win):
            diagnostics["allowed"] = False
            diagnostics["reason"] = "displacement_no_thesis_dominance"
            diagnostics["thesis_flow_win"] = flow_win
            diagnostics["thesis_regime_win"] = regime_win
            diagnostics["thesis_dp_win"] = dp_win
            return False, "displacement_no_thesis_dominance", diagnostics

    diagnostics["allowed"] = True
    diagnostics["reason"] = "displacement_allowed"
    return True, "displacement_allowed", diagnostics
```

---

## 4. Configurations and thresholds (files and registry)

### 4.1 `config/strategy_governance.json`

```json
{
  "strategies": {
    "EQUITY": {
      "position_cap": 25,
      "capital_fraction": 1.0,
      "displacement_allowed": true,
      "can_displace": ["EQUITY"],
      "exit_policy": "equity_exit_v2",
      "promotion_metric": "regime_conditional_expectancy"
    }
  }
}
```

### 4.2 `config/tuning/active.json` (exit weight overlay)

```json
{
  "version": "PROMOTED_DIAGNOSTIC_ALPACA_SCORE_DETERIORATION_EMPHASIS_2026-03-20",
  "exit_weights": {
    "flow_deterioration": 0.17,
    "darkpool_deterioration": 0.1,
    "sentiment_deterioration": 0.1,
    "score_deterioration": 0.28,
    "regime_shift": 0.1,
    "sector_shift": 0.05,
    "vol_expansion": 0.1,
    "thesis_invalidated": 0.1
  },
  "meta": { ... }
}
```

### 4.3 `config/registry.py` — `Thresholds` and `COMPOSITE_WEIGHTS_V2` (excerpt)

```python
class Thresholds:
    MIN_EXEC_SCORE = get_env("MIN_EXEC_SCORE", 2.5, float)
    MAX_CONCURRENT_POSITIONS = get_env("MAX_CONCURRENT_POSITIONS", 16, int)
    MAX_NEW_POSITIONS_PER_CYCLE = 6
    TRAILING_STOP_PCT = get_env("TRAILING_STOP_PCT", 0.015, float)
    TIME_EXIT_MINUTES = get_env("TIME_EXIT_MINUTES", 240, int)
    DISPLACEMENT_MIN_AGE_HOURS = get_env("DISPLACEMENT_MIN_AGE_HOURS", 4, int)
    DISPLACEMENT_MAX_PNL_PCT = get_env("DISPLACEMENT_MAX_PNL_PCT", 0.01, float)
    DISPLACEMENT_SCORE_ADVANTAGE = get_env("DISPLACEMENT_SCORE_ADVANTAGE", 2.0, float)
    DISPLACEMENT_COOLDOWN_HOURS = get_env("DISPLACEMENT_COOLDOWN_HOURS", 6, int)
    POSITION_SIZE_USD = get_env("POSITION_SIZE_USD", 500, float)
    MAX_THEME_NOTIONAL_USD = get_env("MAX_THEME_NOTIONAL_USD", 50000, float)
    ...

COMPOSITE_WEIGHTS_V2: Dict[str, Any] = {
    "version": "2026-01-20_wt1",
    "vol_center": 0.20,
    "vol_scale": 0.25,
    "vol_bonus_max": 0.70,
    "low_vol_penalty_center": 0.15,
    "low_vol_penalty_max": -0.15,
    "beta_center": 1.00,
    "beta_scale": 1.00,
    "beta_bonus_max": 0.45,
    "uw_center": 0.55,
    "uw_scale": 0.45,
    "uw_bonus_max": 0.25,
    "premarket_align_bonus": 0.15,
    "premarket_misalign_penalty": -0.15,
    "regime_align_bonus": 0.55,
    "regime_misalign_penalty": -0.35,
    "posture_conf_strong": 0.65,
    "high_vol_multiplier": 1.15,
    "mid_vol_multiplier": 1.00,
    "low_vol_multiplier": 0.90,
    "misalign_dampen": 0.25,
    "neutral_dampen": 0.60,
    "uw": { ... },  # nested intel weights — see full registry
}
```

### 4.4 `main.py` — `DEFAULT_COMPONENT_WEIGHTS` (legacy / per-ticker path)

```python
    DEFAULT_COMPONENT_WEIGHTS = {
        "flow_count": 1.0,
        "flow_premium": 1.0,
        "gamma": 1.0,
        "net_premium": 1.0,
        "volatility": 1.0,
        "institutional": 1.0,
        "market_tide": 1.0,
        "calendar": 1.0,
        "greeks_gamma": 1.2,
        "ftd_pressure": 1.0,
        "iv_rank": 1.0,
        "oi_change": 1.1,
        "darkpool": 0.0,
        "congress": 0.0,
        "shorts_squeeze": 0.0,
        "etf_flow": 0.0,
        "squeeze_score": 0.0
    }
```

---

## 5. Source file index

| Area | Primary files |
|------|----------------|
| Composite score | `uw_composite_v2.py` |
| Entry loop / gates | `main.py` |
| Risk sizing | `risk_management.py` |
| UW sizing modifier | `signals/uw.py` |
| Exit score | `src/exit/exit_score_v2.py`, `config/tuning/active.json`, `config/tuning/tuning_loader.py` |
| Stops / targets | `src/exit/stops_v2.py`, `src/exit/profit_targets_v2.py` |
| Displacement | `main.py` (`find_displacement_candidate`, `execute_displacement`), `trading/displacement_policy.py` |
| Registry | `config/registry.py` |
| Governance JSON | `config/strategy_governance.json` |

For **line-accurate** copies of any truncated block, open the cited path in the repository.
