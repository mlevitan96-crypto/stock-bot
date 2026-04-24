#!/usr/bin/env python3
"""
Run a single scenario review against the last-387 exit baseline. DROPLET ONLY.
Read-only: no live changes. Writes reports/board/scenarios/<scenario_id>_review.json and .md.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _iter_exit_attribution_last_n(base: Path, n: int) -> list:
    p = base / "logs" / "exit_attribution.jsonl"
    if not p.exists():
        return []
    lines = [ln for ln in p.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()]
    recent = lines[-n:] if len(lines) > n else lines
    out = []
    for ln in recent:
        try:
            out.append(json.loads(ln))
        except json.JSONDecodeError:
            continue
    return out

def run_a1(base: Path, baseline: dict) -> dict:
    blocked = baseline.get("blocked_trade_distribution") or {}
    n = blocked.get("displacement_blocked", 0)
    pnl = baseline.get("pnl") or {}
    total_exits = pnl.get("total_exits") or 1
    total_pnl = pnl.get("total_pnl_attribution_usd") or 0
    avg_pnl_per = total_pnl / total_exits if total_exits else 0
    win_rate = pnl.get("win_rate") or 0
    return {
        "scenario_id": "A1",
        "name": "Ignore displacement_blocked",
        "additional_trades_admitted": n,
        "counterfactual_pnl_proxy_usd": round(n * avg_pnl_per, 2),
        "baseline_win_rate": win_rate,
        "risk_note": "Relaxing displacement may increase drawdown; capacity unchanged.",
        "expected_improvement": "neutral_to_negative if avg executed PnL stays negative",
    }

def run_a2(base: Path, baseline: dict) -> dict:
    blocked = baseline.get("blocked_trade_distribution") or {}
    n = blocked.get("max_positions_reached", 0)
    pnl = baseline.get("pnl") or {}
    total_exits = pnl.get("total_exits") or 1
    total_pnl = pnl.get("total_pnl_attribution_usd") or 0
    avg_pnl_per = total_pnl / total_exits if total_exits else 0
    return {
        "scenario_id": "A2",
        "name": "Ignore max_positions_reached",
        "additional_trades_admitted": n,
        "counterfactual_pnl_proxy_usd": round(n * avg_pnl_per, 2),
        "risk_note": "Increases concentration; regulatory/risk limit exposure.",
        "expected_improvement": "low; more positions can worsen tail.",
    }

def run_a3(base: Path, baseline: dict) -> dict:
    blocked = baseline.get("blocked_trade_distribution") or {}
    n = blocked.get("expectancy_blocked:score_floor_breach", 0)
    pnl = baseline.get("pnl") or {}
    total_exits = pnl.get("total_exits") or 1
    total_pnl = pnl.get("total_pnl_attribution_usd") or 0
    avg_pnl_per = total_pnl / total_exits if total_exits else 0
    return {
        "scenario_id": "A3",
        "name": "Lower expectancy score floor by one notch",
        "additional_trades_admitted_estimate": max(20, min(40, n // 4)),
        "blocked_at_floor": n,
        "counterfactual_pnl_proxy_usd": round((n // 4) * avg_pnl_per, 2),
        "risk_note": "Lower floor admits lower-score trades; backtest recommended.",
        "expected_improvement": "moderate if score band 2.5-3.0 is profitable.",
    }

def run_b1(base: Path, baseline: dict) -> dict:
    exits = _iter_exit_attribution_last_n(base, 387)
    if not exits:
        return {"scenario_id": "B1", "name": "Extend minimum hold +X min", "error": "No exit_attribution data", "expected_improvement": "TBD"}
    hold_minutes = []
    pnls = []
    for r in exits:
        h = r.get("time_in_trade_minutes") or r.get("hold_minutes")
        if h is not None:
            try:
                hold_minutes.append(float(h))
            except (TypeError, ValueError):
                pass
        p = r.get("pnl_usd") or r.get("pnl") or r.get("realized_pnl_usd") or 0
        try:
            pnls.append(float(p))
        except (TypeError, ValueError):
            pass
    avg_hold = sum(hold_minutes) / len(hold_minutes) if hold_minutes else 0
    X = 15
    would_exclude = sum(1 for h in hold_minutes if h < X)
    return {
        "scenario_id": "B1",
        "name": "Extend minimum hold by +15 min",
        "baseline_avg_hold_minutes": round(avg_hold, 2),
        "exits_with_hold_below_15min": would_exclude,
        "expectancy_delta_note": "Excluding early exits may reduce churn; hold vs drawdown TBD.",
        "expected_improvement": "moderate if early exits are net negative.",
    }

def run_b2(base: Path, baseline: dict) -> dict:
    exits = _iter_exit_attribution_last_n(base, 387)
    if not exits:
        return {"scenario_id": "B2", "name": "Remove early signal_decay exits", "error": "No exit_attribution data", "expected_improvement": "TBD"}
    early_decay = 0
    for r in exits:
        reason = str(r.get("exit_reason") or r.get("close_reason") or "")
        if "signal_decay" in reason:
            h = r.get("time_in_trade_minutes") or r.get("hold_minutes")
            if h is not None and float(h) < 30:
                early_decay += 1
    dist = baseline.get("exit_reason_distribution") or {}
    total_decay = sum(v for k, v in dist.items() if "signal_decay" in k)
    return {
        "scenario_id": "B2",
        "name": "Remove early signal_decay exits",
        "early_signal_decay_exits_under_30min": early_decay,
        "total_signal_decay_exits_in_scope": total_decay,
        "expectancy_delta_note": "Removing early decay may extend winners; test on replay.",
        "expected_improvement": "moderate if early decay cuts winners.",
    }

def run_b3(base: Path, baseline: dict) -> dict:
    dist = baseline.get("exit_reason_distribution") or {}
    time_based = sum(v for k, v in dist.items() if "signal_decay" in k or "time" in k.lower())
    tp_like = sum(v for k, v in dist.items() if "tp" in k.lower() or "target" in k.lower() or "take_profit" in k.lower())
    other = sum(dist.values()) - time_based - tp_like
    return {
        "scenario_id": "B3",
        "name": "Favor TP over time-based exits",
        "time_based_exit_count": time_based,
        "tp_like_exit_count": tp_like,
        "other": other,
        "hold_time_vs_drawdown_note": "Current mix is time/signal_decay heavy; TP favor needs rule change.",
        "expected_improvement": "moderate if TP captures more upside.",
    }

def run_c1(base: Path, baseline: dict) -> dict:
    blocked = baseline.get("blocked_trade_distribution") or {}
    pnl = baseline.get("pnl") or {}
    total_exits = pnl.get("total_exits") or 1
    total_pnl = pnl.get("total_pnl_attribution_usd") or 0
    avg_pnl = total_pnl / total_exits if total_exits else 0
    ranked = sorted(blocked.items(), key=lambda x: -x[1])
    opportunity_cost_proxy = [(r[0], r[1], round(r[1] * avg_pnl, 2)) for r in ranked[:5]]
    return {
        "scenario_id": "C1",
        "name": "Re-rank block reasons by realized opportunity cost",
        "ranked_by_count": [r[0] for r in ranked],
        "opportunity_cost_proxy_usd": dict((r[0], r[2]) for r in opportunity_cost_proxy),
        "expected_improvement": "Prioritize relaxing blocks with highest negative opportunity cost.",
    }

def run_c2(base: Path, baseline: dict) -> dict:
    blocked = baseline.get("blocked_trade_distribution") or {}
    return {
        "scenario_id": "C2",
        "name": "Identify blocks that correlate with positive counterfactual PnL",
        "good_vetoes_note": "Blocks that would have lost (need estimate_blocked_outcome per block).",
        "missed_winners_note": "Blocks that would have won (same). Run counter_intelligence_analysis on droplet for full C2.",
        "block_reason_counts": blocked,
        "expected_improvement": "High if we can relax only 'missed winner' blocks.",
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-dir", default=".", help="Repo root (e.g. . on droplet)")
    ap.add_argument("--scenario-id", required=True, choices=["A1","A2","A3","B1","B2","B3","C1","C2"])
    args = ap.parse_args()
    base = Path(args.base_dir)
    baseline_path = base / "reports" / "board" / "last387_comprehensive_review.json"
    baseline = _load_json(baseline_path)
    if not baseline:
        print("Baseline last387_comprehensive_review.json not found", file=sys.stderr)
        return 1
    runners = {"A1": run_a1, "A2": run_a2, "A3": run_a3, "B1": run_b1, "B2": run_b2, "B3": run_b3, "C1": run_c1, "C2": run_c2}
    result = runners[args.scenario_id](base, baseline)
    result["baseline_scope"] = "last 387 exits"
    result["run_ts"] = datetime.now(timezone.utc).isoformat()
    out_dir = base / "reports" / "board" / "scenarios"
    out_dir.mkdir(parents=True, exist_ok=True)
    sid = result["scenario_id"]
    json_path = out_dir / f"{sid}_review.json"
    md_path = out_dir / f"{sid}_review.md"
    json_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    md_lines = [f"# Scenario {sid}: {result.get('name', sid)}", "", f"**Run (UTC):** {result.get('run_ts')}", ""]
    for k, v in result.items():
        if k in ("scenario_id", "name", "run_ts", "baseline_scope"):
            continue
        md_lines.append(f"- **{k}:** {v}")
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
