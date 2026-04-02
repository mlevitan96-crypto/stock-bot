"""
Paper-only execution promo: PASSIVE_THEN_CROSS vs MARKETABLE A/B (hour-sliced).

B arm: enqueue pending to state/paper_exec_pending.jsonl (non-blocking); worker completes TTL + cross.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Set, Tuple

_REPO = Path(__file__).resolve().parents[2]
_LOG_PATH = _REPO / "logs" / "paper_exec_mode_decisions.jsonl"
_PENDING_PATH = _REPO / "state" / "paper_exec_pending.jsonl"
_DONE_PATH = _REPO / "state" / "paper_exec_done.jsonl"


def pending_path() -> Path:
    return _PENDING_PATH


def done_path() -> Path:
    return _DONE_PATH


def decisions_log_path() -> Path:
    return _LOG_PATH


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


def strict_paper_gateway(config: Any) -> bool:
    return _strict_paper_gateway(config)


def fail_closed() -> bool:
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


def pretrade_key(symbol: str, side: str, ts_iso: str, mode: str) -> str:
    raw = f"{symbol}|{side}|{ts_iso}|{mode}"
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


def append_paper_exec_decision(row: Dict[str, Any]) -> None:
    try:
        _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str) + "\n")
    except Exception:
        pass


def append_paper_exec_pending(row: Dict[str, Any]) -> None:
    try:
        _PENDING_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _PENDING_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str) + "\n")
    except Exception:
        pass


def append_paper_exec_done(row: Dict[str, Any]) -> None:
    try:
        _DONE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _DONE_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str) + "\n")
    except Exception:
        pass


def load_done_pretrade_keys() -> Set[str]:
    keys: Set[str] = set()
    if not _DONE_PATH.is_file():
        return keys
    with _DONE_PATH.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
                pk = o.get("pretrade_key")
                if pk:
                    keys.add(str(pk))
            except json.JSONDecodeError:
                continue
    return keys


def load_pending_rows() -> list:
    rows = []
    if not _PENDING_PATH.is_file():
        return rows
    with _PENDING_PATH.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def _append_log(row: Dict[str, Any]) -> None:
    append_paper_exec_decision(row)


def _decision_close_from_1m_bars(api: Any, symbol: str) -> Optional[Tuple[float, str]]:
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
                "pretrade_key": pretrade_key(sym, side, ts0, "A"),
                "entry_score": entry_score,
                "regime": effective_regime,
            }
        )
        return None

    dc = _decision_close_from_1m_bars(executor.api, sym)
    if dc is None:
        if fail_closed():
            _append_log(
                {
                    "ts": ts0,
                    "symbol": sym,
                    "side": side,
                    "mode": "PASSIVE_THEN_CROSS",
                    "ab_arm": "B",
                    "ttl": ttl,
                    "error": "no_bars_for_decision_close",
                    "pretrade_key": pretrade_key(sym, side, ts0, "B_FAIL"),
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
    pk = pretrade_key(sym, side, ts0, "B_PENDING")

    q_submit = max(1, int(round(float(qty))))
    try:
        o = executor._submit_order_guarded(
            symbol=sym,
            qty=q_submit,
            side=side,
            order_type="limit",
            time_in_force="day",
            limit_price=limit_px,
            client_order_id=lim_cid,
            caller="paper_exec_mode:passive_limit_enqueue",
            extended_hours=False,
        )
        oid = getattr(o, "id", None) if o is not None else None
        if not oid:
            raise RuntimeError("no_order_id_limit")

        enq_ts = datetime.now(timezone.utc)
        deadline = enq_ts + timedelta(minutes=float(ttl))
        append_paper_exec_pending(
            {
                "pretrade_key": pk,
                "ts": ts0,
                "enqueued_ts": enq_ts.isoformat(),
                "symbol": sym,
                "side": side,
                "qty": q_submit,
                "ttl_minutes": ttl,
                "limit_px": limit_px,
                "order_id": str(oid),
                "client_order_id_lim": lim_cid,
                "client_order_id_base": cob,
                "decision_price_ref": f"decision_bar_close:{bar_ts}",
                "bars_ref": "1Min_df_iloc_-2_close",
                "deadline_iso": deadline.isoformat(),
                "deadline_epoch": deadline.timestamp(),
                "ab_arm": "B",
                "entry_score": entry_score,
                "regime": effective_regime,
                "synthetic": False,
            }
        )
        return o, None, "limit", 0, "submitted_unfilled"
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
                "pretrade_key": pretrade_key(sym, side, ts0, "B_EXC"),
            }
        )
        if fail_closed():
            return None, None, "paper_exec_error", 0, str(e)[:200]
        return None
