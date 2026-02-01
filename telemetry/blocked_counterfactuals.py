"""
Blocked-Trade Counterfactual Engine (telemetry only; no behavior change).

For every trade_intent that is BLOCKED:
- Record: ts, symbol, side, score, blocked_reason, incumbent_position_pnl, regime snapshot.
- Optionally compute counterfactual PnL at +5m, +15m, +30m when bars are available.

Outputs:
- telemetry/YYYY-MM-DD/blocked_counterfactuals.json
- telemetry/YYYY-MM-DD/computed/blocked_counterfactuals_summary.json

READ-ONLY from live trading; does not change gates or execution.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# Repo root when run from scripts/ or cwd
ROOT = Path(__file__).resolve().parents[1]
LOGS = ROOT / "logs"
TELEMETRY_DIR = ROOT / "telemetry"


def _parse_ts(v: Any) -> Optional[datetime]:
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


def _date_str(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")


def _load_run_jsonl(path: Path, date_str: str) -> List[Dict]:
    out: List[Dict] = []
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
            ts = rec.get("ts") or rec.get("_dt") or rec.get("timestamp")
            dt = _parse_ts(ts)
            if dt and _date_str(dt) != date_str:
                continue
            out.append(rec)
        except Exception:
            continue
    return out


def _get_regime_snapshot(state_dir: Path, ts: Optional[datetime]) -> Dict[str, Any]:
    """Best-effort regime/vol_bucket from state files."""
    out: Dict[str, Any] = {"regime": "", "vol_bucket": ""}
    try:
        rp = state_dir / "regime_detector_state.json"
        if rp.exists():
            data = json.loads(rp.read_text(encoding="utf-8"))
            out["regime"] = data.get("regime") or data.get("dominant_regime") or ""
            out["vol_bucket"] = data.get("volatility_bucket") or data.get("vol_bucket") or ""
    except Exception:
        pass
    return out


def _price_at_time(bars: List[Dict], target_ts: datetime, default: Optional[float]) -> Optional[float]:
    """Return close price at or just before target_ts from bars (list of {t, o, h, l, c})."""
    if not bars:
        return default
    best = None
    for b in bars:
        t = b.get("t") or b.get("timestamp")
        dt = _parse_ts(t)
        if dt and dt <= target_ts:
            best = float(b.get("c") or b.get("close") or 0)
        elif dt and dt > target_ts:
            break
    return best if best is not None else default


def _counterfactual_pnl(
    entry_price: float,
    exit_price: float,
    side: str,
    qty: float = 1.0,
) -> float:
    if side and str(side).lower() in ("short", "sell"):
        return (entry_price - exit_price) * qty
    return (exit_price - entry_price) * qty


def collect_blocked_intents(
    date_str: str,
    run_path: Optional[Path] = None,
    state_dir: Optional[Path] = None,
    get_bars_for_symbol: Optional[Callable[[str, datetime, int], Optional[List[Dict]]]] = None,
) -> List[Dict]:
    """
    Collect all blocked trade_intent records for date_str.
    If get_bars_for_symbol(symbol, intent_ts, limit_minutes) is provided, compute
    counterfactual PnL at +5m, +15m, +30m; otherwise counterfactual fields are null.
    """
    run_path = run_path or LOGS / "run.jsonl"
    state_dir = state_dir or ROOT / "state"
    records = _load_run_jsonl(run_path, date_str)
    intents = [
        r for r in records
        if r.get("event_type") == "trade_intent"
        and str(r.get("decision_outcome", "")).lower() != "entered"
    ]
    out: List[Dict] = []
    for r in intents:
        ts = r.get("ts") or r.get("_dt")
        dt = _parse_ts(ts)
        symbol = r.get("symbol") or "?"
        side = r.get("side") or "long"
        score = r.get("score")
        if score is not None:
            try:
                score = float(score)
            except Exception:
                pass
        blocked_reason = r.get("blocked_reason") or "unknown"
        # Incumbent PnL: from details if displacement
        incumbent_pnl: Optional[float] = None
        details = r.get("details") or {}
        if isinstance(details, dict):
            incumbent_pnl = details.get("incumbent_position_pnl") or details.get("incumbent_pnl")
            if incumbent_pnl is not None:
                try:
                    incumbent_pnl = float(incumbent_pnl)
                except Exception:
                    incumbent_pnl = None
        regime_snapshot = _get_regime_snapshot(state_dir, dt)
        # Intent price: from feature_snapshot or score context (best-effort)
        intent_price: Optional[float] = None
        fs = r.get("feature_snapshot") or {}
        if isinstance(fs, dict):
            intent_price = fs.get("last_price") or fs.get("close") or fs.get("price")
        if intent_price is not None:
            try:
                intent_price = float(intent_price)
            except Exception:
                intent_price = None

        rec: Dict[str, Any] = {
            "ts": ts,
            "symbol": symbol,
            "side": side,
            "score": score,
            "blocked_reason": blocked_reason,
            "incumbent_position_pnl": incumbent_pnl,
            "regime": regime_snapshot.get("regime"),
            "vol_bucket": regime_snapshot.get("vol_bucket"),
            "counterfactual_pnl_5m": None,
            "counterfactual_pnl_15m": None,
            "counterfactual_pnl_30m": None,
        }
        if get_bars_for_symbol and dt and intent_price is not None and symbol and symbol != "?":
            try:
                bars_30 = get_bars_for_symbol(symbol, dt, 35)
                if bars_30:
                    # bars are list of {t, c} or {timestamp, close}
                    for label, minutes in [("5m", 5), ("15m", 15), ("30m", 30)]:
                        target = dt + timedelta(minutes=minutes)
                        exit_price = _price_at_time(bars_30, target, intent_price)
                        if exit_price is not None:
                            pnl = _counterfactual_pnl(intent_price, exit_price, side)
                            rec[f"counterfactual_pnl_{label}"] = round(pnl, 4)
            except Exception:
                pass
        out.append(rec)
    return out


def build_summary(records: List[Dict]) -> Dict[str, Any]:
    """Build blocked_counterfactuals_summary.json content."""
    by_reason: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"count": 0, "pnl_sum_5m": 0.0, "pnl_sum_15m": 0.0, "pnl_sum_30m": 0.0, "winners_5m": 0, "winners_15m": 0, "winners_30m": 0})
    by_symbol: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"count": 0, "pnl_sum_5m": 0.0, "pnl_sum_15m": 0.0, "pnl_sum_30m": 0.0})
    for r in records:
        reason = r.get("blocked_reason") or "unknown"
        sym = r.get("symbol") or "?"
        by_reason[reason]["count"] += 1
        by_symbol[sym]["count"] += 1
        for label in ["5m", "15m", "30m"]:
            pnl = r.get(f"counterfactual_pnl_{label}")
            if pnl is not None:
                by_reason[reason][f"pnl_sum_{label}"] += pnl
                by_symbol[sym][f"pnl_sum_{label}"] += pnl
                if pnl > 0:
                    by_reason[reason][f"winners_{label}"] += 1
    per_reason = {}
    for reason, v in by_reason.items():
        c = v["count"]
        per_reason[reason] = {
            "count": c,
            "avg_counterfactual_pnl_5m": round(v["pnl_sum_5m"] / c, 4) if c else None,
            "avg_counterfactual_pnl_15m": round(v["pnl_sum_15m"] / c, 4) if c else None,
            "avg_counterfactual_pnl_30m": round(v["pnl_sum_30m"] / c, 4) if c else None,
            "pct_would_win_5m": round(100 * v["winners_5m"] / c, 2) if c else None,
            "pct_would_win_15m": round(100 * v["winners_15m"] / c, 2) if c else None,
            "pct_would_win_30m": round(100 * v["winners_30m"] / c, 2) if c else None,
        }
    # Top symbols by count and by avg PnL
    top_symbols_count = sorted(by_symbol.items(), key=lambda x: -x[1]["count"])[:20]
    top_symbols_pnl_30m = [(s, v) for s, v in by_symbol.items() if v.get("pnl_sum_30m") is not None]
    top_symbols_pnl_30m.sort(key=lambda x: -x[1]["pnl_sum_30m"])
    top_symbols_pnl_30m = top_symbols_pnl_30m[:20]
    return {
        "per_blocked_reason": per_reason,
        "top_symbols_by_count": [{"symbol": s, **v} for s, v in top_symbols_count],
        "top_symbols_by_counterfactual_pnl_30m": [{"symbol": s, "count": v["count"], "pnl_sum_30m": v["pnl_sum_30m"]} for s, v in top_symbols_pnl_30m],
    }


def run(date_str: str, output_dir: Optional[Path] = None, get_bars: Optional[Callable] = None) -> Tuple[Path, Path]:
    """
    Collect blocked intents, optionally compute counterfactuals, write JSON artifacts.
    Returns (blocked_counterfactuals_path, summary_path).
    """
    output_dir = output_dir or (TELEMETRY_DIR / date_str)
    output_dir.mkdir(parents=True, exist_ok=True)
    computed_dir = output_dir / "computed"
    computed_dir.mkdir(parents=True, exist_ok=True)

    records = collect_blocked_intents(date_str, get_bars_for_symbol=get_bars)
    raw_path = output_dir / "blocked_counterfactuals.json"
    raw_path.write_text(
        json.dumps({"date": date_str, "count": len(records), "records": records}, indent=2),
        encoding="utf-8",
    )
    summary = build_summary(records)
    summary_path = computed_dir / "blocked_counterfactuals_summary.json"
    summary_path.write_text(
        json.dumps({"date": date_str, **summary}, indent=2),
        encoding="utf-8",
    )
    return raw_path, summary_path
