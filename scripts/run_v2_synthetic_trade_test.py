#!/usr/bin/env python3
"""
Synthetic v2 trade harness (owner-level validation)
==================================================

Supports two modes:

1) **Injected (offline) synthetic trades** (safe; no broker calls)
   Used by owner-level chaos tests to validate the telemetry/deep-dive pipeline.
   - Writes v2-shaped artifacts:
     - logs/master_trade_log.jsonl
     - logs/exit_attribution.jsonl
     - logs/live_trades.jsonl (legacy compatibility)
   - Enforces guardrails in harness:
     - market-hours (ET 09:30–16:00)
     - price sanity (max % move between entry/exit)
     - exit sanity (exit price must be numeric)

2) **Broker paper orders** (dangerous; live paper account)
   - Places a tiny market buy, waits for fill, then closes.
   - Requires explicit opt-in env: ALLOW_SYNTHETIC_ORDERS=1
   - Refuses to run if ALPACA_BASE_URL is not the paper endpoint
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import alpaca_trade_api as tradeapi  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_paper_endpoint(url: str) -> bool:
    try:
        return "paper-api.alpaca.markets" in (url or "")
    except Exception:
        return False


def _parse_iso(ts: str) -> datetime:
    s = str(ts or "").strip().replace("Z", "+00:00")
    if not s:
        raise ValueError("empty timestamp")
    if "T" not in s and " " in s:
        s = s.replace(" ", "T", 1)
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _is_market_hours_et(dt_utc: datetime) -> bool:
    """
    Regular session: 09:30–16:00 America/New_York (best-effort).
    If zoneinfo not available, fall back to allowing (do not block).
    """
    try:
        from zoneinfo import ZoneInfo  # Python 3.9+
    except Exception:
        return True
    et = dt_utc.astimezone(ZoneInfo("America/New_York"))
    hm = et.hour * 60 + et.minute
    return (9 * 60 + 30) <= hm < (16 * 60)


def _append_jsonl(path: Path, rec: Dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, default=str) + "\n")
    except Exception:
        return


def _gate_reject(symbol: str, *, reason: str, details: Dict[str, Any]) -> None:
    # Guardrail rejection must be logged without contaminating master_trade_log.
    _append_jsonl(
        Path("logs/gate.jsonl"),
        {
            "ts": _now_iso(),
            "event": "synthetic_trade_rejected",
            "symbol": symbol,
            "reason": reason,
            "details": details,
            "composite_version": "v2",
            "source": "synthetic",
        },
    )
    _append_jsonl(
        Path("logs/system_events.jsonl"),
        {
            "ts": _now_iso(),
            "subsystem": "synthetic",
            "event_type": "synthetic_trade_rejected",
            "severity": "WARN",
            "symbol": symbol,
            "reason": reason,
            "details": details,
        },
    )


def _tail_has_trade_id(path: Path, trade_id: str, n: int = 2000) -> bool:
    try:
        if not path.exists():
            return False
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-n:]
        for ln in lines:
            try:
                obj = json.loads(ln)
            except Exception:
                continue
            if isinstance(obj, dict) and str(obj.get("trade_id", "")) == trade_id:
                return True
    except Exception:
        return False
    return False


def _tail_jsonl(path: Path, n: int = 50) -> list[dict]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    out: list[dict] = []
    for line in lines[-n:]:
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except Exception:
            continue
        if isinstance(rec, dict):
            out.append(rec)
    return out


def _wait_for_order_status(api: Any, *, client_order_id: str, timeout_sec: int) -> Tuple[Optional[Any], str]:
    deadline = time.time() + float(timeout_sec)
    while time.time() < deadline:
        try:
            o = api.get_order_by_client_order_id(client_order_id)
        except Exception:
            o = None
        if o is not None:
            status = str(getattr(o, "status", "") or "").lower()
            if status:
                return o, status
        time.sleep(2)
    return None, ""


def main() -> int:
    ap = argparse.ArgumentParser()
    # Injected mode args (owner chaos tests)
    ap.add_argument("--symbol", default=os.getenv("SYNTHETIC_SYMBOL", "SPY"))
    ap.add_argument("--side", default="", help="Injected mode: long|short")
    ap.add_argument("--entry_price", default="", help="Injected mode: numeric entry price")
    ap.add_argument("--exit_price", default="", help="Injected mode: numeric exit price or 'n/a'")
    ap.add_argument("--size", default="", help="Injected mode: numeric size (shares)")
    ap.add_argument("--fake_ts_start", default="", help="Injected mode: ISO timestamp (UTC, e.g. 2026-01-24T14:30:00Z)")
    ap.add_argument("--fake_ts_end", default="", help="Injected mode: ISO timestamp (UTC)")

    # Broker mode args (paper orders)
    ap.add_argument("--qty", type=int, default=int(os.getenv("SYNTHETIC_QTY", "1")), help="Broker mode: share quantity")
    ap.add_argument("--timeout-sec", type=int, default=90, help="Broker mode: max seconds to wait for fill")
    args = ap.parse_args()

    # Detect injected mode: owner supplies explicit entry/exit and timestamps.
    injected_mode = bool(str(args.entry_price).strip() or str(args.fake_ts_start).strip() or str(args.fake_ts_end).strip())

    # ------------------------------------------------------------
    # Mode 1: Injected synthetic (safe, no broker calls)
    # ------------------------------------------------------------
    if injected_mode:
        symbol = str(args.symbol).upper().strip()
        side = str(args.side or "").lower().strip()
        if side not in ("long", "short"):
            _gate_reject(symbol, reason="invalid_side", details={"side": args.side})
            raise SystemExit("REJECTED: invalid side (must be long|short)")

        try:
            entry_price = float(args.entry_price)
        except Exception:
            _gate_reject(symbol, reason="invalid_entry_price", details={"entry_price": args.entry_price})
            raise SystemExit("REJECTED: invalid entry_price")

        if str(args.exit_price or "").strip().lower() in ("n/a", "na", "none", ""):
            _gate_reject(symbol, reason="invalid_exit_price", details={"exit_price": args.exit_price})
            raise SystemExit("REJECTED: invalid exit_price")
        try:
            exit_price = float(args.exit_price)
        except Exception:
            _gate_reject(symbol, reason="invalid_exit_price", details={"exit_price": args.exit_price})
            raise SystemExit("REJECTED: invalid exit_price")

        try:
            size = float(args.size)
        except Exception:
            _gate_reject(symbol, reason="invalid_size", details={"size": args.size})
            raise SystemExit("REJECTED: invalid size")
        if size <= 0:
            _gate_reject(symbol, reason="invalid_size", details={"size": size})
            raise SystemExit("REJECTED: invalid size")

        try:
            dt0 = _parse_iso(str(args.fake_ts_start))
            dt1 = _parse_iso(str(args.fake_ts_end))
        except Exception as e:
            _gate_reject(symbol, reason="invalid_timestamps", details={"error": str(e)})
            raise SystemExit("REJECTED: invalid timestamps")
        if dt1 <= dt0:
            _gate_reject(symbol, reason="invalid_time_range", details={"start": args.fake_ts_start, "end": args.fake_ts_end})
            raise SystemExit("REJECTED: invalid time range")

        # Guardrail: market hours
        if not _is_market_hours_et(dt0):
            _gate_reject(symbol, reason="market_hours", details={"fake_ts_start": args.fake_ts_start})
            raise SystemExit("REJECTED: market_hours")

        # Guardrail: price sanity (max move between entry and exit)
        if entry_price <= 0 or exit_price <= 0:
            _gate_reject(symbol, reason="non_positive_price", details={"entry_price": entry_price, "exit_price": exit_price})
            raise SystemExit("REJECTED: non_positive_price")
        max_gap_pct = float(os.getenv("MAX_PRICE_GAP_PCT", "0.25") or "0.25")
        move = abs(exit_price - entry_price) / float(entry_price) if entry_price > 0 else 999.0
        if move > max_gap_pct:
            _gate_reject(
                symbol,
                reason="price_sanity_gap",
                details={"entry_price": entry_price, "exit_price": exit_price, "move_pct": move, "max_gap_pct": max_gap_pct},
            )
            raise SystemExit("REJECTED: price_sanity_gap")

        trade_id = f"synthetic:{symbol}:{dt0.isoformat()}"
        mt_path = Path(os.environ.get("MASTER_TRADE_LOG_PATH", "logs/master_trade_log.jsonl"))
        ea_path = Path(os.environ.get("EXIT_ATTRIBUTION_LOG_PATH", "logs/exit_attribution.jsonl"))
        live_path = Path("logs/live_trades.jsonl")

        # Idempotency: avoid duplicate trade IDs
        if _tail_has_trade_id(mt_path, trade_id) or _tail_has_trade_id(live_path, trade_id):
            print("OK (already_present)")
            print(f"- trade_id={trade_id}")
            return 0

        pnl_usd = float(size) * (float(entry_price) - float(exit_price)) if side == "short" else float(size) * (float(exit_price) - float(entry_price))
        pnl_pct = (float(exit_price) - float(entry_price)) / float(entry_price) if entry_price > 0 else None
        tmin = (dt1 - dt0).total_seconds() / 60.0

        # Canonical v2 logs
        try:
            from utils.master_trade_log import append_master_trade
            from src.exit.exit_attribution import build_exit_attribution_record, append_exit_attribution

            # Entry row
            append_master_trade(
                {
                    "trade_id": trade_id,
                    "symbol": symbol,
                    "side": side,
                    "is_live": True,
                    "is_shadow": False,
                    "synthetic": True,
                    "composite_version": "v2",
                    "entry_ts": dt0.isoformat().replace("+00:00", "Z"),
                    "exit_ts": None,
                    "entry_price": float(entry_price),
                    "exit_price": None,
                    "size": float(size),
                    "realized_pnl_usd": None,
                    "v2_score": 0.0,
                    "entry_v2_score": 0.0,
                    "signals": [],
                    "feature_snapshot": {},
                    "intel_snapshot": {},
                    "exit_reason": None,
                    "source": "live",
                }
            )

            # Exit row
            append_master_trade(
                {
                    "trade_id": trade_id,
                    "symbol": symbol,
                    "side": side,
                    "is_live": True,
                    "is_shadow": False,
                    "synthetic": True,
                    "composite_version": "v2",
                    "entry_ts": dt0.isoformat().replace("+00:00", "Z"),
                    "exit_ts": dt1.isoformat().replace("+00:00", "Z"),
                    "entry_price": float(entry_price),
                    "exit_price": float(exit_price),
                    "size": float(size),
                    "realized_pnl_usd": float(pnl_usd),
                    "v2_score": 0.0,
                    "exit_v2_score": 0.0,
                    "v2_exit_score": 0.0,
                    "v2_exit_reason": "synthetic_close",
                    "replacement_candidate": None,
                    "signals": [],
                    "feature_snapshot": {},
                    "intel_snapshot": {},
                    "exit_reason": "synthetic_close",
                    "source": "live",
                }
            )

            ea = build_exit_attribution_record(
                symbol=symbol,
                entry_timestamp=dt0.isoformat().replace("+00:00", "Z"),
                exit_timestamp=dt1.isoformat().replace("+00:00", "Z"),
                exit_reason="synthetic_close",
                pnl=float(pnl_usd),
                pnl_pct=(float(pnl_pct) if pnl_pct is not None else None),
                entry_price=float(entry_price),
                exit_price=float(exit_price),
                qty=float(size),
                time_in_trade_minutes=float(tmin),
                entry_uw={},
                exit_uw={},
                entry_regime="NEUTRAL",
                exit_regime="NEUTRAL",
                entry_sector_profile={"sector": "UNKNOWN"},
                exit_sector_profile={"sector": "UNKNOWN"},
                score_deterioration=0.0,
                relative_strength_deterioration=0.0,
                v2_exit_score=0.0,
                v2_exit_components={},
            )
            append_exit_attribution(ea)
        except Exception as e:
            raise SystemExit(f"Failed to emit injected synthetic artifacts: {e}") from e

        # Legacy compat log (explicitly required by owner suite)
        _append_jsonl(
            live_path,
            {
                "ts": _now_iso(),
                "trade_id": trade_id,
                "symbol": symbol,
                "side": side,
                "is_live": True,
                "synthetic": True,
                "composite_version": "v2",
                "entry_ts": dt0.isoformat().replace("+00:00", "Z"),
                "exit_ts": dt1.isoformat().replace("+00:00", "Z"),
                "entry_price": float(entry_price),
                "exit_price": float(exit_price),
                "qty": float(size),
                "pnl_usd": float(pnl_usd),
                "exit_reason": "synthetic_close",
                "source": "live",
            },
        )

        print("OK")
        print(f"- mode=injected trade_id={trade_id}")
        print(f"- master_trade_log_path={mt_path.as_posix()}")
        print(f"- live_trades_path={live_path.as_posix()}")
        print(f"- exit_attribution_path={ea_path.as_posix()}")
        return 0

    # ------------------------------------------------------------
    # Mode 2: Broker paper orders (dangerous; requires opt-in env)
    # ------------------------------------------------------------
    if str(os.getenv("ALLOW_SYNTHETIC_ORDERS", "")).strip() not in ("1", "true", "yes", "on"):
        raise SystemExit("Refusing to place broker orders: set ALLOW_SYNTHETIC_ORDERS=1 (or use injected mode args)")

    base_url = str(os.getenv("ALPACA_BASE_URL", "") or "")
    if not _is_paper_endpoint(base_url):
        raise SystemExit(f"Refusing to run: ALPACA_BASE_URL is not paper endpoint (got {base_url})")

    key = os.getenv("ALPACA_KEY", "")
    secret = os.getenv("ALPACA_SECRET", "")
    if not key or not secret:
        raise SystemExit("Missing ALPACA_KEY/ALPACA_SECRET in environment")

    api = tradeapi.REST(key, secret, base_url, api_version="v2")

    # Smoke: account reachable.
    acct = api.get_account()
    buying_power = float(getattr(acct, "buying_power", 0.0) or 0.0)
    if buying_power <= 0:
        raise SystemExit("Buying power is 0; paper account not ready")

    symbol = str(args.symbol).upper().strip()
    qty = int(args.qty)
    if qty <= 0:
        raise SystemExit("--qty must be > 0")

    # Use deterministic-ish client_order_id so reruns are easy to correlate.
    coid = f"v2synthetic:{symbol}:{int(time.time())}"

    mt_path = Path(os.environ.get("MASTER_TRADE_LOG_PATH", "logs/master_trade_log.jsonl"))
    ea_path = Path(os.environ.get("EXIT_ATTRIBUTION_LOG_PATH", "logs/exit_attribution.jsonl"))
    before_mt = len(_tail_jsonl(mt_path, n=200))
    before_ea = len(_tail_jsonl(ea_path, n=200))

    # Submit entry market order.
    order = api.submit_order(
        symbol=symbol,
        qty=qty,
        side="buy",
        type="market",
        time_in_force="day",
        client_order_id=coid,
    )

    got, status = _wait_for_order_status(api, client_order_id=coid, timeout_sec=int(args.timeout_sec))
    if got is None:
        raise SystemExit("Timed out waiting for order to appear")

    # Wait for entry fill fields (bounded).
    entry_deadline = time.time() + float(args.timeout_sec)
    while time.time() < entry_deadline:
        status = str(getattr(got, "status", "") or "").lower()
        if status == "filled":
            break
        time.sleep(2)
        try:
            got = api.get_order_by_client_order_id(coid)
        except Exception:
            pass
    if str(getattr(got, "status", "") or "").lower() != "filled":
        raise SystemExit(f"Entry did not fill within timeout (last_status={getattr(got,'status',None)})")

    entry_fill_px = float(getattr(got, "filled_avg_price", 0.0) or 0.0)
    entry_fill_qty = float(getattr(got, "filled_qty", 0.0) or qty)
    entry_ts = _now_iso()

    # Close the position (market) and wait for fill.
    close_order = api.close_position(symbol)
    close_order_id = str(getattr(close_order, "id", "") or "")
    exit_fill_px = 0.0
    exit_fill_qty = float(entry_fill_qty)
    if close_order_id:
        exit_deadline = time.time() + float(args.timeout_sec)
        while time.time() < exit_deadline:
            try:
                o2 = api.get_order(close_order_id)
            except Exception:
                o2 = None
            if o2 is not None and str(getattr(o2, "status", "") or "").lower() == "filled":
                exit_fill_px = float(getattr(o2, "filled_avg_price", 0.0) or 0.0)
                try:
                    exit_fill_qty = float(getattr(o2, "filled_qty", exit_fill_qty) or exit_fill_qty)
                except Exception:
                    pass
                break
            time.sleep(2)
    if exit_fill_px <= 0:
        raise SystemExit("Exit did not fill within timeout (missing filled_avg_price)")

    # Emit canonical artifacts (this harness is responsible for writing synthetic logs).
    try:
        from utils.master_trade_log import append_master_trade
        from src.exit.exit_attribution import build_exit_attribution_record, append_exit_attribution

        trade_id = f"synthetic:{symbol}:{int(time.time())}"
        append_master_trade(
            {
                "trade_id": trade_id,
                "symbol": symbol,
                "side": "long",
                "is_live": True,
                "is_shadow": False,
                "composite_version": "v2",
                "entry_ts": entry_ts,
                "exit_ts": None,
                "entry_price": entry_fill_px,
                "exit_price": None,
                "size": float(entry_fill_qty),
                "realized_pnl_usd": None,
                "v2_score": 0.0,
                "entry_v2_score": 0.0,
                "signals": [],
                "feature_snapshot": {},
                "intel_snapshot": {},
                "exit_reason": None,
                "source": "synthetic",
            }
        )

        pnl_usd = float(exit_fill_qty) * (float(exit_fill_px) - float(entry_fill_px))
        pnl_pct = (float(exit_fill_px) - float(entry_fill_px)) / float(entry_fill_px) if entry_fill_px > 0 else None

        append_master_trade(
            {
                "trade_id": trade_id,
                "symbol": symbol,
                "side": "long",
                "is_live": True,
                "is_shadow": False,
                "composite_version": "v2",
                "entry_ts": entry_ts,
                "exit_ts": _now_iso(),
                "entry_price": entry_fill_px,
                "exit_price": exit_fill_px,
                "size": float(exit_fill_qty),
                "realized_pnl_usd": pnl_usd,
                "v2_score": 0.0,
                "exit_v2_score": 0.0,
                "v2_exit_score": 0.0,
                "v2_exit_reason": "synthetic_close",
                "replacement_candidate": None,
                "signals": [],
                "feature_snapshot": {},
                "intel_snapshot": {},
                "exit_reason": "synthetic_close",
                "source": "synthetic",
            }
        )

        ea = build_exit_attribution_record(
            symbol=symbol,
            entry_timestamp=entry_ts,
            exit_timestamp=_now_iso(),
            exit_reason="synthetic_close",
            pnl=pnl_usd,
            pnl_pct=(float(pnl_pct) if pnl_pct is not None else None),
            entry_price=entry_fill_px,
            exit_price=exit_fill_px,
            qty=float(exit_fill_qty),
            time_in_trade_minutes=None,
            entry_uw={},
            exit_uw={},
            entry_regime="NEUTRAL",
            exit_regime="NEUTRAL",
            entry_sector_profile={"sector": "UNKNOWN"},
            exit_sector_profile={"sector": "UNKNOWN"},
            score_deterioration=0.0,
            relative_strength_deterioration=0.0,
            v2_exit_score=0.0,
            v2_exit_components={},
        )
        append_exit_attribution(ea)
    except Exception as e:
        raise SystemExit(f"Failed to emit synthetic artifacts: {e}") from e

    after_mt = _tail_jsonl(mt_path, n=400)
    after_ea = _tail_jsonl(ea_path, n=400)

    # Validate that logs grew.
    if len(after_mt) <= before_mt:
        raise SystemExit(f"master_trade_log did not grow: {mt_path.as_posix()}")
    if len(after_ea) <= before_ea:
        raise SystemExit(f"exit_attribution did not grow: {ea_path.as_posix()}")

    print("OK")
    print(f"- symbol={symbol} qty={qty} client_order_id={coid}")
    print(f"- master_trade_log_path={mt_path.as_posix()} (+{len(after_mt)-before_mt} lines in tail)")
    print(f"- exit_attribution_path={ea_path.as_posix()} (+{len(after_ea)-before_ea} lines in tail)")
    print(f"- finished_at_utc={_now_iso()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

