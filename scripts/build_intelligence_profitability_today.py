#!/usr/bin/env python3
"""
Build profitability-aware intelligence artifacts (read-only; no behavior change).

Writes to telemetry/YYYY-MM-DD/computed/:
- signal_profitability.json (per signal_family: count, avg PnL, contribution)
- gate_profitability.json (per gate: PnL of passed trades, counterfactual of blocked)
- intelligence_recommendations.json (status, confidence, suggested_action per signal/gate)

Used ONLY for display and human decision-making; does not change weights or gates.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

REPO = Path(__file__).resolve().parents[1]
REPORTS = REPO / "reports"
TELEMETRY_DIR = REPO / "telemetry"


def _load(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Build signal/gate profitability and recommendations")
    ap.add_argument("--date", default=None, help="YYYY-MM-DD (default: latest telemetry or today)")
    args = ap.parse_args()

    date_str = args.date
    if not date_str:
        if TELEMETRY_DIR.exists():
            dates = [d.name for d in TELEMETRY_DIR.iterdir() if d.is_dir() and len(d.name) == 10]
            date_str = max(dates) if dates else datetime.now(timezone.utc).strftime("%Y-%m-%d")
        else:
            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    raw = _load(REPORTS / "PERF_TODAY_RAW_STATS.json")
    blocked = _load(TELEMETRY_DIR / date_str / "computed" / "blocked_counterfactuals_summary.json")
    signals_summary = (raw or {}).get("signals_summary") or {}
    gates_summary = (raw or {}).get("gates_summary") or {}
    stats = (raw or {}).get("stats") or {}
    total_pnl = float(stats.get("net_pnl_usd") or 0)

    # signal_profitability.json (profitability_alignment_score: -1 to 1, confidence, suggested_action)
    by_sig = signals_summary.get("by_signal_family") or {}
    signal_profitability = []
    for name, v in by_sig.items():
        if not isinstance(v, dict):
            continue
        count = int(v.get("count") or 0)
        pnl_sum = float(v.get("pnl_sum") or 0)
        avg_pnl = pnl_sum / count if count else 0
        contrib = (pnl_sum / total_pnl * 100) if total_pnl else 0
        status = "support" if avg_pnl > 0 else ("hurt" if avg_pnl < 0 else "neutral")
        confidence = "high" if count >= 50 else ("med" if count >= 10 else "low")
        action = "consider_upweight" if avg_pnl > 0 else ("consider_downweight" if avg_pnl < 0 else "monitor_only")
        align = 1.0 if status == "support" else (-1.0 if status == "hurt" else 0.0)
        signal_profitability.append({
            "signal_family": name,
            "count": count,
            "avg_pnl_per_trade": round(avg_pnl, 4),
            "contribution_to_total_pnl_pct": round(contrib, 2),
            "profitability_alignment_score": align,
            "status": status,
            "confidence": confidence,
            "suggested_action": action,
        })
    out_dir = TELEMETRY_DIR / date_str / "computed"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "signal_profitability.json").write_text(
        json.dumps({"date": date_str, "signals": signal_profitability, "total_pnl_usd": total_pnl}, indent=2),
        encoding="utf-8",
    )

    # gate_profitability.json (profitability_alignment_score per gate where applicable)
    disp_blocked = int(gates_summary.get("displacement_blocked") or 0)
    disp_allowed = int(gates_summary.get("displacement_allowed") or 0)
    cf_pnl_blocked = 0.0
    disp_align = 0.0
    disp_action = "monitor_only"
    if blocked and isinstance(blocked.get("per_blocked_reason"), dict):
        disp = blocked["per_blocked_reason"].get("displacement_blocked") or {}
        if isinstance(disp, dict) and disp.get("count"):
            if disp.get("avg_counterfactual_pnl_30m") is not None:
                cf_pnl_blocked = disp["count"] * disp["avg_counterfactual_pnl_30m"]
            acf = disp.get("avg_counterfactual_pnl_30m")
            if acf is not None:
                disp_align = 1.0 if acf > 0 else (-1.0 if acf < 0 else 0.0)
                disp_action = "consider_relax" if acf > 0 else ("consider_tighten" if acf < 0 else "monitor_only")
    gate_profitability = {
        "date": date_str,
        "displacement": {
            "allowed_count": disp_allowed,
            "blocked_count": disp_blocked,
            "pnl_of_passed_trades": total_pnl,
            "counterfactual_pnl_blocked_30m": round(cf_pnl_blocked, 2),
            "profitability_alignment_score": disp_align,
            "suggested_action": disp_action,
        },
        "directional_gate": {
            "events": int(gates_summary.get("directional_gate_events") or 0),
            "blocked_approx": int(gates_summary.get("directional_gate_blocked_approx") or 0),
        },
    }
    (out_dir / "gate_profitability.json").write_text(json.dumps(gate_profitability, indent=2), encoding="utf-8")

    # intelligence_recommendations.json (status, confidence, suggested_action, profitability_alignment_score)
    recommendations = []
    for s in signal_profitability:
        recommendations.append({
            "entity_type": "signal_family",
            "entity": s["signal_family"],
            "status": s.get("status", "neutral"),
            "confidence": s.get("confidence", "low"),
            "suggested_action": s.get("suggested_action", "monitor_only"),
            "profitability_alignment_score": s.get("profitability_alignment_score", 0.0),
        })
    # Gate recommendations from blocked counterfactuals
    if blocked and isinstance(blocked.get("per_blocked_reason"), dict):
        for reason, v in blocked["per_blocked_reason"].items():
            if not isinstance(v, dict):
                continue
            avg_cf = v.get("avg_counterfactual_pnl_30m")
            pct_win = v.get("pct_would_win_30m")
            count = v.get("count") or 0
            if avg_cf is None:
                continue
            status = "support" if avg_cf > 0 else ("hurt" if avg_cf < 0 else "neutral")
            confidence = "high" if count >= 100 else ("med" if count >= 20 else "low")
            if "displacement" in reason and avg_cf > 0:
                action = "consider_relax"
            elif "displacement" in reason and avg_cf < 0:
                action = "consider_tighten"
            else:
                action = "monitor_only"
            align = 1.0 if status == "support" else (-1.0 if status == "hurt" else 0.0)
            recommendations.append({
                "entity_type": "gate",
                "entity": reason,
                "status": status,
                "confidence": confidence,
                "suggested_action": action,
                "profitability_alignment_score": align,
            })
    (out_dir / "intelligence_recommendations.json").write_text(
        json.dumps({"date": date_str, "recommendations": recommendations}, indent=2),
        encoding="utf-8",
    )
    print(f"[OK] Wrote signal_profitability.json, gate_profitability.json, intelligence_recommendations.json to {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
