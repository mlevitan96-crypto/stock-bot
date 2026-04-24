#!/usr/bin/env python3
"""
Run a single exit replay scenario over closed trades (offline only).
Applies scenario filters: min_hold_minutes, signal_decay_threshold, remove_components.
TP/SL/trail require bar data for full simulation; this replay uses actual exit price and filters.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.analysis.attribution_loader import load_joined_closed_trades
from scripts.exit_research.exit_component_map import (
    get_component_vector,
    parse_signal_decay_from_reason,
)


def _day_utc(ts: Any) -> str:
    if ts is None:
        return ""
    s = str(ts)[:10]
    return s if len(s) == 10 and s[4] == "-" else ""


def _load_config(config_path: Path) -> Dict[str, Any]:
    if not config_path.exists():
        return {}
    return json.loads(config_path.read_text(encoding="utf-8"))


def _would_exit_under_scenario(
    trade: Dict[str, Any],
    scenario: Dict[str, Any],
    decay_threshold_numeric: float,
) -> bool:
    """
    True if this trade would count as closed under the scenario.
    - min_hold: actual hold >= min_hold else exclude (would still be open).
    - signal_decay_threshold: if exit_reason is signal_decay(X), only include if X >= threshold (we exited at or above this decay level).
    - remove_components: recompute effective exit score without those components; if still >= 0.55, include.
    """
    hold = trade.get("time_in_trade_minutes")
    if hold is not None:
        try:
            hold = float(hold)
        except (TypeError, ValueError):
            hold = 0
    else:
        hold = 0
    min_hold = scenario.get("min_hold_minutes") or 0
    if min_hold > 0 and hold < min_hold:
        return False

    reason = trade.get("exit_reason") or ""
    decay_val = parse_signal_decay_from_reason(reason)
    if decay_threshold_numeric > 0:
        if decay_val is not None:
            if decay_val < decay_threshold_numeric:
                return False
        elif "signal_decay" in str(reason).lower():
            return False

    remove = scenario.get("remove_components") or []
    if remove:
        comp_vec = get_component_vector(trade)
        exit_score = float(trade.get("v2_exit_score") or 0)
        if exit_score <= 0:
            exit_score = sum(comp_vec.values())
        effective = exit_score - sum(comp_vec.get(r, 0) for r in remove)
        if effective < 0.55:
            return False
    return True


def run_scenario(
    base_path: Path,
    config: Dict[str, Any],
    scenario: Dict[str, Any],
    start_date: str,
    end_date: str,
) -> Dict[str, Any]:
    attr_path = base_path / (config.get("attribution_path") or "logs/attribution.jsonl")
    exit_path = base_path / (config.get("exit_attribution_path") or "logs/exit_attribution.jsonl")
    if not exit_path.exists():
        return {
            "error": "exit_attribution.jsonl not found",
            "scenario": scenario.get("name"),
            "total_trades": 0,
        }
    joined = load_joined_closed_trades(attr_path, exit_path, start_date=start_date, end_date=end_date)
    decay_threshold = float(scenario.get("signal_decay_threshold") or 0)

    filtered: List[Dict[str, Any]] = []
    for t in joined:
        if _would_exit_under_scenario(t, scenario, decay_threshold):
            filtered.append(t)

    pnls: List[float] = []
    holds: List[float] = []
    reasons: Counter = Counter()
    by_regime: Dict[str, List[float]] = {}

    for t in filtered:
        pnl = float(t.get("pnl") or t.get("pnl_usd") or 0)
        pnls.append(pnl)
        hold = t.get("time_in_trade_minutes")
        if hold is not None:
            try:
                holds.append(float(hold))
            except (TypeError, ValueError):
                pass
        reason = str(t.get("exit_reason") or "unknown").strip() or "unknown"
        reasons[reason] += 1
        regime = str(t.get("entry_regime") or "UNKNOWN").strip()
        if regime not in by_regime:
            by_regime[regime] = []
        by_regime[regime].append(pnl)

    n = len(filtered)
    total_pnl = sum(pnls)
    expectancy = total_pnl / n if n else 0
    wins = sum(1 for p in pnls if p > 0)
    win_rate = wins / n if n else 0
    avg_hold = sum(holds) / len(holds) if holds else None
    pnls_sorted = sorted(pnls)
    tail_5pct = pnls_sorted[int(len(pnls_sorted) * 0.05)] if len(pnls_sorted) > 20 else (pnls_sorted[0] if pnls_sorted else 0)
    tail_1pct = pnls_sorted[int(len(pnls_sorted) * 0.01)] if len(pnls_sorted) > 100 else (pnls_sorted[0] if pnls_sorted else 0)

    per_regime = {}
    for reg, vals in by_regime.items():
        per_regime[reg] = {
            "trades": len(vals),
            "total_pnl": round(sum(vals), 2),
            "expectancy": round(sum(vals) / len(vals), 4) if vals else 0,
        }

    summary = {
        "scenario_name": scenario.get("name"),
        "scenario_params": {k: v for k, v in scenario.items() if k != "name"},
        "window_start": start_date,
        "window_end": end_date,
        "total_trades_in_window": len(joined),
        "total_trades_in_scenario": n,
        "total_pnl": round(total_pnl, 2),
        "expectancy_per_trade": round(expectancy, 4),
        "win_rate": round(win_rate, 4),
        "avg_hold_minutes": round(avg_hold, 2) if avg_hold is not None else None,
        "tail_loss_5pct": round(tail_5pct, 2) if n else None,
        "tail_loss_1pct": round(tail_1pct, 2) if n else None,
        "exit_reason_distribution": dict(reasons.most_common(20)),
        "per_regime": per_regime,
        "giveback_stats": None,
    }
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None, help="Path to exit_replay_config.json")
    ap.add_argument("--scenario", required=True, help="Scenario name or path to single scenario JSON")
    ap.add_argument("--start", default=None, help="Override start_date")
    ap.add_argument("--end", default=None, help="Override end_date")
    ap.add_argument("--base", default=None, help="Repo base path")
    ap.add_argument("--out-dir", default=None, help="Output directory for summary.json")
    args = ap.parse_args()

    base = Path(args.base) if args.base else REPO
    config_path = Path(args.config) if args.config else base / "scripts" / "exit_research" / "exit_replay_config.json"
    config = _load_config(config_path)
    start_date = args.start or config.get("start_date") or "2026-02-01"
    end_date = args.end or config.get("end_date") or "2026-03-02"
    out_dir = Path(args.out_dir) if args.out_dir else base / (config.get("scenarios_subdir") or "reports/exit_research/scenarios")

    scenario: Dict[str, Any]
    if args.scenario.endswith(".json"):
        scenario = json.loads(Path(args.scenario).read_text(encoding="utf-8"))
        scenario.setdefault("name", Path(args.scenario).stem)
    else:
        scenarios_path = base / (config.get("scenario_grid") or "scripts/exit_research/exit_scenarios.json")
        if not scenarios_path.exists():
            print(f"Scenarios file not found: {scenarios_path}", file=sys.stderr)
            return 1
        grid = json.loads(scenarios_path.read_text(encoding="utf-8"))
        scenarios_list = grid.get("scenarios") or grid
        scenario = next((s for s in scenarios_list if s.get("name") == args.scenario), None)
        if not scenario:
            print(f"Scenario '{args.scenario}' not found", file=sys.stderr)
            return 1

    summary = run_scenario(base, config, scenario, start_date, end_date)
    if summary.get("error"):
        print(summary["error"], file=sys.stderr)
        return 1

    scenario_name = summary["scenario_name"]
    scenario_out = out_dir / scenario_name
    scenario_out.mkdir(parents=True, exist_ok=True)
    (scenario_out / "summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(f"Wrote {scenario_out / 'summary.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
