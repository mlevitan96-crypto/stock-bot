"""
Exit Attribution Enhancer (telemetry only; no behavior change).

For every exit: record ts_entry, ts_exit, symbol, side, exit_reason, realized PnL,
MFE/MAE (when bar data available; else N/A), time_in_trade, left_on_table, regime at entry/exit.

Outputs:
- telemetry/YYYY-MM-DD/exit_attribution.json
- telemetry/YYYY-MM-DD/computed/exit_quality_summary.json

READ-ONLY from live trading; does not change execution.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
LOGS = ROOT / "logs"
TELEMETRY_DIR = ROOT / "telemetry"
STATE = ROOT / "state"


def _parse_ts(v: Any) -> Optional[Any]:
    from datetime import datetime, timezone
    if v is None:
        return None
    try:
        if isinstance(v, (int, float)):
            return datetime.fromtimestamp(float(v), tz=timezone.utc)
        s = str(v).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _date_str(rec: dict) -> Optional[str]:
    ts = rec.get("timestamp") or rec.get("ts") or rec.get("entry_timestamp")
    dt = _parse_ts(ts)
    return dt.strftime("%Y-%m-%d") if dt else None


def _load_jsonl(path: Path, date_str: str) -> List[Dict]:
    out: List[Dict] = []
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
            d = _date_str(rec)
            if d != date_str:
                continue
            out.append(rec)
        except Exception:
            continue
    return out


def _mfe_mae_from_bars(
    bars: List[Dict],
    entry_ts: Any,
    exit_ts: Any,
    entry_price: Optional[float],
    side: str,
) -> Tuple[Optional[float], Optional[float]]:
    """Compute MFE/MAE from OHLC bars. Uses data.bars_loader.mfe_mae when available."""
    if not bars or entry_price is None or entry_price <= 0:
        return None, None
    try:
        from data.bars_loader import mfe_mae
        entry_dt = _parse_ts(entry_ts)
        exit_dt = _parse_ts(exit_ts)
        if not entry_dt or not exit_dt:
            return None, None
        return mfe_mae(bars, entry_dt, exit_dt, float(entry_price), side or "long")
    except Exception:
        return None, None


def collect_exit_records(
    date_str: str,
    exit_attr_path: Optional[Path] = None,
    attribution_path: Optional[Path] = None,
    state_dir: Optional[Path] = None,
    get_bars: Optional[Callable[[str, str, Any, Any], List[Dict]]] = None,
) -> List[Dict]:
    """
    Build enhanced exit records from logs/exit_attribution.jsonl and logs/attribution.jsonl.
    When get_bars(symbol, date_str, start_ts, end_ts) is provided, compute MFE/MAE and left_on_table.
    """
    exit_attr_path = exit_attr_path or LOGS / "exit_attribution.jsonl"
    attribution_path = attribution_path or LOGS / "attribution.jsonl"
    state_dir = state_dir or STATE
    exits = _load_jsonl(exit_attr_path, date_str)
    attr = _load_jsonl(attribution_path, date_str)
    # Build by (symbol, entry_timestamp) for PnL lookup
    attr_by_key: Dict[tuple, Dict] = {}
    for r in attr:
        if r.get("type") != "attribution" or str(r.get("trade_id", "")).startswith("open_"):
            continue
        sym = r.get("symbol")
        ts = r.get("ts") or r.get("_dt")
        entry_ts = r.get("entry_timestamp") or r.get("entry_ts")
        if not entry_ts and ts:
            entry_ts = ts
        if sym and entry_ts:
            attr_by_key[(sym, str(entry_ts)[:19])] = r

    def _regime_at(ts: Any) -> Dict[str, str]:
        out = {"regime": "", "vol_bucket": ""}
        try:
            rp = state_dir / "regime_detector_state.json"
            if rp.exists():
                data = json.loads(rp.read_text(encoding="utf-8"))
                out["regime"] = str(data.get("regime") or data.get("dominant_regime") or "")
                out["vol_bucket"] = str(data.get("volatility_bucket") or data.get("vol_bucket") or "")
        except Exception:
            pass
        return out

    records: List[Dict] = []
    for r in exits:
        ts_exit = r.get("timestamp") or r.get("ts")
        ts_entry = r.get("entry_timestamp")
        symbol = r.get("symbol") or "?"
        exit_reason = r.get("exit_reason") or "unknown"
        pnl = r.get("pnl")
        if pnl is not None:
            try:
                pnl = float(pnl)
            except Exception:
                pnl = None
        entry_price = r.get("entry_price")
        exit_price = r.get("exit_price")
        time_in_trade = r.get("time_in_trade_minutes")
        if time_in_trade is not None:
            try:
                time_in_trade = float(time_in_trade)
            except Exception:
                time_in_trade = None
        qty = r.get("qty") or r.get("quantity")
        if qty is not None:
            try:
                qty = float(qty)
            except Exception:
                qty = None
        # Side from attribution or default long
        side = "long"
        key = (symbol, (str(ts_entry) or "")[:19])
        if key in attr_by_key:
            a = attr_by_key[key]
            if a.get("side"):
                side = str(a["side"]).lower()
            if pnl is None and a.get("pnl_usd") is not None:
                pnl = float(a["pnl_usd"])
            if qty is None and a.get("qty") is not None:
                try:
                    qty = float(a["qty"])
                except Exception:
                    pass
        entry_regime = _regime_at(ts_entry)
        exit_regime = _regime_at(ts_exit)
        mfe, mae = None, None
        left_on_table = None
        if get_bars and symbol and symbol != "?" and entry_price is not None:
            try:
                entry_dt = _parse_ts(ts_entry)
                exit_dt = _parse_ts(ts_exit)
                if entry_dt and exit_dt:
                    bars = get_bars(symbol, date_str, entry_dt, exit_dt)
                    mfe, mae = _mfe_mae_from_bars(bars, ts_entry, ts_exit, entry_price, side)
                    if mfe is not None and pnl is not None:
                        mult = float(qty) if qty and qty > 0 else 1.0
                        left_on_table = round(float(mfe) * mult - float(pnl), 4)
            except Exception:
                pass
        records.append({
            "ts_entry": ts_entry,
            "ts_exit": ts_exit,
            "symbol": symbol,
            "side": side,
            "exit_reason": exit_reason,
            "realized_pnl": pnl,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "mfe": mfe,
            "mae": mae,
            "left_on_table": left_on_table,
            "time_in_trade_minutes": time_in_trade,
            "regime_entry": entry_regime,
            "regime_exit": exit_regime,
        })
    return records


def build_exit_quality_summary(records: List[Dict]) -> Dict[str, Any]:
    """Build exit_quality_summary.json content."""
    by_reason: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "count": 0, "pnl_sum": 0.0, "mfe_sum": 0.0, "mae_sum": 0.0, "left_on_table_sum": 0.0,
        "time_in_trade_minutes": [],
    })
    for r in records:
        reason = r.get("exit_reason") or "unknown"
        by_reason[reason]["count"] += 1
        pnl = r.get("realized_pnl")
        if pnl is not None:
            by_reason[reason]["pnl_sum"] += pnl
        mfe = r.get("mfe")
        mae = r.get("mae")
        left = r.get("left_on_table")
        if mfe is not None:
            by_reason[reason]["mfe_sum"] += mfe
        if mae is not None:
            by_reason[reason]["mae_sum"] += mae
        if left is not None:
            by_reason[reason]["left_on_table_sum"] += left
        elif mfe is not None and pnl is not None:
            by_reason[reason]["left_on_table_sum"] += (mfe - pnl)
        t = r.get("time_in_trade_minutes")
        if t is not None:
            by_reason[reason]["time_in_trade_minutes"].append(t)
    per_reason = {}
    for reason, v in by_reason.items():
        c = v["count"]
        times = v["time_in_trade_minutes"]
        per_reason[reason] = {
            "count": c,
            "avg_pnl": round(v["pnl_sum"] / c, 4) if c else None,
            "avg_mfe": round(v["mfe_sum"] / c, 4) if c and v["mfe_sum"] else None,
            "avg_mae": round(v["mae_sum"] / c, 4) if c and v["mae_sum"] else None,
            "left_on_table_avg": round(v["left_on_table_sum"] / c, 4) if c and v["left_on_table_sum"] else None,
            "avg_time_in_trade_minutes": round(sum(times) / len(times), 2) if times else None,
            "time_in_trade_distribution": sorted(times)[:10] if times else [],
        }
    return {
        "per_exit_reason": per_reason,
    }


def run(date_str: str, output_dir: Optional[Path] = None, get_bars: Optional[Callable] = None) -> tuple:
    """Write exit_attribution.json and computed/exit_quality_summary.json. Returns (raw_path, summary_path)."""
    output_dir = output_dir or (TELEMETRY_DIR / date_str)
    output_dir.mkdir(parents=True, exist_ok=True)
    computed_dir = output_dir / "computed"
    computed_dir.mkdir(parents=True, exist_ok=True)

    records = collect_exit_records(date_str, get_bars=get_bars)
    raw_path = output_dir / "exit_attribution.json"
    raw_path.write_text(
        json.dumps({"date": date_str, "count": len(records), "records": records}, indent=2),
        encoding="utf-8",
    )
    summary = build_exit_quality_summary(records)
    summary_path = computed_dir / "exit_quality_summary.json"
    summary_path.write_text(
        json.dumps({"date": date_str, **summary}, indent=2),
        encoding="utf-8",
    )
    return raw_path, summary_path
