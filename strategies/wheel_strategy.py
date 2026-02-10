"""
Wheel strategy: Cash-secured puts (CSP) -> Covered calls (CC).

- CSP phase: Sell puts on wheel universe tickers.
- CC phase: Sell covered calls on assigned shares from wheel CSPs.
- All orders tagged with strategy_id="wheel", phase="CSP" or "CC".
- Regime is modifier-only; must never gate or block wheel entries.
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config.registry import Directories, StateFiles, read_json, atomic_write_json, append_jsonl, LogFiles

log = logging.getLogger(__name__)

WHEEL_STATE_PATH = getattr(StateFiles, "WHEEL_STATE", None) or Path("state") / "wheel_state.json"
STRATEGY_ID = "wheel"

# Resolve repo root for logs (cwd-independent)
_REPO_ROOT = Path(__file__).resolve().parents[1]
_SYSTEM_EVENTS_PATH = _REPO_ROOT / "logs" / "system_events.jsonl"


def _wheel_system_event(event_type: str, symbol: Optional[str] = None, phase: Optional[str] = None, reason: Optional[str] = None, order_id: Optional[str] = None, premium: Optional[float] = None, **extra) -> None:
    """Append wheel lifecycle event to system_events.jsonl for visibility. Best-effort; never raises."""
    try:
        _SYSTEM_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        rec = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "subsystem": "wheel",
            "event_type": event_type,
            "strategy_id": STRATEGY_ID,
        }
        if symbol:
            rec["symbol"] = symbol
        if phase:
            rec["phase"] = phase
        if reason is not None:
            rec["reason"] = reason
        if order_id is not None:
            rec["order_id"] = order_id
        if premium is not None:
            rec["premium"] = round(premium, 2)
        rec.update(extra)
        with _SYSTEM_EVENTS_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
    except Exception as e:
        log.debug("Wheel system event write failed: %s", e)

# Default liquidity filters
MIN_OPEN_INTEREST = 10
MIN_VOLUME = 1


def _load_strategies_config() -> dict:
    """Load strategies.yaml."""
    path = Path("config") / "strategies.yaml"
    if not path.exists():
        return {"strategies": {"wheel": {"enabled": False}}}
    try:
        import yaml
        with path.open() as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        log.warning("Failed to load strategies.yaml: %s", e)
        return {"strategies": {"wheel": {"enabled": False}}}


def _load_universe(config: dict) -> List[str]:
    """Load wheel universe from universe_config or universe_source."""
    uc = config.get("universe_source") or config.get("universe_config", "config/universe_wheel.yaml")
    path = Path(uc)
    if not path.exists():
        return ["SPY", "QQQ", "DIA", "IWM"]
    try:
        import yaml
        with path.open() as f:
            data = yaml.safe_load(f) or {}
        return data.get("universe", {}).get("tickers", ["SPY", "QQQ", "DIA", "IWM"])
    except Exception as e:
        log.warning("Failed to load universe %s: %s", uc, e)
        return ["SPY", "QQQ", "DIA", "IWM"]


def _select_wheel_tickers(api, config: dict) -> Tuple[List[str], List[dict], List[dict]]:
    """
    Use universe selector if configured; else fall back to static universe.
    Returns (ticker_list, selected_metadata, all_candidates_metadata).
    """
    if not config.get("universe_max_candidates"):
        tickers = _load_universe(config)
        return tickers, [], []

    try:
        from strategies.wheel_universe_selector import select_wheel_candidates

        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        selected, all_scored = select_wheel_candidates(date_str, api, config)
        tickers = [r["symbol"] for r in selected]
        if not tickers:
            tickers = _load_universe(config)[: config.get("universe_max_candidates", 10)]
        return tickers, selected, all_scored
    except Exception as e:
        log.warning("Wheel universe selector failed, using static universe: %s", e)
        tickers = _load_universe(config)
        return tickers, [], []


def _load_wheel_state() -> dict:
    """Load wheel position/assignment tracking."""
    if not WHEEL_STATE_PATH.exists():
        return {"assigned_shares": {}, "csp_history": [], "cc_history": [], "open_csps": {}, "open_ccs": {}}
    try:
        return read_json(WHEEL_STATE_PATH, default={})
    except Exception:
        return {"assigned_shares": {}, "csp_history": [], "cc_history": [], "open_csps": {}, "open_ccs": {}}


def _save_wheel_state(state: dict) -> None:
    """Save wheel state."""
    WHEEL_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(WHEEL_STATE_PATH, state)


def _log_wheel_telemetry(
    symbol: str,
    side: str,
    phase: str,
    option_type: str,
    strike: Optional[float] = None,
    expiry: Optional[str] = None,
    dte: Optional[int] = None,
    delta_at_entry: Optional[float] = None,
    premium: Optional[float] = None,
    assigned: Optional[bool] = None,
    called_away: Optional[bool] = None,
    order_id: Optional[str] = None,
    qty: int = 1,
    price: Optional[float] = None,
    **extra,
) -> None:
    """Append wheel trade to telemetry."""
    rec = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "symbol": symbol,
        "strategy_id": STRATEGY_ID,
        "side": side,
        "phase": phase,
        "option_type": option_type,
        "qty": qty,
        "price": price,
        "order_id": order_id,
        **extra,
    }
    if strike is not None:
        rec["strike"] = strike
    if expiry is not None:
        rec["expiry"] = expiry
    if dte is not None:
        rec["dte"] = dte
    if delta_at_entry is not None:
        rec["delta_at_entry"] = delta_at_entry
    if premium is not None:
        rec["premium"] = premium
    if assigned is not None:
        rec["assigned"] = assigned
    if called_away is not None:
        rec["called_away"] = called_away
    append_jsonl(LogFiles.TELEMETRY, rec)


def _log_wheel_universe_telemetry(
    wheel_universe_candidates: list,
    wheel_universe_selected: list,
    wheel_universe_scores: dict,
) -> None:
    """Append wheel universe selection to telemetry."""
    rec = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "strategy_id": STRATEGY_ID,
        "event": "wheel_universe_selection",
        "wheel_universe_candidates": wheel_universe_candidates,
        "wheel_universe_selected": wheel_universe_selected,
        "wheel_universe_scores": wheel_universe_scores,
    }
    append_jsonl(LogFiles.TELEMETRY, rec)


def _emit_wheel_candidate_ranked(
    tickers: List[str],
    selected_meta: List[dict],
    first_placed_symbol: Optional[str],
    csp_placed: int,
    *,
    reason_none_override: Optional[str] = None,
) -> None:
    """Emit wheel_candidate_ranked system event: top 5 candidates, UW metrics, final chosen or reason none."""
    try:
        top_5 = selected_meta[:5] if selected_meta else [{"symbol": s, "uw_composite_score": None} for s in (tickers or [])[:5]]
        payload: Dict[str, Any] = {
            "top_5_symbols": [r.get("symbol") for r in top_5],
            "top_5_uw_scores": [r.get("uw_composite_score") for r in top_5],
            "top_5_liquidity": [r.get("liquidity_score") for r in top_5 if "liquidity_score" in r],
        }
        if first_placed_symbol:
            payload["chosen"] = first_placed_symbol
        else:
            payload["chosen"] = None
            payload["reason_none"] = reason_none_override if reason_none_override else ("no_order_placed" if csp_placed == 0 else "none_this_cycle")
        _wheel_system_event("wheel_candidate_ranked", **payload)
    except Exception as e:
        log.debug("wheel_candidate_ranked emit failed: %s", e)


def _alpaca_options_request(
    api,
    method: str,
    path: str,
    params: Optional[dict] = None,
) -> Optional[dict]:
    """Call Alpaca options API via REST. Uses api's credentials if available."""
    try:
        import requests
        base = getattr(api, "_base_url", None) or os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
        key = os.getenv("ALPACA_KEY") or os.getenv("ALPACA_API_KEY", "")
        secret = os.getenv("ALPACA_SECRET") or os.getenv("ALPACA_API_SECRET", "")
        url = base.rstrip("/") + path
        headers = {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret}
        r = requests.request(method, url, params=params, headers=headers, timeout=15)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        log.warning("Alpaca options request failed: %s", e)
    return None


def _get_option_contracts(
    api,
    underlying: str,
    opt_type: str,
    expiration_gte: str,
    expiration_lte: str,
) -> List[dict]:
    """Fetch option contracts from Alpaca."""
    data = _alpaca_options_request(
        api,
        "GET",
        "/v2/options/contracts",
        params={
            "underlying_symbols": underlying,
            "type": opt_type,
            "expiration_date_gte": expiration_gte,
            "expiration_date_lte": expiration_lte,
        },
    )
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "option_contracts" in data:
        return data["option_contracts"]
    return []


def _estimate_put_delta(strike: float, spot: float) -> float:
    """
    Rough delta estimate for puts: OTM puts have negative delta.
    -0.2 to -0.3 typically when strike ~2-5% below spot.
    TODO: Replace with real greeks when Alpaca Data API available.
    """
    if spot <= 0:
        return -0.25
    moneyness = strike / spot
    if moneyness >= 1.0:
        return -0.5
    if moneyness >= 0.98:
        return -0.35
    if moneyness >= 0.95:
        return -0.25
    if moneyness >= 0.90:
        return -0.15
    return -0.10


def _estimate_call_delta(strike: float, spot: float) -> float:
    """Rough call delta: 0.2-0.3 when strike slightly above spot."""
    if spot <= 0:
        return 0.25
    moneyness = strike / spot
    if moneyness <= 1.0:
        return 0.5
    if moneyness <= 1.02:
        return 0.35
    if moneyness <= 1.05:
        return 0.25
    if moneyness <= 1.10:
        return 0.15
    return 0.10


def _check_earnings(underlying: str, window_days: int) -> bool:
    """Skip if earnings within window. TODO: Integrate earnings calendar."""
    return False


def _check_iv_rank(underlying: str, min_iv_rank: float) -> bool:
    """Skip if IV rank < min. TODO: Integrate IV data; stub returns True (pass)."""
    return True


# -----------------------------------------------------------------------------
# Alpaca quote contract and spot resolution (single source of truth)
# -----------------------------------------------------------------------------


def normalize_alpaca_quote(raw_quote: Any) -> Optional[Dict[str, Any]]:
    """
    Normalize raw api.get_quote() return into a canonical dict.
    Never raises. Returns None only if raw_quote is None.
    """
    if raw_quote is None:
        return None
    out: Dict[str, Any] = {
        "ask": None,
        "bid": None,
        "last_trade": None,
        "source_fields_present": [],
    }
    fields_found: List[str] = []

    def _try_float(val: Any) -> Optional[float]:
        try:
            if val is None:
                return None
            v = float(val)
            return v if v > 0 else None
        except (TypeError, ValueError):
            return None

    # Ask: multiple possible attribute names (object or dict)
    for key in ("ap", "ask_price", "askprice", "AskPrice", "ask"):
        try:
            if hasattr(raw_quote, key):
                v = _try_float(getattr(raw_quote, key))
                if v is not None and out["ask"] is None:
                    out["ask"] = v
                    fields_found.append(key)
            elif isinstance(raw_quote, dict) and key in raw_quote:
                v = _try_float(raw_quote[key])
                if v is not None and out["ask"] is None:
                    out["ask"] = v
                    fields_found.append(key)
        except Exception:
            pass

    # Bid
    for key in ("bp", "bid_price", "bidprice", "BidPrice", "bid"):
        try:
            if hasattr(raw_quote, key):
                v = _try_float(getattr(raw_quote, key))
                if v is not None and out["bid"] is None:
                    out["bid"] = v
                    if key not in fields_found:
                        fields_found.append(key)
            elif isinstance(raw_quote, dict) and key in raw_quote:
                v = _try_float(raw_quote[key])
                if v is not None and out["bid"] is None:
                    out["bid"] = v
                    if key not in fields_found:
                        fields_found.append(key)
        except Exception:
            pass

    # Last trade (nested object or dict with price / p)
    try:
        lt = getattr(raw_quote, "last_trade", None) or (raw_quote.get("last_trade") if isinstance(raw_quote, dict) else None)
        if lt is not None:
            for pk in ("price", "p", "Price"):
                p = getattr(lt, pk, None) if not isinstance(lt, dict) else lt.get(pk)
                v = _try_float(p)
                if v is not None:
                    out["last_trade"] = v
                    if "last_trade" not in fields_found:
                        fields_found.append("last_trade")
                    break
    except Exception:
        pass

    out["source_fields_present"] = fields_found
    return out


def resolve_spot_from_market_data(
    normalized_quote: Optional[Dict[str, Any]],
    bar_close: Optional[float],
) -> Tuple[Optional[float], Optional[str]]:
    """
    Single place where spot is resolved. Strict order: ask > bid > last_trade > bar_close.
    Returns (spot_price, spot_source). spot_source is one of "ask"|"bid"|"last_trade"|"bar_close".
    Returns (None, None) if no valid price.
    """
    if normalized_quote:
        ask = normalized_quote.get("ask")
        if ask is not None and ask > 0:
            return (ask, "ask")
        bid = normalized_quote.get("bid")
        if bid is not None and bid > 0:
            return (bid, "bid")
        last_trade = normalized_quote.get("last_trade")
        if last_trade is not None and last_trade > 0:
            return (last_trade, "last_trade")
    if bar_close is not None and bar_close > 0:
        return (bar_close, "bar_close")
    return (None, None)


def _get_latest_bar_close(api: Any, symbol: str) -> Optional[float]:
    """Fetch most recent 1Min bar close. Never raises; returns None on failure."""
    try:
        bars = api.get_bars(symbol, "1Min", limit=1)
        if bars is None:
            return None
        if hasattr(bars, "df") and bars.df is not None and not bars.df.empty:
            df = bars.df
            close = df["c"].iloc[-1] if "c" in df.columns else df["close"].iloc[-1]
            return float(close) if close is not None else None
        if isinstance(bars, list) and bars:
            b = bars[-1]
            c = getattr(b, "c", None) or getattr(b, "close", None)
            if c is None and isinstance(b, dict):
                c = b.get("c") or b.get("close")
            return float(c) if c is not None else None
    except Exception as e:
        log.debug("get_bars(%s) for spot failed: %s", symbol, e)
    return None


def _resolve_spot(api: Any, symbol: str) -> Tuple[float, str]:
    """
    Resolve spot for symbol using normalized quote contract + bar fallback.
    Emits wheel_spot_resolved or wheel_spot_unavailable. Returns (spot, source) for caller;
    if unavailable, returns (0.0, "none") so no_spot skip is correct.
    """
    raw_quote = None
    try:
        raw_quote = api.get_quote(symbol)
    except Exception as e:
        log.debug("get_quote(%s) failed: %s", symbol, e)
    normalized = normalize_alpaca_quote(raw_quote)
    bar_close = _get_latest_bar_close(api, symbol)
    spot, source = resolve_spot_from_market_data(normalized, bar_close)

    quote_fields_present = (normalized.get("source_fields_present") or []) if normalized else []
    bar_used = source == "bar_close"
    bar_attempted = bar_close is not None

    if spot is not None and spot > 0 and source:
        _wheel_system_event(
            "wheel_spot_resolved",
            symbol=symbol,
            spot_price=round(spot, 2),
            spot_source=source,
            quote_fields_present=quote_fields_present,
            bar_used=bar_used,
        )
        return (spot, source)
    _wheel_system_event(
        "wheel_spot_unavailable",
        symbol=symbol,
        quote_fields_present=quote_fields_present,
        bar_attempted=bar_attempted,
    )
    return (0.0, "none")


def _run_csp_phase(api, config: dict, account_equity: float, buying_power: float, positions: list, open_orders: list) -> Tuple[int, Optional[str], List[dict]]:
    """Sell cash-secured puts. Returns (count placed, first placed symbol or None, selected_meta for telemetry)."""
    from capital.strategy_allocator import can_allocate

    csp_cfg = config.get("csp", {})
    risk_cfg = config.get("risk", {})
    max_pos = config.get("max_concurrent_positions") or config.get("max_positions", 5)
    per_position_frac_of_wheel = config.get("per_position_fraction_of_wheel_budget", 0.5)
    max_per_symbol = risk_cfg.get("max_positions_per_symbol", 2)
    avoid_earnings = risk_cfg.get("avoid_earnings_window_days", 3)
    min_iv = risk_cfg.get("min_iv_rank", 20)
    dte_min = csp_cfg.get("target_dte_min", 5)
    dte_max = csp_cfg.get("target_dte_max", 10)
    delta_min = csp_cfg.get("delta_min", -0.3)
    delta_max = csp_cfg.get("delta_max", -0.2)
    tickers, selected_meta, all_candidates = _select_wheel_tickers(api, config)
    state = _load_wheel_state()

    # Telemetry and logging: universe selection
    if selected_meta or all_candidates:
        log.info("Wheel universe selected: %s (from %d candidates)", tickers, len(all_candidates))
        _log_wheel_universe_telemetry(
            wheel_universe_candidates=[{"symbol": r["symbol"], "wheel_suitability_score": r.get("wheel_suitability_score"), "sector": r.get("sector"), "passed": r.get("passed"), "uw_composite_score": r.get("uw_composite_score")} for r in all_candidates],
            wheel_universe_selected=[r["symbol"] for r in selected_meta],
            wheel_universe_scores={r["symbol"]: {"liquidity_score": r.get("liquidity_score"), "iv_score": r.get("iv_score"), "spread_score": r.get("spread_score"), "wheel_suitability_score": r.get("wheel_suitability_score"), "uw_composite_score": r.get("uw_composite_score")} for r in selected_meta},
        )
    open_csps = state.get("open_csps", {})
    placed = 0
    first_placed_symbol: Optional[str] = None
    today = datetime.now(timezone.utc).date()
    exp_gte = (today + timedelta(days=dte_min)).strftime("%Y-%m-%d")
    exp_lte = (today + timedelta(days=dte_max)).strftime("%Y-%m-%d")
    total_wheel_positions = sum(len(v) if isinstance(v, list) else 1 for v in open_csps.values())
    per_symbol_count = {}
    for t in tickers:
        if placed >= max_pos or total_wheel_positions >= max_pos:
            _wheel_system_event("wheel_csp_skipped", symbol=t, reason="max_positions_reached")
            break
        if _check_earnings(t, avoid_earnings):
            log.info("Wheel CSP: skip %s (earnings window)", t)
            _wheel_system_event("wheel_csp_skipped", symbol=t, reason="earnings_window")
            continue
        if not _check_iv_rank(t, min_iv):
            log.info("Wheel CSP: skip %s (IV rank < %s)", t, min_iv)
            _wheel_system_event("wheel_csp_skipped", symbol=t, reason="iv_rank")
            continue
        sym_count = per_symbol_count.get(t, 0) + len(open_csps.get(t, []) or [])
        if sym_count >= max_per_symbol:
            _wheel_system_event("wheel_csp_skipped", symbol=t, reason="max_per_symbol")
            continue
        spot, spot_source = _resolve_spot(api, t)
        if spot <= 0:
            _wheel_system_event("wheel_csp_skipped", symbol=t, reason="no_spot")
            continue
        contracts = _get_option_contracts(api, t, "put", exp_gte, exp_lte)
        if not contracts and dte_max - dte_min < 18:
            exp_lte_wide = (today + timedelta(days=21)).strftime("%Y-%m-%d")
            contracts = _get_option_contracts(api, t, "put", exp_gte, exp_lte_wide)
        candidates = []
        for c in contracts:
            strike = float(c.get("strike_price", 0))
            if strike <= 0:
                continue
            delta_est = _estimate_put_delta(strike, spot)
            if not (delta_min <= delta_est <= delta_max):
                continue
            exp = c.get("expiration_date", "")
            if exp:
                try:
                    exp_dt = datetime.strptime(exp[:10], "%Y-%m-%d").date()
                    dte = (exp_dt - today).days
                except Exception:
                    dte = (dte_min + dte_max) // 2
            else:
                dte = (dte_min + dte_max) // 2
            candidates.append({
                "contract": c,
                "strike": strike,
                "delta_est": delta_est,
                "dte": dte,
                "symbol": c.get("symbol") or c.get("id", ""),
            })
        if not candidates:
            _wheel_system_event("wheel_csp_skipped", symbol=t, reason="no_contracts_in_range")
            continue
        candidates.sort(key=lambda x: (abs(x["delta_est"] - (delta_min + delta_max) / 2), abs(x["dte"] - (dte_min + dte_max) / 2)))
        chosen = candidates[0]
        occ_symbol = chosen["symbol"]
        if not occ_symbol:
            continue
        notional = chosen["strike"] * 100
        allowed, alloc_details = can_allocate("wheel", notional, account_equity, state)
        _wheel_system_event(
            "wheel_capital_check",
            wheel_budget=alloc_details["strategy_budget"],
            wheel_used=alloc_details["strategy_used"],
            wheel_available=alloc_details["strategy_available"],
            required_notional=alloc_details["required_notional"],
            decision="allow" if allowed else "block",
            reason=alloc_details["decision_reason"],
        )
        if not allowed:
            log.info("Wheel CSP: capital blocked (available=%.0f, required=%.0f)", alloc_details["strategy_available"], notional)
            _wheel_system_event("wheel_capital_blocked", symbol=t, wheel_budget=alloc_details["strategy_budget"], wheel_used=alloc_details["strategy_used"], wheel_available=alloc_details["strategy_available"], required_notional=notional, reason=alloc_details["decision_reason"])
            continue
        wheel_budget = alloc_details["strategy_budget"]
        per_position_limit = wheel_budget * per_position_frac_of_wheel
        position_limit_ok = notional <= per_position_limit
        _wheel_system_event(
            "wheel_position_limit_check",
            wheel_budget=round(wheel_budget, 2),
            per_position_limit=round(per_position_limit, 2),
            required_notional=round(notional, 2),
            decision="allow" if position_limit_ok else "block",
            reason="ok" if position_limit_ok else "per_position_limit_exceeded",
        )
        if not position_limit_ok:
            log.info("Wheel CSP: per-position limit for %s (notional=%.0f > limit=%.0f)", t, notional, per_position_limit)
            _wheel_system_event("wheel_position_limit_blocked", symbol=t, wheel_budget=round(wheel_budget, 2), per_position_limit=round(per_position_limit, 2), required_notional=round(notional, 2), reason="per_position_limit_exceeded")
            _wheel_system_event("wheel_csp_skipped", symbol=t, reason="per_position_limit")
            continue
        existing = [o for o in (open_orders or []) if getattr(o, "symbol", "") == occ_symbol]
        if existing:
            _wheel_system_event("wheel_csp_skipped", symbol=t, reason="existing_order")
            continue
        try:
            client_order_id = f"wheel-CSP-{t}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
            order = api.submit_order(
                symbol=occ_symbol,
                qty=1,
                side="sell",
                type="limit",
                time_in_force="day",
                limit_price=0.05,
                client_order_id=client_order_id,
            )
        except Exception as e:
            log.warning("Wheel CSP order failed for %s: %s", t, e)
            _wheel_system_event("wheel_order_failed", symbol=t, phase="CSP", reason=str(e)[:200])
            continue
        order_id = getattr(order, "id", None) or (order.get("id") if isinstance(order, dict) else None)
        _wheel_system_event("wheel_order_submitted", symbol=t, phase="CSP", order_id=str(order_id) if order_id else None)
        premium_filled: Optional[float] = None
        if order_id and hasattr(api, "get_order"):
            for _ in range(5):
                time.sleep(2)
                try:
                    o = api.get_order(order_id)
                    status = getattr(o, "status", None) or (o.get("status") if isinstance(o, dict) else None)
                    if str(status or "").lower() == "filled":
                        filled_avg = float(getattr(o, "filled_avg_price", 0) or 0)
                        if filled_avg > 0:
                            premium_filled = filled_avg * 100.0
                            _wheel_system_event("wheel_order_filled", symbol=t, phase="CSP", order_id=str(order_id), premium=premium_filled)
                        break
                except Exception:
                    pass
        _log_wheel_telemetry(
            symbol=t,
            side="sell",
            phase="CSP",
            option_type="put",
            strike=chosen["strike"],
            expiry=chosen["contract"].get("expiration_date"),
            dte=chosen["dte"],
            delta_at_entry=chosen["delta_est"],
            premium=premium_filled,
            order_id=str(order_id) if order_id else None,
            qty=1,
        )
        open_csps.setdefault(t, []).append({
            "symbol": occ_symbol,
            "strike": chosen["strike"],
            "expiry": chosen["contract"].get("expiration_date"),
            "order_id": order_id,
        })
        state["open_csps"] = open_csps
        _save_wheel_state(state)
        placed += 1
        total_wheel_positions += 1
        first_placed_symbol = first_placed_symbol or t
        # state["open_csps"] already updated above; next can_allocate will see new used
    return placed, first_placed_symbol, selected_meta


def _run_cc_phase(api, config: dict, account_equity: float, positions: list) -> int:
    """Sell covered calls on wheel-assigned shares. Returns count of orders placed."""
    cc_cfg = config.get("cc", {})
    state = _load_wheel_state()
    assigned = state.get("assigned_shares", {})
    if not assigned:
        return 0
    dte_min = cc_cfg.get("target_dte_min", 7)
    dte_max = cc_cfg.get("target_dte_max", 21)
    delta_min = cc_cfg.get("delta_min", 0.2)
    delta_max = cc_cfg.get("delta_max", 0.3)
    today = datetime.now(timezone.utc).date()
    exp_gte = (today + timedelta(days=dte_min)).strftime("%Y-%m-%d")
    exp_lte = (today + timedelta(days=dte_max)).strftime("%Y-%m-%d")
    placed = 0
    open_ccs = state.get("open_ccs", {})
    for symbol, lots in assigned.items():
        if not isinstance(lots, list):
            lots = [lots] if lots else []
        total_qty = sum(int(l.get("qty", 100)) for l in lots)
        if total_qty < 100:
            continue
        contracts_out = sum(1 for x in (open_ccs.get(symbol) or []) for _ in ([x] if isinstance(x, dict) else x))
        if contracts_out >= total_qty // 100:
            continue
        cost_basis = 0.0
        if lots:
            cb_sum = sum(float(l.get("cost_basis", l.get("strike", 0))) for l in lots)
            cost_basis = cb_sum / len(lots)
        spot, spot_source = _resolve_spot(api, symbol)
        if spot <= 0:
            continue
        call_contracts = _get_option_contracts(api, symbol, "call", exp_gte, exp_lte)
        candidates = []
        for c in call_contracts:
            strike = float(c.get("strike_price", 0))
            if strike < cost_basis:
                continue
            delta_est = _estimate_call_delta(strike, spot)
            if not (delta_min <= delta_est <= delta_max):
                continue
            exp = c.get("expiration_date", "")
            dte = (dte_min + dte_max) // 2
            if exp:
                try:
                    exp_dt = datetime.strptime(exp[:10], "%Y-%m-%d").date()
                    dte = (exp_dt - today).days
                except Exception:
                    pass
            candidates.append({
                "contract": c,
                "strike": strike,
                "delta_est": delta_est,
                "dte": dte,
                "symbol": c.get("symbol") or c.get("id", ""),
            })
        if not candidates:
            continue
        candidates.sort(key=lambda x: (abs(x["delta_est"] - (delta_min + delta_max) / 2), -x["strike"]))
        chosen = candidates[0]
        occ_symbol = chosen["symbol"]
        if not occ_symbol:
            continue
        try:
            client_order_id = f"wheel-CC-{symbol}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
            order = api.submit_order(
                symbol=occ_symbol,
                qty=1,
                side="sell",
                type="limit",
                time_in_force="day",
                limit_price=0.05,
                client_order_id=client_order_id,
            )
        except Exception as e:
            log.warning("Wheel CC order failed for %s: %s", symbol, e)
            continue
        order_id = getattr(order, "id", None) or (order.get("id") if isinstance(order, dict) else None)
        _log_wheel_telemetry(
            symbol=symbol,
            side="sell",
            phase="CC",
            option_type="call",
            strike=chosen["strike"],
            expiry=chosen["contract"].get("expiration_date"),
            dte=chosen["dte"],
            delta_at_entry=chosen["delta_est"],
            premium=None,
            order_id=str(order_id) if order_id else None,
            qty=1,
        )
        open_ccs.setdefault(symbol, []).append({
            "symbol": occ_symbol,
            "strike": chosen["strike"],
            "expiry": chosen["contract"].get("expiration_date"),
            "order_id": order_id,
        })
        state["open_ccs"] = open_ccs
        _save_wheel_state(state)
        placed += 1
    return placed


def run(api, config: dict) -> dict:
    """
    Run wheel strategy: CSP phase then CC phase.
    Regime is modifier-only; must never gate or block wheel entries.

    Args:
        api: Alpaca REST API (tradeapi.REST or compatible).
        config: Wheel config from strategies.yaml.

    Returns:
        Dict with orders_placed, csp_placed, cc_placed, errors.
    """
    result = {"orders_placed": 0, "csp_placed": 0, "cc_placed": 0, "errors": []}
    tickers = _load_universe(config)
    if config.get("universe_max_candidates"):
        tickers, _, _ = _select_wheel_tickers(api, config)
    _wheel_system_event("wheel_run_started", reason="ok", ticker_count=len(tickers))
    # Regime is modifier-only; never a gate. Log for audit.
    _regime_label = "unknown"
    try:
        for _path in [getattr(StateFiles, "REGIME_POSTURE_STATE", None), getattr(StateFiles, "REGIME_DETECTOR", None)]:
            if _path and _path.exists():
                _data = read_json(_path) or {}
                _regime_label = _data.get("regime_label") or _data.get("current_regime") or _data.get("regime") or "unknown"
                break
    except Exception:
        pass
    _wheel_system_event("wheel_regime_audit", regime_label=_regime_label, modifier_only=True)
    try:
        account = api.get_account()
        account_equity = float(getattr(account, "equity", 0) or 0)
        buying_power = float(getattr(account, "buying_power", 0) or 0)
    except Exception as e:
        result["errors"].append(f"account_fetch: {e}")
        _wheel_system_event("wheel_run_failed", reason="account_fetch", error=str(e)[:200])
        return result
    try:
        positions = api.list_positions() or []
    except Exception:
        positions = []
    try:
        open_orders = api.list_orders(status="open") if hasattr(api, "list_orders") else []
    except Exception:
        open_orders = []
    csp_placed, first_placed_symbol, selected_meta = _run_csp_phase(api, config, account_equity, buying_power, positions, open_orders)
    result["csp_placed"] = csp_placed
    result["orders_placed"] += csp_placed
    _emit_wheel_candidate_ranked(tickers, selected_meta, first_placed_symbol, csp_placed)
    cc_placed = _run_cc_phase(api, config, account_equity, positions)
    result["cc_placed"] = cc_placed
    result["orders_placed"] += cc_placed
    return result
