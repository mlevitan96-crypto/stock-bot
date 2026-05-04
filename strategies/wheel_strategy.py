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
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config.registry import Directories, StateFiles, read_json, atomic_write_json, append_jsonl, LogFiles

log = logging.getLogger(__name__)

WHEEL_STATE_PATH = getattr(StateFiles, "WHEEL_STATE", None) or Path("state") / "wheel_state.json"
STRATEGY_ID = "wheel"
WHEEL_EVENT_SCHEMA_VERSION = 1

# Resolve repo root for logs (cwd-independent)
_REPO_ROOT = Path(__file__).resolve().parents[1]
_SYSTEM_EVENTS_PATH = _REPO_ROOT / "logs" / "system_events.jsonl"

# Idempotency: max recent_orders to keep in state (prune older)
RECENT_ORDERS_MAX = 200


def build_wheel_client_order_id(cycle_id: Optional[str], underlying_symbol: str, side: str, expiry: Optional[str], strike: float, qty: int) -> str:
    """Stable, short client_order_id for idempotency. Format: WHEEL|<cycle8>|<SYM>|<SIDE>|<YYYYMMDD>|<STRIKE>|<QTY>."""
    cycle8 = (cycle_id or "")[:8].replace("-", "") or "00000000"
    sym = (underlying_symbol or "XXX")[:6].upper()
    side_short = "CSP" if side.upper() in ("CSP", "PUT", "SELL") else "CC"
    if expiry:
        try:
            ymd = expiry[:10].replace("-", "") if len(expiry) >= 10 else "00000000"
        except Exception:
            ymd = "00000000"
    else:
        ymd = datetime.now(timezone.utc).strftime("%Y%m%d")
    strike_str = str(int(strike)) if strike == int(strike) else f"{strike:.1f}"
    return f"WHEEL|{cycle8}|{sym}|{side_short}|{ymd}|{strike_str}|{qty}"


def idempotency_skip(state: dict, client_order_id: str) -> bool:
    """True if we should skip submission (already submitted or filled). Used by tests and inlined check."""
    recent = state.get("recent_orders") or {}
    if not isinstance(recent, dict):
        return False
    entry = recent.get(client_order_id)
    if not isinstance(entry, dict):
        return False
    return (entry.get("status") or "") in ("submitted", "filled")


def _wheel_system_event(event_type: str, symbol: Optional[str] = None, phase: Optional[str] = None, reason: Optional[str] = None, order_id: Optional[str] = None, premium: Optional[float] = None, **extra) -> None:
    """Append wheel lifecycle event to system_events.jsonl for visibility. Best-effort; never raises. All events include event_schema_version."""
    try:
        _SYSTEM_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        rec = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "subsystem": "wheel",
            "event_type": event_type,
            "strategy_id": STRATEGY_ID,
            "event_schema_version": WHEEL_EVENT_SCHEMA_VERSION,
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


def _notify_wheel_critical_abort(reason: str, detail: str, cycle_id: Optional[str] = None) -> None:
    """Telegram pager for fail-closed wheel cycle aborts (dedupe + cooldown in critical_alert)."""
    try:
        from src.critical_alert import send_critical_wheel_alert

        body = (detail or "")[:1500]
        if cycle_id:
            body = f"cycle_id={cycle_id}\n{body}"
        send_critical_wheel_alert(
            f"Wheel cycle abort: {reason}",
            body,
            dedupe_key=f"wheel_abort:{reason}",
        )
    except Exception:
        pass


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


def _wheel_state_defaults() -> Dict[str, Any]:
    return {
        "assigned_shares": {},
        "csp_history": [],
        "cc_history": [],
        "open_csps": {},
        "open_ccs": {},
        "last_cycle_id_processed": None,
        "recent_orders": {},
    }


def _backup_wheel_state_raw(raw_text: str, reason: str) -> None:
    """Write corrupt wheel_state.json body to a timestamped sibling file (never guess broker truth)."""
    try:
        WHEEL_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        ts = int(time.time())
        bak = WHEEL_STATE_PATH.parent / f"wheel_state.corrupt.{ts}.json"
        bak.write_text(raw_text, encoding="utf-8")
        log.warning("wheel_state corrupt snapshot written: %s (%s)", bak, reason)
    except Exception as e:
        log.warning("wheel_state backup failed: %s", e)


def _heal_wheel_state_dict(data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Normalize wheel_state.json shape in-memory. Does not invent positions.

    Returns (healed_state, repair_tags). Any non-dict leg entries are dropped (reconcile uses broker).
    """
    repairs: List[str] = []
    default = _wheel_state_defaults()
    out = default.copy()
    known = set(default.keys())
    extras = {k: v for k, v in data.items() if k not in known}

    # assigned_shares: symbol -> list[dict]
    ass = data.get("assigned_shares") or default["assigned_shares"]
    if not isinstance(ass, dict):
        repairs.append("assigned_shares_reset_dict")
        out["assigned_shares"] = {}
    else:
        fixed_a: Dict[str, Any] = {}
        for sym, lots in ass.items():
            sk = str(sym).upper()
            if isinstance(lots, list):
                fl = [x for x in lots if isinstance(x, dict)]
                if len(fl) != len(lots):
                    repairs.append(f"assigned_pruned_{sk}")
                fixed_a[sk] = fl
            elif isinstance(lots, dict):
                fixed_a[sk] = [lots]
            else:
                repairs.append(f"assigned_drop_{sk}")
        out["assigned_shares"] = fixed_a

    def _coerce_leg_map(raw: Any, label: str) -> Dict[str, List[dict]]:
        if not isinstance(raw, dict):
            repairs.append(f"{label}_reset_dict")
            return {}
        out_m: Dict[str, List[dict]] = {}
        for sym, legs in raw.items():
            sk = str(sym).upper()
            if isinstance(legs, list):
                fl = [x for x in legs if isinstance(x, dict)]
                if len(fl) != len(legs):
                    repairs.append(f"{label}_pruned_{sk}")
                out_m[sk] = fl
            elif isinstance(legs, dict):
                out_m[sk] = [legs]
            else:
                repairs.append(f"{label}_drop_{sk}")
        return out_m

    out["open_csps"] = _coerce_leg_map(data.get("open_csps") or {}, "open_csps")
    out["open_ccs"] = _coerce_leg_map(data.get("open_ccs") or {}, "open_ccs")

    for hist_key in ("csp_history", "cc_history"):
        h = data.get(hist_key) or default[hist_key]
        if not isinstance(h, list):
            repairs.append(f"{hist_key}_reset_list")
            out[hist_key] = []
        else:
            hl = [x for x in h if isinstance(x, dict)]
            if len(hl) != len(h):
                repairs.append(f"{hist_key}_pruned")
            out[hist_key] = hl

    ro = data.get("recent_orders") or default["recent_orders"]
    if not isinstance(ro, dict):
        repairs.append("recent_orders_reset_dict")
        out["recent_orders"] = {}
    else:
        out["recent_orders"] = {str(k): v for k, v in ro.items() if isinstance(v, dict)}

    lcp = data.get("last_cycle_id_processed", default["last_cycle_id_processed"])
    out["last_cycle_id_processed"] = lcp if lcp is None or isinstance(lcp, str) else str(lcp)

    out.update(extras)
    return out, repairs


def _load_wheel_state() -> dict:
    """
    Load wheel position/assignment tracking with self-healing for malformed JSON or bad shapes.

    - Unreadable JSON: backup raw body, replace file with safe defaults, emit events + optional pager.
    - Bad shapes: heal + persist (broker reconciliation remains authoritative; we never invent legs).
    """
    default = _wheel_state_defaults()
    if not WHEEL_STATE_PATH.exists():
        return default.copy()

    raw_text = ""
    try:
        raw_text = WHEEL_STATE_PATH.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        log.warning("wheel_state read failed: %s", e)
        return default.copy()

    if not raw_text.strip():
        return default.copy()

    parsed: Any = None
    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as e:
        _backup_wheel_state_raw(raw_text, "json_decode")
        try:
            atomic_write_json(WHEEL_STATE_PATH, default.copy())
        except Exception as werr:
            log.warning("wheel_state reset write failed: %s", werr)
        _wheel_system_event("wheel_state_recovered", reason="json_decode_error", detail=str(e)[:200])
        try:
            from src.critical_alert import send_critical_wheel_alert

            send_critical_wheel_alert(
                "wheel_state.json unreadable",
                f"JSON decode error; file reset to safe defaults. Backup written under state/. Error: {e}"[:1800],
                dedupe_key="wheel_state_json_decode",
            )
        except Exception:
            pass
        return default.copy()

    if not isinstance(parsed, dict):
        _backup_wheel_state_raw(raw_text, "non_dict_root")
        try:
            atomic_write_json(WHEEL_STATE_PATH, default.copy())
        except Exception as werr:
            log.warning("wheel_state reset write failed: %s", werr)
        _wheel_system_event("wheel_state_recovered", reason="non_dict_root")
        try:
            from src.critical_alert import send_critical_wheel_alert

            send_critical_wheel_alert(
                "wheel_state.json invalid root",
                "Root JSON value was not an object; reset to safe defaults. Backup under state/.",
                dedupe_key="wheel_state_non_dict",
            )
        except Exception:
            pass
        return default.copy()

    healed, repairs = _heal_wheel_state_dict(parsed)
    if repairs:
        try:
            _backup_wheel_state_raw(raw_text, "pre_heal_shape")
            atomic_write_json(WHEEL_STATE_PATH, healed)
            _wheel_system_event("wheel_state_self_healed", repairs=repairs[:50])
            try:
                from src.critical_alert import send_critical_wheel_alert

                send_critical_wheel_alert(
                    "wheel_state.json self-healed",
                    "Repairs: " + "; ".join(repairs[:40]),
                    dedupe_key="wheel_state_shape_heal",
                )
            except Exception:
                pass
        except Exception as werr:
            log.warning("wheel_state heal persist failed: %s", werr)
    return healed


def _prune_recent_orders(state: dict) -> None:
    """Keep only last RECENT_ORDERS_MAX entries by created_at to avoid unbounded growth."""
    recent = state.get("recent_orders") or {}
    if not isinstance(recent, dict) or len(recent) <= RECENT_ORDERS_MAX:
        return
    by_created = [(cid, (v.get("created_at") or "")) for cid, v in recent.items() if isinstance(v, dict)]
    by_created.sort(key=lambda x: x[1], reverse=True)
    keep = {cid for cid, _ in by_created[:RECENT_ORDERS_MAX]}
    state["recent_orders"] = {k: v for k, v in recent.items() if k in keep}


def _save_wheel_state(state: dict, *, cycle_id: Optional[str] = None, change_type: Optional[str] = None, symbol: Optional[str] = None, previous_summary: Optional[dict] = None, new_summary: Optional[dict] = None) -> None:
    """Save wheel state and optionally emit wheel_position_state_changed."""
    WHEEL_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if cycle_id is not None:
        state["last_cycle_id_processed"] = cycle_id
    _prune_recent_orders(state)
    atomic_write_json(WHEEL_STATE_PATH, state)
    if change_type and (previous_summary is not None or new_summary is not None):
        _wheel_system_event(
            "wheel_position_state_changed",
            cycle_id=cycle_id,
            symbol=symbol,
            change_type=change_type,
            previous_state_summary=previous_summary or {},
            new_state_summary=new_summary or {},
        )


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
    cycle_id: Optional[str] = None,
) -> None:
    """Emit wheel_candidate_ranked system event: top 5 candidates, UW metrics, final chosen or reason none."""
    try:
        top_5 = selected_meta[:5] if selected_meta else [{"symbol": s, "uw_composite_score": None} for s in (tickers or [])[:5]]
        payload: Dict[str, Any] = {
            "top_5_symbols": [r.get("symbol") for r in top_5],
            "top_5_uw_scores": [r.get("uw_composite_score") for r in top_5],
            "top_5_liquidity": [r.get("liquidity_score") for r in top_5 if "liquidity_score" in r],
        }
        if cycle_id:
            payload["cycle_id"] = cycle_id
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
    """True => skip CSP (earnings inside window). UW-backed; fail-closed when data missing."""
    try:
        from src.options_engine import should_skip_for_earnings

        return should_skip_for_earnings(underlying, window_days)
    except Exception as e:
        log.warning("Wheel earnings gate failed for %s: %s", underlying, e)
        return True


def _check_iv_rank(underlying: str, min_iv_rank: float) -> bool:
    """True => IV rank OK (>= min). Fail-closed on UW errors."""
    try:
        from src.options_engine import iv_rank_at_least

        return iv_rank_at_least(underlying, float(min_iv_rank))
    except Exception as e:
        log.warning("Wheel IV rank gate failed for %s: %s", underlying, e)
        return False


# -----------------------------------------------------------------------------
# Alpaca quote contract and spot resolution (single source of truth)
# -----------------------------------------------------------------------------


def _fetch_alpaca_option_quote_via_data_rest(occ_symbol: str) -> Optional[Any]:
    """
    OCC option NBBO from **Alpaca Market Data** ``GET /v1beta1/options/quotes/latest``.

    Trading REST ``get_latest_quote(OCC)`` is for **equities**; OCC symbols do not resolve there,
    which produced persistent ``no_quote`` for wheel CSP pricing. Data host defaults to
    ``https://data.alpaca.markets`` (override with ``ALPACA_DATA_BASE_URL``).
    """
    from types import SimpleNamespace

    import requests

    occ = str(occ_symbol).strip().upper()
    if not occ:
        return None
    base = (os.getenv("ALPACA_DATA_BASE_URL") or "https://data.alpaca.markets").rstrip("/")
    key = os.getenv("ALPACA_KEY") or os.getenv("ALPACA_API_KEY") or os.getenv("APCA_API_KEY_ID") or ""
    secret = os.getenv("ALPACA_SECRET") or os.getenv("ALPACA_API_SECRET_KEY") or os.getenv("ALPACA_API_SECRET") or ""
    if not key or not secret:
        log.debug("option Data API: missing APCA keys in environment")
        return None
    url = f"{base}/v1beta1/options/quotes/latest"
    headers = {"APCA-API-KEY-ID": key.strip(), "APCA-API-SECRET-KEY": secret.strip()}
    for feed in ("opra", "indicative"):
        try:
            r = requests.get(url, params={"symbols": occ, "feed": feed}, headers=headers, timeout=20)
            if r.status_code != 200:
                log.debug(
                    "option quotes latest HTTP %s feed=%s occ=%s snippet=%s",
                    r.status_code,
                    feed,
                    occ,
                    (r.text or "")[:160],
                )
                continue
            body = r.json() if r.text else {}
            quotes = (body or {}).get("quotes") or {}
            q = quotes.get(occ)
            if not isinstance(q, dict):
                continue
            bp, ap = q.get("bp"), q.get("ap")
            if bp is None and ap is None:
                continue
            return SimpleNamespace(
                bp=bp,
                ap=ap,
                bid_price=bp,
                ask_price=ap,
                bidsize=q.get("bs"),
                asksize=q.get("as"),
            )
        except Exception as e:
            log.debug("option quotes latest error feed=%s occ=%s: %s", feed, occ, e)
    return None


def fetch_alpaca_latest_quote(api: Any, symbol: str) -> Optional[Any]:
    """
    Fetch a quote-like object for **equities** (trading REST) or **options OCC** (Market Data API).

    OCC symbols use ``GET /v1beta1/options/quotes/latest`` on ``data.alpaca.markets`` — not
    ``get_latest_quote``, which targets stock symbols on the trading API.
    """
    if not symbol:
        return None
    sym = str(symbol).strip()
    if not sym:
        return None

    try:
        from src.options_engine import occ_strike_price

        is_occ = occ_strike_price(sym) is not None
    except Exception:
        is_occ = False

    if is_occ:
        oq = _fetch_alpaca_option_quote_via_data_rest(sym)
        if oq is not None:
            return oq
        log.warning(
            "Wheel: option Data API returned no NBBO for %s (OPRA subscription or indicative feed; check keys and ALPACA_DATA_BASE_URL)",
            sym,
        )
        return None

    if not api:
        return None
    try:
        fn = getattr(api, "get_latest_quote", None)
        if callable(fn):
            return fn(sym)
    except Exception as e:
        log.debug("get_latest_quote(%s): %s", sym, e)
    try:
        fn = getattr(api, "get_quote", None)
        if callable(fn):
            return fn(sym)
    except Exception as e:
        log.debug("get_quote(%s): %s", sym, e)
    return None


def submit_wheel_broker_order(
    api: Any,
    order_executor: Any,
    *,
    symbol: str,
    qty: int,
    side: str,
    order_type: str,
    time_in_force: str,
    limit_price: Optional[float],
    client_order_id: Optional[str],
    caller: str,
) -> Any:
    """
    Submit a wheel options order via AlpacaExecutor._submit_order_guarded when ``order_executor`` is set
    (audit guard, paper safety, submit_order_called telemetry). Otherwise raw ``api.submit_order``.
    """
    if order_executor is not None and hasattr(order_executor, "_submit_order_guarded"):
        return order_executor._submit_order_guarded(
            symbol=symbol,
            qty=qty,
            side=side,
            order_type=order_type,
            time_in_force=time_in_force,
            limit_price=limit_price,
            client_order_id=client_order_id,
            caller=caller,
        )
    return api.submit_order(
        symbol=symbol,
        qty=qty,
        side=side,
        type=order_type,
        time_in_force=time_in_force,
        limit_price=limit_price,
        client_order_id=client_order_id,
    )


def normalize_alpaca_quote(raw_quote: Any) -> Optional[Dict[str, Any]]:
    """
    Normalize raw quote object (``get_latest_quote`` / legacy ``get_quote``) into a canonical dict.
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


# NBBO wider than this fraction of mid: do not use ask alone for spot (moneyness skew); use mid instead.
WHEEL_SPOT_WIDE_NBBO_FRAC = float(os.getenv("WHEEL_SPOT_WIDE_NBBO_FRAC", "0.05") or "0.05")


def resolve_spot_from_market_data(
    normalized_quote: Optional[Dict[str, Any]],
    bar_close: Optional[float],
    *,
    wide_nbbo_frac: Optional[float] = None,
) -> Tuple[Optional[float], Optional[str]]:
    """
    Resolve underlying spot for wheel strike / delta heuristics.

    When both bid and ask exist and (ask-bid)/mid > wide_nbbo_frac, returns **mid** (``mid_nbbo_wide``)
    instead of ask so wide markets do not inflate spot. Otherwise: ask, bid, last_trade, bar_close.
    """
    frac = float(wide_nbbo_frac if wide_nbbo_frac is not None else WHEEL_SPOT_WIDE_NBBO_FRAC)
    if normalized_quote:
        ask = normalized_quote.get("ask")
        bid = normalized_quote.get("bid")
        last_trade = normalized_quote.get("last_trade")
        if (
            ask is not None
            and ask > 0
            and bid is not None
            and bid > 0
        ):
            mid = (ask + bid) / 2.0
            if mid > 0 and (ask - bid) / mid > frac:
                return (mid, "mid_nbbo_wide")
        if ask is not None and ask > 0:
            return (ask, "ask")
        if bid is not None and bid > 0:
            return (bid, "bid")
        if last_trade is not None and last_trade > 0:
            return (last_trade, "last_trade")
    if bar_close is not None and bar_close > 0:
        return (bar_close, "bar_close")
    return (None, None)


def resolve_option_short_sell_limit_per_share(
    api: Any,
    occ_symbol: str,
    *,
    min_limit: float = 0.01,
) -> Tuple[Optional[float], str, str]:
    """
    Discover limit price (per share) for sell-to-open option orders.

    Anchors to **bid** when present (natural side for receiving premium on a sell).
    Falls back to discounted last trade, then discounted ask. No broker submit here.

    Returns (limit_or_none, price_source, fail_reason). fail_reason empty when limit is set.
    """
    try:
        raw = fetch_alpaca_latest_quote(api, occ_symbol)
    except Exception as e:
        log.warning("Wheel CSP: pricing failed for %s: %s", occ_symbol, e)
        return None, "", "quote_error"
    if raw is None:
        log.warning("Wheel CSP: pricing failed for %s (no quote from Alpaca)", occ_symbol)
        return None, "", "no_quote"
    n = normalize_alpaca_quote(raw)
    if not n:
        log.warning("Wheel CSP: pricing failed for %s (unparseable quote)", occ_symbol)
        return None, "", "no_quote"
    bid = n.get("bid")
    ask = n.get("ask")
    lt = n.get("last_trade")
    if bid is not None and float(bid) > 0:
        lim = max(float(min_limit), round(float(bid), 2))
        return lim, "bid", ""
    if lt is not None and float(lt) > 0:
        lim = max(float(min_limit), round(float(lt) * 0.99, 2))
        return lim, "last_trade_discount", ""
    if ask is not None and float(ask) > 0:
        lim = max(float(min_limit), round(float(ask) * 0.95, 2))
        return lim, "ask_discount", ""
    return None, "", "no_option_price"


def _poll_wheel_order_status(
    api: Any,
    order_id: str,
    *,
    max_rounds: int = 5,
    sleep_sec: float = 2.0,
) -> Tuple[str, float, int]:
    """Poll Alpaca order until terminal-ish state. Returns (status_lower, filled_avg_price, filled_qty)."""
    last_st = "unknown"
    last_fap = 0.0
    last_fq = 0
    for _ in range(max(1, int(max_rounds))):
        time.sleep(float(sleep_sec))
        try:
            o = api.get_order(order_id)
            last_st = str(getattr(o, "status", None) or (o.get("status") if isinstance(o, dict) else "") or "").lower()
            last_fq = int(float(getattr(o, "filled_qty", 0) or (o.get("filled_qty", 0) if isinstance(o, dict) else 0) or 0))
            last_fap = float(getattr(o, "filled_avg_price", 0) or (o.get("filled_avg_price", 0) if isinstance(o, dict) else 0) or 0)
            if last_st == "filled" or last_fq >= 1:
                return last_st, last_fap, last_fq
            if last_st in ("canceled", "cancelled", "expired", "rejected", "done_for_day"):
                return last_st, last_fap, last_fq
        except Exception:
            pass
    return "timeout", last_fap, last_fq


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
        raw_quote = fetch_alpaca_latest_quote(api, symbol)
    except Exception as e:
        log.warning("Wheel spot: pricing failed for %s: %s", symbol, e)
    if raw_quote is None:
        log.warning("Wheel spot: pricing unavailable for %s (no quote; bar fallback if any)", symbol)
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


def _config_snapshot_for_audit(config: dict) -> dict:
    """Key config values for decision_context (no secrets)."""
    csp = config.get("csp", {})
    risk = config.get("risk", {})
    cap = _load_strategies_config().get("capital_allocation", {})
    wheel_cap = (cap.get("strategies") or {}).get("wheel", {})
    return {
        "allocation_pct": wheel_cap.get("allocation_pct", 25),
        "per_position_fraction_of_wheel_budget": config.get("per_position_fraction_of_wheel_budget", 0.5),
        "max_concurrent_positions": config.get("max_concurrent_positions") or config.get("max_positions", 5),
        "delta_min": csp.get("delta_min", -0.3),
        "delta_max": csp.get("delta_max", -0.2),
        "dte_min": csp.get("target_dte_min", 5),
        "dte_max": csp.get("target_dte_max", 10),
        "avoid_earnings_window_days": risk.get("avoid_earnings_window_days", 21),
        "max_sector_notional_fraction": risk.get("max_sector_notional_fraction", 0.25),
        "require_cash_secured": risk.get("require_cash_secured", True),
        "allow_margin_account": risk.get("allow_margin_account", False),
        "avoid_ex_dividend_days": risk.get("avoid_ex_dividend_days", 0),
        "max_rsi_for_csp_entry": risk.get("max_rsi_for_csp_entry", 70),
    }


def _run_csp_phase(
    api,
    config: dict,
    account_equity: float,
    buying_power: float,
    positions: list,
    open_orders: list,
    *,
    cycle_id: Optional[str] = None,
    tickers_override: Optional[List[str]] = None,
    selected_meta_override: Optional[List[dict]] = None,
    all_candidates_override: Optional[List[dict]] = None,
    account_fields: Optional[Dict[str, Any]] = None,
    order_executor: Any = None,
) -> Tuple[int, Optional[str], List[dict]]:
    """Sell cash-secured puts. Returns (count placed, first placed symbol or None, selected_meta for telemetry)."""
    from capital.strategy_allocator import can_allocate

    csp_cfg = config.get("csp", {})
    risk_cfg = config.get("risk", {})
    max_pos = config.get("max_concurrent_positions") or config.get("max_positions", 5)
    per_position_frac_of_wheel = config.get("per_position_fraction_of_wheel_budget", 0.5)
    max_per_symbol = risk_cfg.get("max_positions_per_symbol", 2)
    avoid_earnings = risk_cfg.get("avoid_earnings_window_days", 21)
    min_iv = risk_cfg.get("min_iv_rank", 50)
    put_wall_min_oi = int(risk_cfg.get("put_wall_min_oi", 5000) or 5000)
    min_credit_usd = float(risk_cfg.get("min_credit_usd", 0) or 0)
    max_sector_frac = float(risk_cfg.get("max_sector_notional_fraction", 0.25) or 0.25)
    avoid_ex_div = int(risk_cfg.get("avoid_ex_dividend_days", 0) or 0)
    require_cash_secured = bool(risk_cfg.get("require_cash_secured", True))
    allow_margin_account = bool(risk_cfg.get("allow_margin_account", False))
    max_rsi_csp = float(risk_cfg.get("max_rsi_for_csp_entry", 70) or 70)
    dte_min = csp_cfg.get("target_dte_min", 5)
    dte_max = csp_cfg.get("target_dte_max", 10)
    delta_min = csp_cfg.get("delta_min", -0.3)
    delta_max = csp_cfg.get("delta_max", -0.2)
    if tickers_override is not None and selected_meta_override is not None:
        tickers = tickers_override
        selected_meta = selected_meta_override
        all_candidates = all_candidates_override or []
    else:
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
    for rank, t in enumerate(tickers):
        uw_score = None
        if rank < len(selected_meta) and isinstance(selected_meta[rank], dict):
            uw_score = selected_meta[rank].get("uw_composite_score")
        def _emit_candidate_evaluated(next_step: str, skip_reason: Optional[str] = None, **kw: Any) -> None:
            payload: Dict[str, Any] = {"cycle_id": cycle_id, "symbol": t, "rank": rank, "uw_score": uw_score, "next_step": next_step}
            if skip_reason:
                payload["skip_reason"] = skip_reason
            payload.update(kw)
            _wheel_system_event("wheel_candidate_evaluated", **payload)

        if placed >= max_pos or total_wheel_positions >= max_pos:
            _wheel_system_event("wheel_csp_skipped", symbol=t, reason="max_positions_reached")
            _emit_candidate_evaluated("skip", "max_positions_reached")
            break
        try:
            from src.options_engine import is_wheel_csp_underlying_eligible

            if not is_wheel_csp_underlying_eligible(t):
                _wheel_system_event("wheel_csp_skipped", symbol=t, reason="not_wheel_eligible")
                _emit_candidate_evaluated("skip", "not_wheel_eligible")
                continue
        except Exception as e:
            log.warning("Wheel SP100 gate import failed: %s", e)
            _wheel_system_event("wheel_csp_skipped", symbol=t, reason="sp100_gate_error")
            _emit_candidate_evaluated("skip", "sp100_gate_error")
            continue
        if _check_earnings(t, avoid_earnings):
            log.info("Wheel CSP: skip %s (earnings window)", t)
            _wheel_system_event("wheel_csp_skipped", symbol=t, reason="earnings_window")
            _emit_candidate_evaluated("skip", "earnings_window")
            continue
        if not _check_iv_rank(t, min_iv):
            log.info("Wheel CSP: skip %s (IV rank < %s)", t, min_iv)
            _wheel_system_event("wheel_csp_skipped", symbol=t, reason="iv_rank")
            _emit_candidate_evaluated("skip", "iv_rank")
            continue
        if max_rsi_csp > 0:
            try:
                from src.options_engine import should_veto_csp_rsi_overbought

                rsi_veto, rsi_detail = should_veto_csp_rsi_overbought(api, t, max_rsi_csp)
                if rsi_veto:
                    _wheel_system_event("wheel_csp_skipped", symbol=t, reason="rsi_overbought", rsi_detail=rsi_detail)
                    _emit_candidate_evaluated("skip", "rsi_overbought", rsi_detail=rsi_detail)
                    continue
            except Exception as e:
                log.warning("Wheel RSI gate failed for %s: %s", t, e)
        if avoid_ex_div > 0:
            try:
                from src.wheel_risk_gates import should_skip_dividend_ex_zone

                if should_skip_dividend_ex_zone(t, avoid_ex_div):
                    _wheel_system_event("wheel_csp_skipped", symbol=t, reason="dividend_ex_zone")
                    _emit_candidate_evaluated("skip", "dividend_ex_zone")
                    continue
            except Exception as e:
                log.warning("Wheel dividend gate failed for %s: %s", t, e)
                _wheel_system_event("wheel_csp_skipped", symbol=t, reason="dividend_gate_error")
                _emit_candidate_evaluated("skip", "dividend_gate_error")
                continue
        sym_count = per_symbol_count.get(t, 0) + len(open_csps.get(t, []) or [])
        if sym_count >= max_per_symbol:
            _wheel_system_event("wheel_csp_skipped", symbol=t, reason="max_per_symbol")
            _emit_candidate_evaluated("skip", "max_per_symbol")
            continue
        spot, spot_source = _resolve_spot(api, t)
        if spot <= 0:
            _wheel_system_event("wheel_csp_skipped", symbol=t, reason="no_spot")
            _emit_candidate_evaluated("skip", "no_spot", spot_price=0, spot_source="none")
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
            _emit_candidate_evaluated("skip", "no_contracts_in_range", spot_price=round(spot, 2), spot_source=spot_source, required_notional=0)
            continue
        candidates.sort(key=lambda x: (abs(x["delta_est"] - (delta_min + delta_max) / 2), abs(x["dte"] - (dte_min + dte_max) / 2)))
        chosen = candidates[0]
        occ_symbol = chosen["symbol"]
        if not occ_symbol:
            continue
        csp_put_wall_strike: Optional[float] = None
        try:
            from src.options_engine import institutional_put_floor_ok, premium_meets_min_credit

            ok_wall, wall_snap = institutional_put_floor_ok(t, spot, chosen["strike"], min_wall_oi=put_wall_min_oi)
            if not ok_wall:
                _wheel_system_event(
                    "wheel_csp_skipped",
                    symbol=t,
                    reason="put_wall",
                    wall_strike=wall_snap.wall_strike,
                    wall_oi=wall_snap.wall_oi,
                    wall_reason=wall_snap.reason,
                )
                _emit_candidate_evaluated(
                    "skip",
                    "put_wall",
                    spot_price=round(spot, 2),
                    spot_source=spot_source,
                    wall_strike=wall_snap.wall_strike,
                    wall_oi=wall_snap.wall_oi,
                )
                continue
            ws = getattr(wall_snap, "wall_strike", None)
            if ws is not None:
                try:
                    csp_put_wall_strike = float(ws)
                except (TypeError, ValueError):
                    csp_put_wall_strike = None
        except Exception as e:
            log.warning("Wheel put-wall gate failed for %s: %s", t, e)
            _wheel_system_event("wheel_csp_skipped", symbol=t, reason="put_wall_gate_error")
            _emit_candidate_evaluated("skip", "put_wall_gate_error")
            continue
        limit_price, opt_px_src, opt_px_fail = resolve_option_short_sell_limit_per_share(api, occ_symbol)
        if limit_price is None or limit_price <= 0:
            _wheel_system_event(
                "wheel_csp_skipped",
                symbol=t,
                reason="no_option_quote",
                option_symbol=occ_symbol,
                option_price_fail=opt_px_fail,
            )
            _emit_candidate_evaluated(
                "skip",
                "no_option_quote",
                option_symbol=occ_symbol,
                option_price_fail=opt_px_fail,
            )
            continue
        try:
            if not premium_meets_min_credit(limit_price, min_credit_usd):
                _wheel_system_event(
                    "wheel_csp_skipped",
                    symbol=t,
                    reason="dust_floor",
                    min_credit_usd=min_credit_usd,
                    limit_price=limit_price,
                )
                _emit_candidate_evaluated("skip", "dust_floor", min_credit_usd=min_credit_usd, limit_price=limit_price)
                continue
        except Exception as e:
            log.warning("Wheel dust floor check failed for %s: %s", t, e)
            _emit_candidate_evaluated("skip", "dust_floor_gate_error")
            continue
        notional = chosen["strike"] * 100
        try:
            from strategies.wheel_universe_selector import _get_sector
            from src.wheel_risk_gates import sector_cap_allows_new_csp, strict_cash_secured_put_ok

            ok_sec, sec_reason, by_sec = sector_cap_allows_new_csp(
                open_csps, t, notional, account_equity, max_sector_frac, _get_sector
            )
            if not ok_sec:
                _wheel_system_event(
                    "wheel_csp_skipped",
                    symbol=t,
                    reason="sector_cap",
                    sector_detail=sec_reason,
                    sector_breakdown=by_sec,
                )
                _emit_candidate_evaluated("skip", "sector_cap", sector_detail=sec_reason)
                continue
            if account_fields and require_cash_secured:
                cash = float(account_fields.get("cash") or 0)
                mult = float(account_fields.get("multiplier") or 1)
                ok_cash, cash_reason = strict_cash_secured_put_ok(
                    cash=cash,
                    multiplier=mult,
                    csp_notional=notional,
                    allow_margin_account=allow_margin_account,
                )
                if not ok_cash:
                    _wheel_system_event(
                        "wheel_csp_skipped",
                        symbol=t,
                        reason="cash_secured",
                        cash_secured_detail=cash_reason,
                        cash=cash,
                        multiplier=mult,
                        required_notional=notional,
                    )
                    _emit_candidate_evaluated("skip", "cash_secured", cash_secured_detail=cash_reason)
                    continue
        except Exception as e:
            log.warning("Wheel sector/cash gate failed for %s: %s", t, e)
            _wheel_system_event("wheel_csp_skipped", symbol=t, reason="sector_cash_gate_error")
            _emit_candidate_evaluated("skip", "sector_cash_gate_error")
            continue
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
            _emit_candidate_evaluated("skip", "allocation_exceeded", spot_price=round(spot, 2), spot_source=spot_source, required_notional=round(notional, 2), capital_check_decision="block", reason=alloc_details["decision_reason"], wheel_budget=alloc_details["strategy_budget"], wheel_used=alloc_details["strategy_used"], wheel_available=alloc_details["strategy_available"])
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
            _emit_candidate_evaluated("skip", "per_position_limit_exceeded", spot_price=round(spot, 2), spot_source=spot_source, required_notional=round(notional, 2), capital_check_decision="allow", position_limit_decision="block", per_position_limit=round(per_position_limit, 2))
            continue
        _emit_candidate_evaluated("fetch_chain", spot_price=round(spot, 2), spot_source=spot_source, required_notional=round(notional, 2), capital_check_decision="allow", position_limit_decision="allow", wheel_budget=round(wheel_budget, 2), wheel_available=alloc_details["strategy_available"], per_position_limit=round(per_position_limit, 2))
        existing = [o for o in (open_orders or []) if getattr(o, "symbol", "") == occ_symbol]
        if existing:
            _wheel_system_event("wheel_csp_skipped", symbol=t, reason="existing_order")
            _emit_candidate_evaluated("skip", "existing_order", spot_price=round(spot, 2), spot_source=spot_source, required_notional=round(notional, 2))
            continue
        expiry_str = chosen["contract"].get("expiration_date")
        client_order_id = build_wheel_client_order_id(cycle_id, t, "CSP", expiry_str, chosen["strike"], 1)
        if idempotency_skip(state, client_order_id):
            existing = (state.get("recent_orders") or {}).get(client_order_id) or {}
            _wheel_system_event(
                "wheel_order_idempotency_hit",
                cycle_id=cycle_id,
                client_order_id=client_order_id,
                existing_status=existing.get("status"),
                existing_order_id=existing.get("alpaca_order_id"),
            )
            continue
        _wheel_system_event(
            "wheel_contract_selected",
            cycle_id=cycle_id,
            symbol=t,
            option_symbol=occ_symbol,
            side="CSP",
            strike=chosen["strike"],
            expiry=expiry_str,
            dte=chosen["dte"],
            delta=chosen["delta_est"],
            mid_or_limit_price=limit_price,
            option_limit_price_source=opt_px_src,
            credit_expected=limit_price * 100.0,
            selection_reason="best_delta_dte",
            filter_summary="delta_dte_sort",
        )
        try:
            order = submit_wheel_broker_order(
                api,
                order_executor,
                symbol=occ_symbol,
                qty=1,
                side="sell",
                order_type="limit",
                time_in_force="day",
                limit_price=limit_price,
                client_order_id=client_order_id,
                caller="wheel_csp",
            )
        except Exception as e:
            log.warning("Wheel CSP order failed for %s: %s", t, e)
            _wheel_system_event("wheel_order_failed", symbol=t, phase="CSP", reason=str(e)[:200])
            continue
        order_id = getattr(order, "id", None) or (order.get("id") if isinstance(order, dict) else None)
        if order_id:
            try:
                from src.options_engine import fetch_iv_rank
                from src.wheel_first_five_telegram import maybe_telegram_wheel_first_five_submit

                iv_n, _iv_why = fetch_iv_rank(t)
                maybe_telegram_wheel_first_five_submit(
                    phase="CSP",
                    underlying=t,
                    action="sell CSP (cash-secured put)",
                    strike=float(chosen["strike"]),
                    order_id=str(order_id),
                    iv_rank=iv_n,
                    underlying_mid=float(spot),
                    put_wall_strike=csp_put_wall_strike,
                )
            except Exception as fe:
                log.debug("Wheel First-5 submit pager: %s", fe)
        state.setdefault("recent_orders", {})[client_order_id] = {
            "cycle_id": cycle_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "symbol": t,
            "side": "CSP",
            "option_symbol": occ_symbol,
            "status": "submitted",
            "alpaca_order_id": order_id,
        }
        expected_credit = limit_price * 100.0
        _wheel_system_event(
            "wheel_order_submitted",
            cycle_id=cycle_id,
            symbol=t,
            phase="CSP",
            order_id=str(order_id) if order_id else None,
            client_order_id=client_order_id,
            option_symbol=occ_symbol,
            side="CSP",
            strike=chosen["strike"],
            expiry=expiry_str,
            limit_price=limit_price,
            option_limit_price_source=opt_px_src,
            qty=1,
            expected_credit=expected_credit,
            spot_at_submit=round(spot, 2),
        )
        premium_filled: Optional[float] = None
        fill_st = "unknown"
        filled_avg = 0.0
        filled_qty = 0
        if order_id and hasattr(api, "get_order"):
            fill_st, filled_avg, filled_qty = _poll_wheel_order_status(api, str(order_id))
            if fill_st == "filled" or filled_qty >= 1:
                if filled_avg > 0 and filled_qty > 0:
                    premium_filled = filled_avg * 100.0 * filled_qty
                elif filled_avg > 0:
                    premium_filled = filled_avg * 100.0
                else:
                    premium_filled = limit_price * 100.0 * max(1, int(filled_qty or 1))
                if client_order_id and state.get("recent_orders") and client_order_id in state["recent_orders"]:
                    state["recent_orders"][client_order_id]["status"] = "filled"
                _wheel_system_event(
                    "wheel_order_filled",
                    cycle_id=cycle_id,
                    symbol=t,
                    phase="CSP",
                    order_id=str(order_id),
                    client_order_id=client_order_id,
                    premium=premium_filled,
                    fill_price=filled_avg,
                    filled_qty=filled_qty,
                    credit_realized_est=premium_filled,
                )
            else:
                if client_order_id and state.get("recent_orders") and client_order_id in state["recent_orders"]:
                    state["recent_orders"][client_order_id]["status"] = fill_st
                _wheel_system_event(
                    "wheel_order_not_filled",
                    cycle_id=cycle_id,
                    symbol=t,
                    phase="CSP",
                    order_id=str(order_id) if order_id else None,
                    client_order_id=client_order_id,
                    status=fill_st,
                    filled_qty=filled_qty,
                )
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
            qty=max(1, filled_qty) if filled_qty else 1,
        )
        if fill_st != "filled" and filled_qty < 1:
            _save_wheel_state(state, cycle_id=cycle_id)
            continue
        opened_at_iso = datetime.now(timezone.utc).isoformat()
        qty_open = max(1, int(filled_qty or 1))
        new_entry = {
            "symbol": occ_symbol,
            "option_symbol": occ_symbol,
            "underlying_symbol": t,
            "strike": chosen["strike"],
            "expiry": chosen["contract"].get("expiration_date"),
            "qty": qty_open,
            "opened_at": opened_at_iso,
            "open_credit": premium_filled,
            "spot_at_open": round(spot, 2),
            "cycle_id_opened": cycle_id,
            "status": "open",
            "linked_cc": None,
            "order_id": order_id,
        }
        prev_summary = {"open_csps_count": sum(len(v) if isinstance(v, list) else 1 for v in open_csps.values())}
        open_csps.setdefault(t, []).append(new_entry)
        state["open_csps"] = open_csps
        new_summary = {"open_csps_count": sum(len(v) if isinstance(v, list) else 1 for v in open_csps.values()), "added": t}
        _save_wheel_state(state, cycle_id=cycle_id, change_type="open_csp_added", symbol=t, previous_summary=prev_summary, new_summary=new_summary)
        placed += 1
        total_wheel_positions += 1
        first_placed_symbol = first_placed_symbol or t
        # state["open_csps"] already updated above; next can_allocate will see new used
    return placed, first_placed_symbol, selected_meta


def _run_cc_phase(
    api,
    config: dict,
    account_equity: float,
    positions: list,
    *,
    order_executor: Any = None,
) -> int:
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
        cc_limit, cc_px_src, cc_px_fail = resolve_option_short_sell_limit_per_share(api, occ_symbol)
        if cc_limit is None or cc_limit <= 0:
            _wheel_system_event(
                "wheel_cc_skipped",
                symbol=symbol,
                reason="no_option_quote",
                option_symbol=occ_symbol,
                option_price_fail=cc_px_fail,
            )
            continue
        try:
            client_order_id = f"wheel-CC-{symbol}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
            order = submit_wheel_broker_order(
                api,
                order_executor,
                symbol=occ_symbol,
                qty=1,
                side="sell",
                order_type="limit",
                time_in_force="day",
                limit_price=cc_limit,
                client_order_id=client_order_id,
                caller="wheel_cc",
            )
        except Exception as e:
            log.warning("Wheel CC order failed for %s: %s", symbol, e)
            continue
        order_id = getattr(order, "id", None) or (order.get("id") if isinstance(order, dict) else None)
        if order_id:
            try:
                from src.options_engine import fetch_iv_rank
                from src.wheel_first_five_telegram import maybe_telegram_wheel_first_five_submit

                iv_n, _iv_why = fetch_iv_rank(symbol)
                maybe_telegram_wheel_first_five_submit(
                    phase="CC",
                    underlying=symbol,
                    action="sell CC (covered call)",
                    strike=float(chosen["strike"]),
                    order_id=str(order_id),
                    iv_rank=iv_n,
                    underlying_mid=float(spot),
                    put_wall_strike=None,
                )
            except Exception as fe:
                log.debug("Wheel First-5 submit pager CC: %s", fe)
        premium_cc: Optional[float] = None
        fill_st_cc = "unknown"
        fq_cc = 0
        if order_id and hasattr(api, "get_order"):
            fill_st_cc, fap_cc, fq_cc = _poll_wheel_order_status(api, str(order_id))
            if fill_st_cc == "filled" or fq_cc >= 1:
                if fap_cc > 0 and fq_cc > 0:
                    premium_cc = fap_cc * 100.0 * fq_cc
                elif fap_cc > 0:
                    premium_cc = fap_cc * 100.0
                else:
                    premium_cc = cc_limit * 100.0 * max(1, fq_cc)
        _log_wheel_telemetry(
            symbol=symbol,
            side="sell",
            phase="CC",
            option_type="call",
            strike=chosen["strike"],
            expiry=chosen["contract"].get("expiration_date"),
            dte=chosen["dte"],
            delta_at_entry=chosen["delta_est"],
            premium=premium_cc,
            order_id=str(order_id) if order_id else None,
            qty=max(1, fq_cc) if fq_cc else 1,
        )
        if fill_st_cc != "filled" and fq_cc < 1:
            _save_wheel_state(state)
            continue
        open_ccs.setdefault(symbol, []).append({
            "symbol": occ_symbol,
            "strike": chosen["strike"],
            "expiry": chosen["contract"].get("expiration_date"),
            "order_id": order_id,
            "qty": max(1, int(fq_cc or 1)),
        })
        state["open_ccs"] = open_ccs
        _save_wheel_state(state)
        placed += 1
    return placed


def run(api, config: dict, order_executor: Any = None) -> dict:
    """
    Run wheel strategy: CSP phase then CC phase.
    Regime is modifier-only; must never gate or block wheel entries.

    :param order_executor: Optional ``AlpacaExecutor``; when set, CSP/CC use ``_submit_order_guarded``.
    """
    result = {"orders_placed": 0, "csp_placed": 0, "cc_placed": 0, "errors": []}
    cycle_id = str(uuid.uuid4())
    tickers, selected_meta, all_candidates = _select_wheel_tickers(api, config)
    if not config.get("universe_max_candidates"):
        tickers = _load_universe(config)
        selected_meta = [{"symbol": s, "uw_composite_score": None} for s in tickers]
        all_candidates = selected_meta.copy()
    _wheel_system_event("wheel_run_started", reason="ok", ticker_count=len(tickers), cycle_id=cycle_id)
    config_snapshot = _config_snapshot_for_audit(config)
    _wheel_system_event(
        "wheel_config_snapshot",
        allocation_pct=config_snapshot.get("allocation_pct", 25),
        per_position_fraction_of_wheel_budget=config_snapshot.get("per_position_fraction_of_wheel_budget", 0.5),
        max_concurrent_positions=config_snapshot.get("max_concurrent_positions", 5),
    )
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
        account_fields = {
            "cash": float(getattr(account, "cash", 0) or 0),
            "multiplier": float(getattr(account, "multiplier", 1) or 1),
            "buying_power": buying_power,
        }
    except Exception as e:
        result["errors"].append(f"account_fetch: {e}")
        _wheel_system_event("wheel_run_failed", reason="account_fetch", error=str(e)[:200])
        _notify_wheel_critical_abort("account_fetch", str(e), cycle_id=cycle_id)
        return result
    try:
        positions = api.list_positions() or []
    except Exception as e:
        result["errors"].append(f"list_positions: {e}")
        log.warning("Wheel: list_positions failed — aborting cycle (fail-closed): %s", e)
        _wheel_system_event("wheel_run_failed", reason="list_positions", error=str(e)[:200], cycle_id=cycle_id)
        _notify_wheel_critical_abort("list_positions", str(e), cycle_id=cycle_id)
        return result
    try:
        open_orders = api.list_orders(status="open") if hasattr(api, "list_orders") else []
    except Exception as e:
        result["errors"].append(f"list_orders: {e}")
        log.warning("Wheel: list_orders failed — aborting cycle (fail-closed): %s", e)
        _wheel_system_event("wheel_run_failed", reason="list_orders", error=str(e)[:200], cycle_id=cycle_id)
        _notify_wheel_critical_abort("list_orders", str(e), cycle_id=cycle_id)
        return result
    state = _load_wheel_state()
    try:
        from capital.strategy_allocator import can_allocate as _can_allocate
        _, alloc_details = _can_allocate("wheel", 0, account_equity, state)
    except Exception:
        alloc_details = {"strategy_budget": round(account_equity * 0.25, 2), "strategy_used": 0, "strategy_available": round(account_equity * 0.25, 2)}
    wheel_budget = alloc_details.get("strategy_budget", 0)
    wheel_used = alloc_details.get("strategy_used", 0)
    wheel_available = alloc_details.get("strategy_available", 0)
    per_position_frac = config.get("per_position_fraction_of_wheel_budget", 0.5)
    per_position_limit = wheel_budget * per_position_frac
    excluded = config.get("universe_excluded_sectors") or []
    top_10 = (selected_meta or [])[:10]
    _wheel_system_event(
        "wheel_decision_context",
        cycle_id=cycle_id,
        posture=_regime_label,
        regime=_regime_label,
        excluded_sectors=excluded,
        universe_size=len(all_candidates or []),
        candidates_considered=len(tickers),
        top_10_symbols=[r.get("symbol") for r in top_10],
        top_10_uw_scores=[r.get("uw_composite_score") for r in top_10],
        config_snapshot=config_snapshot,
        wheel_budget=round(wheel_budget, 2),
        wheel_used=round(wheel_used, 2),
        wheel_available=round(wheel_available, 2),
        per_position_limit=round(per_position_limit, 2),
    )
    csp_placed, first_placed_symbol, selected_meta = _run_csp_phase(
        api, config, account_equity, buying_power, positions, open_orders,
        cycle_id=cycle_id,
        tickers_override=tickers,
        selected_meta_override=selected_meta,
        all_candidates_override=all_candidates,
        account_fields=account_fields,
        order_executor=order_executor,
    )
    result["csp_placed"] = csp_placed
    result["orders_placed"] += csp_placed
    if csp_placed == 0 and len(tickers) > 0:
        _wheel_system_event("wheel_alert_stuck", cycle_id=cycle_id, reason="no_submission_this_cycle", candidates_considered=len(tickers))
    _emit_wheel_candidate_ranked(tickers, selected_meta, first_placed_symbol, csp_placed, cycle_id=cycle_id)
    cc_placed = _run_cc_phase(api, config, account_equity, positions, order_executor=order_executor)
    result["cc_placed"] = cc_placed
    result["orders_placed"] += cc_placed
    return result
