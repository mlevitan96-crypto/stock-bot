"""
Paper-only execution promo: PASSIVE_THEN_CROSS vs MARKETABLE A/B (hour-sliced).

Called only from AlpacaExecutor.submit_entry when strict paper gateway is on.
Never call from live paths. Uses executor._submit_order_guarded (paper API only when Config is paper).
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Set, Tuple

_REPO = Path(__file__).resolve().parents[2]
_LOG_PATH = _REPO / "logs" / "paper_exec_mode_decisions.jsonl"


def _strict_paper_gateway(config: Any) -> bool:
    if not getattr(config, "PAPER_TRADING", True):
        return False
    base = (getattr(config, "ALPACA_BASE_URL", None) or "") or ""
    if "paper" not in str(base).lower():
        return False
    try:
        from risk_management import is_paper_mode

        return bool(is_paper_mode())
    except Exception:
        return False


def _fail_closed() -> bool:
    return os.environ.get("PAPER_EXEC_FAIL_CLOSED", "1").strip() == "1"


def _promo_enabled() -> bool:
    return os.environ.get("PAPER_EXEC_PROMO_ENABLED", "").strip().lower() in ("1", "true", "yes")


def _ttl_minutes() -> int:
    try:
        return max(1, min(30, int(os.environ.get("PAPER_EXEC_TTL_MINUTES", "3"))))
    except ValueError:
        return 3


def _universe_path() -> Path:
    p = os.environ.get("PAPER_EXEC_UNIVERSE_PATH", "").strip()
    if p:
        return Path(p)
    return _REPO / "reports" / "daily" / "2026-04-01" / "evidence" / "EXEC_MODE_UNIVERSE_TOP20_LAST3D.json"


def _load_universe_symbols() -> Set[str]:
    path = _universe_path()
    if not path.is_file():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        syms = data.get("top20_symbols_by_trade_count") or []
        return {str(s).upper() for s in syms if s}
    except Exception:
        return set()


def ab_arm_marketable_vs_treatment() -> str:
    """
    Fixed schedule: even America/New_York hour -> A (MARKETABLE baseline path).
    Odd ET hour -> B (PASSIVE_THEN_CROSS).
    Override: PAPER_EXEC_AB_FORCE=marketable|passive_then_cross
    """
    force = os.environ.get("PAPER_EXEC_AB_FORCE", "").strip().lower()
    if force in ("marketable", "m", "a"):
        return "MARKETABLE"
    if force in ("passive_then_cross", "p2", "b", "treatment"):
        return "PASSIVE_THEN_CROSS"
    try:
        from zoneinfo import ZoneInfo

        h = datetime.now(ZoneInfo("America/New_York")).hour
    except Exception:
        h = datetime.now(timezone.utc).hour
    return "MARKETABLE" if (h % 2 == 0) else "PASSIVE_THEN_CROSS"


def _pretrade_key(symbol: str, side: str, ts_iso: str, mode: str) -> str:
    raw = f"{symbol}|{side}|{ts_iso}|{mode}"
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


def _append_log(row: Dict[str, Any]) -> None:
    try:
        _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str) + "\n")
    except Exception:
        pass


def _decision_close_from_1m_bars(api: Any, symbol: str) -> Optional[Tuple[float, str]]:
    """Returns (decision_close, bar_ts_iso) using second-to-last completed bar close."""
    try:
        raw = api.get_bars(symbol, "1Min", limit=8)
        df = getattr(raw, "df", None)
        if df is None or len(df) < 2:
            return None
        row = df.iloc[-2]
        c = float(row["close"])
        ts = df.index[-2]
        ts_iso = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)
        return c, ts_iso
    except Exception:
        return None


def try_paper_exec_ab_entry(
    executor: Any,
    symbol: str,
    qty: int,
    side: str,
    ref_price: float,
    *,
    client_order_id_base: Optional[str],
    entry_score: Optional[float],
    effective_regime: str,
) -> Optional[Tuple[Any, Any, str, int, str]]:
    """
    Returns None -> caller continues normal submit_entry.
    Returns tuple -> same as submit_entry success path.
    """
    try:
        from config import Config
    except Exception:
        return None

    if not _promo_enabled():
        return None
    if not _strict_paper_gateway(Config):
        return None

    sym = str(symbol).upper()
    universe = _load_universe_symbols()
    if not universe or sym not in universe:
        return None

    arm = ab_arm_marketable_vs_treatment()
    ttl = _ttl_minutes()
    ts0 = datetime.now(timezone.utc).isoformat()

    if arm == "MARKETABLE":
        _append_log(
            {
                "ts": ts0,
                "symbol": sym,
                "side": side,
                "mode": "MARKETABLE",
                "ab_arm": "A",
                "ttl": ttl,
                "decision_price_ref": "baseline_submit_entry",
                "fill_model": "P0_delegated",
                "fill_ts": None,
                "fill_price": None,
                "cross_event": False,
                "pretrade_key": _pretrade_key(sym, side, ts0, "A"),
                "entry_score": entry_score,
                "regime": effective_regime,
            }
        )
        return None

    # B: PASSIVE_THEN_CROSS (real limit wait + market cross on Alpaca paper)
    dc = _decision_close_from_1m_bars(executor.api, sym)
    if dc is None:
        if _fail_closed():
            _append_log(
                {
                    "ts": ts0,
                    "symbol": sym,
                    "side": side,
                    "mode": "PASSIVE_THEN_CROSS",
                    "ab_arm": "B",
                    "ttl": ttl,
                    "error": "no_bars_for_decision_close",
                    "pretrade_key": _pretrade_key(sym, side, ts0, "B_FAIL"),
                }
            )
            return None, None, "paper_exec_fail_closed", 0, "paper_exec_no_bars"
        return None

    decision_close, bar_ts = dc
    try:
        from main import normalize_equity_limit_price
    except Exception:

        def normalize_equity_limit_price(x: float) -> float:
            return round(float(x), 2)

    limit_px = normalize_equity_limit_price(decision_close)
    cob = (client_order_id_base or f"pexec-{sym}")[:48]
    lim_cid = f"{cob}-pexec-lim"

    cross_event = False
    fill_ts: Optional[str] = None
    fill_price: Optional[float] = None
    fill_model = "P2_passive"
    o: Any = None
    filled_qty = 0

    try:
        q_submit = max(1, int(round(float(qty))))
        o = executor._submit_order_guarded(
            symbol=sym,
            qty=q_submit,
            side=side,
            order_type="limit",
            time_in_force="day",
            limit_price=limit_px,
            client_order_id=lim_cid,
            caller="paper_exec_mode:passive_limit",
            extended_hours=False,
        )
        oid = getattr(o, "id", None) if o is not None else None
        if not oid:
            raise RuntimeError("no_order_id_limit")

        deadline = time.time() + float(ttl * 60)
        while time.time() < deadline:
            filled, fq, fp = executor.check_order_filled(oid, max_wait_sec=4.0)
            if filled and fq > 0 and fp and fp > 0:
                fill_ts = datetime.now(timezone.utc).isoformat()
                fill_price = float(fp)
                filled_qty = int(fq)
                break
            time.sleep(3.0)

        if fill_ts:
            _append_log(
                {
                    "ts": ts0,
                    "symbol": sym,
                    "side": side,
                    "mode": "PASSIVE_THEN_CROSS",
                    "ab_arm": "B",
                    "ttl": ttl,
                    "decision_price_ref": f"decision_bar_close:{bar_ts}",
                    "decision_close": limit_px,
                    "fill_model": fill_model,
                    "fill_ts": fill_ts,
                    "fill_price": fill_price,
                    "cross_event": False,
                    "pretrade_key": _pretrade_key(sym, side, ts0, "B_PASSIVE"),
                    "entry_score": entry_score,
                    "regime": effective_regime,
                }
            )
            return o, fill_price, "limit", filled_qty, "filled"

        try:
            executor.api.cancel_order(oid)
        except Exception:
            pass

        cross_event = True
        fill_model = "P2_cross_market"
        mkt_cid = f"{cob}-pexec-mkt"
        o2 = executor._submit_order_guarded(
            symbol=sym,
            qty=q_submit,
            side=side,
            order_type="market",
            time_in_force="day",
            client_order_id=mkt_cid,
            caller="paper_exec_mode:cross_market",
            extended_hours=False,
        )
        oid2 = getattr(o2, "id", None) if o2 is not None else None
        if not oid2:
            raise RuntimeError("no_order_id_market")
        filled, fq, fp = executor.check_order_filled(oid2, max_wait_sec=15.0)
        if filled and fq > 0 and fp and fp > 0:
            fill_ts = datetime.now(timezone.utc).isoformat()
            fill_price = float(fp)
            filled_qty = int(fq)
            _append_log(
                {
                    "ts": ts0,
                    "symbol": sym,
                    "side": side,
                    "mode": "PASSIVE_THEN_CROSS",
                    "ab_arm": "B",
                    "ttl": ttl,
                    "decision_price_ref": f"decision_bar_close:{bar_ts}",
                    "decision_close": limit_px,
                    "fill_model": fill_model,
                    "fill_ts": fill_ts,
                    "fill_price": fill_price,
                    "cross_event": True,
                    "pretrade_key": _pretrade_key(sym, side, ts0, "B_CROSS"),
                    "entry_score": entry_score,
                    "regime": effective_regime,
                }
            )
            return o2, fill_price, "market", filled_qty, "filled"

        _append_log(
            {
                "ts": ts0,
                "symbol": sym,
                "side": side,
                "mode": "PASSIVE_THEN_CROSS",
                "ab_arm": "B",
                "ttl": ttl,
                "error": "market_not_filled",
                "cross_event": True,
                "pretrade_key": _pretrade_key(sym, side, ts0, "B_FAIL"),
            }
        )
        return o2, None, "market", 0, "submitted_unfilled"
    except Exception as e:
        _append_log(
            {
                "ts": ts0,
                "symbol": sym,
                "side": side,
                "mode": "PASSIVE_THEN_CROSS",
                "ab_arm": "B",
                "ttl": ttl,
                "error": str(e)[:500],
                "cross_event": cross_event,
                "pretrade_key": _pretrade_key(sym, side, ts0, "B_EXC"),
            }
        )
        if _fail_closed():
            return None, None, "paper_exec_error", 0, str(e)[:200]
        return None
