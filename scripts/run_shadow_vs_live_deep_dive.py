#!/usr/bin/env python3
"""
Shadow vs Live Deep Dive (v2-only, date-scoped, read-only)
==========================================================

Purpose:
- Historically: compare SHADOW vs LIVE performance across every major dimension.
- Now (v2-only): keep the same headings, but mark shadow-vs-live comparisons as not applicable
  when shadow artifacts are absent (shadow trading removed).

Contract:
- Additive only: writes ONLY under analysis_packs/YYYY-MM-DD/
- Safe-by-default: missing inputs are recorded; report still generates.
- Idempotent: same inputs -> same output file contents.
- MUST NOT modify any trading logic, scoring logic, or exit logic.

Inputs (best-effort; may be missing / not applicable):
- logs/master_trade_log.jsonl
- logs/exit_attribution.jsonl
- telemetry/<date>/computed/*.json
- telemetry/<date>/state/*.json
- telemetry/<date>/logs/*.jsonl
- Any UW intel snapshots available (from telemetry state + trade snapshots)

Output:
- analysis_packs/<date>/SHADOW_VS_LIVE_DEEP_DIVE.md
"""

from __future__ import annotations

import argparse
import json
import math
import os
import platform
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date as _date, datetime, time as _time, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.signal_normalization import normalize_signals  # noqa: E402

try:
    # Python 3.9+
    from zoneinfo import ZoneInfo  # type: ignore
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _today_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _read_json(path: Path) -> Any:
    try:
        return json.loads(_read_text(path))
    except Exception:
        return None


def _write_text(path: Path, text: str) -> None:
    _ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8", errors="replace")


def _utc_day_from_ts(ts: Any) -> Optional[str]:
    if ts is None:
        return None
    s = str(ts).strip()
    if not s:
        return None
    # ISO-like fast-path
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return s[:10]
    return s[:10] if len(s) >= 10 else None


def _parse_iso(ts: Any) -> Optional[datetime]:
    try:
        s = str(ts or "").strip().replace("Z", "+00:00")
        if not s:
            return None
        if "T" not in s and " " in s:
            s = s.replace(" ", "T", 1)
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _safe_float(v: Any) -> Optional[float]:
    try:
        if v is None:
            return None
        x = float(v)
        if not math.isfinite(x):
            return None
        return x
    except Exception:
        return None


def _safe_int(v: Any) -> Optional[int]:
    try:
        if v is None:
            return None
        return int(v)
    except Exception:
        return None


def _side_normalize(side: Any, direction: Any = None) -> str:
    s = str(side or "").lower().strip()
    if s in ("short", "sell", "bearish"):
        return "short"
    if s in ("long", "buy", "bullish"):
        return "long"
    d = str(direction or "").lower().strip()
    if d in ("short", "sell", "bearish"):
        return "short"
    return "long"


def _normalize_feature_snapshot(v: Any) -> Dict[str, Any]:
    return dict(v) if isinstance(v, dict) else {}


def _normalize_regime_snapshot(v: Any) -> Dict[str, Any]:
    return dict(v) if isinstance(v, dict) else {}


def _normalize_exit_reason(v: Any) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None


def _iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    """
    Stream JSONL records (safe for large files).
    Never raises; skips malformed lines.
    """
    try:
        if not path.exists() or not path.is_file():
            return
        with path.open("r", encoding="utf-8", errors="replace") as f:
            for ln in f:
                ln = (ln or "").strip()
                if not ln:
                    continue
                try:
                    obj = json.loads(ln)
                    if isinstance(obj, dict):
                        yield obj
                except Exception:
                    continue
    except Exception:
        return


def _float_fmt(x: Optional[float], nd: int = 2) -> str:
    if x is None:
        return "n/a"
    try:
        v = float(x)
        if not math.isfinite(v):
            return "n/a"
        return f"{v:,.{nd}f}"
    except Exception:
        return "n/a"


def _pct_fmt(x: Optional[float], nd: int = 2) -> str:
    if x is None:
        return "n/a"
    try:
        v = float(x)
        if not math.isfinite(v):
            return "n/a"
        return f"{v*100.0:.{nd}f}%"
    except Exception:
        return "n/a"


def _md_table(headers: List[str], rows: List[List[Any]]) -> str:
    # Minimal escaping to keep table readable.
    def esc(v: Any) -> str:
        s = "" if v is None else str(v)
        s = s.replace("\n", " ").replace("|", "\\|")
        return s

    out: List[str] = []
    out.append("| " + " | ".join([esc(h) for h in headers]) + " |")
    out.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for r in rows:
        out.append("| " + " | ".join([esc(x) for x in r]) + " |")
    return "\n".join(out) + "\n"


def _basic_stats(values: List[float]) -> Dict[str, Any]:
    xs = [float(x) for x in values if _safe_float(x) is not None]
    xs = [float(x) for x in xs if math.isfinite(float(x))]
    if not xs:
        return {"n": 0}
    xs.sort()
    n = len(xs)
    mean = sum(xs) / float(n) if n else 0.0
    med = xs[n // 2] if (n % 2 == 1) else (xs[n // 2 - 1] + xs[n // 2]) / 2.0

    def pct(p: float) -> float:
        if n == 1:
            return xs[0]
        i = int(round((p / 100.0) * (n - 1)))
        i = max(0, min(n - 1, i))
        return xs[i]

    return {
        "n": n,
        "min": xs[0],
        "p25": pct(25),
        "p50": pct(50),
        "p75": pct(75),
        "max": xs[-1],
        "mean": mean,
        "median": med,
    }


def _compute_pnl_from_prices(entry_price: Optional[float], exit_price: Optional[float], qty: Optional[float], side: str) -> Optional[float]:
    try:
        e = _safe_float(entry_price)
        x = _safe_float(exit_price)
        q = _safe_float(qty)
        if e is None or x is None or q is None:
            return None
        if e <= 0 or x <= 0 or q <= 0:
            return None
        pnl = q * (e - x) if side == "short" else q * (x - e)
        return float(pnl)
    except Exception:
        return None


def _infer_sector(rec: Dict[str, Any]) -> str:
    # Best-effort sector extraction from multiple potential locations.
    for k in ("sector", "entry_sector", "exit_sector"):
        v = rec.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip().upper()
    fs = rec.get("feature_snapshot") if isinstance(rec.get("feature_snapshot"), dict) else {}
    for k in ("sector", "sector_name", "sector_label"):
        v = fs.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip().upper()
    rs = rec.get("regime_snapshot") if isinstance(rec.get("regime_snapshot"), dict) else {}
    for k in ("sector", "sector_label"):
        v = rs.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip().upper()
    # Exit attribution schema (shadow-only)
    attrib = rec.get("_exit_attrib") if isinstance(rec.get("_exit_attrib"), dict) else {}
    entry_sector_profile = attrib.get("entry_sector_profile") if isinstance(attrib.get("entry_sector_profile"), dict) else {}
    v = entry_sector_profile.get("sector")
    if isinstance(v, str) and v.strip():
        return v.strip().upper()
    return "UNKNOWN"


def _infer_regime(rec: Dict[str, Any]) -> str:
    for k in ("regime", "entry_regime", "exit_regime", "regime_label"):
        v = rec.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    rs = rec.get("regime_snapshot") if isinstance(rec.get("regime_snapshot"), dict) else {}
    for k in ("regime_label", "regime", "label"):
        v = rs.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    attrib = rec.get("_exit_attrib") if isinstance(rec.get("_exit_attrib"), dict) else {}
    v = attrib.get("entry_regime")
    if isinstance(v, str) and v.strip():
        return v.strip()
    return ""


def _trade_key(rec: Dict[str, Any]) -> Tuple[str, str]:
    # Used to merge shadow exits (exit_attribution) onto master trades.
    sym = str(rec.get("symbol", "") or "").upper()
    entry_ts = str(rec.get("entry_ts") or rec.get("entry_timestamp") or rec.get("entry_time") or "").strip()
    return sym, entry_ts


def _clean_trade_schema(t: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enforce a consistent, analysis-safe schema for appendix rows.
    This is reporting-only (no changes to trading logic).
    """
    out = dict(t or {})
    out.setdefault("trade_id", out.get("trade_id") or out.get("id") or "")
    out["symbol"] = str(out.get("symbol", "") or "").upper()
    out["source"] = str(out.get("source", "") or "unknown")
    out["side"] = _side_normalize(out.get("side"), out.get("direction"))
    out["entry_ts"] = out.get("entry_ts") or ""
    out["exit_ts"] = out.get("exit_ts") or None
    out["entry_price"] = _safe_float(out.get("entry_price"))
    out["exit_price"] = _safe_float(out.get("exit_price"))
    out["qty"] = _safe_float(out.get("qty"))
    out["realized_pnl_usd"] = _safe_float(out.get("realized_pnl_usd"))
    out["unrealized_pnl_usd"] = _safe_float(out.get("unrealized_pnl_usd"))
    out["pnl_total_usd"] = _safe_float(out.get("pnl_total_usd"))
    out["signals"] = normalize_signals(out.get("signals"))
    out["feature_snapshot"] = _normalize_feature_snapshot(out.get("feature_snapshot"))
    out["regime_snapshot"] = _normalize_regime_snapshot(out.get("regime_snapshot"))
    out["exit_reason"] = _normalize_exit_reason(out.get("exit_reason"))
    out["sector"] = _infer_sector(out)
    out["regime"] = _infer_regime(out)
    out["time_in_trade_minutes"] = _safe_float(out.get("time_in_trade_minutes"))
    # carry-through optional merge artifacts (appendix only)
    if "_exit_attrib" in out and not isinstance(out.get("_exit_attrib"), dict):
        out["_exit_attrib"] = None
    return out


def _parse_yyyy_mm_dd(s: str) -> _date:
    try:
        return datetime.strptime(str(s).strip(), "%Y-%m-%d").date()
    except Exception:
        raise ValueError(f"Invalid date: {s!r} (expected YYYY-MM-DD)")


def _iter_dates(start: _date, end: _date) -> List[str]:
    if end < start:
        return []
    out: List[str] = []
    d = start
    while d <= end:
        out.append(d.strftime("%Y-%m-%d"))
        d = d + timedelta(days=1)
    return out


def _resolve_date_range(args: argparse.Namespace) -> Tuple[str, List[str], str]:
    """
    Returns:
    - range_label: "YYYY-MM-DD" or "YYYY-MM-DD_to_YYYY-MM-DD"
    - days: list of YYYY-MM-DD strings (inclusive)
    - mode: "single" | "range"
    """
    date_arg = (getattr(args, "date", "") or "").strip()
    sd = (getattr(args, "start_date", "") or "").strip()
    ed = (getattr(args, "end_date", "") or "").strip()

    if sd or ed:
        if not (sd and ed):
            # best-effort: treat missing one side as the other
            sd = sd or ed
            ed = ed or sd
        start = _parse_yyyy_mm_dd(sd)
        end = _parse_yyyy_mm_dd(ed)
        days = _iter_dates(start, end)
        label = f"{days[0]}_to_{days[-1]}" if days else f"{sd}_to_{ed}"
        return label, days, "range"

    day = (date_arg or _today_utc()).strip()
    # validate
    _ = _parse_yyyy_mm_dd(day)
    return day, [day], "single"


def _market_hours_flags(ts: Any) -> Tuple[bool, Optional[str]]:
    """
    Returns (outside_market_hours, note).
    Uses America/New_York regular session 09:30–16:00 (best-effort).
    """
    dt = _parse_iso(ts)
    if not dt:
        return False, "timestamp_unparseable"
    if ZoneInfo is None:
        # Best-effort fallback: treat UTC as local.
        return False, "zoneinfo_unavailable"
    try:
        et = dt.astimezone(ZoneInfo("America/New_York"))
        o = datetime.combine(et.date(), _time(9, 30), tzinfo=et.tzinfo)
        c = datetime.combine(et.date(), _time(16, 0), tzinfo=et.tzinfo)
        outside = not (o <= et <= c)
        return outside, None
    except Exception:
        return False, "tz_convert_failed"


@dataclass(frozen=True)
class ShadowIntegrityIssue:
    kind: str
    symbol: str
    day: str
    trade_id: str
    detail: str


def _normalize_master_trade(rec: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = dict(rec or {})
    out["symbol"] = str(out.get("symbol", "") or "").upper()
    out["signals"] = normalize_signals(out.get("signals"))
    out["feature_snapshot"] = _normalize_feature_snapshot(out.get("feature_snapshot"))
    out["regime_snapshot"] = _normalize_regime_snapshot(out.get("regime_snapshot"))
    out["exit_reason"] = _normalize_exit_reason(out.get("exit_reason"))

    source = str(out.get("source") or "").lower().strip()
    is_live = bool(out.get("is_live")) or (source == "live")
    is_shadow = bool(out.get("is_shadow")) or (source == "shadow")
    if source not in ("live", "shadow"):
        source = "live" if is_live and not is_shadow else ("shadow" if is_shadow and not is_live else (source or "unknown"))
    out["source"] = source
    out["side"] = _side_normalize(out.get("side"), out.get("direction"))

    # Canonical timestamps
    out["entry_ts"] = out.get("entry_ts") or out.get("entry_timestamp") or out.get("entry_time") or out.get("ts") or out.get("timestamp")
    out["exit_ts"] = out.get("exit_ts") or out.get("exit_timestamp") or out.get("exit_time")

    # Canonical prices / sizes
    out["entry_price"] = _safe_float(out.get("entry_price"))
    out["exit_price"] = _safe_float(out.get("exit_price"))
    out["qty"] = _safe_float(out.get("qty") or out.get("size") or out.get("shares"))

    realized = _safe_float(out.get("realized_pnl_usd") or out.get("pnl_usd") or out.get("pnl"))
    unreal = _safe_float(out.get("unrealized_pnl_usd") or out.get("unrealized_pnl"))
    if realized is None:
        realized = _compute_pnl_from_prices(out.get("entry_price"), out.get("exit_price"), out.get("qty"), out["side"])
    out["realized_pnl_usd"] = realized
    out["unrealized_pnl_usd"] = unreal
    out["pnl_total_usd"] = (float(realized or 0.0) + float(unreal or 0.0)) if (realized is not None or unreal is not None) else None

    # Time-in-trade minutes
    dt0 = _parse_iso(out.get("entry_ts"))
    dt1 = _parse_iso(out.get("exit_ts"))
    if dt0 and dt1:
        out["time_in_trade_minutes"] = (dt1 - dt0).total_seconds() / 60.0
    else:
        out["time_in_trade_minutes"] = _safe_float(out.get("time_in_trade_minutes"))

    # Derived labels
    out["sector"] = _infer_sector(out)
    out["regime"] = _infer_regime(out)
    return _clean_trade_schema(out)


def _load_trades_for_days(days_set: set, master_log: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for rec in _iter_jsonl(master_log):
        entry_day = _utc_day_from_ts(rec.get("entry_ts") or rec.get("entry_timestamp") or rec.get("timestamp") or rec.get("ts"))
        exit_day = _utc_day_from_ts(rec.get("exit_ts") or rec.get("exit_timestamp"))
        if (entry_day not in days_set) and (exit_day not in days_set):
            continue
        t = _normalize_master_trade(rec)
        t["entry_day"] = entry_day
        t["exit_day"] = exit_day
        rows.append(t)
    return rows


def _load_exit_attribution_for_days(days_set: set, path: Path) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for rec in _iter_jsonl(path):
        d = _utc_day_from_ts(rec.get("timestamp") or rec.get("ts"))
        if d not in days_set:
            continue
        if isinstance(rec, dict):
            r = dict(rec)
            r["symbol"] = str(r.get("symbol", "") or "").upper()
            r["exit_reason"] = _normalize_exit_reason(r.get("exit_reason"))
            r["_day"] = d
            out.append(r)
    return out


def _load_shadow_events_for_days(days_set: set, path: Path) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for rec in _iter_jsonl(path):
        d = _utc_day_from_ts(rec.get("ts") or rec.get("timestamp"))
        if d not in days_set:
            continue
        if isinstance(rec, dict):
            r = dict(rec)
            r["symbol"] = str(r.get("symbol", "") or "").upper()
            r["signals"] = normalize_signals(r.get("signals"))
            r["_day"] = d
            out.append(r)
    return out


def _merge_exit_attribution(trades: List[Dict[str, Any]], exit_attrib: List[Dict[str, Any]]) -> None:
    by_key: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for r in exit_attrib:
        sym = str(r.get("symbol", "") or "").upper()
        ent = str(r.get("entry_timestamp", "") or "").strip()
        if sym and ent:
            by_key[(sym, ent)] = r
    for t in trades:
        sym, ent = _trade_key(t)
        attrib = by_key.get((sym, ent))
        if attrib:
            t["_exit_attrib"] = attrib
            # Prefer attribution exit_reason when missing.
            if t.get("exit_reason") is None:
                t["exit_reason"] = _normalize_exit_reason(attrib.get("exit_reason"))
            # Prefer attribution pnl when missing.
            if t.get("realized_pnl_usd") is None:
                t["realized_pnl_usd"] = _safe_float(attrib.get("pnl"))
                t["pnl_total_usd"] = t.get("realized_pnl_usd")
            if t.get("time_in_trade_minutes") is None:
                t["time_in_trade_minutes"] = _safe_float(attrib.get("time_in_trade_minutes"))
            # Enrich sector/regime if available.
            if t.get("sector") in (None, "", "UNKNOWN"):
                t["sector"] = _infer_sector(t)
            if not t.get("regime"):
                t["regime"] = _infer_regime(t)
            # keep schema consistent post-merge
            cleaned = _clean_trade_schema(t)
            t.clear()
            t.update(cleaned)


def _split_live_shadow(trades: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    live: List[Dict[str, Any]] = []
    shadow: List[Dict[str, Any]] = []
    for t in trades:
        src = str(t.get("source") or "").lower()
        if src == "shadow" or bool(t.get("is_shadow")):
            shadow.append(t)
        elif src == "live" or bool(t.get("is_live")):
            live.append(t)
        else:
            # Best-effort classification fallback (if unknown, treat as live-like).
            live.append(t)
    return live, shadow


def _closed_trades(trades: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for t in trades:
        pnl = _safe_float(t.get("realized_pnl_usd"))
        if pnl is None:
            # Treat as closed if exit_ts exists and pnl_total computed.
            if t.get("exit_ts") and _safe_float(t.get("pnl_total_usd")) is not None:
                out.append(t)
            continue
        out.append(t)
    return out


def _perf_block(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    closed = _closed_trades(trades)
    pnls = [float(t.get("realized_pnl_usd") or 0.0) for t in closed]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    win_rate = (len(wins) / float(len(pnls))) if pnls else 0.0
    avg_win = (sum(wins) / float(len(wins))) if wins else 0.0
    avg_loss = (sum(losses) / float(len(losses))) if losses else 0.0
    expectancy = (sum(pnls) / float(len(pnls))) if pnls else 0.0
    tmins = [float(t.get("time_in_trade_minutes")) for t in closed if _safe_float(t.get("time_in_trade_minutes")) is not None]
    avg_tmin = (sum(tmins) / float(len(tmins))) if tmins else None
    exit_reasons = Counter([str(t.get("exit_reason") or "") for t in closed])
    sides = Counter([str(t.get("side") or "") for t in trades])
    realized = sum([float(t.get("realized_pnl_usd") or 0.0) for t in closed]) if closed else 0.0
    unreal = sum([float(t.get("unrealized_pnl_usd") or 0.0) for t in trades if _safe_float(t.get("unrealized_pnl_usd")) is not None]) or 0.0
    return {
        "trade_count_total": len(trades),
        "trade_count_closed": len(closed),
        "pnl_realized_usd": realized,
        "pnl_unrealized_usd": unreal,
        "pnl_total_usd": realized + unreal,
        "win_rate": win_rate,
        "expectancy_usd": expectancy,
        "avg_win_usd": avg_win,
        "avg_loss_usd": avg_loss,
        "avg_time_in_trade_minutes": avg_tmin,
        "exit_reason_distribution": dict(exit_reasons),
        "long_short_breakdown": dict(sides),
    }


def _group_by(trades: List[Dict[str, Any]], key_fn) -> Dict[str, List[Dict[str, Any]]]:
    out: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for t in trades:
        k = key_fn(t)
        out[str(k)].append(t)
    return out


def _numeric_feature_means(trades: List[Dict[str, Any]]) -> Dict[str, float]:
    sums: Dict[str, float] = defaultdict(float)
    cnts: Dict[str, int] = defaultdict(int)
    for t in trades:
        fs = t.get("feature_snapshot") if isinstance(t.get("feature_snapshot"), dict) else {}
        for k, v in fs.items():
            x = _safe_float(v)
            if x is None:
                continue
            sums[str(k)] += float(x)
            cnts[str(k)] += 1
    means: Dict[str, float] = {}
    for k, s in sums.items():
        n = cnts.get(k, 0) or 0
        if n:
            means[k] = float(s) / float(n)
    return means


def _collect_signals(trades: List[Dict[str, Any]]) -> List[str]:
    c = Counter()
    for t in trades:
        for s in normalize_signals(t.get("signals")):
            c[str(s)] += 1
    # deterministic output: by count desc, then name
    return [k for k, _ in sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))]


def _quantile_bins(xs: List[float], bins: int = 10) -> List[float]:
    ys = [float(x) for x in xs if _safe_float(x) is not None]
    ys.sort()
    if not ys:
        return []
    if len(ys) < bins:
        # unique-ish breakpoints
        uniq = sorted(set(ys))
        return uniq
    edges: List[float] = []
    for i in range(bins + 1):
        q = i / float(bins)
        idx = int(round(q * (len(ys) - 1)))
        idx = max(0, min(len(ys) - 1, idx))
        edges.append(float(ys[idx]))
    # ensure monotonic and unique
    out: List[float] = []
    for e in edges:
        if not out or e > out[-1]:
            out.append(e)
    return out


def _bin_index(edges: List[float], x: float) -> int:
    # edges sorted ascending; last edge is max. Return bin index in [0, len(edges)-2]
    if len(edges) < 2:
        return 0
    if x <= edges[0]:
        return 0
    for i in range(1, len(edges)):
        if x <= edges[i]:
            return max(0, i - 1)
    return len(edges) - 2


def _psi(d1: List[float], d2: List[float], bins: int = 10) -> Optional[float]:
    # Population Stability Index using common quantile edges (from pooled data).
    a = [float(x) for x in d1 if _safe_float(x) is not None]
    b = [float(x) for x in d2 if _safe_float(x) is not None]
    if len(a) < 10 or len(b) < 10:
        return None
    edges = _quantile_bins(a + b, bins=bins)
    if len(edges) < 3:
        return None
    ca = [0] * (len(edges) - 1)
    cb = [0] * (len(edges) - 1)
    for x in a:
        ca[_bin_index(edges, x)] += 1
    for x in b:
        cb[_bin_index(edges, x)] += 1
    na = float(sum(ca)) or 1.0
    nb = float(sum(cb)) or 1.0
    psi = 0.0
    for i in range(len(ca)):
        pa = max(1e-9, ca[i] / na)
        pb = max(1e-9, cb[i] / nb)
        psi += (pa - pb) * math.log(pa / pb)
    return float(psi) if math.isfinite(psi) else None


def _ev_curve(trades: List[Dict[str, Any]], feature: str, bins: int = 10) -> Dict[str, Any]:
    xs: List[float] = []
    ys: List[float] = []
    for t in _closed_trades(trades):
        fs = t.get("feature_snapshot") if isinstance(t.get("feature_snapshot"), dict) else {}
        x = _safe_float(fs.get(feature))
        p = _safe_float(t.get("realized_pnl_usd"))
        if x is None or p is None:
            continue
        xs.append(float(x))
        ys.append(float(p))
    if len(xs) < 10:
        return {"n": len(xs), "bins": []}
    edges = _quantile_bins(xs, bins=bins)
    if len(edges) < 2:
        return {"n": len(xs), "bins": []}
    sums = [0.0] * (len(edges) - 1)
    cnts = [0] * (len(edges) - 1)
    for x, p in zip(xs, ys):
        bi = _bin_index(edges, x)
        sums[bi] += float(p)
        cnts[bi] += 1
    out_bins: List[Dict[str, Any]] = []
    for i in range(len(sums)):
        out_bins.append(
            {
                "x_lo": edges[i],
                "x_hi": edges[i + 1],
                "count": cnts[i],
                "avg_pnl_usd": (sums[i] / float(cnts[i])) if cnts[i] else 0.0,
            }
        )
    return {"n": len(xs), "bins": out_bins}


def _load_telemetry_bundle(day: str) -> Dict[str, Any]:
    base = ROOT / "telemetry" / day
    out: Dict[str, Any] = {"_base": str(base), "computed": {}, "state": {}, "logs": {}}
    if not base.exists() or not base.is_dir():
        return out
    # computed
    comp = base / "computed"
    if comp.exists() and comp.is_dir():
        for p in sorted(comp.glob("*.json")):
            out["computed"][p.name] = _read_json(p)
    # state
    st = base / "state"
    if st.exists() and st.is_dir():
        for p in sorted(st.glob("*.json")):
            out["state"][p.name] = _read_json(p)
    # logs (jsonl)
    lg = base / "logs"
    if lg.exists() and lg.is_dir():
        for p in sorted(lg.glob("*.jsonl")):
            # Keep logs lightweight; only load first N lines for appendix.
            lines = _read_text(p).splitlines()
            out["logs"][p.name] = lines[:5000]
    return out


def _uw_snapshots_from_telemetry_state(telemetry_state: Dict[str, Any]) -> List[Dict[str, Any]]:
    snaps: List[Dict[str, Any]] = []
    for name, doc in (telemetry_state or {}).items():
        if not isinstance(doc, dict):
            continue
        # Heuristics: these are typical UW intel state files.
        if "uw" in name.lower() or "intel" in name.lower() or "unusual" in name.lower():
            snaps.append({"_file": name, **doc})
            continue
        # Or: content includes obvious UW keys.
        keys = " ".join([str(k).lower() for k in doc.keys()])
        if "unusual" in keys or "uw_" in keys or "flow" in keys:
            snaps.append({"_file": name, **doc})
    return snaps


def _uw_families_from_trade_snapshots(trades: List[Dict[str, Any]]) -> Dict[str, Counter]:
    """
    Build UW "feature family" usage counts from trade feature_snapshot keys.
    Family mapping is heuristic and advisory-only.
    """
    fam = defaultdict(Counter)
    for t in trades:
        fs = t.get("feature_snapshot") if isinstance(t.get("feature_snapshot"), dict) else {}
        for k, v in fs.items():
            key = str(k)
            if not key.lower().startswith("uw_"):
                continue
            x = _safe_float(v)
            if x is None:
                continue
            # family is uw_<family>_...
            parts = key.split("_")
            family = parts[1] if len(parts) >= 2 else "unknown"
            fam[family]["count"] += 1
    return {k: v for k, v in fam.items()}


def _load_telemetry_bundles(days: List[str]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for d in days:
        out[d] = _load_telemetry_bundle(d)
    return out


def _shadow_price_bounds_from_events(shadow_events: List[Dict[str, Any]]) -> Dict[Tuple[str, str], Dict[str, float]]:
    """
    Compute per-(day,symbol) price min/max from shadow events (current_price/entry_price/exit_price).
    This satisfies "bar source if available, or from shadow price logs" using shadow logs.
    """
    bounds: Dict[Tuple[str, str], Dict[str, float]] = {}
    for e in shadow_events:
        d = str(e.get("_day") or "")
        sym = str(e.get("symbol") or "").upper()
        if not d or not sym:
            continue
        xs: List[float] = []
        for k in ("current_price", "entry_price", "exit_price"):
            v = _safe_float(e.get(k))
            if v is not None and v > 0:
                xs.append(float(v))
        if not xs:
            continue
        key = (d, sym)
        if key not in bounds:
            bounds[key] = {"min": min(xs), "max": max(xs)}
        else:
            bounds[key]["min"] = min(bounds[key]["min"], min(xs))
            bounds[key]["max"] = max(bounds[key]["max"], max(xs))
    return bounds


def _shadow_integrity_audit(
    *,
    days: List[str],
    shadow_trades: List[Dict[str, Any]],
    shadow_events: List[Dict[str, Any]],
    max_expected_minutes: float = 2.0 * 24.0 * 60.0,
) -> Dict[str, Any]:
    """
    Shadow-centric integrity audit:
    - price sanity (range vs observed min/max from shadow price logs)
    - pnl sanity (recompute from prices/qty/side)
    - time sanity (negative, too long)
    - exit sanity (inconsistent exit fields)
    """
    days_set = set(days)
    bounds = _shadow_price_bounds_from_events(shadow_events)

    issues: List[ShadowIntegrityIssue] = []
    counts = Counter()

    # Build a quick per-(day,symbol) median-ish price for gap checks
    px_samples: Dict[Tuple[str, str], List[float]] = defaultdict(list)
    for e in shadow_events:
        d = str(e.get("_day") or "")
        sym = str(e.get("symbol") or "").upper()
        if d in days_set and sym:
            v = _safe_float(e.get("current_price"))
            if v is not None and v > 0:
                px_samples[(d, sym)].append(float(v))
    px_ref: Dict[Tuple[str, str], float] = {}
    for k, xs in px_samples.items():
        xs2 = sorted(xs)
        if xs2:
            px_ref[k] = xs2[len(xs2) // 2]

    def record(kind: str, t: Dict[str, Any], detail: str) -> None:
        counts[kind] += 1
        issues.append(
            ShadowIntegrityIssue(
                kind=kind,
                symbol=str(t.get("symbol") or "").upper(),
                day=str(t.get("entry_day") or t.get("exit_day") or ""),
                trade_id=str(t.get("trade_id") or ""),
                detail=str(detail),
            )
        )

    closed = _closed_trades(shadow_trades)
    for t in shadow_trades:
        sym = str(t.get("symbol") or "").upper()
        day = str(t.get("entry_day") or t.get("exit_day") or "")
        if day and day not in days_set:
            continue
        key = (day, sym)
        b = bounds.get(key)
        ref = px_ref.get(key)

        entry_price = _safe_float(t.get("entry_price"))
        exit_price = _safe_float(t.get("exit_price"))
        entry_ts = t.get("entry_ts")
        exit_ts = t.get("exit_ts")

        # Market hours sanity
        outside_entry, note_entry = _market_hours_flags(entry_ts)
        outside_exit, note_exit = _market_hours_flags(exit_ts) if exit_ts else (False, None)
        if outside_entry:
            record("trades_outside_market_hours", t, f"entry_ts={entry_ts} note={note_entry}")
        if outside_exit:
            record("trades_outside_market_hours", t, f"exit_ts={exit_ts} note={note_exit}")

        # Price range sanity vs observed min/max
        if b:
            lo = float(b["min"])
            hi = float(b["max"])
            tol = 0.02  # 2% tolerance vs observed range
            if entry_price is not None and (entry_price < lo * (1 - tol) or entry_price > hi * (1 + tol)):
                record("out_of_range_prices", t, f"entry_price={entry_price} observed_min={lo} observed_max={hi}")
            if exit_price is not None and (exit_price < lo * (1 - tol) or exit_price > hi * (1 + tol)):
                record("out_of_range_prices", t, f"exit_price={exit_price} observed_min={lo} observed_max={hi}")
        # Extreme gap sanity vs reference price
        if ref and entry_price is not None and ref > 0:
            gap = abs(entry_price - ref) / ref
            if gap >= 0.25:
                record("extreme_gaps", t, f"entry_price={entry_price} ref_price={ref} gap_pct={round(gap*100.0,2)}")
        if ref and exit_price is not None and ref > 0:
            gap = abs(exit_price - ref) / ref
            if gap >= 0.25:
                record("extreme_gaps", t, f"exit_price={exit_price} ref_price={ref} gap_pct={round(gap*100.0,2)}")

        # Exit sanity (field consistency)
        if exit_ts and t.get("exit_reason") in (None, "", "n/a"):
            record("exit_reason_missing", t, f"exit_ts present but exit_reason missing (exit_ts={exit_ts})")
        if (not exit_ts) and _safe_float(t.get("realized_pnl_usd")) is not None:
            record("exit_ts_missing", t, f"realized_pnl_usd present but exit_ts missing (pnl={t.get('realized_pnl_usd')})")

    # PnL + time sanity only for closed trades
    for t in closed:
        entry_price = _safe_float(t.get("entry_price"))
        exit_price = _safe_float(t.get("exit_price"))
        qty = _safe_float(t.get("qty"))
        side = str(t.get("side") or "long")
        pnl = _safe_float(t.get("realized_pnl_usd"))
        if entry_price is not None and exit_price is not None and qty is not None and pnl is not None and qty > 0:
            expected = _compute_pnl_from_prices(entry_price, exit_price, qty, side)
            if expected is not None:
                eps = max(0.02, 0.001 * abs(expected) + 0.02)
                if abs(pnl - expected) > eps:
                    record("mismatched_pnl", t, f"pnl={pnl} expected={expected} eps={eps} entry={entry_price} exit={exit_price} qty={qty} side={side}")
        # time sanity
        tmin = _safe_float(t.get("time_in_trade_minutes"))
        if tmin is not None:
            if tmin < -1e-6:
                record("negative_durations", t, f"time_in_trade_minutes={tmin}")
            if tmin > max_expected_minutes:
                record("durations_too_long", t, f"time_in_trade_minutes={tmin} max_expected_minutes={max_expected_minutes}")

    # Summaries
    out = {
        "counts": dict(counts),
        "total_shadow_trades": len(shadow_trades),
        "closed_shadow_trades": len(closed),
        "issues": [i.__dict__ for i in issues[:1000]],  # cap to keep report size bounded
        "notes": {
            "price_bounds_source": "shadow_events (current_price/entry_price/exit_price)",
            "market_hours": "America/New_York regular session 09:30–16:00 (best-effort)",
            "max_expected_minutes": max_expected_minutes,
            "issues_capped": len(issues) > 1000,
        },
    }
    return out


def _shape_monotonicity(bins: List[Dict[str, Any]]) -> Dict[str, Any]:
    ys = [float(_safe_float(b.get("avg_pnl_usd")) or 0.0) for b in (bins or [])]
    if len(ys) < 2:
        return {"monotonicity": None, "slope": None, "note": "insufficient_bins"}
    slope = ys[-1] - ys[0]
    good = 0
    tot = 0
    for i in range(1, len(ys)):
        dy = ys[i] - ys[i - 1]
        if dy == 0:
            continue
        tot += 1
        if slope >= 0 and dy > 0:
            good += 1
        if slope < 0 and dy < 0:
            good += 1
    mono = (good / float(tot)) if tot else 0.0
    return {"monotonicity": mono, "slope": slope, "bin_count": len(ys)}


def _per_day_shadow_metrics(days: List[str], shadow_trades: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    by_day: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for t in shadow_trades:
        d = str(t.get("entry_day") or t.get("exit_day") or "")
        if d in set(days):
            by_day[d].append(t)
    out: Dict[str, Dict[str, Any]] = {}
    for d in days:
        pb = _perf_block(by_day.get(d, []))
        out[d] = pb
    return out


def _render_report(
    *,
    range_label: str,
    days: List[str],
    mode: str,
    trades_live: List[Dict[str, Any]],
    trades_shadow: List[Dict[str, Any]],
    exit_attrib_today: List[Dict[str, Any]],
    telemetry: Dict[str, Any],  # kept for backwards compatibility (single-day)
    telemetry_by_day: Dict[str, Dict[str, Any]],
    shadow_events_today: List[Dict[str, Any]],
    anomalies: List[str],
    missing_inputs: List[str],
) -> str:
    lines: List[str] = []

    # Metadata
    lines.append(f"# SHADOW vs LIVE Deep Dive — {range_label}")
    lines.append("")
    lines.append("## Data source & build metadata")
    lines.append(f"- Generated at (UTC): **{_now_iso()}**")
    lines.append(f"- Host: **{platform.node()}**")
    lines.append(f"- Platform: **{platform.platform()}**")
    lines.append(f"- Repo root: `{ROOT.as_posix()}`")
    lines.append(f"- Mode: **{mode}**")
    if mode == "range":
        lines.append(f"- Days in range: **{len(days)}** (`{days[0]}` → `{days[-1]}`)")
    lines.append("")
    if missing_inputs:
        lines.append("### Missing inputs (best-effort; report still generated)")
        for m in missing_inputs:
            lines.append(f"- {m}")
        lines.append("")

    # ===== SHADOW INTEGRITY AUDIT =====
    lines.append("## SHADOW INTEGRITY AUDIT")
    integrity = _shadow_integrity_audit(days=days, shadow_trades=trades_shadow, shadow_events=shadow_events_today)
    counts = integrity.get("counts") if isinstance(integrity.get("counts"), dict) else {}
    lines.append(_md_table(
        ["check", "count"],
        [[k, counts.get(k, 0)] for k in sorted(counts.keys())],
    ))
    lines.append("- Notes:")
    lines.append(f"  - price_bounds_source: `{(integrity.get('notes') or {}).get('price_bounds_source')}`")
    lines.append(f"  - market_hours: `{(integrity.get('notes') or {}).get('market_hours')}`")
    lines.append(f"  - issues_capped: `{(integrity.get('notes') or {}).get('issues_capped')}`")
    lines.append("")
    lines.append("### Sample issues (capped)")
    sample_issues = integrity.get("issues") if isinstance(integrity.get("issues"), list) else []
    if not sample_issues:
        lines.append("- None detected.")
    else:
        rows = []
        for r in sample_issues[:50]:
            if isinstance(r, dict):
                rows.append([r.get("kind"), r.get("day"), r.get("symbol"), r.get("trade_id"), r.get("detail")])
        if rows:
            lines.append(_md_table(["kind", "day", "symbol", "trade_id", "detail"], rows))
    lines.append("")

    # ===== 1. TOP-LINE SUMMARY =====
    lines.append("## 1. TOP-LINE SUMMARY")
    live = _perf_block(trades_live)
    shadow = _perf_block(trades_shadow)
    delta_total = float(shadow.get("pnl_total_usd") or 0.0) - float(live.get("pnl_total_usd") or 0.0)
    lines.append(_md_table(
        ["Metric", "LIVE", "SHADOW", "DELTA (SHADOW-LIVE)"],
        [
            ["Total trades (all)", live["trade_count_total"], shadow["trade_count_total"], int(shadow["trade_count_total"]) - int(live["trade_count_total"])],
            ["Total trades (closed)", live["trade_count_closed"], shadow["trade_count_closed"], int(shadow["trade_count_closed"]) - int(live["trade_count_closed"])],
            ["PnL realized (USD)", _float_fmt(live["pnl_realized_usd"]), _float_fmt(shadow["pnl_realized_usd"]), _float_fmt(float(shadow["pnl_realized_usd"]) - float(live["pnl_realized_usd"]))],
            ["PnL unrealized (USD)", _float_fmt(live["pnl_unrealized_usd"]), _float_fmt(shadow["pnl_unrealized_usd"]), _float_fmt(float(shadow["pnl_unrealized_usd"]) - float(live["pnl_unrealized_usd"]))],
            ["PnL total (USD)", _float_fmt(live["pnl_total_usd"]), _float_fmt(shadow["pnl_total_usd"]), _float_fmt(delta_total)],
            ["Win rate (closed)", _pct_fmt(live["win_rate"]), _pct_fmt(shadow["win_rate"]), _pct_fmt(float(shadow["win_rate"]) - float(live["win_rate"]))],
            ["Expectancy (USD/trade, closed)", _float_fmt(live["expectancy_usd"], 4), _float_fmt(shadow["expectancy_usd"], 4), _float_fmt(float(shadow["expectancy_usd"]) - float(live["expectancy_usd"]), 4)],
            ["Avg time-in-trade (min, closed)", _float_fmt(live["avg_time_in_trade_minutes"], 2), _float_fmt(shadow["avg_time_in_trade_minutes"], 2), "n/a"],
            ["Long/short mix (all)", live["long_short_breakdown"], shadow["long_short_breakdown"], "n/a"],
        ],
    ))
    lines.append("### Exit reason distribution (closed trades)")
    lines.append("- LIVE:")
    lines.append(f"  - `{live.get('exit_reason_distribution', {})}`")
    lines.append("- SHADOW:")
    lines.append(f"  - `{shadow.get('exit_reason_distribution', {})}`")
    lines.append("")

    # ===== SHADOW PERFORMANCE (MULTI-DAY) =====
    lines.append("## SHADOW PERFORMANCE (MULTI-DAY)")
    sh_closed = _closed_trades(trades_shadow)
    sh_pb = _perf_block(trades_shadow)
    lines.append(_md_table(
        ["metric", "value"],
        [
            ["Total shadow trades (all)", sh_pb.get("trade_count_total")],
            ["Total shadow trades (closed)", sh_pb.get("trade_count_closed")],
            ["Shadow realized pnl (USD)", _float_fmt(sh_pb.get("pnl_realized_usd"))],
            ["Shadow expectancy (USD/trade, closed)", _float_fmt(sh_pb.get("expectancy_usd"), 4)],
            ["Shadow win rate (closed)", _pct_fmt(sh_pb.get("win_rate"))],
            ["Shadow long/short mix (all)", sh_pb.get("long_short_breakdown")],
        ],
    ))
    # Shadow slicing tables
    def _pnl_slice(trs: List[Dict[str, Any]], key_fn) -> List[List[Any]]:
        g = _group_by(_closed_trades(trs), key_fn)
        rows = []
        for k, tt in g.items():
            pb = _perf_block(tt)
            rows.append([k, pb["trade_count_closed"], _float_fmt(pb["pnl_realized_usd"]), _float_fmt(pb["expectancy_usd"], 4), _pct_fmt(pb["win_rate"])])
        rows = sorted(rows, key=lambda r: float(str(r[2]).replace(",", "")) if isinstance(r[2], str) and r[2] not in ("n/a", "") else 0.0, reverse=True)
        return rows

    lines.append("### Shadow PnL by symbol (closed trades)")
    lines.append(_md_table(["symbol", "n", "pnl_usd", "expectancy_usd", "win_rate"], _pnl_slice(trades_shadow, lambda t: t.get("symbol", ""))[:200]))
    lines.append("### Shadow PnL by sector (closed trades)")
    lines.append(_md_table(["sector", "n", "pnl_usd", "expectancy_usd", "win_rate"], _pnl_slice(trades_shadow, lambda t: _infer_sector(t) or "UNKNOWN")[:200]))
    lines.append("### Shadow PnL by regime (closed trades)")
    lines.append(_md_table(["regime", "n", "pnl_usd", "expectancy_usd", "win_rate"], _pnl_slice(trades_shadow, lambda t: _infer_regime(t) or "UNKNOWN")[:200]))
    lines.append("### Shadow PnL by long vs short (closed trades)")
    lines.append(_md_table(["side", "n", "pnl_usd", "expectancy_usd", "win_rate"], _pnl_slice(trades_shadow, lambda t: t.get("side", ""))[:20]))
    lines.append("### Shadow PnL by exit_reason (closed trades)")
    lines.append(_md_table(["exit_reason", "n", "pnl_usd", "expectancy_usd", "win_rate"], _pnl_slice(trades_shadow, lambda t: str(t.get("exit_reason") or ""))[:200]))
    lines.append("")
    # Top winners/losers
    winners = sorted(sh_closed, key=lambda t: float(_safe_float(t.get("realized_pnl_usd")) or 0.0), reverse=True)[:20]
    losers = sorted(sh_closed, key=lambda t: float(_safe_float(t.get("realized_pnl_usd")) or 0.0))[:20]
    def _trade_detail_rows(trs: List[Dict[str, Any]]) -> List[List[Any]]:
        rows = []
        for t in trs:
            rows.append(
                [
                    t.get("trade_id"),
                    t.get("symbol"),
                    t.get("side"),
                    t.get("entry_ts"),
                    t.get("exit_ts"),
                    _float_fmt(_safe_float(t.get("entry_price")), 4),
                    _float_fmt(_safe_float(t.get("exit_price")), 4),
                    _float_fmt(_safe_float(t.get("qty")), 4),
                    _float_fmt(_safe_float(t.get("realized_pnl_usd")), 2),
                    t.get("exit_reason"),
                    t.get("signals"),
                    t.get("sector"),
                    t.get("regime"),
                    _float_fmt(_safe_float(t.get("time_in_trade_minutes")), 2),
                ]
            )
        return rows

    lines.append("### Top 20 shadow winners (full detail; closed trades)")
    lines.append(_md_table(
        ["trade_id", "symbol", "side", "entry_ts", "exit_ts", "entry_price", "exit_price", "qty", "pnl_usd", "exit_reason", "signals", "sector", "regime", "tmin"],
        _trade_detail_rows(winners),
    ))
    lines.append("### Top 20 shadow losers (full detail; closed trades)")
    lines.append(_md_table(
        ["trade_id", "symbol", "side", "entry_ts", "exit_ts", "entry_price", "exit_price", "qty", "pnl_usd", "exit_reason", "signals", "sector", "regime", "tmin"],
        _trade_detail_rows(losers),
    ))
    lines.append("")

    # ===== 2. PER-SYMBOL PERFORMANCE =====
    lines.append("## 2. PER-SYMBOL PERFORMANCE")
    by_sym_live = _group_by(trades_live, lambda t: t.get("symbol", ""))
    by_sym_shadow = _group_by(trades_shadow, lambda t: t.get("symbol", ""))
    all_syms = sorted(set(list(by_sym_live.keys()) + list(by_sym_shadow.keys())))
    per_sym_rows: List[Dict[str, Any]] = []
    for sym in all_syms:
        lv = _perf_block(by_sym_live.get(sym, []))
        sh = _perf_block(by_sym_shadow.get(sym, []))
        per_sym_rows.append(
            {
                "symbol": sym,
                "live_pnl_usd": float(lv.get("pnl_total_usd") or 0.0),
                "shadow_pnl_usd": float(sh.get("pnl_total_usd") or 0.0),
                "delta_pnl_usd": float(sh.get("pnl_total_usd") or 0.0) - float(lv.get("pnl_total_usd") or 0.0),
                "live_trade_count": int(lv.get("trade_count_total") or 0),
                "shadow_trade_count": int(sh.get("trade_count_total") or 0),
                "live_long_short": lv.get("long_short_breakdown", {}),
                "shadow_long_short": sh.get("long_short_breakdown", {}),
                "live_expectancy_usd": float(lv.get("expectancy_usd") or 0.0),
                "shadow_expectancy_usd": float(sh.get("expectancy_usd") or 0.0),
                "live_exit_reasons": lv.get("exit_reason_distribution", {}),
                "shadow_exit_reasons": sh.get("exit_reason_distribution", {}),
                "live_signals": _collect_signals(by_sym_live.get(sym, []))[:20],
                "shadow_signals": _collect_signals(by_sym_shadow.get(sym, []))[:20],
                "live_feature_means": _numeric_feature_means(by_sym_live.get(sym, [])),
                "shadow_feature_means": _numeric_feature_means(by_sym_shadow.get(sym, [])),
            }
        )

    # Sort required:
    # - delta_pnl_usd (desc)
    # - shadow expectancy (desc)
    per_sym_rows_sorted = sorted(per_sym_rows, key=lambda r: (float(r.get("delta_pnl_usd") or 0.0), float(r.get("shadow_expectancy_usd") or 0.0)), reverse=True)
    lines.append(_md_table(
        ["symbol", "live_pnl_usd", "shadow_pnl_usd", "delta_pnl_usd", "live_trade_count", "shadow_trade_count", "live long/short", "shadow long/short", "shadow expectancy", "exit reasons (shadow)"],
        [
            [
                r["symbol"],
                _float_fmt(r["live_pnl_usd"]),
                _float_fmt(r["shadow_pnl_usd"]),
                _float_fmt(r["delta_pnl_usd"]),
                r["live_trade_count"],
                r["shadow_trade_count"],
                r["live_long_short"],
                r["shadow_long_short"],
                _float_fmt(r["shadow_expectancy_usd"], 4),
                r["shadow_exit_reasons"],
            ]
            for r in per_sym_rows_sorted[:200]
        ],
    ))
    # Per-symbol detail blocks (required fields per symbol)
    lines.append("### Per-symbol detail (all symbols traded today)")
    for r in per_sym_rows_sorted:
        sym = r.get("symbol") or ""
        lines.append(f"<details><summary><b>{sym}</b> — delta_pnl_usd={_float_fmt(r.get('delta_pnl_usd'))} shadow_exp={_float_fmt(r.get('shadow_expectancy_usd'),4)}</summary>")
        lines.append("")
        lines.append(_md_table(
            ["field", "value"],
            [
                ["live_pnl_usd", _float_fmt(r.get("live_pnl_usd"))],
                ["shadow_pnl_usd", _float_fmt(r.get("shadow_pnl_usd"))],
                ["delta_pnl_usd", _float_fmt(r.get("delta_pnl_usd"))],
                ["live_trade_count", r.get("live_trade_count")],
                ["shadow_trade_count", r.get("shadow_trade_count")],
                ["long/short mix (live)", r.get("live_long_short")],
                ["long/short mix (shadow)", r.get("shadow_long_short")],
                ["expectancy (live, closed)", _float_fmt(r.get("live_expectancy_usd"), 4)],
                ["expectancy (shadow, closed)", _float_fmt(r.get("shadow_expectancy_usd"), 4)],
                ["exit reasons (live)", r.get("live_exit_reasons")],
                ["exit reasons (shadow)", r.get("shadow_exit_reasons")],
                ["signals used (live)", r.get("live_signals")],
                ["signals used (shadow)", r.get("shadow_signals")],
            ],
        ))
        # feature_snapshot averages (top deltas for readability)
        lm = r.get("live_feature_means", {}) if isinstance(r.get("live_feature_means"), dict) else {}
        sm = r.get("shadow_feature_means", {}) if isinstance(r.get("shadow_feature_means"), dict) else {}
        keys = sorted(set(lm.keys()) | set(sm.keys()))
        diffs = []
        for k in keys:
            a = _safe_float(lm.get(k))
            b = _safe_float(sm.get(k))
            if a is None and b is None:
                continue
            diffs.append((k, (b or 0.0) - (a or 0.0), a, b))
        diffs_sorted = sorted(diffs, key=lambda x: abs(float(x[1])), reverse=True)[:25]
        if diffs_sorted:
            lines.append("#### feature_snapshot averages (top deltas)")
            lines.append(_md_table(
                ["feature", "live_mean", "shadow_mean", "delta(shadow-live)"],
                [[k, _float_fmt(a, 4), _float_fmt(b, 4), _float_fmt(d, 4)] for (k, d, a, b) in diffs_sorted],
            ))
        lines.append("</details>")
        lines.append("")

    # ===== 3. PER-SIGNAL PERFORMANCE (LIVE VS SHADOW) =====
    lines.append("## 3. PER-SIGNAL PERFORMANCE (LIVE VS SHADOW)")
    def signal_rows(trades: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        out: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for t in trades:
            sigs = normalize_signals(t.get("signals"))
            if not sigs:
                out["(no_signals)"].append(t)
            else:
                for s in sigs:
                    out[str(s)].append(t)
        return out

    sig_live = signal_rows(trades_live)
    sig_shadow = signal_rows(trades_shadow)
    all_sigs = sorted(set(list(sig_live.keys()) + list(sig_shadow.keys())))

    sig_perf_rows: List[Dict[str, Any]] = []
    for s in all_sigs:
        lv = _perf_block(sig_live.get(s, []))
        sh = _perf_block(sig_shadow.get(s, []))
        # regime + sector breakdowns (best-effort)
        reg_lv = Counter([_infer_regime(t) or "UNKNOWN" for t in _closed_trades(sig_live.get(s, []))])
        reg_sh = Counter([_infer_regime(t) or "UNKNOWN" for t in _closed_trades(sig_shadow.get(s, []))])
        sec_lv = Counter([_infer_sector(t) or "UNKNOWN" for t in _closed_trades(sig_live.get(s, []))])
        sec_sh = Counter([_infer_sector(t) or "UNKNOWN" for t in _closed_trades(sig_shadow.get(s, []))])
        sig_perf_rows.append(
            {
                "signal": s,
                "live_expectancy": float(lv.get("expectancy_usd") or 0.0),
                "shadow_expectancy": float(sh.get("expectancy_usd") or 0.0),
                "live_win_rate": float(lv.get("win_rate") or 0.0),
                "shadow_win_rate": float(sh.get("win_rate") or 0.0),
                "trade_count_live": int(lv.get("trade_count_closed") or 0),
                "trade_count_shadow": int(sh.get("trade_count_closed") or 0),
                "delta_expectancy": float(sh.get("expectancy_usd") or 0.0) - float(lv.get("expectancy_usd") or 0.0),
                "regime_breakdown_live": dict(reg_lv),
                "regime_breakdown_shadow": dict(reg_sh),
                "sector_breakdown_live": dict(sec_lv),
                "sector_breakdown_shadow": dict(sec_sh),
            }
        )

    # Sort by delta expectancy desc, then shadow trade count desc.
    sig_perf_rows_sorted = sorted(sig_perf_rows, key=lambda r: (float(r.get("delta_expectancy") or 0.0), int(r.get("trade_count_shadow") or 0)), reverse=True)
    lines.append(_md_table(
        [
            "signal",
            "live expectancy",
            "shadow expectancy",
            "live win_rate",
            "shadow win_rate",
            "trade_count_live(closed)",
            "trade_count_shadow(closed)",
            "delta expectancy",
            "regime breakdown (live)",
            "regime breakdown (shadow)",
            "sector breakdown (live)",
            "sector breakdown (shadow)",
        ],
        [
            [
                r["signal"],
                _float_fmt(r["live_expectancy"], 4),
                _float_fmt(r["shadow_expectancy"], 4),
                _pct_fmt(r["live_win_rate"]),
                _pct_fmt(r["shadow_win_rate"]),
                r["trade_count_live"],
                r["trade_count_shadow"],
                _float_fmt(r["delta_expectancy"], 4),
                r["regime_breakdown_live"],
                r["regime_breakdown_shadow"],
                r["sector_breakdown_live"],
                r["sector_breakdown_shadow"],
            ]
            for r in sig_perf_rows_sorted[:250]
        ],
    ))
    lines.append("")

    # ===== 4. FEATURE EV CURVES (LIVE VS SHADOW) =====
    lines.append("## 4. FEATURE EV CURVES (LIVE VS SHADOW)")
    # Feature set: union of feature_snapshot keys across both sets (numeric only).
    feat_counts: Counter = Counter()
    for t in trades_live + trades_shadow:
        fs = t.get("feature_snapshot") if isinstance(t.get("feature_snapshot"), dict) else {}
        for k, v in fs.items():
            if _safe_float(v) is not None:
                feat_counts[str(k)] += 1
    numeric_feats = [k for k, _ in feat_counts.most_common()]
    # Also track non-numeric features (for explicit reporting).
    non_numeric_counts: Counter = Counter()
    for t in trades_live + trades_shadow:
        fs = t.get("feature_snapshot") if isinstance(t.get("feature_snapshot"), dict) else {}
        for k, v in fs.items():
            if _safe_float(v) is None:
                non_numeric_counts[str(k)] += 1

    replacement_anomalies = None
    if isinstance(telemetry.get("computed"), dict):
        rte = telemetry["computed"].get("replacement_telemetry_expanded.json")
        if isinstance(rte, dict):
            replacement_anomalies = rte.get("replacement_anomaly_detected")

    feat_rows: List[Dict[str, Any]] = []
    ev_curves_all: Dict[str, Any] = {}
    for f in numeric_feats:
        curve_live = _ev_curve(trades_live, f)
        curve_shadow = _ev_curve(trades_shadow, f)
        # drift (feature value distribution live vs shadow)
        xs_l = []
        xs_s = []
        for t in trades_live:
            fs = t.get("feature_snapshot") if isinstance(t.get("feature_snapshot"), dict) else {}
            x = _safe_float(fs.get(f))
            if x is not None:
                xs_l.append(float(x))
        for t in trades_shadow:
            fs = t.get("feature_snapshot") if isinstance(t.get("feature_snapshot"), dict) else {}
            x = _safe_float(fs.get(f))
            if x is not None:
                xs_s.append(float(x))
        drift = _psi(xs_l, xs_s, bins=10)
        # missing/anomaly rate: how often is the feature missing or non-numeric?
        total_obs = len(trades_live) + len(trades_shadow)
        present_obs = len(xs_l) + len(xs_s)
        missing_rate = 1.0 - (present_obs / float(total_obs)) if total_obs else 1.0
        # stability score heuristic: penalize missing + drift (PSI)
        drift_pen = min(1.0, (float(drift) / 0.5)) if drift is not None else 0.0
        stability = max(0.0, 100.0 * (1.0 - missing_rate) * (1.0 - drift_pen))
        feat_rows.append(
            {
                "feature": f,
                "n_live": int(curve_live.get("n") or 0),
                "n_shadow": int(curve_shadow.get("n") or 0),
                "drift_psi": drift,
                "missing_rate": missing_rate,
                "stability_score": stability,
                "curve_live": curve_live,
                "curve_shadow": curve_shadow,
            }
        )
        ev_curves_all[f] = {"live": curve_live, "shadow": curve_shadow, "drift_psi": drift, "missing_rate": missing_rate, "stability_score": stability}

    # Sort by stability desc, then sample size desc.
    feat_rows_sorted = sorted(feat_rows, key=lambda r: (float(r.get("stability_score") or 0.0), int(r.get("n_live") or 0) + int(r.get("n_shadow") or 0)), reverse=True)
    lines.append(_md_table(
        ["feature", "n_live", "n_shadow", "drift_PSI", "missing_rate", "feature_stability_score", "live EV curve", "shadow EV curve"],
        [
            [
                r["feature"],
                r["n_live"],
                r["n_shadow"],
                _float_fmt(r.get("drift_psi"), 4),
                _pct_fmt(r.get("missing_rate"), 2),
                _float_fmt(r.get("stability_score"), 1),
                f"bins={len((r.get('curve_live') or {}).get('bins') or [])}",
                f"bins={len((r.get('curve_shadow') or {}).get('bins') or [])}",
            ]
            for r in feat_rows_sorted[:200]
        ],
    ))
    lines.append("### Replacement telemetry anomalies")
    lines.append(f"- replacement_anomaly_detected (telemetry): **{replacement_anomalies}**")
    lines.append("### Non-numeric feature keys observed in `feature_snapshot` (not eligible for EV curves)")
    if non_numeric_counts:
        top_nn = [k for k, _ in non_numeric_counts.most_common(40)]
        lines.append(f"- examples (top 40 by frequency): `{top_nn}`")
    else:
        lines.append("- none detected")
    lines.append("")
    lines.append("### Full EV curves (all numeric features; collapsed)")
    for r in feat_rows_sorted:
        f = r["feature"]
        lines.append(f"<details><summary><b>{f}</b> — drift_PSI={_float_fmt(r.get('drift_psi'),4)} stability={_float_fmt(r.get('stability_score'),1)}</summary>")
        lines.append("")
        cl = (r.get("curve_live") or {}).get("bins") or []
        cs = (r.get("curve_shadow") or {}).get("bins") or []
        if cl:
            lines.append("#### LIVE EV curve (binned)")
            lines.append(_md_table(["x_lo", "x_hi", "count", "avg_pnl_usd"], [[b.get("x_lo"), b.get("x_hi"), b.get("count"), _float_fmt(_safe_float(b.get("avg_pnl_usd")), 4)] for b in cl]))
        else:
            lines.append("- LIVE EV curve: insufficient_data")
        if cs:
            lines.append("#### SHADOW EV curve (binned)")
            lines.append(_md_table(["x_lo", "x_hi", "count", "avg_pnl_usd"], [[b.get("x_lo"), b.get("x_hi"), b.get("count"), _float_fmt(_safe_float(b.get("avg_pnl_usd")), 4)] for b in cs]))
        else:
            lines.append("- SHADOW EV curve: insufficient_data")
        lines.append("</details>")
        lines.append("")
    lines.append("")

    # ===== SHADOW FEATURE & SIGNAL KNOB AUDIT =====
    lines.append("## SHADOW FEATURE & SIGNAL KNOB AUDIT")
    # Feature curves + stability across days (shadow-only)
    # Use numeric features from shadow trades only
    feat_counts_shadow = Counter()
    for t in trades_shadow:
        fs = t.get("feature_snapshot") if isinstance(t.get("feature_snapshot"), dict) else {}
        for k, v in fs.items():
            if _safe_float(v) is not None:
                feat_counts_shadow[str(k)] += 1
    shadow_features = [k for k, _ in feat_counts_shadow.most_common()]

    # Per-day feature distribution samples for stability
    per_day_shadow = _group_by(trades_shadow, lambda t: str(t.get("entry_day") or t.get("exit_day") or ""))
    feature_stability_rows: List[List[Any]] = []
    feature_flags: Dict[str, List[str]] = defaultdict(list)

    for feat in shadow_features:
        # Binned EV curve (shadow-only; multi-day pooled)
        curve = _ev_curve(trades_shadow, feat, bins=10)
        bins_list = curve.get("bins") if isinstance(curve.get("bins"), list) else []
        shape = _shape_monotonicity(bins_list)

        # Stability across days: slope sign consistency + PSI first vs last day (if possible)
        slopes: List[float] = []
        days_with_data = 0
        values_by_day: Dict[str, List[float]] = {}
        for d in days:
            trs = per_day_shadow.get(d, [])
            xs = []
            for t in trs:
                fs = t.get("feature_snapshot") if isinstance(t.get("feature_snapshot"), dict) else {}
                x = _safe_float(fs.get(feat))
                if x is not None:
                    xs.append(float(x))
            if xs:
                values_by_day[d] = xs
        for d in days:
            if d not in values_by_day:
                continue
            days_with_data += 1
            # compute EV curve for that day (if enough closed trades)
            cday = _ev_curve(per_day_shadow.get(d, []), feat, bins=8)
            bl = cday.get("bins") if isinstance(cday.get("bins"), list) else []
            sh2 = _shape_monotonicity(bl)
            s = _safe_float(sh2.get("slope"))
            if s is not None:
                slopes.append(float(s))

        psi_first_last = None
        if len(days) >= 2 and (days[0] in values_by_day) and (days[-1] in values_by_day):
            psi_first_last = _psi(values_by_day[days[0]], values_by_day[days[-1]], bins=10)

        # Flags
        missing_rate = 1.0
        if trades_shadow:
            present = sum(
                1
                for t in trades_shadow
                if isinstance(t.get("feature_snapshot"), dict) and _safe_float((t.get("feature_snapshot") or {}).get(feat)) is not None
            )
            missing_rate = 1.0 - (present / float(len(trades_shadow)))
        if missing_rate > 0.5:
            feature_flags[feat].append("missing_features")
        mono = _safe_float(shape.get("monotonicity"))
        slope = _safe_float(shape.get("slope"))
        if mono is not None and mono < 0.25:
            feature_flags[feat].append("flat_or_noisy")
        if slope is not None and abs(slope) < 0.5 and (curve.get("n") or 0) >= 30:
            feature_flags[feat].append("flat_features")
        if slope is not None and slope < -1.0 and mono is not None and mono >= 0.6:
            feature_flags[feat].append("inverted_features")
        if psi_first_last is not None and psi_first_last >= 0.25:
            feature_flags[feat].append("drift_flag")

        feature_stability_rows.append(
            [
                feat,
                curve.get("n"),
                _float_fmt(mono, 3),
                _float_fmt(slope, 3),
                _float_fmt(psi_first_last, 4),
                _pct_fmt(missing_rate, 2),
                sorted(set(feature_flags.get(feat, []))),
            ]
        )

    # Show top features by sample count
    feature_stability_rows = sorted(feature_stability_rows, key=lambda r: int(r[1] or 0), reverse=True)
    lines.append("### Feature knob audit (shadow-only)")
    lines.append(_md_table(
        ["feature", "n", "monotonicity", "slope", "psi(first_vs_last_day)", "missing_rate", "flags"],
        feature_stability_rows[:250],
    ))
    lines.append("")
    lines.append("### Feature EV curves (shadow-only; collapsed)")
    for r in feature_stability_rows[:120]:
        feat = str(r[0])
        curve = _ev_curve(trades_shadow, feat, bins=10)
        bl = curve.get("bins") if isinstance(curve.get("bins"), list) else []
        lines.append(f"<details><summary><b>{feat}</b> — n={curve.get('n')} flags={feature_flags.get(feat, [])}</summary>")
        if bl:
            lines.append(_md_table(["x_lo", "x_hi", "count", "avg_pnl_usd"], [[b.get("x_lo"), b.get("x_hi"), b.get("count"), _float_fmt(_safe_float(b.get("avg_pnl_usd")), 4)] for b in bl]))
        else:
            lines.append("- insufficient_data")
        lines.append("</details>")
        lines.append("")

    # Signal family audit (shadow-only)
    lines.append("### Signal family audit (shadow-only)")
    sig_rows = defaultdict(list)
    for t in trades_shadow:
        sigs = normalize_signals(t.get("signals"))
        if not sigs:
            sig_rows["(no_signals)"].append(t)
        else:
            for s in sigs:
                sig_rows[str(s)].append(t)
    sig_audit_rows: List[List[Any]] = []
    for s, trs in sig_rows.items():
        pb = _perf_block(trs)
        reg = Counter([_infer_regime(t) or "UNKNOWN" for t in _closed_trades(trs)])
        sec = Counter([_infer_sector(t) or "UNKNOWN" for t in _closed_trades(trs)])
        exp = float(pb.get("expectancy_usd") or 0.0)
        n = int(pb.get("trade_count_closed") or 0)
        note = "ignore"
        if n < 5:
            note = "watch"
        elif exp >= 0.5:
            note = "boost"
        elif exp <= -0.5:
            note = "cut"
        else:
            note = "watch"
        sig_audit_rows.append([s, n, _float_fmt(pb.get("pnl_realized_usd")), _float_fmt(exp, 4), _pct_fmt(pb.get("win_rate")), dict(reg), dict(sec), note])
    sig_audit_rows = sorted(sig_audit_rows, key=lambda r: int(r[1] or 0), reverse=True)
    lines.append(_md_table(
        ["signal", "closed_n", "pnl_usd", "expectancy_usd", "win_rate", "regime_breakdown", "sector_breakdown", "advisory_note"],
        sig_audit_rows[:300],
    ))
    lines.append("")

    # ===== SHADOW LONG/SHORT ENGINE AUDIT =====
    lines.append("## SHADOW LONG/SHORT ENGINE AUDIT")
    shadow_closed = _closed_trades(trades_shadow)
    by_side = _group_by(shadow_closed, lambda t: str(t.get("side") or ""))
    rows = []
    for side, trs in sorted(by_side.items(), key=lambda kv: kv[0]):
        pb = _perf_block(trs)
        rows.append([side, pb["trade_count_closed"], _float_fmt(pb["pnl_realized_usd"]), _float_fmt(pb["expectancy_usd"], 4), _pct_fmt(pb["win_rate"])])
    lines.append("### Long vs short (shadow, closed trades)")
    lines.append(_md_table(["side", "n", "pnl_usd", "expectancy_usd", "win_rate"], rows))
    lines.append("### Long vs short by sector (shadow, closed trades)")
    by_sec = _group_by(shadow_closed, lambda t: _infer_sector(t) or "UNKNOWN")
    rows = []
    for sec, trs in sorted(by_sec.items(), key=lambda kv: kv[0]):
        by_s = _group_by(trs, lambda t: str(t.get("side") or ""))
        for side, tt in sorted(by_s.items(), key=lambda kv: kv[0]):
            pb = _perf_block(tt)
            rows.append([sec, side, pb["trade_count_closed"], _float_fmt(pb["pnl_realized_usd"]), _float_fmt(pb["expectancy_usd"], 4)])
    lines.append(_md_table(["sector", "side", "n", "pnl_usd", "expectancy_usd"], rows[:500]))
    lines.append("### Long vs short by regime (shadow, closed trades)")
    by_reg = _group_by(shadow_closed, lambda t: _infer_regime(t) or "UNKNOWN")
    rows = []
    for reg, trs in sorted(by_reg.items(), key=lambda kv: kv[0]):
        by_s = _group_by(trs, lambda t: str(t.get("side") or ""))
        for side, tt in sorted(by_s.items(), key=lambda kv: kv[0]):
            pb = _perf_block(tt)
            rows.append([reg, side, pb["trade_count_closed"], _float_fmt(pb["pnl_realized_usd"]), _float_fmt(pb["expectancy_usd"], 4)])
    lines.append(_md_table(["regime", "side", "n", "pnl_usd", "expectancy_usd"], rows[:500]))
    lines.append("")
    lines.append("### Symbols where long works but short fails (shadow, closed trades)")
    by_sym = _group_by(shadow_closed, lambda t: t.get("symbol", ""))
    rows = []
    for sym, trs in by_sym.items():
        by_s = _group_by(trs, lambda t: str(t.get("side") or ""))
        pl = _perf_block(by_s.get("long", []))
        ps = _perf_block(by_s.get("short", []))
        nl = int(pl.get("trade_count_closed") or 0)
        ns = int(ps.get("trade_count_closed") or 0)
        el = float(pl.get("expectancy_usd") or 0.0)
        es = float(ps.get("expectancy_usd") or 0.0)
        if nl >= 3 and ns >= 3 and el > 0.5 and es < -0.5:
            rows.append([sym, nl, _float_fmt(el, 4), ns, _float_fmt(es, 4), _float_fmt(float(pl.get("pnl_realized_usd") or 0.0), 2), _float_fmt(float(ps.get("pnl_realized_usd") or 0.0), 2)])
    rows = sorted(rows, key=lambda r: float(str(r[6]).replace(",", "")) if isinstance(r[6], str) and r[6] not in ("n/a", "") else 0.0, reverse=True)
    lines.append(_md_table(["symbol", "long_n", "long_exp", "short_n", "short_exp", "long_pnl", "short_pnl"], rows[:200]))
    lines.append("### Symbols where short works but long fails (shadow, closed trades)")
    rows = []
    for sym, trs in by_sym.items():
        by_s = _group_by(trs, lambda t: str(t.get("side") or ""))
        pl = _perf_block(by_s.get("long", []))
        ps = _perf_block(by_s.get("short", []))
        nl = int(pl.get("trade_count_closed") or 0)
        ns = int(ps.get("trade_count_closed") or 0)
        el = float(pl.get("expectancy_usd") or 0.0)
        es = float(ps.get("expectancy_usd") or 0.0)
        if nl >= 3 and ns >= 3 and es > 0.5 and el < -0.5:
            rows.append([sym, nl, _float_fmt(el, 4), ns, _float_fmt(es, 4), _float_fmt(float(pl.get("pnl_realized_usd") or 0.0), 2), _float_fmt(float(ps.get("pnl_realized_usd") or 0.0), 2)])
    rows = sorted(rows, key=lambda r: float(str(r[6]).replace(",", "")) if isinstance(r[6], str) and r[6] not in ("n/a", "") else 0.0, reverse=True)
    lines.append(_md_table(["symbol", "long_n", "long_exp", "short_n", "short_exp", "long_pnl", "short_pnl"], rows[:200]))
    lines.append("")

    # ===== SHADOW MULTI-DAY CONSISTENCY =====
    if mode == "range":
        lines.append("## SHADOW MULTI-DAY CONSISTENCY")
        by_day_metrics = _per_day_shadow_metrics(days, trades_shadow)
        rows = []
        for d in days:
            pb = by_day_metrics.get(d, {})
            rows.append([d, pb.get("trade_count_closed", 0), _float_fmt(pb.get("pnl_realized_usd")), _float_fmt(pb.get("expectancy_usd"), 4), _pct_fmt(pb.get("win_rate"))])
        lines.append("### PnL / expectancy / win rate by day (shadow, closed trades)")
        lines.append(_md_table(["day", "closed_n", "pnl_usd", "expectancy_usd", "win_rate"], rows))
        # Recurring winners/losers across days
        sym_day_pnl: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        for t in _closed_trades(trades_shadow):
            d = str(t.get("exit_day") or t.get("entry_day") or "")
            sym = str(t.get("symbol") or "").upper()
            p = float(_safe_float(t.get("realized_pnl_usd")) or 0.0)
            if d and sym:
                sym_day_pnl[sym][d] += p
        recurring = []
        for sym, mp in sym_day_pnl.items():
            pos_days = sum(1 for _, v in mp.items() if v > 0)
            neg_days = sum(1 for _, v in mp.items() if v < 0)
            tot = sum(mp.values())
            recurring.append([sym, _float_fmt(tot, 2), pos_days, neg_days, {k: round(v, 2) for k, v in sorted(mp.items())}])
        recurring_sorted = sorted(recurring, key=lambda r: float(str(r[1]).replace(",", "")) if isinstance(r[1], str) and r[1] not in ("n/a", "") else 0.0, reverse=True)
        lines.append("### Top recurring winners (by total PnL across days; shadow)")
        lines.append(_md_table(["symbol", "total_pnl_usd", "pos_days", "neg_days", "pnl_by_day"], recurring_sorted[:30]))
        recurring_sorted2 = sorted(recurring, key=lambda r: float(str(r[1]).replace(",", "")) if isinstance(r[1], str) and r[1] not in ("n/a", "") else 0.0)
        lines.append("### Top recurring losers (by total PnL across days; shadow)")
        lines.append(_md_table(["symbol", "total_pnl_usd", "pos_days", "neg_days", "pnl_by_day"], recurring_sorted2[:30]))
        # Day-level anomaly flags from integrity counts
        lines.append("### Day-level anomalies (best-effort)")
        lines.append(f"- integrity_counts: `{counts}`")
        lines.append("")

    # ===== 5. REGIME & SECTOR ANALYSIS =====
    lines.append("## 5. REGIME & SECTOR ANALYSIS")
    lines.append("### Regime timeline for the day (telemetry)")
    rt = telemetry.get("computed", {}).get("regime_timeline.json") if isinstance(telemetry.get("computed"), dict) else None
    if isinstance(rt, dict):
        lines.append("```")
        lines.append(json.dumps(rt, indent=2, sort_keys=True, default=str)[:8000])
        lines.append("```")
    else:
        lines.append("- (missing `telemetry/<date>/computed/regime_timeline.json`)")
    lines.append("")

    # Performance by regime / sector
    lines.append("### Shadow vs live performance by regime (closed trades)")
    reg_live = _group_by(_closed_trades(trades_live), lambda t: _infer_regime(t) or "UNKNOWN")
    reg_shadow = _group_by(_closed_trades(trades_shadow), lambda t: _infer_regime(t) or "UNKNOWN")
    regs = sorted(set(list(reg_live.keys()) + list(reg_shadow.keys())))
    rows = []
    for r in regs:
        lv = _perf_block(reg_live.get(r, []))
        sh = _perf_block(reg_shadow.get(r, []))
        rows.append([r, int(lv.get("trade_count_closed") or 0), _float_fmt(lv.get("pnl_realized_usd")), _float_fmt(lv.get("expectancy_usd"), 4),
                    int(sh.get("trade_count_closed") or 0), _float_fmt(sh.get("pnl_realized_usd")), _float_fmt(sh.get("expectancy_usd"), 4)])
    lines.append(_md_table(["regime", "n_live", "live pnl", "live exp", "n_shadow", "shadow pnl", "shadow exp"], rows))
    lines.append("")

    lines.append("### Shadow vs live performance by sector (closed trades)")
    sec_live = _group_by(_closed_trades(trades_live), lambda t: _infer_sector(t) or "UNKNOWN")
    sec_shadow = _group_by(_closed_trades(trades_shadow), lambda t: _infer_sector(t) or "UNKNOWN")
    secs = sorted(set(list(sec_live.keys()) + list(sec_shadow.keys())))
    rows = []
    for s in secs:
        lv = _perf_block(sec_live.get(s, []))
        sh = _perf_block(sec_shadow.get(s, []))
        rows.append([s, int(lv.get("trade_count_closed") or 0), _float_fmt(lv.get("pnl_realized_usd")), _float_fmt(lv.get("expectancy_usd"), 4),
                    int(sh.get("trade_count_closed") or 0), _float_fmt(sh.get("pnl_realized_usd")), _float_fmt(sh.get("expectancy_usd"), 4)])
    rows = sorted(rows, key=lambda r: float(str(r[6]).replace(",", "")) if isinstance(r[6], str) and r[6] not in ("n/a", "") else 0.0, reverse=True)
    lines.append(_md_table(["sector", "n_live", "live pnl", "live exp", "n_shadow", "shadow pnl", "shadow exp"], rows))
    lines.append("")

    # Sector posture correctness / regime alignment correctness / buckets (best-effort)
    lines.append("### Sector posture correctness / Regime alignment correctness / Volatility & trend buckets")
    lines.append("- Best-effort only: shown when the required posture/bucket fields exist in `regime_snapshot` or telemetry state.")
    # bucket behavior
    def bucket_group(trs: List[Dict[str, Any]], key: str) -> Dict[str, List[Dict[str, Any]]]:
        out: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for t in trs:
            rs = t.get("regime_snapshot") if isinstance(t.get("regime_snapshot"), dict) else {}
            v = rs.get(key)
            if v is None:
                continue
            out[str(v)].append(t)
        return out

    for bucket_key in ("volatility_bucket", "vol_bucket", "trend_bucket"):
        bL = bucket_group(_closed_trades(trades_live), bucket_key)
        bS = bucket_group(_closed_trades(trades_shadow), bucket_key)
        if not bL and not bS:
            continue
        keys = sorted(set(list(bL.keys()) + list(bS.keys())))
        rows = []
        for k in keys:
            lv = _perf_block(bL.get(k, []))
            sh = _perf_block(bS.get(k, []))
            rows.append([bucket_key, k, int(lv.get("trade_count_closed") or 0), _float_fmt(lv.get("pnl_realized_usd")), _float_fmt(lv.get("expectancy_usd"), 4),
                         int(sh.get("trade_count_closed") or 0), _float_fmt(sh.get("pnl_realized_usd")), _float_fmt(sh.get("expectancy_usd"), 4)])
        lines.append(_md_table(["bucket", "value", "n_live", "live pnl", "live exp", "n_shadow", "shadow pnl", "shadow exp"], rows))
    lines.append("")

    # ===== 6. EXIT INTELLIGENCE ANALYSIS =====
    lines.append("## 6. EXIT INTELLIGENCE ANALYSIS")
    # Exit reason performance
    def stop_profit_bucket(reason: Optional[str]) -> str:
        r = str(reason or "").lower()
        if any(x in r for x in ("stop", "stopped")):
            return "stop"
        if any(x in r for x in ("target", "profit", "tp", "take_profit")):
            return "profit"
        if not r:
            return "unknown"
        return "other"

    def exit_perf(trades: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        by = _group_by(_closed_trades(trades), lambda t: str(t.get("exit_reason") or ""))
        out: Dict[str, Dict[str, Any]] = {}
        for k, trs in by.items():
            pb = _perf_block(trs)
            out[k] = {"count": pb["trade_count_closed"], "pnl_usd": pb["pnl_realized_usd"], "expectancy_usd": pb["expectancy_usd"]}
        return out

    lines.append("### Exit reason performance (live vs shadow)")
    live_exit_perf = exit_perf(trades_live)
    shadow_exit_perf = exit_perf(trades_shadow)
    reasons = sorted(set(list(live_exit_perf.keys()) + list(shadow_exit_perf.keys())))
    rows = []
    for r in reasons:
        l = live_exit_perf.get(r, {})
        s = shadow_exit_perf.get(r, {})
        rows.append([r or "(empty)", l.get("count", 0), _float_fmt(l.get("pnl_usd")), _float_fmt(l.get("expectancy_usd"), 4),
                     s.get("count", 0), _float_fmt(s.get("pnl_usd")), _float_fmt(s.get("expectancy_usd"), 4)])
    lines.append(_md_table(["exit_reason", "n_live", "live pnl", "live exp", "n_shadow", "shadow pnl", "shadow exp"], rows[:250]))
    lines.append("")

    lines.append("### Stop vs profit behavior (closed trades)")
    for label, trs_live in [("LIVE", trades_live), ("SHADOW", trades_shadow)]:
        by_bucket = _group_by(_closed_trades(trs_live), lambda t: stop_profit_bucket(t.get("exit_reason")))
        rows = []
        for b, tt in sorted(by_bucket.items(), key=lambda kv: kv[0]):
            pb = _perf_block(tt)
            rows.append([b, pb["trade_count_closed"], _float_fmt(pb["pnl_realized_usd"]), _float_fmt(pb["expectancy_usd"], 4), _pct_fmt(pb["win_rate"])])
        lines.append(f"- {label}:")
        lines.append(_md_table(["bucket", "n", "pnl_usd", "expectancy_usd", "win_rate"], rows))
    lines.append("")

    # Time-in-trade distribution
    lines.append("### Time-in-trade distribution (minutes, closed trades)")
    for label, trs in [("LIVE", trades_live), ("SHADOW", trades_shadow)]:
        tmins = [float(t.get("time_in_trade_minutes")) for t in _closed_trades(trs) if _safe_float(t.get("time_in_trade_minutes")) is not None]
        st = _basic_stats(tmins)
        lines.append(f"- {label}: `{st}`")
    lines.append("")

    # Exit score distribution (shadow only)
    lines.append("### Exit score distribution (shadow only; exit_attribution)")
    scores = []
    for r in exit_attrib_today:
        x = _safe_float(r.get("v2_exit_score"))
        if x is not None:
            scores.append(float(x))
    lines.append(f"- v2_exit_score stats: `{_basic_stats(scores)}`")
    lines.append("")

    # Exit completeness / anomalies
    lines.append("### Exit completeness & anomalies")
    excomp = telemetry.get("computed", {}).get("exit_intel_completeness.json") if isinstance(telemetry.get("computed"), dict) else None
    if isinstance(excomp, dict):
        lines.append("```")
        lines.append(json.dumps(excomp, indent=2, sort_keys=True, default=str)[:8000])
        lines.append("```")
    else:
        lines.append("- (missing `telemetry/<date>/computed/exit_intel_completeness.json`)")
    lines.append("")

    # ===== 7. PARITY ANALYSIS (LIVE VS SHADOW) =====
    lines.append("## 7. PARITY ANALYSIS (LIVE VS SHADOW)")
    parity = telemetry.get("computed", {}).get("shadow_vs_live_parity.json") if isinstance(telemetry.get("computed"), dict) else None
    if isinstance(parity, dict):
        notes = parity.get("notes") if isinstance(parity.get("notes"), dict) else {}
        agg = parity.get("aggregate_metrics") if isinstance(parity.get("aggregate_metrics"), dict) else {}
        lines.append(f"- parity_available: **{notes.get('parity_available')}**")
        lines.append(f"- match_rate: **{agg.get('match_rate')}** matched_pairs={agg.get('matched_pairs')}")
        lines.append(f"- mean_entry_ts_delta_seconds: **{agg.get('mean_entry_ts_delta_seconds')}**")
        lines.append(f"- mean_score_delta: **{agg.get('mean_score_delta')}**")
        lines.append(f"- mean_price_delta_usd: **{agg.get('mean_price_delta_usd')}**")
        ep = parity.get("entry_parity") if isinstance(parity.get("entry_parity"), dict) else {}
        allowed = ep.get("allowed_classifications") if isinstance(ep.get("allowed_classifications"), list) else []
        lines.append(f"- allowed_classifications: `{allowed}`")
        # classification distribution
        rows = ep.get("rows") if isinstance(ep.get("rows"), list) else []
        cls = Counter([str(r.get("classification")) for r in rows if isinstance(r, dict)])
        lines.append(f"- classification_counts: `{dict(cls)}`")
    else:
        lines.append("- (missing `telemetry/<date>/computed/shadow_vs_live_parity.json`)")
    lines.append("")
    lines.append("### Parity anomalies")
    parity_rows = telemetry.get("computed", {}).get("entry_parity_details.json", {}).get("rows") if isinstance(telemetry.get("computed"), dict) else None
    if isinstance(parity_rows, list):
        # Normalize classification labels to the user-required names:
        def norm_cls(c: Any) -> str:
            s = str(c or "")
            if s == "missing_in_v1":
                return "missing_in_live"
            if s == "missing_in_v2":
                return "missing_in_shadow"
            return s
        for r in parity_rows:
            if isinstance(r, dict):
                r["classification_normalized"] = norm_cls(r.get("classification"))
        bad = [r for r in parity_rows if isinstance(r, dict) and str(r.get("classification")) in ("divergent", "missing_in_v1", "missing_in_v2", "missing_in_live", "missing_in_shadow")]
        lines.append(f"- anomalous_rows_count: **{len(bad)}** (divergent/missing)")
        # show top 15
        rows = []
        for r in bad[:15]:
            rows.append([r.get("symbol"), r.get("classification_normalized") or r.get("classification"), r.get("entry_ts_delta_seconds"), r.get("score_delta"), r.get("price_delta_usd"), r.get("missing_fields")])
        if rows:
            lines.append(_md_table(["symbol", "classification", "entry_ts_delta_seconds", "score_delta", "price_delta_usd", "missing_fields"], rows))
    else:
        lines.append("- (missing `telemetry/<date>/computed/entry_parity_details.json`)")
    lines.append("")

    # ===== 8. UW INTEL & EQUALIZER KNOB ANALYSIS =====
    lines.append("## 8. UW INTEL & EQUALIZER KNOB ANALYSIS")
    uw_snaps = _uw_snapshots_from_telemetry_state(telemetry.get("state") if isinstance(telemetry.get("state"), dict) else {})
    lines.append(f"- UW intel snapshots found (telemetry state): **{len(uw_snaps)}**")
    if uw_snaps:
        lines.append("### UW intel snapshot index")
        for s in uw_snaps[:20]:
            lines.append(f"- `{s.get('_file')}` keys={len([k for k in (s or {}).keys() if not str(k).startswith('_')])}")
        if len(uw_snaps) > 20:
            lines.append(f"- ... ({len(uw_snaps)-20} more)")
    lines.append("")

    # UW feature families (from trade feature_snapshot uw_* keys)
    fam_live = _uw_families_from_trade_snapshots(trades_live)
    fam_shadow = _uw_families_from_trade_snapshots(trades_shadow)
    fams = sorted(set(list(fam_live.keys()) + list(fam_shadow.keys())))
    rows = []
    for f in fams:
        # expectancy deltas within this family are approximated via trades where any uw_<family>_* is present
        def has_family(t: Dict[str, Any]) -> bool:
            fs = t.get("feature_snapshot") if isinstance(t.get("feature_snapshot"), dict) else {}
            for k, v in fs.items():
                if str(k).lower().startswith(f"uw_{f.lower()}_") and _safe_float(v) is not None:
                    return True
            return False
        def family_values(t: Dict[str, Any]) -> List[float]:
            fs = t.get("feature_snapshot") if isinstance(t.get("feature_snapshot"), dict) else {}
            outv: List[float] = []
            for k, v in fs.items():
                if str(k).lower().startswith(f"uw_{f.lower()}_"):
                    x = _safe_float(v)
                    if x is not None:
                        outv.append(float(x))
            return outv
        lv_tr = [t for t in trades_live if has_family(t)]
        sh_tr = [t for t in trades_shadow if has_family(t)]
        lv = _perf_block(lv_tr)
        sh = _perf_block(sh_tr)
        delta = float(sh.get("expectancy_usd") or 0.0) - float(lv.get("expectancy_usd") or 0.0)
        # Drift/stability: compare pooled feature values across the family (live vs shadow).
        lv_vals: List[float] = []
        sh_vals: List[float] = []
        for t in trades_live:
            lv_vals.extend(family_values(t))
        for t in trades_shadow:
            sh_vals.extend(family_values(t))
        drift = _psi(lv_vals, sh_vals, bins=10)
        total_obs = len(trades_live) + len(trades_shadow)
        present_obs = len([t for t in trades_live if has_family(t)]) + len([t for t in trades_shadow if has_family(t)])
        missing_rate = 1.0 - (present_obs / float(total_obs)) if total_obs else 1.0
        drift_pen = min(1.0, (float(drift) / 0.5)) if drift is not None else 0.0
        stability = max(0.0, 100.0 * (1.0 - missing_rate) * (1.0 - drift_pen))
        # advisory nudge: small magnitude, bounded
        nudge = max(-0.2, min(0.2, delta / 50.0)) if (lv_tr or sh_tr) else 0.0
        rows.append([f, int(lv.get("trade_count_closed") or 0), _float_fmt(lv.get("expectancy_usd"), 4),
                     int(sh.get("trade_count_closed") or 0), _float_fmt(sh.get("expectancy_usd"), 4),
                     _float_fmt(delta, 4), _float_fmt(drift, 4), _float_fmt(stability, 1), _pct_fmt(missing_rate, 2),
                     _float_fmt(nudge, 4), (fam_live.get(f) or {}).get("count", 0), (fam_shadow.get(f) or {}).get("count", 0)])
    if rows:
        lines.append(_md_table(
            ["uw_family", "n_live(closed)", "live expectancy", "n_shadow(closed)", "shadow expectancy", "delta", "drift_PSI", "stability", "missing_rate", "recommended_weight_nudge(advisory)", "usage_count_live", "usage_count_shadow"],
            sorted(rows, key=lambda r: float(str(r[5]).replace(",", "")) if isinstance(r[5], str) and r[5] not in ("n/a", "") else 0.0, reverse=True)[:250],
        ))
    else:
        lines.append("- (No `uw_*` numeric features found in trade feature snapshots.)")
    lines.append("")

    # ===== 9. LONG/SHORT CORRECTNESS AUDIT =====
    lines.append("## 9. LONG/SHORT CORRECTNESS AUDIT")
    lines.append("### Long vs short performance (closed trades)")
    def side_breakdown(trs: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        by = _group_by(_closed_trades(trs), lambda t: str(t.get("side") or ""))
        return {k: _perf_block(v) for k, v in by.items()}
    for label, trs in [("LIVE", trades_live), ("SHADOW", trades_shadow)]:
        sb = side_breakdown(trs)
        rows = []
        for side, pb in sorted(sb.items(), key=lambda kv: kv[0]):
            rows.append([side, pb["trade_count_closed"], _pct_fmt(pb["win_rate"]), _float_fmt(pb["pnl_realized_usd"]), _float_fmt(pb["expectancy_usd"], 4)])
        lines.append(f"- {label}:")
        lines.append(_md_table(["side", "n", "win_rate", "pnl_realized_usd", "expectancy_usd"], rows))
    lines.append("")

    lines.append("### Sector-specific long/short correctness (shadow, closed trades)")
    shadow_closed = _closed_trades(trades_shadow)
    by_sec = _group_by(shadow_closed, lambda t: _infer_sector(t) or "UNKNOWN")
    rows = []
    for sec, trs in sorted(by_sec.items(), key=lambda kv: kv[0]):
        by_side = _group_by(trs, lambda t: str(t.get("side") or ""))
        for side, tt in sorted(by_side.items(), key=lambda kv: kv[0]):
            pb = _perf_block(tt)
            rows.append([sec, side, pb["trade_count_closed"], _float_fmt(pb["pnl_realized_usd"]), _float_fmt(pb["expectancy_usd"], 4), _pct_fmt(pb["win_rate"])])
    lines.append(_md_table(["sector", "side", "n", "pnl_usd", "expectancy_usd", "win_rate"], rows[:400]))
    lines.append("")

    lines.append("### Regime-specific long/short correctness (shadow, closed trades)")
    by_reg = _group_by(shadow_closed, lambda t: _infer_regime(t) or "UNKNOWN")
    rows = []
    for reg, trs in sorted(by_reg.items(), key=lambda kv: kv[0]):
        by_side = _group_by(trs, lambda t: str(t.get("side") or ""))
        for side, tt in sorted(by_side.items(), key=lambda kv: kv[0]):
            pb = _perf_block(tt)
            rows.append([reg, side, pb["trade_count_closed"], _float_fmt(pb["pnl_realized_usd"]), _float_fmt(pb["expectancy_usd"], 4), _pct_fmt(pb["win_rate"])])
    lines.append(_md_table(["regime", "side", "n", "pnl_usd", "expectancy_usd", "win_rate"], rows[:400]))
    lines.append("")

    lines.append("### Symbol-level long/short correctness (shadow, closed trades)")
    by_sym = _group_by(shadow_closed, lambda t: t.get("symbol", ""))
    rows = []
    for sym, trs in sorted(by_sym.items(), key=lambda kv: kv[0]):
        by_side = _group_by(trs, lambda t: str(t.get("side") or ""))
        for side, tt in sorted(by_side.items(), key=lambda kv: kv[0]):
            pb = _perf_block(tt)
            rows.append([sym, side, pb["trade_count_closed"], _float_fmt(pb["pnl_realized_usd"]), _float_fmt(pb["expectancy_usd"], 4), _pct_fmt(pb["win_rate"])])
    rows = sorted(rows, key=lambda r: float(str(r[3]).replace(",", "")) if isinstance(r[3], str) and r[3] not in ("n/a", "") else 0.0, reverse=True)
    lines.append(_md_table(["symbol", "side", "n", "pnl_usd", "expectancy_usd", "win_rate"], rows[:400]))
    lines.append("")

    # ===== 10. SHADOW PROMOTION READINESS SCORE =====
    lines.append("## 10. SHADOW PROMOTION READINESS SCORE")
    # Readiness rubric (advisory only; no auto-promotion).
    # This explicitly scores the required dimensions:
    # - shadow outperforming live
    # - parity stability
    # - exit intelligence stability
    # - feature stability
    # - signal stability
    # - regime stability
    # - no anomalies in telemetry
    # - no missing fields
    # - no drift flags
    components: List[Tuple[str, float, str]] = []

    # 1) Shadow outperforming live (0..20)
    pnl_delta = float(shadow.get("pnl_total_usd") or 0.0) - float(live.get("pnl_total_usd") or 0.0)
    if pnl_delta > 0:
        pts = 20.0
        why = f"shadow pnl > live pnl by {_float_fmt(pnl_delta)}"
    elif abs(pnl_delta) < 1e-6:
        pts = 10.0
        why = "no pnl delta detected"
    else:
        pts = 0.0
        why = f"shadow pnl < live pnl by {_float_fmt(abs(pnl_delta))}"
    components.append(("shadow_outperforming_live", pts, why))

    # 2) Parity stability (0..15)
    mr = None
    mean_ts = None
    mean_score = None
    mean_price = None
    if isinstance(parity, dict):
        agg = parity.get("aggregate_metrics") if isinstance(parity.get("aggregate_metrics"), dict) else {}
        mr = _safe_float(agg.get("match_rate"))
        mean_ts = _safe_float(agg.get("mean_entry_ts_delta_seconds"))
        mean_score = _safe_float(agg.get("mean_score_delta"))
        mean_price = _safe_float(agg.get("mean_price_delta_usd"))
    if mr is None:
        pts = 5.0
        why = "parity not available"
    else:
        pts = 0.0
        pts += 10.0 if mr >= 0.75 else (7.0 if mr >= 0.6 else (3.0 if mr >= 0.4 else 0.0))
        # small penalties for large mean deltas (best-effort)
        if mean_ts is not None and abs(mean_ts) > 120:
            pts -= 2.0
        if mean_price is not None and abs(mean_price) > 0.25:
            pts -= 2.0
        if mean_score is not None and abs(mean_score) > 0.75:
            pts -= 2.0
        pts = max(0.0, min(15.0, pts))
        why = f"match_rate={mr} mean_ts_delta_s={mean_ts} mean_price_delta={mean_price} mean_score_delta={mean_score}"
    components.append(("parity_stability", pts, why))

    # 3) Exit intelligence stability (0..15)
    if isinstance(excomp, dict):
        cnts = excomp.get("counts") if isinstance(excomp.get("counts"), dict) else {}
        cr = _safe_float(cnts.get("complete_rate"))
        if cr is None:
            pts = 7.0
            why = "exit completeness unknown"
        else:
            pts = 15.0 if cr >= 0.9 else (12.0 if cr >= 0.8 else (8.0 if cr >= 0.6 else (3.0 if cr >= 0.4 else 0.0)))
            why = f"exit completeness_rate={cr}"
    else:
        pts = 5.0
        why = "exit_intel_completeness telemetry missing"
    components.append(("exit_intelligence_stability", pts, why))

    # 4) Feature stability (0..15) using average stability score across top features
    if feat_rows_sorted:
        top = feat_rows_sorted[:20]
        avg_stab = sum([float(r.get("stability_score") or 0.0) for r in top]) / float(len(top))
        pts = 15.0 if avg_stab >= 85 else (12.0 if avg_stab >= 70 else (8.0 if avg_stab >= 50 else (3.0 if avg_stab >= 30 else 0.0)))
        why = f"avg_feature_stability(top20)={_float_fmt(avg_stab,1)}"
    else:
        pts = 5.0
        why = "no numeric features available"
    components.append(("feature_stability", pts, why))

    # 5) Signal stability (0..10): stable if most signals don't regress badly vs live.
    if sig_perf_rows_sorted:
        eligible = [r for r in sig_perf_rows_sorted if int(r.get("trade_count_shadow") or 0) >= 3]
        if not eligible:
            pts = 5.0
            why = "insufficient per-signal samples"
        else:
            regress = [r for r in eligible if float(r.get("delta_expectancy") or 0.0) < -0.5]
            frac_regress = len(regress) / float(len(eligible))
            pts = 10.0 if frac_regress <= 0.1 else (7.0 if frac_regress <= 0.25 else (4.0 if frac_regress <= 0.5 else 0.0))
            why = f"signals_with_shadow_n>=3={len(eligible)} frac_regressing={_float_fmt(frac_regress,3)}"
    else:
        pts = 5.0
        why = "no signals present"
    components.append(("signal_stability", pts, why))

    # 6) Regime stability (0..10) from telemetry regime_timeline (best-effort)
    pts = 5.0
    why = "regime_timeline unavailable"
    if isinstance(rt, dict):
        day_sum = rt.get("day_summary") if isinstance(rt.get("day_summary"), dict) else {}
        dom = str(day_sum.get("domin/at_regime_label") or "")
        vol_b = str(day_sum.get("volatility_bucket") or "")
        trend_b = str(day_sum.get("trend_bucket") or "")
        if dom:
            pts = 10.0 if dom.upper() in ("RISK_ON", "RISK_OFF", "NEUTRAL") else 7.0
            why = f"dominant_regime={dom} vol_bucket={vol_b} trend_bucket={trend_b}"
    components.append(("regime_stability", pts, why))

    # 7) Telemetry anomalies (0..10)
    pts = 10.0
    why_bits: List[str] = []
    if replacement_anomalies is True:
        pts -= 5.0
        why_bits.append("replacement_anomaly_detected")
    if missing_inputs:
        pts -= min(5.0, 1.0 * len(missing_inputs))
        why_bits.append(f"missing_inputs={len(missing_inputs)}")
    if anomalies:
        pts -= min(5.0, 0.5 * len(anomalies))
        why_bits.append(f"schema_anomalies={len(anomalies)}")
    pts = max(0.0, min(10.0, pts))
    components.append(("no_anomalies_in_telemetry", pts, " ".join(why_bits) if why_bits else "no anomalies detected"))

    # Total score
    total = sum([p for _, p, _ in components])
    total = max(0.0, min(100.0, total))
    recommendation = "promote" if total >= 85 else ("hold" if total >= 65 else "investigate")

    lines.append(_md_table(
        ["component", "points", "why"],
        [[name, _float_fmt(points, 1), why] for (name, points, why) in components],
    ))
    lines.append(_md_table(
        ["readiness_score (0-100)", "recommendation"],
        [[_float_fmt(total, 1), recommendation]],
    ))
    lines.append("")

    # ===== 11. FULL RAW APPENDIX =====
    lines.append("## 11. FULL RAW APPENDIX")
    lines.append("### All shadow events (raw, from `logs/shadow_trades.jsonl` for date)")
    lines.append("```")
    lines.append(json.dumps(shadow_events_today, indent=2, sort_keys=True, default=str)[:200000])
    lines.append("```")
    lines.append("")
    lines.append("### All shadow trades (cleaned)")
    lines.append("```")
    lines.append(json.dumps(trades_shadow, indent=2, sort_keys=True, default=str)[:200000])
    lines.append("```")
    lines.append("")

    lines.append("### All live trades (cleaned)")
    lines.append("```")
    lines.append(json.dumps(trades_live, indent=2, sort_keys=True, default=str)[:200000])
    lines.append("```")
    lines.append("")

    lines.append("### All feature snapshots (per-symbol averages; live vs shadow)")
    sym_feature_rows = []
    for r in per_sym_rows_sorted[:250]:
        # keep concise: top 20 features per symbol by abs(mean_shadow - mean_live)
        lm = r.get("live_feature_means", {}) if isinstance(r.get("live_feature_means"), dict) else {}
        sm = r.get("shadow_feature_means", {}) if isinstance(r.get("shadow_feature_means"), dict) else {}
        keys = sorted(set(lm.keys()) | set(sm.keys()))
        diffs = []
        for k in keys:
            a = _safe_float(lm.get(k))
            b = _safe_float(sm.get(k))
            if a is None and b is None:
                continue
            diffs.append((k, (b or 0.0) - (a or 0.0), a, b))
        diffs_sorted = sorted(diffs, key=lambda x: abs(float(x[1])), reverse=True)[:20]
        sym_feature_rows.append(
            {
                "symbol": r.get("symbol"),
                "top_feature_mean_deltas": [
                    {"feature": k, "delta": d, "live_mean": a, "shadow_mean": b} for k, d, a, b in diffs_sorted
                ],
            }
        )
    lines.append("```")
    lines.append(json.dumps(sym_feature_rows, indent=2, sort_keys=True, default=str)[:200000])
    lines.append("```")
    lines.append("")

    lines.append("### All signals (distinct, live vs shadow)")
    lines.append("```")
    lines.append(json.dumps({"live": _collect_signals(trades_live), "shadow": _collect_signals(trades_shadow)}, indent=2, sort_keys=True, default=str)[:200000])
    lines.append("```")
    lines.append("")

    lines.append("### All exit attributions (today)")
    lines.append("```")
    lines.append(json.dumps(exit_attrib_today, indent=2, sort_keys=True, default=str)[:200000])
    lines.append("```")
    lines.append("")

    lines.append("### All parity rows (telemetry computed)")
    epd = telemetry.get("computed", {}).get("entry_parity_details.json") if isinstance(telemetry.get("computed"), dict) else None
    lines.append("```")
    lines.append(json.dumps(epd, indent=2, sort_keys=True, default=str)[:200000] if epd is not None else "(missing)")
    lines.append("```")
    lines.append("")

    lines.append("### All UW intel snapshots (telemetry state)")
    lines.append("```")
    lines.append(json.dumps(uw_snaps, indent=2, sort_keys=True, default=str)[:200000])
    lines.append("```")
    lines.append("")

    lines.append("### Telemetry computed artifacts (index only)")
    computed_names = sorted(list((telemetry.get("computed") or {}).keys())) if isinstance(telemetry.get("computed"), dict) else []
    lines.append("```")
    lines.append(json.dumps({"computed_files": computed_names}, indent=2, sort_keys=True, default=str))
    lines.append("```")
    lines.append("")

    # ===== SHADOW TUNING APPENDIX =====
    lines.append("## SHADOW TUNING APPENDIX")
    lines.append("- This appendix is large and intended to be machine-readable for future tuning.")
    # Per-symbol tuning blocks (shadow-only)
    sym_groups = _group_by(trades_shadow, lambda t: t.get("symbol", ""))
    tuning_symbols = []
    for sym, trs in sym_groups.items():
        pb = _perf_block(trs)
        if int(pb.get("trade_count_closed") or 0) >= 3:
            tuning_symbols.append((sym, trs, pb))
    tuning_symbols = sorted(tuning_symbols, key=lambda x: float(x[2].get("pnl_realized_usd") or 0.0), reverse=True)
    sym_payloads = []
    for sym, trs, pb in tuning_symbols:
        closed = _closed_trades(trs)
        by_side = _group_by(closed, lambda t: str(t.get("side") or ""))
        side_stats = {k: _perf_block(v) for k, v in by_side.items()}
        sym_payloads.append(
            {
                "symbol": sym,
                "closed_n": pb.get("trade_count_closed"),
                "pnl_realized_usd": pb.get("pnl_realized_usd"),
                "expectancy_usd": pb.get("expectancy_usd"),
                "win_rate": pb.get("win_rate"),
                "long_short": side_stats,
                "feature_profile_means": _numeric_feature_means(trs),
                "signals_used": _collect_signals(trs),
            }
        )
    lines.append("### Per-symbol tuning payload (shadow-only; sufficient samples)")
    lines.append("```")
    lines.append(json.dumps({"range": range_label, "symbols": sym_payloads}, indent=2, sort_keys=True, default=str)[:800000])
    lines.append("```")
    lines.append("")
    # Per-feature EV summaries
    feat_payloads = []
    for feat in shadow_features[:300]:
        curve = _ev_curve(trades_shadow, feat, bins=10)
        bl = curve.get("bins") if isinstance(curve.get("bins"), list) else []
        shape = _shape_monotonicity(bl)
        feat_payloads.append({"feature": feat, "n": curve.get("n"), "shape": shape, "bins": bl})
    lines.append("### Per-feature EV curve summaries (shadow-only)")
    lines.append("```")
    lines.append(json.dumps({"features": feat_payloads}, indent=2, sort_keys=True, default=str)[:800000])
    lines.append("```")
    lines.append("")
    # Per-signal EV summaries
    sig_payloads = []
    for s, trs in sorted(sig_rows.items(), key=lambda kv: len(_closed_trades(kv[1])), reverse=True)[:400]:
        pb = _perf_block(trs)
        sig_payloads.append(
            {
                "signal": s,
                "closed_n": pb.get("trade_count_closed"),
                "pnl_realized_usd": pb.get("pnl_realized_usd"),
                "expectancy_usd": pb.get("expectancy_usd"),
                "win_rate": pb.get("win_rate"),
                "regime_breakdown": dict(Counter([_infer_regime(t) or "UNKNOWN" for t in _closed_trades(trs)])),
                "sector_breakdown": dict(Counter([_infer_sector(t) or "UNKNOWN" for t in _closed_trades(trs)])),
            }
        )
    lines.append("### Per-signal EV summaries (shadow-only)")
    lines.append("```")
    lines.append(json.dumps({"signals": sig_payloads}, indent=2, sort_keys=True, default=str)[:800000])
    lines.append("```")
    lines.append("")

    if anomalies:
        lines.append("## Detected anomalies (best-effort)")
        for a in anomalies:
            lines.append(f"- {a}")
        lines.append("")

    # Final safety: avoid emitting "nan" strings.
    md = "\n".join(lines) + "\n"
    if "nan" in md.lower():
        md = md.replace("nan", "n/a").replace("NaN", "n/a")
    return md


def _validate_report_text(md: str) -> List[str]:
    """
    Validation per user rules:
    - contains all required sections
    - no 'NaN' strings
    """
    issues: List[str] = []
    required = [
        "## 1. TOP-LINE SUMMARY",
        "## 2. PER-SYMBOL PERFORMANCE",
        "## 3. PER-SIGNAL PERFORMANCE (LIVE VS SHADOW)",
        "## 4. FEATURE EV CURVES (LIVE VS SHADOW)",
        "## 5. REGIME & SECTOR ANALYSIS",
        "## 6. EXIT INTELLIGENCE ANALYSIS",
        "## 7. PARITY ANALYSIS (LIVE VS SHADOW)",
        "## 8. UW INTEL & EQUALIZER KNOB ANALYSIS",
        "## 9. LONG/SHORT CORRECTNESS AUDIT",
        "## 10. SHADOW PROMOTION READINESS SCORE",
        "## 11. FULL RAW APPENDIX",
    ]
    for h in required:
        if h not in md:
            issues.append(f"missing_section: {h}")
    if "nan" in md.lower():
        issues.append("contains_nan_string")
    return issues


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="", help="YYYY-MM-DD (default: today UTC)")
    ap.add_argument("--start-date", dest="start_date", default="", help="YYYY-MM-DD (inclusive)")
    ap.add_argument("--end-date", dest="end_date", default="", help="YYYY-MM-DD (inclusive)")
    args = ap.parse_args()

    range_label, days, mode = _resolve_date_range(args)
    days_set = set(days)
    missing_inputs: List[str] = []
    anomalies: List[str] = []

    master_log = ROOT / "logs" / "master_trade_log.jsonl"
    shadow_log = ROOT / "logs" / "shadow_trades.jsonl"
    exit_attr_log = ROOT / "logs" / "exit_attribution.jsonl"

    if not master_log.exists():
        missing_inputs.append("logs/master_trade_log.jsonl (missing)")
    if not shadow_log.exists():
        missing_inputs.append("logs/shadow_trades.jsonl (not applicable: shadow removed)")
    if not exit_attr_log.exists():
        missing_inputs.append("logs/exit_attribution.jsonl (missing)")

    trades = _load_trades_for_days(days_set, master_log) if master_log.exists() else []
    exit_attrib_today = _load_exit_attribution_for_days(days_set, exit_attr_log) if exit_attr_log.exists() else []
    shadow_events_today = _load_shadow_events_for_days(days_set, shadow_log) if shadow_log.exists() else []
    if exit_attrib_today and trades:
        _merge_exit_attribution(trades, exit_attrib_today)

    trades_live, trades_shadow = _split_live_shadow(trades)

    # Basic schema validation (signals list, snapshots dict, exit_reason string|null)
    for t in trades_live + trades_shadow:
        if not isinstance(t.get("signals"), list):
            anomalies.append(f"signals_not_list: symbol={t.get('symbol')} trade_id={t.get('trade_id')}")
            t["signals"] = normalize_signals(t.get("signals"))
        if not isinstance(t.get("feature_snapshot"), dict):
            anomalies.append(f"feature_snapshot_not_dict: symbol={t.get('symbol')} trade_id={t.get('trade_id')}")
            t["feature_snapshot"] = _normalize_feature_snapshot(t.get("feature_snapshot"))
        if not isinstance(t.get("regime_snapshot"), dict):
            anomalies.append(f"regime_snapshot_not_dict: symbol={t.get('symbol')} trade_id={t.get('trade_id')}")
            t["regime_snapshot"] = _normalize_regime_snapshot(t.get("regime_snapshot"))
        er = t.get("exit_reason")
        if er is not None and not isinstance(er, str):
            anomalies.append(f"exit_reason_not_string_or_null: symbol={t.get('symbol')} trade_id={t.get('trade_id')}")
            t["exit_reason"] = _normalize_exit_reason(er)

    telemetry_by_day = _load_telemetry_bundles(days)
    # keep existing single-day telemetry object as "primary"
    telemetry = telemetry_by_day.get(days[0], {}) if days else {}
    for d in days:
        if not (ROOT / "telemetry" / d).exists():
            missing_inputs.append(f"telemetry/{d}/ (missing)")

    out_dir = ROOT / "analysis_packs" / range_label
    out_path = out_dir / "SHADOW_VS_LIVE_DEEP_DIVE.md"
    _ensure_dir(out_dir)

    md = _render_report(
        range_label=range_label,
        days=days,
        mode=mode,
        trades_live=trades_live,
        trades_shadow=trades_shadow,
        exit_attrib_today=exit_attrib_today,
        telemetry=telemetry,
        telemetry_by_day=telemetry_by_day,
        shadow_events_today=shadow_events_today,
        anomalies=anomalies,
        missing_inputs=missing_inputs,
    )
    _write_text(out_path, md)

    # Validation rules (best-effort; do not crash)
    issues = _validate_report_text(md)
    if issues:
        # Append validation issues at bottom (still additive; report remains readable).
        extra = "\n".join(["", "## Validation issues (best-effort)", *[f"- {x}" for x in issues], ""])
        _write_text(out_path, md + extra)

    print(str(out_path.as_posix()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

