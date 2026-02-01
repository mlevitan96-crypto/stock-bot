#!/usr/bin/env python3
"""
Performance Review — Today Only (run ON droplet).

Collects today's trades, trade_intent, exit_intent, self-heal, telemetry;
computes core metrics, signal/gate performance, regime context.
Writes raw JSON artifacts to reports/ for summarization.

Paths are relative to repo root (e.g. /root/stock-bot on droplet).
No trading logic changes; analysis only.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Repo root: when run on droplet, cwd is /root/stock-bot
REPO = Path(".").resolve()
LOGS = REPO / "logs"
STATE = REPO / "state"
DATA = REPO / "data"
REPORTS = REPO / "reports"
TELEMETRY_DIR = REPO / "telemetry"


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


def _date_from_record(rec: dict) -> Optional[str]:
    ts = rec.get("ts") or rec.get("_dt") or rec.get("timestamp")
    dt = _parse_ts(ts)
    return dt.strftime("%Y-%m-%d") if dt else None


def _load_jsonl(p: Path, date_str: Optional[str] = None) -> List[Dict]:
    out: List[Dict] = []
    if not p.exists():
        return out
    try:
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
                if date_str:
                    d = _date_from_record(rec)
                    if d != date_str:
                        continue
                out.append(rec)
            except Exception:
                continue
    except Exception:
        pass
    return out


def _today_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _infer_analysis_date() -> str:
    """Today from run.jsonl or UTC now."""
    run_path = LOGS / "run.jsonl"
    if not run_path.exists():
        return _today_utc()
    dates: List[str] = []
    for line in run_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
            d = _date_from_record(rec)
            if d:
                dates.append(d)
        except Exception:
            continue
    return max(dates) if dates else _today_utc()


# --- Trades & PnL (attribution + orders) ---


def _collect_trades_and_pnl(date_str: str) -> Tuple[List[Dict], Dict[str, Any]]:
    attr_path = LOGS / "attribution.jsonl"
    orders_path = LOGS / "orders.jsonl"
    attribution = _load_jsonl(attr_path, date_str)
    orders = _load_jsonl(orders_path, date_str)
    # Realized trades from attribution (type==attribution, not open_*)
    trades = [
        r for r in attribution
        if r.get("type") == "attribution" and not str(r.get("trade_id", "")).startswith("open_")
    ]
    pnls = [float(r.get("pnl_usd", 0) or 0) for r in trades]
    wins = [t for t in trades if float(t.get("pnl_usd", 0) or 0) > 0]
    losses = [t for t in trades if float(t.get("pnl_usd", 0) or 0) < 0]
    total_pnl = sum(pnls)
    n = len(trades)
    win_rate = (len(wins) / n * 100) if n else 0.0
    avg_win = (sum(float(t.get("pnl_usd", 0)) for t in wins) / len(wins)) if wins else 0.0
    avg_loss = (sum(float(t.get("pnl_usd", 0)) for t in losses) / len(losses)) if losses else 0.0
    # Intraday drawdown: cumulative PnL curve, then max peak-to-trough
    cum = 0.0
    peak = 0.0
    max_dd = 0.0
    for r in sorted(trades, key=lambda x: (x.get("ts") or x.get("_dt") or "")):
        cum += float(r.get("pnl_usd", 0) or 0)
        peak = max(peak, cum)
        max_dd = min(max_dd, cum - peak)
    # Exposure: sum of position sizes from orders (simplified)
    exposure_usd = 0.0
    by_sym: Dict[str, float] = defaultdict(float)
    for o in orders:
        if o.get("dry_run") or "audit_dry_run" in str(o.get("action", "")):
            continue
        qty = float(o.get("qty") or o.get("quantity") or 0)
        # No price in typical orders.jsonl; use placeholder or skip notional
        by_sym[o.get("symbol") or "?"] += qty
    stats = {
        "date": date_str,
        "total_trades": n,
        "net_pnl_usd": round(total_pnl, 2),
        "net_pnl_pct": round((total_pnl / 1.0) * 100, 2) if total_pnl else 0.0,  # placeholder denom
        "win_rate_pct": round(win_rate, 2),
        "avg_win_usd": round(avg_win, 2),
        "avg_loss_usd": round(avg_loss, 2),
        "max_drawdown_usd": round(max_dd, 2),
        "exposure_by_symbol": dict(by_sym),
        "real_orders_count": len([o for o in orders if not o.get("dry_run") and "audit_dry_run" not in str(o.get("action", ""))]),
    }
    # Slim trade records for JSON (drop large blobs)
    trades_slim = []
    for t in trades:
        trades_slim.append({
            "symbol": t.get("symbol"),
            "trade_id": t.get("trade_id"),
            "pnl_usd": t.get("pnl_usd"),
            "ts": t.get("ts") or t.get("_dt"),
            "close_reason": t.get("close_reason"),
        })
    return trades_slim, stats


# --- trade_intent, exit_intent, intelligence_trace ---


def _collect_signals_and_gates(date_str: str) -> Tuple[Dict[str, Any], Dict[str, Any], List[Dict]]:
    run = _load_jsonl(LOGS / "run.jsonl", date_str)
    se = _load_jsonl(LOGS / "system_events.jsonl", date_str)
    intents = [r for r in run if r.get("event_type") == "trade_intent"]
    exits = [r for r in run if r.get("event_type") == "exit_intent"]
    # Per-signal contribution from intelligence_trace (signal_families / layers)
    by_signal: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"count": 0, "entered": 0, "blocked": 0, "pnl_sum": 0.0})
    for r in intents:
        trace = r.get("intelligence_trace") or {}
        layers = trace.get("signal_layers") or trace.get("comps_to_signal_layers") or {}
        for name, val in (layers if isinstance(layers, dict) else {}).items():
            by_signal[name]["count"] += 1
            if str(r.get("decision_outcome", "")).lower() == "entered":
                by_signal[name]["entered"] += 1
            else:
                by_signal[name]["blocked"] += 1
    # Match trades to intents by symbol for PnL attribution to signal (best-effort)
    attr = _load_jsonl(LOGS / "attribution.jsonl", date_str)
    closed = [a for a in attr if a.get("type") == "attribution" and not str(a.get("trade_id", "")).startswith("open_")]
    for c in closed:
        pnl = float(c.get("pnl_usd", 0) or 0)
        sym = c.get("symbol")
        for r in intents:
            if r.get("symbol") == sym:
                trace = r.get("intelligence_trace") or {}
                layers = trace.get("signal_layers") or trace.get("comps_to_signal_layers") or {}
                for name in (layers if isinstance(layers, dict) else {}):
                    by_signal[name]["pnl_sum"] += pnl / max(len(layers), 1)
                break
    blocked_reasons: Dict[str, int] = defaultdict(int)
    for r in intents:
        if str(r.get("decision_outcome", "")).lower() != "entered":
            blocked_reasons[str(r.get("blocked_reason") or "unknown")] += 1
    signals_summary = {
        "trade_intent_count": len(intents),
        "exit_intent_count": len(exits),
        "entered": sum(1 for r in intents if str(r.get("decision_outcome", "")).lower() == "entered"),
        "blocked": sum(1 for r in intents if str(r.get("decision_outcome", "")).lower() != "entered"),
        "blocked_reasons": dict(blocked_reasons),
        "by_signal_family": {k: dict(v) for k, v in by_signal.items()},
    }
    # Gates: displacement + directional_gate from system_events
    disp = [r for r in se if r.get("subsystem") == "displacement" and r.get("event_type") == "displacement_evaluated"]
    dg = [r for r in se if r.get("subsystem") == "directional_gate"]
    gates_summary = {
        "displacement_evaluated": len(disp),
        "displacement_allowed": sum(1 for r in disp if (r.get("details") or {}).get("allowed") is True),
        "displacement_blocked": len(disp) - sum(1 for r in disp if (r.get("details") or {}).get("allowed") is True),
        "directional_gate_events": len(dg),
        "directional_gate_blocked_approx": sum(1 for r in dg if "block" in str(r.get("event_type", "")).lower()),
    }
    # Blocked trade analysis: intents that were blocked (we don't have counterfactual PnL)
    blocked_intents = [r for r in intents if str(r.get("decision_outcome", "")).lower() != "entered"]
    blocked_list = [
        {"symbol": r.get("symbol"), "blocked_reason": r.get("blocked_reason"), "ts": r.get("ts") or r.get("_dt")}
        for r in blocked_intents[:100]
    ]
    return signals_summary, gates_summary, blocked_list


# --- Self-heal ---


def _collect_self_heal(date_str: str) -> List[Dict]:
    path = DATA / "self_heal_events.jsonl"
    if not path.exists():
        path = REPO / "data" / "self_heal_events.jsonl"
    return _load_jsonl(path, date_str)


# --- Telemetry bundles (today) ---


def _collect_telemetry(date_str: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {"bundles": [], "computed": {}}
    day_dir = TELEMETRY_DIR / date_str
    if not day_dir.exists():
        return out
    for name in ["telemetry_manifest.json", "pnl_windows.json"]:
        p = day_dir / name
        if p.exists():
            try:
                out["bundles"].append({"name": name, "path": str(p)})
            except Exception:
                pass
    computed_dir = day_dir / "computed"
    if computed_dir.exists():
        for j in computed_dir.glob("*.json"):
            try:
                data = json.loads(j.read_text(encoding="utf-8"))
                out["computed"][j.name] = data
            except Exception:
                out["computed"][j.name] = {"_read_error": True}
    return out


# --- Regime ---


def _collect_regime(date_str: str, telemetry_computed: Dict[str, Any]) -> Dict[str, Any]:
    regime: Dict[str, Any] = {"date": date_str, "source": "none", "day_summary": {}, "trend_bucket": "", "volatility_bucket": ""}
    rt = telemetry_computed.get("regime_timeline.json") or {}
    if isinstance(rt, dict):
        regime["source"] = "telemetry"
        day = rt.get("day_summary") or {}
        regime["day_summary"] = day
        regime["trend_bucket"] = day.get("trend_bucket") or "unknown"
        regime["volatility_bucket"] = day.get("volatility_bucket") or ""
        regime["dominant_regime"] = day.get("dominant_market_regime") or day.get("dominant_regime_label") or "UNKNOWN"
    # Fallback: state files
    state_regime = STATE / "regime_detector_state.json"
    if state_regime.exists():
        try:
            data = json.loads(state_regime.read_text(encoding="utf-8"))
            regime["state_regime"] = data
        except Exception:
            pass
    return regime


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    date_str = _infer_analysis_date()
    print(f"PERF_TODAY_DATE={date_str}")

    trades_slim, raw_stats = _collect_trades_and_pnl(date_str)
    signals_summary, gates_summary, blocked_list = _collect_signals_and_gates(date_str)
    self_heal = _collect_self_heal(date_str)
    telemetry = _collect_telemetry(date_str)
    regime = _collect_regime(date_str, telemetry.get("computed") or {})

    meta = {
        "date": date_str,
        "self_heal_count": len(self_heal),
        "self_heal_events": [{"event_type": e.get("event_type"), "ts": e.get("ts")} for e in self_heal[:20]],
        "telemetry_bundles": telemetry.get("bundles", []),
        "telemetry_computed_keys": list((telemetry.get("computed") or {}).keys()),
    }
    (REPORTS / "PERF_TODAY_RAW_STATS.json").write_text(
        json.dumps({
            "date": date_str,
            "stats": raw_stats,
            "signals_summary": signals_summary,
            "gates_summary": gates_summary,
            "meta": meta,
        }, indent=2),
        encoding="utf-8",
    )
    (REPORTS / "PERF_TODAY_TRADES.json").write_text(
        json.dumps({"date": date_str, "trades": trades_slim}, indent=2),
        encoding="utf-8",
    )
    (REPORTS / "PERF_TODAY_SIGNALS.json").write_text(
        json.dumps({"date": date_str, **signals_summary, "blocked_sample": blocked_list[:50]}, indent=2),
        encoding="utf-8",
    )
    (REPORTS / "PERF_TODAY_GATES.json").write_text(
        json.dumps({"date": date_str, **gates_summary}, indent=2),
        encoding="utf-8",
    )
    (REPORTS / "PERF_TODAY_REGIME.json").write_text(
        json.dumps(regime, indent=2),
        encoding="utf-8",
    )

    print(f"[OK] Wrote PERF_TODAY_RAW_STATS.json, PERF_TODAY_TRADES.json, PERF_TODAY_SIGNALS.json, PERF_TODAY_GATES.json, PERF_TODAY_REGIME.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
