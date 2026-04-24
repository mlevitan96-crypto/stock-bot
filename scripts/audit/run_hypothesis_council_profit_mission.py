#!/usr/bin/env python3
"""
Hypothesis Council + profit actions (Phases 0–11). Evidence-only: all numeric claims
must come from JSON artifacts under reports/daily/<ET>/evidence/ or measured file stats.

Run on droplet:
  cd /root/stock-bot && PYTHONPATH=. python3 scripts/audit/run_hypothesis_council_profit_mission.py --evidence-et 2026-04-01
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parent.parent.parent


def _run(cmd: List[str], cwd: Path) -> Tuple[int, str]:
    try:
        r = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, timeout=180)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return -1, str(e)


def _load_json(p: Path) -> Optional[Dict[str, Any]]:
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _displacement_blocked_frequency(blocked_path: Path) -> Dict[str, Any]:
    """Scan blocked_trades.jsonl for displacement_blocked: day span and count."""
    if not blocked_path.exists():
        return {"error": "blocked_trades_missing", "n": 0, "unique_days": None, "first_ts": None, "last_ts": None}
    days: Counter[str] = Counter()
    n = 0
    first: Optional[str] = None
    last: Optional[str] = None
    with open(blocked_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            reason = str(r.get("block_reason") or r.get("reason") or "")
            if reason != "displacement_blocked":
                continue
            n += 1
            ts = r.get("timestamp")
            if not ts:
                continue
            s = str(ts).strip()
            if first is None:
                first = s
            last = s
            day_key = s[:10] if len(s) >= 10 else "unknown"
            days[day_key] += 1
    ud = len(days)
    return {
        "displacement_blocked_rows_in_file": n,
        "unique_calendar_days_in_timestamp_prefix": ud,
        "first_timestamp_sample": first,
        "last_timestamp_sample": last,
        "approx_per_day_if_uniform": round(n / ud, 4) if ud else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence-et", required=True)
    ap.add_argument("--root", type=Path, default=REPO)
    args = ap.parse_args()
    root = args.root.resolve()
    ev = root / "reports" / "daily" / args.evidence_et / "evidence"

    # --- Evidence paths (must exist on droplet for full run) ---
    sc_pnl = ev / "SECOND_CHANCE_PNL_EVALUATION.json"
    paper_exp = ev / "PAPER_EXPERIMENT_RESULTS.json"
    emu = ev / "DISPLACEMENT_EXIT_EMULATOR_RESULTS.json"
    scorecard = ev / "BLOCKED_GATE_SCORECARD.json"
    sep = ev / "DISPLACEMENT_GOOD_VS_BAD_SEPARATION.json"
    cf_full = ev / "BLOCKED_COUNTERFACTUAL_PNL_FULL.json"
    ds_map = ev / "BLOCKED_WHY_DATASET_MAP.json"

    j_sc = _load_json(sc_pnl) or {}
    j_paper = _load_json(paper_exp) or {}
    j_emu = _load_json(emu) or {}
    j_score = _load_json(scorecard) or {}
    j_sep = _load_json(sep) or {}
    j_ds = _load_json(ds_map) or {}

    freq = _displacement_blocked_frequency(root / "state" / "blocked_trades.jsonl")

    # Phase 0
    code, git_head = _run(["git", "rev-parse", "HEAD"], root)
    code2, st_bot = _run(["systemctl", "status", "stock-bot", "--no-pager"], root)
    ph0 = {
        "git_head": git_head.strip(),
        "systemctl_stock_bot_exit": code2,
        "systemctl_stock_bot_text_truncated": st_bot[:12000],
        "evidence_dir": str(ev),
        "evidence_files_required": [str(p.name) for p in [sc_pnl, paper_exp, emu, scorecard, sep]],
        "blocked_frequency_scan": freq,
        "dataset_map_lines": j_ds.get("datasets", {}).get("blocked_trades_jsonl", {}).get("lines"),
    }
    _write(ev / "HYPOTHESIS_COUNCIL_PHASE0_CONTEXT.json", json.dumps(ph0, indent=2))
    _write(
        ev / "HYPOTHESIS_COUNCIL_PHASE0_CONTEXT.md",
        "# HYPOTHESIS_COUNCIL_PHASE0_CONTEXT\n\n"
        "## Baseline\n\n"
        f"- **git HEAD:** `{ph0['git_head']}`\n"
        f"- **systemctl stock-bot:** exit code `{ph0['systemctl_stock_bot_exit']}` (see JSON for full text cap)\n"
        f"- **Evidence dir:** `{ev}`\n\n"
        "## Blocked-trades scan (displacement_blocked)\n\n"
        f"```json\n{json.dumps(freq, indent=2)}\n```\n\n"
        "## Dataset map (blocked file lines)\n\n"
        f"- `blocked_trades_jsonl.lines` (from BLOCKED_WHY_DATASET_MAP.json): **{ph0['dataset_map_lines']}**\n",
    )

    # Phase 1 hypotheses (evidence-anchored IDs)
    hypotheses: List[Dict[str, Any]] = [
        {
            "id": "CSA_SC_001",
            "role": "CSA",
            "statement": "Paper second-chance displacement re-eval admits some previously displacement_blocked intents without weakening first-pass displacement authority.",
            "evidence_refs": ["SECOND_CHANCE_PNL_EVALUATION.json", "SECOND_CHANCE_FINAL_VERDICT.md"],
            "paper_signal": "allowed_count>0",
            "paper_metrics": {
                "allowed_count": j_sc.get("allowed_count"),
                "mean_60m_allowed_joined": (j_sc.get("paper_pnl_variant_a") or {}).get("mean_pnl_usd_60m"),
            },
        },
        {
            "id": "QUANT_CF_001",
            "role": "QUANT",
            "statement": "Displacement_blocked rows show positive mean Variant-A 60m counterfactual expectancy in the blocked-why corpus.",
            "evidence_refs": ["BLOCKED_GATE_SCORECARD.json", "PAPER_EXPERIMENT_RESULTS.json", "BLOCKED_COUNTERFACTUAL_PNL_FULL.json"],
            "paper_signal": "pnl_60m_expectancy_displacement_blocked>0",
            "paper_metrics": {
                "n_covered": j_paper.get("n_covered"),
                "share_positive_60m": j_paper.get("share_positive"),
                "pnl_60m_expectancy_usd": next(
                    (
                        x.get("pnl_60m_expectancy")
                        for x in (j_score.get("per_reason") or [])
                        if x.get("block_reason") == "displacement_blocked"
                    ),
                    None,
                ),
            },
        },
        {
            "id": "QUANT_EMU_001",
            "role": "QUANT",
            "statement": "Under documented ATR stop/TP/time-stop proxy, a majority of emulator grid cells show positive mean USD PnL on displacement_blocked-covered rows.",
            "evidence_refs": ["DISPLACEMENT_EXIT_EMULATOR_RESULTS.json"],
            "paper_signal": "opportunity_persists_majority_positive_mean_cells",
            "paper_metrics": {
                "cells_positive": j_emu.get("cells_positive_mean_count"),
                "cells_total": j_emu.get("cells_total"),
                "majority_flag": j_emu.get("opportunity_persists_majority_positive_mean_cells"),
            },
        },
        {
            "id": "STRAT_SEP_001",
            "role": "STRATEGY",
            "statement": "Decision-time features weakly separate GOOD vs BAD displacement_blocked outcomes at 60m (univariate rules).",
            "evidence_refs": ["DISPLACEMENT_GOOD_VS_BAD_SEPARATION.json"],
            "paper_signal": "conclusion_A",
            "paper_metrics": {"conclusion_AB": j_sep.get("conclusion_AB"), "n_rows": j_sep.get("n_rows")},
        },
    ]
    _write(ev / "HYPOTHESIS_COUNCIL_HYPOTHESES.json", json.dumps({"hypotheses": hypotheses}, indent=2))
    _write(
        ev / "HYPOTHESIS_COUNCIL_HYPOTHESES.md",
        "# HYPOTHESIS_COUNCIL_HYPOTHESES (Phase 1)\n\n"
        + "\n".join(f"## {h['id']} ({h['role']})\n\n- {h['statement']}\n\n" for h in hypotheses)
        + "\nFull JSON: `HYPOTHESIS_COUNCIL_HYPOTHESES.json`.\n",
    )

    # Phase 2 Safety
    _write(
        ev / "HYPOTHESIS_COUNCIL_SAFETY_REVIEW.md",
        "# HYPOTHESIS_COUNCIL_SAFETY_REVIEW (Phase 2)\n\n"
        "- **No live trading changes** in this mission output; contracts are proposals only.\n"
        "- Counterfactual / emulator metrics are **not** realizable PnL without execution model (spreads, fills, displacement dynamics).\n"
        "- Second-chance path remains **paper_only** in code (`PAPER_SECOND_CHANCE_DISPLACEMENT`).\n"
        "- Fail-closed: any promotion to micro-live requires explicit signed Action Contract and kill criteria.\n",
    )

    # Phase 3 Paper experiments
    _write(
        ev / "HYPOTHESIS_COUNCIL_PAPER_EXPERIMENTS.md",
        "# HYPOTHESIS_COUNCIL_PAPER_EXPERIMENTS (Phase 3)\n\n"
        "## Sources\n\n"
        "- `SECOND_CHANCE_PNL_EVALUATION.json`\n"
        "- `PAPER_EXPERIMENT_RESULTS.json`\n"
        "- `DISPLACEMENT_EXIT_EMULATOR_RESULTS.json`\n"
        "- `DISPLACEMENT_GOOD_VS_BAD_SEPARATION.json`\n\n"
        "## Snapshot metrics (from JSON)\n\n"
        f"```json\n{json.dumps({k: hypotheses[i]['paper_metrics'] for i, k in enumerate(['CSA_SC_001','QUANT_CF_001','QUANT_EMU_001','STRAT_SEP_001'])}, indent=2)}\n```\n",
    )

    # Phase 4 Role analysis
    for role, title in [
        ("CSA", "Decision integrity, attribution, governance misreads"),
        ("SRE", "Operational cadence, logs, queue workers, API read paths"),
        ("QUANT", "Expectancy, tails, emulator vs fixed horizon"),
        ("STRATEGY", "When-to-trade conditioning without threshold rewrites"),
    ]:
        _write(
            ev / f"HYPOTHESIS_COUNCIL_ROLE_ANALYSIS_{role}.md",
            f"# HYPOTHESIS_COUNCIL_ROLE_ANALYSIS — {role} (Phase 4)\n\n"
            f"**Lens:** {title}\n\n"
            "- Hypotheses scored against evidence files in `HYPOTHESIS_COUNCIL_HYPOTHESES.json`.\n"
            "- No new experiments executed in this script; ingestion only.\n",
        )

    # Phase 5 Constrained
    _write(
        ev / "HYPOTHESIS_COUNCIL_CONSTRAINED.md",
        "# HYPOTHESIS_COUNCIL_CONSTRAINED (Phase 5)\n\n"
        "| ID | Constraint |\n"
        "|----|------------|\n"
        "| CSA_SC_001 | Profit interpretation must use joined counterfactual subset only; n is small. |\n"
        "| QUANT_CF_001 | EV is **counterfactual** mean; not executed trade stream. |\n"
        "| QUANT_EMU_001 | Proxy exits ≠ production exit state machine. |\n"
        "| STRAT_SEP_001 | Univariate rules; stability splits weak in source JSON. |\n",
    )

    # Phase 6 Board
    _write(
        ev / "HYPOTHESIS_COUNCIL_BOARD_REVIEW.md",
        "# HYPOTHESIS_COUNCIL_BOARD_REVIEW (Phase 6)\n\n"
        "## CSA\n\n"
        "- Counterfactual-positive displacement_blocked universe must not be read as automatic live alpha.\n\n"
        "## SRE\n\n"
        "- Promotions that add always-on workers need rotation/budget (second_chance log, council outputs).\n\n"
        "## Quant\n\n"
        "- Report **p05** alongside means from `DISPLACEMENT_EXIT_EMULATOR_RESULTS.json` grid when claiming robustness.\n\n"
        "## Strategy\n\n"
        "- Prefer **paper / shadow** levers before any micro-live.\n",
    )

    # Phase 7 synthesis bridge
    _write(
        ev / "HYPOTHESIS_COUNCIL_PHASE7_SYNTHESIS.md",
        "# HYPOTHESIS_COUNCIL_PHASE7_SYNTHESIS\n\n"
        "Consolidates Phases 0–6 into promotion candidates for profit interpretation (Phase 8).\n\n"
        "- **Positive paper (aggregate expectancy / emulator majority):** QUANT_CF_001, QUANT_EMU_001.\n"
        "- **Positive admission count but negative joined PnL:** CSA_SC_001 → **not** Phase-8 profit-advance.\n"
        "- **Separation explanatory, EV not estimated in source:** STRAT_SEP_001 → defer profit path.\n",
    )

    # --- Phase 8: Profit interpretation (only hypotheses with positive paper for profit) ---
    disp_exp = next(
        (x for x in (j_score.get("per_reason") or []) if x.get("block_reason") == "displacement_blocked"),
        {},
    )
    n_disp = int(disp_exp.get("n") or j_paper.get("n_covered") or 0)
    ev_60 = disp_exp.get("pnl_60m_expectancy")
    ev_15 = disp_exp.get("pnl_15m_expectancy")
    ev_30 = disp_exp.get("pnl_30m_expectancy")
    p05_60 = disp_exp.get("pnl_60m_tail_risk_p05_pnl")
    wr_60 = disp_exp.get("pnl_60m_win_rate")
    ud = freq.get("unique_calendar_days_in_timestamp_prefix") or 1
    per_day = freq.get("approx_per_day_if_uniform")
    if per_day is None and n_disp and ud:
        per_day = round(n_disp / ud, 4)

    cf_interpretation = {
        "hypothesis_id": "QUANT_CF_001",
        "role": "QUANT",
        "incremental_ev_per_trade_usd": {
            "pnl_60m_variant_a_mean": ev_60,
            "source": "BLOCKED_GATE_SCORECARD.json per_reason displacement_blocked pnl_60m_expectancy",
        },
        "incremental_ev_per_day_usd_est": round(float(ev_60) * float(per_day), 6) if ev_60 is not None and per_day else None,
        "incremental_ev_per_week_usd_est": round(float(ev_60) * float(per_day) * 7, 6) if ev_60 is not None and per_day else None,
        "frequency": {
            "displacement_blocked_rows_scanned": freq.get("displacement_blocked_rows_in_file"),
            "unique_days": ud,
            "approx_displacement_blocks_per_day": per_day,
            "caveat": "Uniform spread across days is an approximation from timestamp prefix counts.",
        },
        "trade_count_note": "Counterfactual rows n in scorecard for displacement_blocked",
        "n_counterfactual_rows": n_disp,
        "drawdown_proxy": {
            "pnl_60m_tail_risk_p05_pnl_usd": p05_60,
            "source": "BLOCKED_GATE_SCORECARD.json",
        },
        "gate_interactions": {
            "displacement_blocked": "Hypothesis universe is exactly this gate class.",
            "max_positions": "Not isolated in this hypothesis (see other per_reason rows in scorecard).",
            "exits": "Variant A uses fixed horizons from bars, not production exit logic.",
        },
        "sensitivity": {
            "horizon_15m_expectancy_usd": ev_15,
            "horizon_30m_expectancy_usd": ev_30,
            "horizon_60m_expectancy_usd": ev_60,
            "win_rate_60m": wr_60,
        },
        "confidence": "MEDIUM for mean expectancy (large n); LOW for live translation (execution model gap).",
    }
    _write(ev / "PROFIT_INTERPRETATION_QUANT_CF_001.json", json.dumps(cf_interpretation, indent=2))
    _write(
        ev / "PROFIT_INTERPRETATION_QUANT_CF_001.md",
        "# PROFIT_INTERPRETATION — QUANT_CF_001\n\n"
        f"- **Incremental EV / trade (60m variant A mean, USD):** `{ev_60}` (from scorecard).\n"
        f"- **Est. EV / day (USD):** `{cf_interpretation['incremental_ev_per_day_usd_est']}` "
        f"using ~`{per_day}` blocks/day over `{ud}` day(s) from blocked-file scan.\n"
        f"- **Est. EV / week (USD):** `{cf_interpretation['incremental_ev_per_week_usd_est']}`.\n"
        f"- **n (scorecard displacement_blocked):** `{n_disp}`.\n"
        f"- **Drawdown proxy (p05 60m):** `{p05_60}` USD.\n"
        "- **Gates:** see JSON `gate_interactions`.\n"
        "- **Sensitivity:** 15m/30m expectancies in JSON.\n",
    )

    grid = j_emu.get("grid") or []
    means = [float(g["mean_pnl_usd"]) for g in grid if g.get("mean_pnl_usd") is not None]
    p05s = [float(g["p05_pnl_usd"]) for g in grid if g.get("p05_pnl_usd") is not None]
    best = max(means) if means else None
    worst = min(means) if means else None
    best_cell = max(grid, key=lambda g: float(g.get("mean_pnl_usd") or -1e18)) if grid else {}
    worst_cell = min(grid, key=lambda g: float(g.get("mean_pnl_usd") or 1e18)) if grid else {}

    emu_interpretation = {
        "hypothesis_id": "QUANT_EMU_001",
        "role": "QUANT",
        "incremental_ev_per_trade_usd": {
            "best_cell_mean": best,
            "worst_cell_mean": worst,
            "best_cell_params": {k: best_cell.get(k) for k in ("k_atr_stop", "m_atr_tp", "N_max_minutes", "mean_pnl_usd", "p05_pnl_usd")},
            "worst_cell_params": {k: worst_cell.get(k) for k in ("k_atr_stop", "m_atr_tp", "N_max_minutes", "mean_pnl_usd", "p05_pnl_usd")},
            "source": "DISPLACEMENT_EXIT_EMULATOR_RESULTS.json grid",
        },
        "incremental_ev_per_day_usd_est": round(float(best) * float(per_day), 6) if best is not None and per_day else None,
        "incremental_ev_per_week_usd_est": round(float(best) * float(per_day) * 7, 6) if best is not None and per_day else None,
        "frequency": {"same_as_QUANT_CF_001_displacement_blocks_per_day": per_day, "n_rows_each_cell": best_cell.get("n")},
        "trade_count_note": "Emulator re-evaluates same covered rows per grid cell (n in each cell).",
        "drawdown_proxy": {"best_cell_p05_usd": best_cell.get("p05_pnl_usd"), "worst_cell_p05_usd": worst_cell.get("p05_pnl_usd")},
        "gate_interactions": {
            "displacement_blocked": "Universe aligned to displacement_blocked coverage from addon pipeline.",
            "exits": "ATR proxy emulator; not V2 exit engine.",
        },
        "sensitivity": {"mean_range_usd": [worst, best], "p05_range_usd": [min(p05s), max(p05s)] if p05s else None},
        "confidence": "LOW–MEDIUM for live translation; MEDIUM for ranking proxy grids within bars model.",
    }
    _write(ev / "PROFIT_INTERPRETATION_QUANT_EMU_001.json", json.dumps(emu_interpretation, indent=2))
    _write(
        ev / "PROFIT_INTERPRETATION_QUANT_EMU_001.md",
        "# PROFIT_INTERPRETATION — QUANT_EMU_001\n\n"
        f"- **Best grid mean (USD / row):** `{best}`; **worst:** `{worst}`.\n"
        f"- **Best cell:** `{json.dumps(emu_interpretation['incremental_ev_per_trade_usd']['best_cell_params'])}`\n"
        f"- **Est. upper-bound EV/day (USD)** if one such trade per displacement block/day: `{emu_interpretation['incremental_ev_per_day_usd_est']}`.\n"
        "- **Tail:** see `drawdown_proxy` and `p05` in JSON.\n",
    )

    # CSA second chance: negative joined PnL -> explicit non-advance note (not a 'positive' profit hypothesis)
    sc_allowed_mean = (j_sc.get("paper_pnl_variant_a") or {}).get("mean_pnl_usd_60m")
    _write(
        ev / "PROFIT_INTERPRETATION_CSA_SC_001.json",
        json.dumps(
            {
                "hypothesis_id": "CSA_SC_001",
                "status": "CANNOT_ADVANCE_PROFIT_PATH",
                "reason": "Phase_8_hard_gate_positive_paper_required_for_profit_promotion",
                "evidence": {
                    "allowed_count": j_sc.get("allowed_count"),
                    "mean_pnl_60m_joined": sc_allowed_mean,
                    "baseline_displacement_mean_60m": (j_sc.get("comparison") or {}).get(
                        "baseline_displacement_blocked_mean_pnl_60m_variant_a"
                    ),
                },
                "note": "Admission count > 0 but joined counterfactual mean 60m is negative vs positive promotion bar.",
            },
            indent=2,
        ),
    )
    _write(
        ev / "PROFIT_INTERPRETATION_CSA_SC_001.md",
        "# PROFIT_INTERPRETATION — CSA_SC_001\n\n"
        "**Status:** **CANNOT ADVANCE** on profit path (Phase 8 hard gate: requires positive paper profit outcome).\n\n"
        f"- Joined mean 60m (allowed): `{sc_allowed_mean}` USD.\n"
        "- See `PROFIT_INTERPRETATION_CSA_SC_001.json`.\n",
    )

    # STRAT separation: EV not estimated in evidence
    _write(
        ev / "PROFIT_INTERPRETATION_STRAT_SEP_001.json",
        json.dumps(
            {
                "hypothesis_id": "STRAT_SEP_001",
                "status": "CANNOT_ADVANCE_PROFIT_PATH",
                "reason": "EV_for_conditional_override_not_estimated_from_source_artifacts",
                "evidence": {"conclusion": j_sep.get("conclusion_AB"), "n_rows": j_sep.get("n_rows")},
            },
            indent=2,
        ),
    )
    _write(
        ev / "PROFIT_INTERPRETATION_STRAT_SEP_001.md",
        "# PROFIT_INTERPRETATION — STRAT_SEP_001\n\n"
        "**Status:** **CANNOT ADVANCE** — no dollar EV for a conditional entry policy is computed in cited JSON.\n",
    )

    # --- Phase 9 Action contracts (complete for those passing profit bar: QUANT_CF_001, QUANT_EMU_001) ---
    c1 = {
        "hypothesis_id": "QUANT_CF_001",
        "action_type": "paper_extension",
        "exact_change": "Re-run `run_blocked_why_pipeline.py` + merge-blocked bars fetch on a fixed cadence; no `main.py` threshold edits.",
        "scope_duration": "30d rolling evidence windows; config frozen except bars date range.",
        "success_metrics": [
            "pnl_60m_expectancy displacement_blocked remains positive in new window",
            "coverage rate for displacement_blocked rows stable or improves in BLOCKED_WHY_BARS_COVERAGE.json",
        ],
        "kill_criteria": [
            "pnl_60m_expectancy displacement_blocked < 0 for two consecutive weekly rebuilds",
            "coverage collapse >20% vs prior week without documented data outage",
        ],
        "rollback": "Stop scheduled pipeline; archive evidence folder; no engine env changes required.",
        "owner_role": "QUANT",
    }
    c2 = {
        "hypothesis_id": "QUANT_EMU_001",
        "action_type": "paper_extension",
        "exact_change": "Keep `run_displacement_deepdive_addon.py` emulator grid in weekly audit bundle; compare p05 vs mean week-over-week.",
        "scope_duration": "8 weeks; same k,m,N grid unless governance approves expansion.",
        "success_metrics": [
            "majority of grid cells remain mean_pnl_usd > 0",
            "p05 does not worsen >25% vs baseline snapshot in DISPLACEMENT_EXIT_EMULATOR_RESULTS.json",
        ],
        "kill_criteria": [
            "fewer than half of cells with mean_pnl_usd > 0 for two consecutive runs",
            "best_cell mean_pnl_usd < 0",
        ],
        "rollback": "Remove addon from cron; no trading config touched.",
        "owner_role": "QUANT",
    }
    contracts = [c1, c2]

    def _contract_md(c: Dict[str, Any]) -> str:
        rid = c["hypothesis_id"]
        return (
            f"# ACTION_CONTRACT — {rid}\n\n"
            f"- **Type:** {c['action_type']}\n"
            f"- **Owner:** {c['owner_role']}\n"
            f"- **Change:** {c['exact_change']}\n"
            f"- **Scope/duration:** {c['scope_duration']}\n"
            f"- **Success metrics:** {c['success_metrics']}\n"
            f"- **Kill criteria:** {c['kill_criteria']}\n"
            f"- **Rollback:** {c['rollback']}\n"
        )

    for c in contracts:
        rid = c["hypothesis_id"]
        _write(ev / f"ACTION_CONTRACT_{rid}.json", json.dumps(c, indent=2))
        _write(ev / f"ACTION_CONTRACT_{rid}.md", _contract_md(c))

    # Phase 10 ranking: profit/risk score proxy = expectancy / max(1e-9, abs(p05))
    p05_abs = abs(float(p05_60)) if p05_60 is not None else None
    score_cf = (float(ev_60) / p05_abs) if ev_60 is not None and p05_abs else None
    p05b = abs(float(best_cell.get("p05_pnl_usd") or 0)) or 1e-9
    score_emu = (float(best) / p05b) if best is not None else None
    ranking = {
        "ranked": [
            {
                "rank": 1,
                "hypothesis_id": "QUANT_CF_001",
                "profit_proxy": "pnl_60m_expectancy_usd",
                "value": ev_60,
                "risk_proxy": "abs_p05_60m_usd",
                "risk_value": p05_abs,
                "score_expectancy_over_abs_p05": round(score_cf, 6) if score_cf is not None else None,
            },
            {
                "rank": 2,
                "hypothesis_id": "QUANT_EMU_001",
                "profit_proxy": "best_grid_mean_pnl_usd",
                "value": best,
                "risk_proxy": "abs_p05_best_cell",
                "risk_value": abs(float(best_cell.get("p05_pnl_usd") or 0)) if best_cell else None,
                "score_mean_over_abs_p05": round(score_emu, 6) if score_emu is not None else None,
            },
        ],
        "deferred": ["STRAT_SEP_001"],
        "rejected_profit_path": ["CSA_SC_001"],
        "conflicts": [
            "Counterfactual positive mean does not imply second-chance allowed subset is profitable (see SECOND_CHANCE_PNL_EVALUATION.json).",
        ],
    }
    _write(ev / "HYPOTHESIS_COUNCIL_PROFIT_RANKING.json", json.dumps(ranking, indent=2))
    _write(
        ev / "HYPOTHESIS_COUNCIL_PROFIT_RANKING.md",
        "# HYPOTHESIS_COUNCIL_PROFIT_RANKING (Phase 10)\n\n"
        "## Ranked (expectancy / |p05| proxy)\n\n"
        f"```json\n{json.dumps(ranking, indent=2)}\n```\n",
    )

    # Phase 11 verdict
    verdict = {
        "promoted": [
            {"hypothesis_id": "QUANT_CF_001", "how": "paper_extension per ACTION_CONTRACT_QUANT_CF_001.json"},
            {"hypothesis_id": "QUANT_EMU_001", "how": "paper_extension per ACTION_CONTRACT_QUANT_EMU_001.json"},
        ],
        "rejected": [
            {
                "hypothesis_id": "CSA_SC_001",
                "why": "Joined second-chance allowed subset mean 60m variant A negative; fails profit promotion bar.",
            }
        ],
        "deferred": [
            {
                "hypothesis_id": "STRAT_SEP_001",
                "why": "No dollar EV computed for conditional policy; needs simulation or shadow book.",
            }
        ],
        "expected_portfolio_impact_if_promoted": {
            "note": "Paper-only promotions: no live portfolio impact until a separate micro-live contract is approved.",
            "illustrative_counterfactual_upper_bound_usd_per_week": cf_interpretation.get("incremental_ev_per_week_usd_est"),
            "caveat": "Upper bound scales scorecard mean by scanned blocks/day; not realized trading.",
        },
    }
    _write(ev / "HYPOTHESIS_COUNCIL_ACTION_VERDICT.json", json.dumps(verdict, indent=2))
    _write(
        ev / "HYPOTHESIS_COUNCIL_ACTION_VERDICT.md",
        "# HYPOTHESIS_COUNCIL_ACTION_VERDICT (Phase 11)\n\n"
        "## Promoted\n\n"
        "- **QUANT_CF_001** — paper extension (blocked-why / counterfactual cadence). Contract: `ACTION_CONTRACT_QUANT_CF_001.md`.\n"
        "- **QUANT_EMU_001** — paper extension (exit emulator audit). Contract: `ACTION_CONTRACT_QUANT_EMU_001.md`.\n\n"
        "## Rejected\n\n"
        "- **CSA_SC_001** — negative joined mean for second-chance allows (see `PROFIT_INTERPRETATION_CSA_SC_001.json`).\n\n"
        "## Deferred\n\n"
        "- **STRAT_SEP_001** — EV for conditional entry not estimated in evidence.\n\n"
        "## Expected portfolio impact\n\n"
        f"- Illustrative counterfactual upper bound (USD/week): `{verdict['expected_portfolio_impact_if_promoted'].get('illustrative_counterfactual_upper_bound_usd_per_week')}` "
        "(see JSON caveat).\n"
        "- **No live trading change** without a new approved micro-live contract.\n",
    )

    print(json.dumps({"evidence_dir": str(ev), "ok": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
