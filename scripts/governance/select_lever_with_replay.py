#!/usr/bin/env python3
"""
Replay-driven lever selection for equity governance (odd cycles).
Compares live recommendation (entry_vs_exit_blame, signal_effectiveness) with top replay
candidate from reports/replay/equity_replay_campaign_*/ranked_candidates.json.
Chooses the lever with stronger evidence (expectancy, trade_count, consistency);
writes overlay_config.json for the cycle. If no replay candidates exist, uses live only.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _load_json(p: Path) -> dict:
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _latest_campaign_dir(base: Path) -> Path | None:
    reports = base / "reports" / "replay"
    if not reports.exists():
        return None
    dirs = sorted(reports.glob("equity_replay_campaign_*"), key=lambda d: d.name, reverse=True)
    return dirs[0] if dirs else None


def _ranked_candidates(campaign_dir: Path) -> list:
    for name in ("ranked_candidates.json", "campaign_results.json"):
        p = campaign_dir / name
        if not p.exists():
            continue
        data = _load_json(p)
        if name == "campaign_results.json":
            return data.get("ranked_candidates") or []
        return data if isinstance(data, list) else []
    return []


def _build_live_overlay(lever: str, rec: dict, run_tag: str) -> dict:
    gov_entry = os.environ.get("GOVERNANCE_ENTRY_THRESHOLD")
    gov_exit = os.environ.get("GOVERNANCE_EXIT_STRENGTH")
    if lever == "entry":
        suggested = rec.get("suggested_min_exec_score")
        if rec.get("entry_lever_type") == "down_weight_signal" and rec.get("worst_signal_id") and rec.get("down_weight_delta") is not None:
            change = {"signal_weight_delta": {rec["worst_signal_id"]: float(rec["down_weight_delta"])}}
        elif gov_entry:
            change = {"type": "entry_bump", "min_exec_score": float(gov_entry)}
        elif suggested is not None:
            change = {"type": "entry_bump", "min_exec_score": float(suggested)}
        else:
            change = {"type": "entry_bump", "delta": 0.2}
        return {"run_tag": run_tag, "lever": "entry", "paper_only": True, "change": change}
    strength = float(gov_exit) if gov_exit else 0.03
    return {"run_tag": run_tag, "lever": "exit", "paper_only": True, "change": {"type": "single_exit_tweak", "strength": strength}}


def _build_replay_overlay(candidate: dict, run_tag: str) -> dict:
    lever_type = (candidate.get("lever_type") or "exit").lower()
    params = candidate.get("lever_params") or {}
    if lever_type == "entry" and "min_exec_score" in params:
        score = float(params["min_exec_score"])
        change = {"type": "entry_bump", "min_exec_score": round(score, 2), "delta": round(score - 2.5, 2)}
        return {"run_tag": run_tag, "lever": "entry", "paper_only": True, "change": change}
    if lever_type == "exit" and "flow_deterioration" in params:
        strength = round(float(params["flow_deterioration"]) - 0.22, 2)
        change = {"type": "single_exit_tweak", "strength": strength}
        return {"run_tag": run_tag, "lever": "exit", "paper_only": True, "change": change}
    strength = float(params.get("flow_deterioration", 0.25)) - 0.22 if params else 0.03
    return {"run_tag": run_tag, "lever": "exit", "paper_only": True, "change": {"type": "single_exit_tweak", "strength": round(strength, 2)}}


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Select lever (live vs top replay); write overlay_config.json")
    ap.add_argument("--recommendation", type=Path, required=True, help="recommendation.json from generate_recommendation")
    ap.add_argument("--baseline-dir", type=Path, required=True, help="Baseline effectiveness dir (for live expectancy)")
    ap.add_argument("--out-dir", type=Path, required=True, help="Governance run out dir (write overlay_config.json)")
    ap.add_argument("--run-tag", type=str, default=None, help="Run tag (default: from env or out_dir name)")
    ap.add_argument("--base-dir", type=Path, default=REPO, help="Repo root for replay dirs")
    args = ap.parse_args()

    rec_path = args.recommendation.resolve()
    if not rec_path.exists():
        print(f"Recommendation not found: {rec_path}", file=sys.stderr)
        return 1
    rec = _load_json(rec_path)
    live_lever = (rec.get("next_lever") or "exit").lower()
    if live_lever not in ("entry", "exit"):
        live_lever = "exit"

    base_agg = _load_json(args.baseline_dir / "effectiveness_aggregates.json")
    live_expectancy = base_agg.get("expectancy_per_trade")
    if live_expectancy is not None:
        try:
            live_expectancy = float(live_expectancy)
        except Exception:
            live_expectancy = None

    run_tag = args.run_tag or os.environ.get("RUN_TAG", args.out_dir.name)
    campaign_dir = _latest_campaign_dir(args.base_dir)
    ranked = _ranked_candidates(campaign_dir) if campaign_dir else []

    chosen_lever = live_lever
    source = "live"
    if ranked and len(ranked) > 0:
        top = ranked[0]
        replay_exp = top.get("expectancy_per_trade")
        replay_trades = top.get("trade_count") or 0
        try:
            replay_exp = float(replay_exp) if replay_exp is not None else None
        except Exception:
            replay_exp = None
        # Prefer replay if: sufficient trades and (replay expectancy > live baseline, or live expectancy missing)
        if replay_trades >= 30 and replay_exp is not None:
            if live_expectancy is None or replay_exp > live_expectancy:
                chosen_lever = (top.get("lever_type") or "exit").lower()
                if chosen_lever not in ("entry", "exit"):
                    chosen_lever = "exit"
                source = "replay"

    if source == "replay" and ranked:
        overlay = _build_replay_overlay(ranked[0], run_tag)
    else:
        overlay = _build_live_overlay(chosen_lever, rec, run_tag)

    out_file = args.out_dir / "overlay_config.json"
    args.out_dir.mkdir(parents=True, exist_ok=True)
    overlay["lever"] = "entry" if chosen_lever == "entry" else "exit"
    out_file.write_text(json.dumps(overlay, indent=2), encoding="utf-8")
    print(f"Lever selection: {source} -> {chosen_lever} (live_expectancy={live_expectancy}, overlay_config written)", file=sys.stderr)
    print(overlay["lever"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
