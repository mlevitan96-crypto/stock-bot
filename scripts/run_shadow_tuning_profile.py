#!/usr/bin/env python3
"""
Run shadow tuning profile (paper simulation only; no live change).

Reads PERF_TODAY_RAW_STATS, blocked_counterfactuals_summary, exit_quality_summary
and applies profile heuristics from config/shadow_tuning_profiles.yaml.
Writes reports/SHADOW_TUNING_<profile>.json and reports/SHADOW_TUNING_<profile>.md.

NOT LIVE: This is analysis only; no trading logic or config is modified.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO = Path(__file__).resolve().parents[1]
REPORTS = REPO / "reports"
CONFIG = REPO / "config"
TELEMETRY_DIR = REPO / "telemetry"


def _load_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _latest_telemetry_date() -> Optional[str]:
    if not TELEMETRY_DIR.exists():
        return None
    dates = [d.name for d in TELEMETRY_DIR.iterdir() if d.is_dir() and len(d.name) == 10 and d.name[:4].isdigit()]
    return max(dates) if dates else None


def run_profile(
    profile_name: str,
    date_str: Optional[str] = None,
    raw_stats: Optional[Dict] = None,
    blocked_summary: Optional[Dict] = None,
    exit_summary: Optional[Dict] = None,
    profiles_config: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Apply profile heuristics to produce hypothetical PnL, block rate, exit quality.
    Returns dict for SHADOW_TUNING_<profile>.json and .md.
    """
    date_str = date_str or _latest_telemetry_date() or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if raw_stats is None:
        raw_stats = _load_json(REPORTS / "PERF_TODAY_RAW_STATS.json") or {}
    stats = raw_stats.get("stats") or {}
    signals = raw_stats.get("signals_summary") or {}
    gates = raw_stats.get("gates_summary") or {}

    if profiles_config is None:
        try:
            import yaml
            cfg_path = CONFIG / "shadow_tuning_profiles.yaml"
            if cfg_path.exists():
                profiles_config = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
            else:
                profiles_config = {}
        except Exception:
            profiles_config = {}

    profiles = profiles_config.get("profiles") or profiles_config
    if isinstance(profiles, dict) and profile_name in profiles and isinstance(profiles.get(profile_name), dict):
        profile = profiles[profile_name]
    else:
        profile = {"displacement_relax_pct": 0, "min_exec_score_delta": 0, "exit_tighten_pct": 0}

    relax_pct = float(profile.get("displacement_relax_pct") or 0) / 100.0
    exit_tighten_pct = float(profile.get("exit_tighten_pct") or 0) / 100.0

    # Baseline from actual
    base_pnl = float(stats.get("net_pnl_usd") or 0)
    base_trades = int(stats.get("total_trades") or 0)
    base_wr = float(stats.get("win_rate_pct") or 0)
    base_dd = float(stats.get("max_drawdown_usd") or 0)
    ti_total = int(signals.get("trade_intent_count") or 0)
    ti_blocked = int(signals.get("blocked") or 0)
    ti_entered = int(signals.get("entered") or 0)
    disp_blocked = int(gates.get("displacement_blocked") or 0)

    out = {
        "profile": profile_name,
        "date": date_str,
        "description": profile.get("description") or "",
        "baseline": {
            "net_pnl_usd": base_pnl,
            "total_trades": base_trades,
            "win_rate_pct": base_wr,
            "max_drawdown_usd": base_dd,
            "trade_intent_total": ti_total,
            "trade_intent_blocked": ti_blocked,
            "trade_intent_entered": ti_entered,
            "displacement_blocked": disp_blocked,
        },
        "hypothetical": {
            "net_pnl_usd": base_pnl,
            "total_trades": base_trades,
            "win_rate_pct": base_wr,
            "max_drawdown_usd": base_dd,
            "block_rate_pct": (100 * ti_blocked / ti_total) if ti_total else 0,
        },
        "notes": [],
    }

    # Relaxed displacement: add counterfactual PnL from blocked_counterfactuals_summary
    if relax_pct > 0 and blocked_summary:
        per_reason = blocked_summary.get("per_blocked_reason") or {}
        disp = per_reason.get("displacement_blocked") or per_reason.get("displacement_blocked") or {}
        if isinstance(disp, dict):
            count = int(disp.get("count") or 0)
            avg_30m = disp.get("avg_counterfactual_pnl_30m")
            if count and avg_30m is not None:
                add_pnl = relax_pct * count * float(avg_30m)
                out["hypothetical"]["net_pnl_usd"] = round(base_pnl + add_pnl, 2)
                out["notes"].append(f"Relaxed displacement: +{relax_pct*100:.0f}% of {count} blocks → +{add_pnl:.2f} USD counterfactual")
        # Fallback: use top_symbols or aggregate from summary
        top = blocked_summary.get("top_symbols_by_counterfactual_pnl_30m") or []
        if not out["notes"] and top:
            total_cf = sum(float(r.get("pnl_sum_30m") or 0) for r in top)
            add_pnl = relax_pct * total_cf
            out["hypothetical"]["net_pnl_usd"] = round(base_pnl + add_pnl, 2)
            out["notes"].append(f"Relaxed displacement (heuristic): +{add_pnl:.2f} USD from counterfactual sum")

    # Exit tighten: reduce "left on table" (heuristic)
    if exit_tighten_pct > 0 and exit_summary:
        per_reason = exit_summary.get("per_exit_reason") or {}
        left_total = 0.0
        count_total = 0
        for v in per_reason.values():
            if isinstance(v, dict):
                c = int(v.get("count") or 0)
                left = v.get("left_on_table_avg")
                if c and left is not None:
                    left_total += c * float(left)
                    count_total += c
        if count_total:
            saved = exit_tighten_pct * left_total
            out["hypothetical"]["net_pnl_usd"] = round(out["hypothetical"]["net_pnl_usd"] + saved, 2)
            out["notes"].append(f"Exit tighten: assume {exit_tighten_pct*100:.0f}% less left on table → +{saved:.2f} USD")

    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Run shadow tuning profile (paper only)")
    ap.add_argument("profile", choices=["baseline", "relaxed_displacement", "higher_min_exec_score", "exit_tighten"], help="Profile name")
    ap.add_argument("--date", default=None, help="YYYY-MM-DD (default: latest telemetry or today)")
    args = ap.parse_args()

    date_str = args.date or _latest_telemetry_date() or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    computed_dir = TELEMETRY_DIR / date_str / "computed"
    blocked_summary = _load_json(computed_dir / "blocked_counterfactuals_summary.json") if computed_dir.exists() else None
    exit_summary = _load_json(computed_dir / "exit_quality_summary.json") if computed_dir.exists() else None
    raw_stats = _load_json(REPORTS / "PERF_TODAY_RAW_STATS.json")

    result = run_profile(
        args.profile,
        date_str=date_str,
        raw_stats=raw_stats,
        blocked_summary=blocked_summary,
        exit_summary=exit_summary,
    )

    REPORTS.mkdir(parents=True, exist_ok=True)
    json_path = REPORTS / f"SHADOW_TUNING_{args.profile}.json"
    md_path = REPORTS / f"SHADOW_TUNING_{args.profile}.md"
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    hyp = result.get("hypothetical") or {}
    lines = [
        f"# Shadow Tuning: {args.profile}",
        "",
        f"**Date:** {date_str}",
        f"**Description:** {result.get('description', '')}",
        "",
        "## Baseline (actual)",
        f"- Net PnL (USD): {result.get('baseline', {}).get('net_pnl_usd', 'N/A')}",
        f"- Trade count: {result.get('baseline', {}).get('total_trades', 'N/A')}",
        f"- Win rate (%): {result.get('baseline', {}).get('win_rate_pct', 'N/A')}",
        f"- Max drawdown (USD): {result.get('baseline', {}).get('max_drawdown_usd', 'N/A')}",
        "",
        "## Hypothetical (profile applied)",
        f"- Net PnL (USD): {hyp.get('net_pnl_usd', 'N/A')}",
        f"- Block rate (%): {hyp.get('block_rate_pct', 'N/A')}",
        "",
        "## Notes",
    ]
    for n in result.get("notes") or []:
        lines.append(f"- {n}")
    lines.append("")
    lines.append("---")
    lines.append("*NOT LIVE YET — paper simulation only.*")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] Wrote {json_path}")
    print(f"[OK] Wrote {md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
