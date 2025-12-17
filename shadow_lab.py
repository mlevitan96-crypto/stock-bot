#!/usr/bin/env python3
"""
Shadow Lab (decision journal + counterfactual evaluator).

Design:
- Append-only logs with versioned contracts (event_contracts.py)
- Centralized paths via config.registry (no hardcoded strings)
- Sidecar-only: does NOT alter trading decisions/execution
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from config.registry import LogFiles, StateFiles, append_jsonl, atomic_write_json, read_json
from event_contracts import EventType, make_event, validate_event


def _now_ts() -> int:
    return int(time.time())


def _run_id() -> str:
    # Stable for a given process lifetime
    # (kept simple; can be overridden for multi-process setups)
    return os.getenv("RUN_ID") or f"run-{os.getpid()}-{int(time.time())}"


RUN_ID = _run_id()


def _parse_iso(ts: str) -> Optional[int]:
    try:
        s = (ts or "").strip()
        if not s:
            return None
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    except Exception:
        return None


def _intent_id(symbol: str, cycle_ts: int, kind: str) -> str:
    # Deterministic-ish id so restarts don't duplicate aggressively.
    return f"intent-{symbol}-{kind}-{cycle_ts}"


def decision_candidate(
    symbol: str,
    cycle_ts: int,
    rank: int,
    direction: str = "",
    source: str = "",
    score: Optional[float] = None,
    regime: str = "",
    components: Optional[dict] = None,
    extra: Optional[dict] = None,
) -> None:
    rec = make_event(
        EventType.DECISION_CANDIDATE,
        symbol,
        run_id=RUN_ID,
        cycle_ts=int(cycle_ts),
        rank=int(rank),
        direction=direction,
        source=source,
        score=score,
        market_regime=regime,
        components=components or {},
        extra=extra or {},
    )
    validate_event(rec, raise_on_error=True)
    append_jsonl(LogFiles.DECISIONS, rec)


def decision_blocked(
    symbol: str,
    cycle_ts: int,
    reason: str,
    direction: str = "",
    score: Optional[float] = None,
    decision_price: Optional[float] = None,
    components: Optional[dict] = None,
    extra: Optional[dict] = None,
) -> None:
    rec = make_event(
        EventType.DECISION_BLOCKED,
        symbol,
        run_id=RUN_ID,
        cycle_ts=int(cycle_ts),
        reason=str(reason),
        direction=direction,
        score=score,
        decision_price=decision_price,
        components=components or {},
        extra=extra or {},
    )
    validate_event(rec, raise_on_error=True)
    append_jsonl(LogFiles.DECISIONS, rec)


def decision_taken(
    symbol: str,
    cycle_ts: int,
    side: str,
    qty: int,
    score: Optional[float] = None,
    entry_price: Optional[float] = None,
    order_type: str = "",
    extra: Optional[dict] = None,
) -> None:
    rec = make_event(
        EventType.DECISION_TAKEN,
        symbol,
        run_id=RUN_ID,
        cycle_ts=int(cycle_ts),
        side=str(side),
        qty=int(qty),
        score=score,
        entry_price=entry_price,
        order_type=order_type,
        extra=extra or {},
    )
    validate_event(rec, raise_on_error=True)
    append_jsonl(LogFiles.DECISIONS, rec)


def enqueue_shadow_intent(
    symbol: str,
    entry_ts: int,
    entry_price: float,
    direction: str,
    kind: str,
    score: Optional[float] = None,
    reason: str = "",
    horizons_min: Optional[List[int]] = None,
) -> str:
    """
    Persist a shadow intent which will be evaluated later.
    kind: 'blocked' or 'taken'
    """
    horizons_min = horizons_min or _default_horizons_min()
    intent_id = _intent_id(symbol, entry_ts, kind)

    state = read_json(StateFiles.SHADOW_PENDING, default={}) or {}
    intents = state.get("intents") or {}

    if intent_id not in intents:
        intents[intent_id] = {
            "intent_id": intent_id,
            "symbol": symbol,
            "entry_ts": int(entry_ts),
            "entry_price": float(entry_price),
            "direction": direction,
            "kind": kind,
            "score": score,
            "reason": reason,
            "horizons_min": [int(x) for x in horizons_min],
            "evaluated": {},  # horizon_min -> bool
        }
        state["intents"] = intents
        atomic_write_json(StateFiles.SHADOW_PENDING, state)

        rec = make_event(
            EventType.SHADOW_INTENT,
            symbol,
            run_id=RUN_ID,
            intent_id=intent_id,
            entry_ts=int(entry_ts),
            entry_price=float(entry_price),
            direction=direction,
            kind=kind,
            score=score,
            reason=reason,
            horizons_min=horizons_min,
        )
        validate_event(rec, raise_on_error=True)
        append_jsonl(LogFiles.SHADOW_OUTCOMES, rec)

    return intent_id


def _default_horizons_min() -> List[int]:
    raw = os.getenv("SHADOW_HORIZONS_MIN", "15,60,240,1440")
    out: List[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            out.append(int(part))
        except Exception:
            continue
    return out or [15, 60, 240, 1440]


def _ret_pct(entry: float, exit_price: float, direction: str) -> float:
    if entry <= 0:
        return 0.0
    r = (exit_price - entry) / entry
    return r * 100.0 if (direction or "").lower().startswith("bull") else (-r * 100.0)


def _default_tp_sl_grids() -> tuple[list[float], list[float]]:
    tp_raw = os.getenv("SHADOW_TP_PCTS", "1.0,2.0")
    sl_raw = os.getenv("SHADOW_SL_PCTS", "0.75,1.5")
    tps: list[float] = []
    sls: list[float] = []
    for p in tp_raw.split(","):
        try:
            tps.append(float(p.strip()))
        except Exception:
            pass
    for p in sl_raw.split(","):
        try:
            sls.append(float(p.strip()))
        except Exception:
            pass
    return (tps or [1.0, 2.0], sls or [0.75, 1.5])


def _emit_shadow_outcome(
    *,
    symbol: str,
    intent_id: str,
    horizon_min: int,
    entry_price: float,
    end_price: float,
    ret_pct: float,
    kind: str,
    score: Any,
    reason: Any,
    high: float | None,
    low: float | None,
    variant: str = "end",
    tp_pct: float | None = None,
    sl_pct: float | None = None,
    hit_tp: bool | None = None,
    hit_sl: bool | None = None,
    ambiguous: bool = False,
) -> None:
    rec = make_event(
        EventType.SHADOW_OUTCOME,
        symbol,
        run_id=RUN_ID,
        intent_id=intent_id,
        horizon_min=horizon_min,
        entry_price=entry_price,
        end_price=float(end_price),
        ret_pct=round(float(ret_pct), 6),
        high=float(high) if high is not None else None,
        low=float(low) if low is not None else None,
        kind=kind,
        score=score,
        reason=reason,
        variant=variant,
        tp_pct=tp_pct,
        sl_pct=sl_pct,
        hit_tp=hit_tp,
        hit_sl=hit_sl,
        ambiguous=ambiguous,
    )
    validate_event(rec, raise_on_error=True)
    append_jsonl(LogFiles.SHADOW_OUTCOMES, rec)


def process_shadow_pending(executor: Any) -> Dict[str, Any]:
    """
    Evaluate any pending shadow intents whose horizons have elapsed.

    Uses executor.api.get_bars(symbol, "1Min", start=..., end=...) if available to compute:
    - end_price (last close)
    - high/low over the window (for TP/SL variant analysis later)

    Returns a small summary dict.
    """
    state = read_json(StateFiles.SHADOW_PENDING, default={}) or {}
    intents: Dict[str, dict] = state.get("intents") or {}
    if not intents:
        return {"processed": 0, "evaluated": 0}

    now_ts = _now_ts()
    processed = 0
    evaluated = 0
    to_delete: List[str] = []

    for intent_id, it in list(intents.items()):
        processed += 1
        symbol = str(it.get("symbol") or "")
        entry_ts = int(it.get("entry_ts") or 0)
        entry_price = float(it.get("entry_price") or 0.0)
        direction = str(it.get("direction") or "")
        horizons = it.get("horizons_min") or []
        eval_map: Dict[str, bool] = it.get("evaluated") or {}

        all_done = True
        for h in horizons:
            h = int(h)
            due_ts = entry_ts + h * 60
            if now_ts < due_ts:
                all_done = False
                continue
            if str(h) in eval_map and eval_map.get(str(h)):
                continue

            # Fetch bars for the elapsed window if possible
            end_price = None
            hi = None
            lo = None
            try:
                api = getattr(executor, "api", None) or executor
                bars = api.get_bars(symbol, "1Min", start=datetime.fromtimestamp(entry_ts, tz=timezone.utc), end=datetime.fromtimestamp(now_ts, tz=timezone.utc)).df
                if bars is not None and len(bars) > 0:
                    try:
                        end_price = float(bars["close"].values[-1])
                        hi = float(max(bars["high"].values))
                        lo = float(min(bars["low"].values))
                    except Exception:
                        end_price = None
            except Exception:
                end_price = None

            if end_price is None:
                try:
                    end_price = float(executor.get_quote_price(symbol))  # type: ignore[attr-defined]
                except Exception:
                    end_price = None

            if end_price is None or entry_price <= 0:
                # Can't evaluate; keep pending
                all_done = False
                continue

            # Baseline outcome: hold until end of horizon
            baseline_ret = _ret_pct(entry_price, float(end_price), direction)
            _emit_shadow_outcome(
                symbol=symbol,
                intent_id=intent_id,
                horizon_min=h,
                entry_price=entry_price,
                end_price=float(end_price),
                ret_pct=float(baseline_ret),
                high=float(hi) if hi is not None else None,
                low=float(lo) if lo is not None else None,
                kind=str(it.get("kind") or ""),
                score=it.get("score"),
                reason=it.get("reason"),
                variant="end",
            )

            # Variant grid: TP/SL hit logic using high/low over the window.
            # This generates many "what-if" outcomes without changing execution.
            if hi is not None and lo is not None and entry_price > 0:
                tps, sls = _default_tp_sl_grids()
                is_bull = (direction or "").lower().startswith("bull")
                for tp in tps:
                    for sl in sls:
                        tp_hit = False
                        sl_hit = False
                        if is_bull:
                            tp_level = entry_price * (1.0 + tp / 100.0)
                            sl_level = entry_price * (1.0 - sl / 100.0)
                            tp_hit = float(hi) >= tp_level
                            sl_hit = float(lo) <= sl_level
                        else:
                            # Bearish: profit when price falls.
                            tp_level = entry_price * (1.0 - tp / 100.0)
                            sl_level = entry_price * (1.0 + sl / 100.0)
                            tp_hit = float(lo) <= tp_level
                            sl_hit = float(hi) >= sl_level

                        base_variant = f"tp{tp:g}_sl{sl:g}"
                        if tp_hit and not sl_hit:
                            _emit_shadow_outcome(
                                symbol=symbol,
                                intent_id=intent_id,
                                horizon_min=h,
                                entry_price=entry_price,
                                end_price=float(end_price),
                                ret_pct=float(tp),
                                high=float(hi),
                                low=float(lo),
                                kind=str(it.get("kind") or ""),
                                score=it.get("score"),
                                reason=it.get("reason"),
                                variant=base_variant,
                                tp_pct=float(tp),
                                sl_pct=float(sl),
                                hit_tp=True,
                                hit_sl=False,
                                ambiguous=False,
                            )
                        elif sl_hit and not tp_hit:
                            _emit_shadow_outcome(
                                symbol=symbol,
                                intent_id=intent_id,
                                horizon_min=h,
                                entry_price=entry_price,
                                end_price=float(end_price),
                                ret_pct=float(-sl),
                                high=float(hi),
                                low=float(lo),
                                kind=str(it.get("kind") or ""),
                                score=it.get("score"),
                                reason=it.get("reason"),
                                variant=base_variant,
                                tp_pct=float(tp),
                                sl_pct=float(sl),
                                hit_tp=False,
                                hit_sl=True,
                                ambiguous=False,
                            )
                        elif tp_hit and sl_hit:
                            # Ambiguous ordering; emit best/worst bounds.
                            _emit_shadow_outcome(
                                symbol=symbol,
                                intent_id=intent_id,
                                horizon_min=h,
                                entry_price=entry_price,
                                end_price=float(end_price),
                                ret_pct=float(tp),
                                high=float(hi),
                                low=float(lo),
                                kind=str(it.get("kind") or ""),
                                score=it.get("score"),
                                reason=it.get("reason"),
                                variant=base_variant + "_best",
                                tp_pct=float(tp),
                                sl_pct=float(sl),
                                hit_tp=True,
                                hit_sl=True,
                                ambiguous=True,
                            )
                            _emit_shadow_outcome(
                                symbol=symbol,
                                intent_id=intent_id,
                                horizon_min=h,
                                entry_price=entry_price,
                                end_price=float(end_price),
                                ret_pct=float(-sl),
                                high=float(hi),
                                low=float(lo),
                                kind=str(it.get("kind") or ""),
                                score=it.get("score"),
                                reason=it.get("reason"),
                                variant=base_variant + "_worst",
                                tp_pct=float(tp),
                                sl_pct=float(sl),
                                hit_tp=True,
                                hit_sl=True,
                                ambiguous=True,
                            )
                        else:
                            # Neither hit; variant equals baseline hold-to-end.
                            _emit_shadow_outcome(
                                symbol=symbol,
                                intent_id=intent_id,
                                horizon_min=h,
                                entry_price=entry_price,
                                end_price=float(end_price),
                                ret_pct=float(baseline_ret),
                                high=float(hi),
                                low=float(lo),
                                kind=str(it.get("kind") or ""),
                                score=it.get("score"),
                                reason=it.get("reason"),
                                variant=base_variant,
                                tp_pct=float(tp),
                                sl_pct=float(sl),
                                hit_tp=False,
                                hit_sl=False,
                                ambiguous=False,
                            )
            eval_map[str(h)] = True
            evaluated += 1

        it["evaluated"] = eval_map
        intents[intent_id] = it
        if all_done and horizons:
            to_delete.append(intent_id)

    for k in to_delete:
        intents.pop(k, None)

    state["intents"] = intents
    atomic_write_json(StateFiles.SHADOW_PENDING, state)
    return {"processed": processed, "evaluated": evaluated, "remaining": len(intents)}

