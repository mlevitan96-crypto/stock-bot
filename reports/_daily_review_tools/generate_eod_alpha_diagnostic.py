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


def _data_availability(attribution_path: Path, gate_path: Path, exit_path: Path, state_paths: Dict[str, Path]) -> Dict[str, str]:
    avail: Dict[str, str] = {}
    for name, p in [("attribution", attribution_path), ("gate", gate_path), ("exit", exit_path)]:
        avail[name] = "PASS" if p.exists() else "FAIL"
    for name, p in state_paths.items():
        avail[name] = "PASS" if p.exists() else "FAIL"
    return avail


def run(date_str: str) -> Path:
    attribution_path = LOG_DIR / "attribution.jsonl"
    gate_path = LOG_DIR / "gate.jsonl"
    exit_path = LOG_DIR / "exit.jsonl"
    se_path = LOG_DIR / "system_events.jsonl"
    attribution = _load_jsonl(attribution_path, date_str)
    gate = _load_jsonl(gate_path, date_str)
    exits = _load_jsonl(exit_path, date_str)
    system_events = _load_jsonl(se_path, date_str) if se_path.exists() else []

    hl = _headline(attribution)
    disp = _displacement_summary([], system_events, date_str)
    state_paths = {
        "market_context_v2": STATE_DIR / "market_context_v2.json",
        "regime_posture_state": STATE_DIR / "regime_posture_state.json",
        "symbol_risk_features": STATE_DIR / "symbol_risk_features.json",
    }
    data_avail = _data_availability(attribution_path, gate_path, exit_path, state_paths)

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
        "## Data availability and substitutions",
        "",
    ])
    for k, v in data_avail.items():
        lines.append(f"- **{k}:** {v}")
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
