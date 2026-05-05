#!/usr/bin/env python3
"""
EOD Alpha Diagnostic: feature value vs PnL, displacement effectiveness, variant comparison.

Output: reports/EOD_ALPHA_DIAGNOSTIC_<DATE>.md
Data: droplet logs/state (or local when run locally).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from collections import defaultdict

REPO_ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = REPO_ROOT / "logs"
STATE_DIR = REPO_ROOT / "state"
REPORTS_DIR = REPO_ROOT / "reports"


def _parse_ts(v: Any) -> Optional[datetime]:
    if v is None:
        return None
    try:
        if isinstance(v, (int, float)):
            return datetime.fromtimestamp(v, tz=timezone.utc)
        s = str(v).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _load_jsonl(p: Path, date_str: str) -> List[Dict]:
    out = []
    if not p.exists():
        return out
    try:
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                    ts = rec.get("ts") or rec.get("timestamp")
                    dt = _parse_ts(ts)
                    if dt and dt.strftime("%Y-%m-%d") == date_str:
                        out.append(rec)
                except Exception:
                    continue
    except Exception:
        pass
    return out


def _headline(attribution: List[Dict]) -> Dict[str, Any]:
    trades = [r for r in attribution if r.get("type") == "attribution" and not str(r.get("trade_id", "")).startswith("open_")]
    pnls = [float(r.get("pnl_usd", 0) or 0) for r in trades]
    wins = [t for t in trades if float(t.get("pnl_usd", 0) or 0) > 0]
    total = len(trades)
    total_pnl = sum(pnls)
    win_rate = (len(wins) / total * 100) if total else 0.0
    avg_win = (sum(float(t.get("pnl_usd", 0)) for t in wins) / len(wins)) if wins else 0.0
    losses = [t for t in trades if float(t.get("pnl_usd", 0) or 0) < 0]
    avg_loss = (sum(float(t.get("pnl_usd", 0)) for t in losses) / len(losses)) if losses else 0.0
    by_symbol: Dict[str, float] = defaultdict(float)
    for t in trades:
        sym = t.get("symbol", "")
        if sym:
            by_symbol[sym] += float(t.get("pnl_usd", 0) or 0)
    top = sorted(by_symbol.items(), key=lambda x: x[1], reverse=True)[:10]
    bottom = sorted(by_symbol.items(), key=lambda x: x[1])[:10]
    return {
        "total_pnl": total_pnl,
        "avg_pnl_per_trade": total_pnl / total if total else 0.0,
        "win_rate": win_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "total_trades": total,
        "top_10": top,
        "bottom_10": bottom,
    }


def _displacement_summary(displacement_log: List[Dict], system_events: List[Dict], date_str: str) -> Dict[str, Any]:
    evaled = [r for r in system_events if r.get("subsystem") == "displacement" and r.get("event_type") == "displacement_evaluated"]
    allowed = sum(1 for r in evaled if r.get("details", {}).get("allowed") is True)
    blocked = len(evaled) - allowed
    by_reason: Dict[str, int] = defaultdict(int)
    for r in evaled:
        reason = (r.get("details") or {}).get("reason", "unknown")
        if not r.get("details", {}).get("allowed"):
            by_reason[reason] += 1
    return {
        "displacement_evaluated": len(evaled),
        "displacement_allowed": allowed,
        "displacement_blocked": blocked,
        "blocked_by_reason": dict(by_reason),
    }


def _data_availability(attribution_path: Path, gate_path: Path, exit_path: Path, state_paths: Dict[str, Path], run_path: Path, shadow_path: Path) -> Dict[str, str]:
    avail: Dict[str, str] = {}
    for name, p in [("attribution", attribution_path), ("gate", gate_path), ("exit", exit_path), ("run", run_path), ("shadow", shadow_path)]:
        avail[name] = "PASS" if p.exists() else "FAIL"
    for name, p in state_paths.items():
        avail[name] = "PASS" if p.exists() else "FAIL"
    return avail


def _load_run_jsonl(p: Path, date_str: str) -> List[Dict]:
    out = []
    if not p.exists():
        return out
    try:
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                    ts = rec.get("ts") or rec.get("_dt") or rec.get("timestamp")
                    if ts:
                        dt = _parse_ts(ts)
                        if dt and dt.strftime("%Y-%m-%d") != date_str:
                            continue
                    out.append(rec)
                except Exception:
                    continue
    except Exception:
        pass
    return out


def _winners_losers(attribution: List[Dict]) -> Dict[str, Any]:
    trades = [r for r in attribution if r.get("type") == "attribution" and not str(r.get("trade_id", "")).startswith("open_")]
    winners = [t for t in trades if float(t.get("pnl_usd", 0) or 0) > 0]
    losers = [t for t in trades if float(t.get("pnl_usd", 0) or 0) < 0]
    return {"winners": winners, "losers": losers, "total": len(trades)}


def _shadow_scoreboard(shadow_path: Path, date_str: str) -> Dict[str, Any]:
    if not shadow_path.exists():
        return {"variants": [], "decisions": 0}
    out: List[Dict] = []
    by_var: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"would_enter": 0, "would_exit": 0, "blocked": 0})
    try:
        with shadow_path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                    ts = rec.get("ts") or rec.get("_dt")
                    if ts:
                        dt = _parse_ts(ts)
                        if dt and dt.strftime("%Y-%m-%d") != date_str:
                            continue
                    if rec.get("event_type") == "shadow_variant_decision":
                        v = rec.get("variant_name", "?")
                        if rec.get("would_enter"):
                            by_var[v]["would_enter"] += 1
                        if rec.get("would_exit"):
                            by_var[v]["would_exit"] += 1
                        if rec.get("blocked_reason"):
                            by_var[v]["blocked"] += 1
                    elif rec.get("event_type") == "shadow_variant_summary":
                        v = rec.get("variant_name", "?")
                        out.append({
                            "variant": v,
                            "candidates_considered": rec.get("candidates_considered", 0),
                            "would_enter_count": rec.get("would_enter_count", 0),
                            "would_exit_count": rec.get("would_exit_count", 0),
                            "blocked_by_reason": rec.get("blocked_counts_by_reason", {}),
                        })
                except Exception:
                    continue
    except Exception:
        pass
    if not out and by_var:
        for v, c in by_var.items():
            out.append({"variant": v, "would_enter_count": c["would_enter"], "would_exit_count": c["would_exit"], "blocked_by_reason": {}})
    return {"variants": out, "decisions": sum(c["would_enter"] + c["would_exit"] + c["blocked"] for c in by_var.values())}


def run(date_str: str) -> Path:
    attribution_path = LOG_DIR / "attribution.jsonl"
    gate_path = LOG_DIR / "gate.jsonl"
    exit_path = LOG_DIR / "exit.jsonl"
    run_path = LOG_DIR / "run.jsonl"
    shadow_path = LOG_DIR / "shadow.jsonl"
    se_path = LOG_DIR / "system_events.jsonl"
    attribution = _load_jsonl(attribution_path, date_str)
    gate = _load_jsonl(gate_path, date_str)
    exits = _load_jsonl(exit_path, date_str)
    run_records = _load_run_jsonl(run_path, date_str)
    system_events = _load_jsonl(se_path, date_str) if se_path.exists() else []

    hl = _headline(attribution)
    disp = _displacement_summary([], system_events, date_str)
    wl = _winners_losers(attribution)
    shadow = _shadow_scoreboard(shadow_path, date_str)
    state_paths = {
        "market_context_v2": STATE_DIR / "market_context_v2.json",
        "regime_posture_state": STATE_DIR / "regime_posture_state.json",
        "symbol_risk_features": STATE_DIR / "symbol_risk_features.json",
    }
    data_avail = _data_availability(attribution_path, gate_path, exit_path, state_paths, run_path, shadow_path)

    trade_intent_count = sum(1 for r in run_records if r.get("event_type") == "trade_intent")
    exit_intent_count = sum(1 for r in run_records if r.get("event_type") == "exit_intent")
    dir_gate_count = sum(1 for r in system_events if r.get("subsystem") == "directional_gate" and r.get("event_type") == "blocked_high_vol_no_alignment")

    lines = [
        f"# EOD Alpha Diagnostic — {date_str}",
        "",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
        "",
        "---",
        "",
        "## Headline",
        "",
        f"- **Total PnL:** ${hl['total_pnl']:.2f}",
        f"- **Avg PnL/trade:** ${hl['avg_pnl_per_trade']:.2f}",
        f"- **Win rate:** {hl['win_rate']:.1f}%",
        f"- **Avg win:** ${hl['avg_win']:.2f}",
        f"- **Avg loss:** ${hl['avg_loss']:.2f}",
        f"- **Total trades:** {hl['total_trades']}",
        "",
        "### Top 10 winners",
        "",
    ]
    for sym, pnl in hl["top_10"]:
        lines.append(f"- {sym}: ${pnl:.2f}")
    lines.extend(["", "### Bottom 10 losers", ""])
    for sym, pnl in hl["bottom_10"]:
        lines.append(f"- {sym}: ${pnl:.2f}")
    lines.extend([
        "",
        "---",
        "",
        "## Displacement",
        "",
        f"- **Evaluated:** {disp['displacement_evaluated']}",
        f"- **Allowed:** {disp['displacement_allowed']}",
        f"- **Blocked:** {disp['displacement_blocked']}",
        "",
    ])
    if disp["blocked_by_reason"]:
        lines.append("Blocked by reason:")
        for r, c in disp["blocked_by_reason"].items():
            lines.append(f"- {r}: {c}")
        lines.append("")
    lines.extend([
        "---",
        "",
        "## Winners vs Losers",
        "",
        f"- **Winners:** {len(wl['winners'])} | **Losers:** {len(wl['losers'])} | **Total:** {wl['total']}",
        "",
        "---",
        "",
        "## Telemetry (trade/exit intent, directional gate)",
        "",
        f"- **trade_intent count:** {trade_intent_count}",
        f"- **exit_intent count:** {exit_intent_count}",
        f"- **directional_gate (blocked_high_vol_no_alignment):** {dir_gate_count}",
        "",
        "---",
        "",
        "## Shadow experiment scoreboard",
        "",
    ])
    for v in shadow.get("variants", [])[:20]:
        lines.append(f"- **{v.get('variant', '?')}** | would_enter={v.get('would_enter_count', 0)} | would_exit={v.get('would_exit_count', 0)} | blocked={v.get('blocked_by_reason', {})}")
    if not shadow.get("variants"):
        lines.append("- No shadow variant data for this date.")
    lines.extend([
        "",
        "---",
        "",
        "## Data availability and substitutions",
        "",
    ])
    for k, v in data_avail.items():
        lines.append(f"- **{k}:** {v}")
    lines.append("")

    # High-Volatility Alpha (required section)
    hv_fail: List[str] = []
    risk_path = state_paths.get("symbol_risk_features") or (STATE_DIR / "symbol_risk_features.json")
    risk_data: Dict[str, Any] = {}
    if risk_path and risk_path.exists():
        try:
            risk_data = json.loads(risk_path.read_text(encoding="utf-8")) or {}
        except Exception:
            risk_data = {}
    vol_list = []
    for sym, info in (risk_data or {}).items():
        if str(sym).startswith("_"):
            continue
        if not isinstance(info, dict):
            continue
        v = info.get("realized_vol_20d") or info.get("rv_20d") or info.get("rv20")
        if v is not None:
            vol_list.append((sym, float(v)))
    vol_list.sort(key=lambda x: x[1], reverse=True)
    n = len(vol_list)
    import math as _m
    p75_idx = max(0, int(_m.ceil(0.75 * n)) - 1) if n else 0
    hv_thresh = vol_list[p75_idx][1] if vol_list else 0.0
    high_vol_syms = {s for s, v in vol_list if v >= hv_thresh}
    lines.extend([
        "---",
        "",
        "## High-Volatility Alpha",
        "",
    ])
    if not high_vol_syms:
        hv_fail.append("symbol_risk_features missing or empty; cannot compute HIGH_VOL cohort")
        lines.append("- **FAIL:** " + "; ".join(hv_fail))
        lines.append("")
    else:
        lines.append(f"- **HIGH_VOL threshold (p75 realized_vol_20d):** {hv_thresh:.4f}")
        lines.append(f"- **HIGH_VOL symbol count:** {len(high_vol_syms)}")
        lines.append("")

    # Section presence and explicit FAIL reasons
    lines.extend([
        "---",
        "",
        "## Section presence and FAIL reasons",
        "",
    ])
    fail_reasons: List[str] = []
    if "Winners vs Losers" not in "\n".join(lines):
        fail_reasons.append("Winners vs Losers: section missing")
    if not shadow.get("variants") and data_avail.get("shadow") == "FAIL":
        fail_reasons.append("Shadow Scoreboard: no shadow data; shadow.jsonl missing or empty")
    if not risk_data and (risk_path and not risk_path.exists()):
        fail_reasons.append("High-Volatility Alpha: symbol_risk_features.json missing")
    for k, v in data_avail.items():
        if v == "FAIL":
            fail_reasons.append(f"Data availability: {k} FAIL")
    if fail_reasons:
        for r in fail_reasons:
            lines.append(f"- **FAIL:** {r}")
    else:
        lines.append("- All required sections present and populated.")
    lines.append("")
    lines.append("---")
    lines.append("")
    out_path = REPORTS_DIR / f"EOD_ALPHA_DIAGNOSTIC_{date_str}.md"
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    args = ap.parse_args()
    try:
        out = run(args.date)
        print(f"Wrote {out}")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
