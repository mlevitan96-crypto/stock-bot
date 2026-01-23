#!/usr/bin/env python3
"""
Shadow executor (v2, shadow-only)
================================

This module is called from the existing shadow A/B compare path in `main.py`.
It never submits orders; it only emits append-only records to logs/shadow_trades.jsonl.
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from src.trading.shadow_logger import append_shadow_trade


STATE_POSITIONS = Path("state/shadow_v2_positions.json")
STATE_HEARTBEAT = Path("state/shadow_heartbeat.json")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_positions() -> Dict[str, Any]:
    try:
        if not STATE_POSITIONS.exists():
            return {"positions": {}}
        d = json.loads(STATE_POSITIONS.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {"positions": {}}
    except Exception:
        return {"positions": {}}


def _write_positions(doc: Dict[str, Any]) -> None:
    try:
        STATE_POSITIONS.parent.mkdir(parents=True, exist_ok=True)
        tmp = STATE_POSITIONS.with_suffix(".tmp")
        tmp.write_text(json.dumps(doc, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(STATE_POSITIONS)
    except Exception:
        return


def _update_shadow_heartbeat(*, symbol: str, event_type: str) -> None:
    """
    Shadow continuity sentinel (observability-only).
    Updated on every v2 shadow decision evaluation.
    """
    try:
        STATE_HEARTBEAT.parent.mkdir(parents=True, exist_ok=True)
        hb = {
            "timestamp": _now_iso(),
            "status": "alive",
            "symbol": str(symbol).upper(),
            "event_type": str(event_type),
        }
        tmp = STATE_HEARTBEAT.with_suffix(".tmp")
        tmp.write_text(json.dumps(hb, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(STATE_HEARTBEAT)
    except Exception:
        return


def _get_risk_feats(symbol: str) -> Dict[str, Any]:
    try:
        rf = json.loads(Path("state/symbol_risk_features.json").read_text(encoding="utf-8"))
        sy = rf.get("symbols") if isinstance(rf, dict) else {}
        rec = (sy or {}).get(str(symbol).upper()) if isinstance(sy, dict) else None
        return rec if isinstance(rec, dict) else {}
    except Exception:
        return {}


def _exit_intel_flags(symbol: str) -> Dict[str, Any]:
    """
    Best-effort: read pre/post exit intel flags (optional).
    """
    flags: Dict[str, Any] = {}
    sym = str(symbol).upper()
    for p in (Path("state/premarket_exit_intel.json"), Path("state/postmarket_exit_intel.json")):
        if not p.exists():
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            sy = d.get("symbols") if isinstance(d, dict) else {}
            r = (sy or {}).get(sym) if isinstance(sy, dict) else None
            if isinstance(r, dict):
                flags.update(r)
        except Exception:
            continue
    return flags


def _pick_universe_replacement(exclude: set[str]) -> Tuple[Optional[str], Optional[float]]:
    """
    Best-effort candidate: highest ranked symbol in daily_universe_v2 not in exclude.
    Returns (symbol, score) where score is the universe score.
    """
    p = Path("state/daily_universe_v2.json")
    if not p.exists():
        return None, None
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        rows = d.get("symbols") if isinstance(d, dict) else []
        if not isinstance(rows, list):
            return None, None
        for r in rows:
            if isinstance(r, dict) and r.get("symbol"):
                s = str(r["symbol"]).upper()
                if s in exclude:
                    continue
                try:
                    sc = float(r.get("score", 0.0) or 0.0)
                except Exception:
                    sc = None  # type: ignore
                return s, sc
    except Exception:
        return None, None
    return None, None


def _side_from_direction(direction: str) -> str:
    d = str(direction or "").lower()
    if d in ("bearish", "short", "sell"):
        return "short"
    return "long"


def _safe_float(v: Any) -> Optional[float]:
    try:
        if v is None:
            return None
        return float(v)
    except Exception:
        return None


def _compute_pnl_usd_pct(*, entry_price: float, exit_price: float, qty: float, side: str) -> Tuple[Optional[float], Optional[float]]:
    try:
        e = float(entry_price)
        x = float(exit_price)
        q = float(qty)
        if e <= 0 or x <= 0 or q <= 0:
            return None, None
        if str(side) == "short":
            pnl_usd = q * (e - x)
        else:
            pnl_usd = q * (x - e)
        pnl_pct = pnl_usd / (q * e) if (q * e) > 0 else None
        return float(pnl_usd), (float(pnl_pct) if pnl_pct is not None else None)
    except Exception:
        return None, None


def _resolve_price_from_api(*, api: Any, symbol: str) -> Optional[float]:
    """
    Best-effort live price read (no orders). Used only for shadow simulation.
    """
    if api is None:
        return None
    sym = str(symbol).upper()
    try:
        lt = api.get_last_trade(sym)
        px = getattr(lt, "price", None)
        pxf = _safe_float(px)
        if pxf and pxf > 0:
            return pxf
    except Exception:
        pass
    try:
        q = api.get_quote(sym)
        bid = _safe_float(getattr(q, "bid", None))
        ask = _safe_float(getattr(q, "ask", None))
        if bid and ask and bid > 0 and ask > 0:
            return float((bid + ask) / 2.0)
    except Exception:
        pass
    return None


def log_shadow_decision(
    *,
    symbol: str,
    direction: str,
    v1_score: float,
    v2_score: float,
    v1_pass: bool,
    v2_pass: bool,
    composite_v2: Dict[str, Any],
    market_regime: str = "",
    posture: str = "",
    regime_label: str = "",
    volatility_regime: str = "",
    # Simulator inputs (best-effort)
    current_price: Optional[float] = None,
    account_equity: Optional[float] = None,
    buying_power: Optional[float] = None,
    position_size_usd: Optional[float] = None,
    api: Any = None,
) -> None:
    """
    Emit a "shadow_trade_candidate" record when v2 would enter (v2_pass True).
    Also emits lightweight compare records for distribution analysis.
    """
    try:
        event_type = "shadow_trade_candidate" if bool(v2_pass) else "shadow_score_compare"
        _update_shadow_heartbeat(symbol=str(symbol), event_type=event_type)
        uw_attr = {
            "uw_intel_version": composite_v2.get("uw_intel_version", ""),
            "v2_uw_inputs": composite_v2.get("v2_uw_inputs", {}),
            "v2_uw_adjustments": composite_v2.get("v2_uw_adjustments", {}),
            "v2_uw_sector_profile": composite_v2.get("v2_uw_sector_profile", {}),
            "v2_uw_regime_profile": composite_v2.get("v2_uw_regime_profile", {}),
        }
        rec: Dict[str, Any] = {
            "event_type": event_type,
            "symbol": str(symbol).upper(),
            "direction": str(direction),
            "v1_score": float(v1_score),
            "v2_score": float(v2_score),
            "v1_pass": bool(v1_pass),
            "v2_pass": bool(v2_pass),
            "composite_version": "v2",
            "universe_scoring_version": str(composite_v2.get("universe_scoring_version", "")),
            "universe_source": str(composite_v2.get("universe_source", "")),
            "in_universe": composite_v2.get("in_universe", None),
            "market_regime": str(market_regime),
            "posture": str(posture),
            "regime_label": str(regime_label),
            "volatility_regime": str(volatility_regime),
            "uw_attribution_snapshot": uw_attr,
            "current_price": _safe_float(current_price),
            "account_equity": _safe_float(account_equity),
            "buying_power": _safe_float(buying_power),
            "position_size_usd": _safe_float(position_size_usd),
        }
        append_shadow_trade(rec)

        # v2 shadow positions + exit intelligence (shadow-only).
        # - If v2_pass => open/refresh a shadow position.
        # - If already open => evaluate exit score and log exit decisions/attribution.
        sym = str(symbol).upper()
        st = _read_positions()
        pos = (st.get("positions") or {}).get(sym) if isinstance(st.get("positions"), dict) else None
        side = _side_from_direction(direction)

        # Resolve price (real, best-effort).
        px_now = _safe_float(current_price)
        if (px_now is None or px_now <= 0) and api is not None:
            px_now = _resolve_price_from_api(api=api, symbol=sym)

        # Entry snapshot
        if bool(v2_pass) and not isinstance(pos, dict):
            if px_now is None or px_now <= 0:
                append_shadow_trade(
                    {
                        "event_type": "shadow_entry_blocked",
                        "symbol": sym,
                        "direction": str(direction),
                        "reason": "price_unavailable",
                        "v2_score": float(v2_score),
                        "v1_score": float(v1_score),
                        "uw_attribution_snapshot": uw_attr,
                    }
                )
                return

            # Mirror v1-ish sizing behavior (best-effort):
            # - Prefer passed position_size_usd; fall back to risk_management.calculate_position_size(account_equity).
            psu = _safe_float(position_size_usd)
            if (psu is None or psu <= 0) and account_equity is not None:
                try:
                    from risk_management import calculate_position_size

                    psu = float(calculate_position_size(float(account_equity)))
                except Exception:
                    psu = None
            if psu is None or psu <= 0:
                psu = 0.0

            qty: float
            if psu > 0 and px_now > 0:
                # If price exceeds cap, allow fractional (matches v1 executor fallback).
                if px_now > psu:
                    fq = psu / px_now if px_now > 0 else 0.0
                    qty = float(fq) if fq >= 0.001 else 0.0
                else:
                    base_qty = max(1, int(psu / px_now))
                    # Apply sizing overlay (best-effort) if available.
                    try:
                        from uw_composite_v2 import apply_sizing_overlay

                        base_qty = int(apply_sizing_overlay(int(base_qty), composite_v2))
                    except Exception:
                        pass
                    qty = float(max(1, int(base_qty)))
            else:
                qty = 1.0

            # Buying power guard (best-effort, does not affect v1)
            bp = _safe_float(buying_power) or 0.0
            if bp > 0 and side == "long":
                try:
                    if (qty * px_now) > (bp * 0.95):
                        append_shadow_trade(
                            {
                                "event_type": "shadow_entry_blocked",
                                "symbol": sym,
                                "direction": str(direction),
                                "reason": "insufficient_buying_power",
                                "required_notional": round(float(qty * px_now), 4),
                                "buying_power": round(float(bp), 4),
                                "v2_score": float(v2_score),
                                "v1_score": float(v1_score),
                                "uw_attribution_snapshot": uw_attr,
                            }
                        )
                        return
                except Exception:
                    pass

            # Best-effort entry sector/regime snapshots from composite payload.
            sec = ((uw_attr.get("v2_uw_sector_profile") or {}) if isinstance(uw_attr.get("v2_uw_sector_profile"), dict) else {}).get("sector", "UNKNOWN")
            reg = ((uw_attr.get("v2_uw_regime_profile") or {}) if isinstance(uw_attr.get("v2_uw_regime_profile"), dict) else {}).get("regime_label", "")
            trade_id = uuid.uuid4().hex
            (st.setdefault("positions", {}))[sym] = {
                "trade_id": trade_id,
                "entry_timestamp": _now_iso(),
                "direction": str(direction),
                "side": str(side),
                "entry_v2_score": float(v2_score),
                "entry_v1_score": float(v1_score),
                "entry_uw": dict(uw_attr),
                "entry_regime": str(reg),
                "entry_sector": str(sec),
                "entry_price": float(px_now),
                "qty": float(qty),
                "position_size_usd": float(psu),
                "last_price": float(px_now),
                "unrealized_pnl_usd": 0.0,
                "unrealized_pnl_pct": 0.0,
            }
            _write_positions(st)
            append_shadow_trade(
                {
                    "event_type": "shadow_entry_opened",
                    "trade_id": trade_id,
                    "symbol": sym,
                    "direction": str(direction),
                    "side": str(side),
                    "entry_price": float(px_now),
                    "entry_ts": (st.get("positions") or {}).get(sym, {}).get("entry_timestamp", _now_iso()),
                    "qty": float(qty),
                    "position_size_usd": float(psu),
                    "v2_score": float(v2_score),
                    "v1_score": float(v1_score),
                    "intel_snapshot": uw_attr,
                }
            )
            # Master trade log (append-only, additive).
            try:
                from utils.master_trade_log import append_master_trade

                adjustments = {}
                try:
                    adjustments = (
                        ((uw_attr.get("v2_uw_adjustments") or {}) if isinstance(uw_attr, dict) else {})
                        if isinstance(uw_attr, dict)
                        else {}
                    )
                except Exception:
                    adjustments = {}
                signals = []
                try:
                    from telemetry.feature_families import active_v2_families_from_adjustments  # type: ignore

                    signals = active_v2_families_from_adjustments(adjustments) or []
                except Exception:
                    signals = []
                append_master_trade(
                    {
                        "trade_id": str(trade_id),
                        "symbol": sym,
                        "side": str(side),
                        "is_live": False,
                        "is_shadow": True,
                        "entry_ts": str((st.get("positions") or {}).get(sym, {}).get("entry_timestamp", _now_iso())),
                        "exit_ts": None,
                        "entry_price": float(px_now),
                        "exit_price": None,
                        "size": float(qty),
                        "realized_pnl_usd": None,
                        "signals": signals,
                        "feature_snapshot": dict(adjustments or {}),
                        "regime_snapshot": {
                            "regime": str(((uw_attr.get("v2_uw_regime_profile") or {}) if isinstance(uw_attr.get("v2_uw_regime_profile"), dict) else {}).get("regime_label", "") or ""),
                            "sector_posture": str(((uw_attr.get("v2_uw_sector_profile") or {}) if isinstance(uw_attr.get("v2_uw_sector_profile"), dict) else {}).get("sector", "UNKNOWN") or "UNKNOWN"),
                            "volatility_bucket": None,
                            "trend_bucket": None,
                        },
                        "exit_reason": None,
                        "source": "shadow",
                    }
                )
            except Exception:
                pass
            return

        # Exit evaluation for open positions
        if isinstance(pos, dict):
            # Mark-to-market update (persisted every evaluation)
            if px_now is not None and px_now > 0:
                epx = _safe_float(pos.get("entry_price")) or 0.0
                qx = _safe_float(pos.get("qty")) or 0.0
                pnl_usd_u, pnl_pct_u = _compute_pnl_usd_pct(entry_price=epx, exit_price=float(px_now), qty=float(qx), side=str(pos.get("side") or side))
                try:
                    pos["last_price"] = float(px_now)
                    pos["unrealized_pnl_usd"] = float(pnl_usd_u or 0.0)
                    pos["unrealized_pnl_pct"] = float(pnl_pct_u or 0.0)
                    pos["last_update_ts"] = _now_iso()
                    _write_positions(st)
                except Exception:
                    pass

            entry_ts = str(pos.get("entry_timestamp", "") or "")
            entry_v2 = float(pos.get("entry_v2_score", 0.0) or 0.0)
            entry_uw = pos.get("entry_uw") if isinstance(pos.get("entry_uw"), dict) else {}
            entry_reg = str(pos.get("entry_regime", "") or "")
            entry_sec = str(pos.get("entry_sector", "") or "UNKNOWN")

            now_uw = dict(uw_attr)
            now_reg = str(((uw_attr.get("v2_uw_regime_profile") or {}) if isinstance(uw_attr.get("v2_uw_regime_profile"), dict) else {}).get("regime_label", "") or "")
            now_sec = str(((uw_attr.get("v2_uw_sector_profile") or {}) if isinstance(uw_attr.get("v2_uw_sector_profile"), dict) else {}).get("sector", "UNKNOWN") or "UNKNOWN")

            rf = _get_risk_feats(sym)
            vol = rf.get("realized_vol_20d")
            try:
                vol_f = float(vol) if vol is not None else None
            except Exception:
                vol_f = None

            # Compute exit score and dynamic stops/targets
            from src.exit.exit_score_v2 import compute_exit_score_v2
            from src.exit.profit_targets_v2 import compute_profit_target
            from src.exit.stops_v2 import compute_stop_price
            from src.exit.replacement_logic_v2 import choose_replacement_candidate
            from src.exit.exit_attribution import append_exit_attribution, build_exit_attribution_record

            thesis = _exit_intel_flags(sym)
            exit_score, exit_components, rec_reason = compute_exit_score_v2(
                symbol=sym,
                direction=str(direction),
                entry_v2_score=float(entry_v2),
                now_v2_score=float(v2_score),
                entry_uw_inputs=((entry_uw.get("v2_uw_inputs") or {}) if isinstance(entry_uw, dict) else {}),
                now_uw_inputs=((now_uw.get("v2_uw_inputs") or {}) if isinstance(now_uw, dict) else {}),
                entry_regime=entry_reg,
                now_regime=now_reg,
                entry_sector=entry_sec,
                now_sector=now_sec,
                realized_vol_20d=vol_f,
                thesis_flags=thesis,
            )

            flow_strength_now = float((((now_uw.get("v2_uw_inputs") or {}) if isinstance(now_uw, dict) else {}).get("flow_strength", 0.0) or 0.0))
            pt_px, pt_reason = compute_profit_target(
                entry_price=pos.get("entry_price"),
                realized_vol_20d=vol_f,
                flow_strength=flow_strength_now,
                regime_label=now_reg,
                sector=now_sec,
                direction=str(direction),
            )
            # Flow reversal: simplistic proxy if flow_strength dropped a lot
            flow_entry = float((((entry_uw.get("v2_uw_inputs") or {}) if isinstance(entry_uw, dict) else {}).get("flow_strength", 0.0) or 0.0))
            flow_reversal = (flow_entry - flow_strength_now) >= 0.35
            stop_px, stop_reason = compute_stop_price(
                entry_price=pos.get("entry_price"),
                realized_vol_20d=vol_f,
                flow_reversal=bool(flow_reversal),
                regime_label=now_reg,
                sector_collapse=bool(thesis.get("sector_collapse", False)),
                direction=str(direction),
            )

            # Replacement best-effort candidate from universe v2
            cand_sym, cand_u_score = _pick_universe_replacement(exclude=set((st.get("positions") or {}).keys()) | {sym})
            replacement, repl_reason = choose_replacement_candidate(
                exit_score=float(exit_score),
                threshold=0.75,
                current_symbol=sym,
                current_v2_score=float(v2_score),
                candidate_symbol=cand_sym,
                candidate_v2_score=cand_u_score,
                margin=0.25,
            )

            # Price-based triggers (profit/stop) when price is available.
            entry_price = _safe_float(pos.get("entry_price")) or 0.0
            qty = _safe_float(pos.get("qty")) or 0.0
            profit_hit = False
            stop_hit = False
            if px_now is not None and px_now > 0 and entry_price > 0:
                try:
                    if pt_px is not None and float(pt_px) > 0:
                        profit_hit = (float(px_now) >= float(pt_px)) if side == "long" else (float(px_now) <= float(pt_px))
                    if stop_px is not None and float(stop_px) > 0:
                        stop_hit = (float(px_now) <= float(stop_px)) if side == "long" else (float(px_now) >= float(stop_px))
                except Exception:
                    profit_hit = False
                    stop_hit = False

            # Exit trigger: any of
            # - profit target hit
            # - stop hit
            # - replacement candidate chosen
            # - intel/score exit signal
            should_exit_score = float(exit_score) >= 0.70 and rec_reason in ("profit", "stop", "intel_deterioration", "replacement")
            should_exit = bool(profit_hit or stop_hit or (replacement is not None) or should_exit_score)
            if should_exit:
                exit_ts = _now_iso()
                exit_price = float(px_now) if (px_now is not None and px_now > 0) else None
                pnl_usd, pnl_pct = (None, None)
                if exit_price is not None and entry_price > 0 and qty > 0:
                    pnl_usd, pnl_pct = _compute_pnl_usd_pct(entry_price=entry_price, exit_price=float(exit_price), qty=float(qty), side=str(pos.get("side") or side))
                # Time in trade
                tmin = None
                try:
                    dt0 = datetime.fromisoformat(entry_ts.replace("Z", "+00:00"))
                    tmin = (datetime.now(timezone.utc) - dt0).total_seconds() / 60.0
                except Exception:
                    tmin = None

                score_det = float(entry_v2) - float(v2_score)
                rs_det = float(exit_components.get("score_deterioration", 0.0) or 0.0)  # placeholder

                # Attribution record
                exit_reason = "profit" if profit_hit else "stop" if stop_hit else ("replacement" if replacement else rec_reason)
                arec = build_exit_attribution_record(
                    symbol=sym,
                    entry_timestamp=entry_ts,
                    exit_reason=str(exit_reason),
                    pnl=pnl_usd,
                    pnl_pct=pnl_pct,
                    entry_price=(float(entry_price) if entry_price > 0 else None),
                    exit_price=exit_price,
                    qty=float(qty) if qty > 0 else None,
                    time_in_trade_minutes=tmin,
                    entry_uw=dict(entry_uw or {}),
                    exit_uw=dict(now_uw or {}),
                    entry_regime=str(entry_reg),
                    exit_regime=str(now_reg),
                    entry_sector_profile=dict((entry_uw.get("v2_uw_sector_profile") or {}) if isinstance(entry_uw, dict) else {}),
                    exit_sector_profile=dict((now_uw.get("v2_uw_sector_profile") or {}) if isinstance(now_uw, dict) else {}),
                    score_deterioration=float(score_det),
                    relative_strength_deterioration=float(rs_det),
                    v2_exit_score=float(exit_score),
                    v2_exit_components=dict(exit_components or {}),
                    replacement_candidate=replacement,
                    replacement_reasoning=repl_reason if replacement else None,
                    exit_timestamp=exit_ts,
                )
                append_exit_attribution(arec)

                append_shadow_trade(
                    {
                        "event_type": "shadow_exit",
                        "trade_id": str(pos.get("trade_id", "") or ""),
                        "symbol": sym,
                        "direction": str(direction),
                        "side": str(pos.get("side") or side),
                        "v1_score": float(v1_score),
                        "v2_score": float(v2_score),
                        "v2_exit_score": float(exit_score),
                        "v2_exit_components": dict(exit_components),
                        "v2_exit_reason": str(exit_reason),
                        "exit_price": exit_price,
                        "exit_ts": exit_ts,
                        "entry_price": entry_price if entry_price > 0 else None,
                        "entry_ts": entry_ts,
                        "qty": float(qty),
                        "pnl": pnl_usd,
                        "pnl_pct": pnl_pct,
                        "intel_snapshot": now_uw,
                        "profit_target_price": pt_px,
                        "profit_target_reasoning": pt_reason,
                        "stop_price": stop_px,
                        "stop_reasoning": stop_reason,
                        "replacement_candidate": replacement,
                        "replacement_reasoning": repl_reason if replacement else None,
                    }
                )
                # Master trade log (append-only, additive).
                try:
                    from utils.master_trade_log import append_master_trade

                    tid2 = str(pos.get("trade_id", "") or "")
                    adjustments2 = {}
                    try:
                        snap2 = now_uw if isinstance(now_uw, dict) else {}
                        adjustments2 = (snap2.get("v2_uw_adjustments") or {}) if isinstance(snap2.get("v2_uw_adjustments"), dict) else {}
                    except Exception:
                        adjustments2 = {}
                    signals2 = []
                    try:
                        from telemetry.feature_families import active_v2_families_from_adjustments  # type: ignore

                        signals2 = active_v2_families_from_adjustments(adjustments2) or []
                    except Exception:
                        signals2 = []
                    append_master_trade(
                        {
                            "trade_id": tid2,
                            "symbol": sym,
                            "side": str(pos.get("side") or side),
                            "is_live": False,
                            "is_shadow": True,
                            "entry_ts": str(pos.get("entry_timestamp") or entry_ts),
                            "exit_ts": str(exit_ts),
                            "entry_price": float(entry_price) if entry_price > 0 else 0.0,
                            "exit_price": float(exit_price) if exit_price is not None else None,
                            "size": float(qty) if qty > 0 else 0.0,
                            "realized_pnl_usd": float(pnl_usd or 0.0) if pnl_usd is not None else None,
                            "signals": signals2,
                            "feature_snapshot": dict(adjustments2 or {}),
                            "regime_snapshot": {
                                "regime": str(now_reg or ""),
                                "sector_posture": str(now_sec or "UNKNOWN"),
                                "volatility_bucket": None,
                                "trend_bucket": None,
                            },
                            "exit_reason": str(exit_reason or ""),
                            "source": "shadow",
                        }
                    )
                except Exception:
                    pass
                # Close position
                try:
                    (st.get("positions") or {}).pop(sym, None)
                except Exception:
                    pass
                _write_positions(st)
    except Exception:
        return

