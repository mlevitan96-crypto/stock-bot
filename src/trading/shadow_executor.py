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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from src.trading.shadow_logger import append_shadow_trade


STATE_POSITIONS = Path("state/shadow_v2_positions.json")


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
) -> None:
    """
    Emit a "shadow_trade_candidate" record when v2 would enter (v2_pass True).
    Also emits lightweight compare records for distribution analysis.
    """
    try:
        uw_attr = {
            "uw_intel_version": composite_v2.get("uw_intel_version", ""),
            "v2_uw_inputs": composite_v2.get("v2_uw_inputs", {}),
            "v2_uw_adjustments": composite_v2.get("v2_uw_adjustments", {}),
            "v2_uw_sector_profile": composite_v2.get("v2_uw_sector_profile", {}),
            "v2_uw_regime_profile": composite_v2.get("v2_uw_regime_profile", {}),
        }
        rec: Dict[str, Any] = {
            "event_type": "shadow_trade_candidate" if bool(v2_pass) else "shadow_score_compare",
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
        }
        append_shadow_trade(rec)

        # v2 shadow positions + exit intelligence (shadow-only).
        # - If v2_pass => open/refresh a shadow position.
        # - If already open => evaluate exit score and log exit decisions/attribution.
        sym = str(symbol).upper()
        st = _read_positions()
        pos = (st.get("positions") or {}).get(sym) if isinstance(st.get("positions"), dict) else None

        # Entry snapshot
        if bool(v2_pass) and not isinstance(pos, dict):
            # Best-effort entry sector/regime snapshots from composite payload.
            sec = ((uw_attr.get("v2_uw_sector_profile") or {}) if isinstance(uw_attr.get("v2_uw_sector_profile"), dict) else {}).get("sector", "UNKNOWN")
            reg = ((uw_attr.get("v2_uw_regime_profile") or {}) if isinstance(uw_attr.get("v2_uw_regime_profile"), dict) else {}).get("regime_label", "")
            (st.setdefault("positions", {}))[sym] = {
                "entry_timestamp": _now_iso(),
                "direction": str(direction),
                "entry_v2_score": float(v2_score),
                "entry_v1_score": float(v1_score),
                "entry_uw": dict(uw_attr),
                "entry_regime": str(reg),
                "entry_sector": str(sec),
                "entry_price": None,  # price unavailable in this call path (best-effort)
            }
            _write_positions(st)
            append_shadow_trade({"event_type": "shadow_entry_opened", "symbol": sym, "direction": str(direction), "v2_score": float(v2_score), "v1_score": float(v1_score)})
            return

        # Exit evaluation for open positions
        if isinstance(pos, dict):
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

            # Exit trigger thresholds (conservative, shadow-only):
            should_exit = float(exit_score) >= 0.70 and rec_reason in ("profit", "stop", "intel_deterioration", "replacement")
            if should_exit:
                # Compute paper PnL if price is known; else None
                pnl = None
                if pos.get("entry_price") is not None and pos.get("exit_price") is not None:
                    try:
                        e = float(pos.get("entry_price"))
                        x = float(pos.get("exit_price"))
                        if e > 0 and x > 0:
                            pnl = ((x - e) / e) if str(direction).lower() == "bullish" else ((e - x) / e)
                    except Exception:
                        pnl = None
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
                arec = build_exit_attribution_record(
                    symbol=sym,
                    entry_timestamp=entry_ts,
                    exit_reason=("replacement" if replacement else rec_reason),
                    pnl=pnl,
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
                )
                append_exit_attribution(arec)

                append_shadow_trade(
                    {
                        "event_type": "shadow_exit",
                        "symbol": sym,
                        "direction": str(direction),
                        "v1_score": float(v1_score),
                        "v2_score": float(v2_score),
                        "v2_exit_score": float(exit_score),
                        "v2_exit_components": dict(exit_components),
                        "v2_exit_reason": ("replacement" if replacement else rec_reason),
                        "profit_target_price": pt_px,
                        "profit_target_reasoning": pt_reason,
                        "stop_price": stop_px,
                        "stop_reasoning": stop_reason,
                        "replacement_candidate": replacement,
                        "replacement_reasoning": repl_reason if replacement else None,
                    }
                )
                # Close position
                try:
                    (st.get("positions") or {}).pop(sym, None)
                except Exception:
                    pass
                _write_positions(st)
    except Exception:
        return

