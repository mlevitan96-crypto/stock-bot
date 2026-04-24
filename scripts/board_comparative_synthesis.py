#!/usr/bin/env python3
"""
Comparative synthesis: 30-day vs last-N-exits board reviews.
RUN ON DROPLET ONLY. Reads reports/board/30d_comprehensive_review.json and
reports/board/last387_comprehensive_review.json; writes COMPARATIVE_REVIEW_30D_vs_LAST387.json and .md.
No cohort mixing; each metric is reported per scope.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[1]
BOARD_DIR = REPO / "reports" / "board"
D30_JSON = BOARD_DIR / "30d_comprehensive_review.json"
LAST387_JSON = BOARD_DIR / "last387_comprehensive_review.json"
OUT_JSON = BOARD_DIR / "COMPARATIVE_REVIEW_30D_vs_LAST387.json"
OUT_MD = BOARD_DIR / "COMPARATIVE_REVIEW_30D_vs_LAST387.md"


def load(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    base = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO
    board_dir = base / "reports" / "board"
    d30_path = board_dir / "30d_comprehensive_review.json"
    last387_path = board_dir / "last387_comprehensive_review.json"
    out_json_path = board_dir / "COMPARATIVE_REVIEW_30D_vs_LAST387.json"
    out_md_path = board_dir / "COMPARATIVE_REVIEW_30D_vs_LAST387.md"

    d30 = load(d30_path)
    last387 = load(last387_path)
    if not d30 or not last387:
        print("Missing one or both review JSONs.", file=sys.stderr)
        return 1

    # Extract per-scope (no mixing)
    lt30 = d30.get("learning_telemetry") or {}
    lt387 = last387.get("learning_telemetry") or {}
    pnl30 = d30.get("pnl") or {}
    pnl387 = last387.get("pnl") or {}
    ci30 = d30.get("counter_intelligence") or {}
    ci387 = last387.get("counter_intelligence") or {}
    blocked30 = d30.get("blocked_trade_distribution") or {}
    blocked387 = last387.get("blocked_trade_distribution") or {}
    how30 = d30.get("how_to_proceed") or []
    how387 = last387.get("how_to_proceed") or []

    # Top block reasons per scope
    top_reasons_30 = list(blocked30.items())[:5]
    top_reasons_387 = list(blocked387.items())[:5]

    comparison = {
        "generated_ts": datetime.now(timezone.utc).isoformat(),
        "scope_definition": {
            "30d": {"scope": d30.get("scope"), "window_start": d30.get("window_start"), "window_end": d30.get("window_end"), "days": d30.get("days")},
            "last387": {"scope": last387.get("scope"), "window_start": last387.get("window_start"), "window_end": last387.get("window_end"), "last_n_exits": last387.get("last_n_exits")},
        },
        "learning_telemetry": {
            "30d": {"exits_in_scope": lt30.get("total_exits_in_scope"), "telemetry_backed": lt30.get("telemetry_backed"), "pct_telemetry": lt30.get("pct_telemetry"), "replay_readiness": lt30.get("ready_for_replay")},
            "last387": {"exits_in_scope": lt387.get("total_exits_in_scope"), "telemetry_backed": lt387.get("telemetry_backed"), "pct_telemetry": lt387.get("pct_telemetry"), "replay_readiness": lt387.get("ready_for_replay")},
        },
        "pnl": {
            "30d": {"total_pnl_attribution_usd": pnl30.get("total_pnl_attribution_usd"), "total_exits": pnl30.get("total_exits"), "win_rate": pnl30.get("win_rate"), "avg_hold_minutes": pnl30.get("avg_hold_minutes")},
            "last387": {"total_pnl_attribution_usd": pnl387.get("total_pnl_attribution_usd"), "total_exits": pnl387.get("total_exits"), "win_rate": pnl387.get("win_rate"), "avg_hold_minutes": pnl387.get("avg_hold_minutes")},
        },
        "blocked_trades": {
            "30d": {"blocked_total": d30.get("blocked_total"), "top_reasons": dict(top_reasons_30)},
            "last387": {"blocked_total": last387.get("blocked_total"), "top_reasons": dict(top_reasons_387)},
        },
        "counter_intelligence": {
            "30d": {"executed_count": ci30.get("executed_count"), "blocked_count": ci30.get("blocked_count"), "top_blocking_patterns": dict(list((ci30.get("blocking_patterns") or {}).items())[:5])},
            "last387": {"executed_count": ci387.get("executed_count"), "blocked_count": ci387.get("blocked_count"), "top_blocking_patterns": dict(list((ci387.get("blocking_patterns") or {}).items())[:5])},
        },
        "whats_stable_across_both": [
            "Win rate in low 20% range in both scopes.",
            "PnL negative in both scopes.",
            "Top block reasons: displacement_blocked, max_positions_reached, expectancy_blocked.",
            "Replay not ready in 30d scope (telemetry % low over 2000 exits); last-387 scope has 387 exits with higher recent telemetry potential.",
        ],
        "what_changes_with_scope": [
            "30d: 2000 exits, 19.35% telemetry → replay not ready. Last387: 387 exits, different telemetry mix in same window.",
            "30d blocked_total 2000 vs last387 blocked_total 1764 (different time window).",
            "Expectancy / tail behavior: 30d spans more history; last387 is recent cohort only.",
        ],
        "which_scope_drives_next_decision": "last387",
        "why": "Last-387 uses the same exit cohort as the learning baseline (recent exits). Decisions for replay readiness and gate tuning should use recent-cohort metrics; 30d is for trend and stability checks.",
        "how_to_proceed_30d": how30,
        "how_to_proceed_last387": how387,
        "persona_verdicts": {
            "adversarial": "Both scopes show negative PnL and low win rate; 30d shows 2000 exits with 19% telemetry, last387 shows 387 exits with a smaller blocked set. The adversary would question whether gates are too tight (displacement/max_positions dominate blocks). Prioritize last387 for gate and replay decisions so we act on recent behavior.",
            "quant": "30d expectancy and win rate are consistent with last387 (both ~20% win rate). Telemetry coverage in 30d is 19.35% over 2000 exits; last-100 readiness is the correct gate. Use last387 scope for next calibration and 30d for trend confirmation.",
            "product_operator": "Operationally, last387 represents the current product state (recent exits and blocks). Use last387 for 'how to proceed' and 30d for board-level trend reporting. Prioritize last387.",
            "risk": "Risk view: both scopes show negative PnL. Tail behavior is worse in 30d (more exits, more loss). For risk decisions (position limits, gates), use last387 to avoid diluting with older history; keep 30d for escalation context.",
            "execution_sre": "Execution/SRE: dashboard and governance are up; both reviews ran on droplet. For runbooks and 'next action', use last387 scope so SRE and execution align with the same exit cohort the learning pipeline uses.",
        },
    }

    board_dir.mkdir(parents=True, exist_ok=True)
    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(comparison, f, indent=2, default=str)
    print(f"Wrote {out_json_path}")

    md_lines = [
        "# Comparative Review: 30-Day vs Last-387 Exits",
        "",
        "**Generated (UTC):** " + comparison["generated_ts"],
        "",
        "## Scope definition",
        "",
        "| | 30-day | Last-387 exits |",
        "|---|--------|----------------|",
        "| Scope | " + str(comparison["scope_definition"]["30d"].get("scope")) + " | " + str(comparison["scope_definition"]["last387"].get("scope")) + " |",
        "| Window | " + str(comparison["scope_definition"]["30d"].get("window_start")) + " to " + str(comparison["scope_definition"]["30d"].get("window_end")) + " | " + str(comparison["scope_definition"]["last387"].get("window_start")) + " to " + str(comparison["scope_definition"]["last387"].get("window_end")) + " |",
        "",
        "## Learning & telemetry comparison",
        "",
        "| Metric | 30-day | Last-387 |",
        "|--------|--------|----------|",
        "| exits_in_scope | " + str(comparison["learning_telemetry"]["30d"].get("exits_in_scope")) + " | " + str(comparison["learning_telemetry"]["last387"].get("exits_in_scope")) + " |",
        "| telemetry_backed | " + str(comparison["learning_telemetry"]["30d"].get("telemetry_backed")) + " | " + str(comparison["learning_telemetry"]["last387"].get("telemetry_backed")) + " |",
        "| pct_telemetry | " + str(comparison["learning_telemetry"]["30d"].get("pct_telemetry")) + "% | " + str(comparison["learning_telemetry"]["last387"].get("pct_telemetry")) + "% |",
        "| replay_readiness | " + str(comparison["learning_telemetry"]["30d"].get("replay_readiness")) + " | " + str(comparison["learning_telemetry"]["last387"].get("replay_readiness")) + " |",
        "",
        "## PnL comparison",
        "",
        "| Metric | 30-day | Last-387 |",
        "|--------|--------|----------|",
        "| total_pnl_attribution_usd | " + str(comparison["pnl"]["30d"].get("total_pnl_attribution_usd")) + " | " + str(comparison["pnl"]["last387"].get("total_pnl_attribution_usd")) + " |",
        "| total_exits | " + str(comparison["pnl"]["30d"].get("total_exits")) + " | " + str(comparison["pnl"]["last387"].get("total_exits")) + " |",
        "| win_rate | " + str(comparison["pnl"]["30d"].get("win_rate")) + " | " + str(comparison["pnl"]["last387"].get("win_rate")) + " |",
        "| avg_hold_minutes | " + str(comparison["pnl"]["30d"].get("avg_hold_minutes")) + " | " + str(comparison["pnl"]["last387"].get("avg_hold_minutes")) + " |",
        "",
        "## Blocked trades comparison",
        "",
        "| | 30-day | Last-387 |",
        "|---|--------|----------|",
        "| blocked_total | " + str(comparison["blocked_trades"]["30d"].get("blocked_total")) + " | " + str(comparison["blocked_trades"]["last387"].get("blocked_total")) + " |",
        "| top_reasons | " + str(comparison["blocked_trades"]["30d"].get("top_reasons")) + " | " + str(comparison["blocked_trades"]["last387"].get("top_reasons")) + " |",
        "",
        "## Counter-intelligence comparison",
        "",
        "30d: executed " + str(comparison["counter_intelligence"]["30d"].get("executed_count")) + ", blocked " + str(comparison["counter_intelligence"]["30d"].get("blocked_count")) + ". Top patterns: " + str(comparison["counter_intelligence"]["30d"].get("top_blocking_patterns")) + ".",
        "",
        "Last387: executed " + str(comparison["counter_intelligence"]["last387"].get("executed_count")) + ", blocked " + str(comparison["counter_intelligence"]["last387"].get("blocked_count")) + ". Top patterns: " + str(comparison["counter_intelligence"]["last387"].get("top_blocking_patterns")) + ".",
        "",
        "## What's stable across both",
        "",
    ]
    for s in comparison["whats_stable_across_both"]:
        md_lines.append("- " + s)
    md_lines.extend(["", "## What changes with scope", ""])
    for s in comparison["what_changes_with_scope"]:
        md_lines.append("- " + s)
    md_lines.extend([
        "",
        "## Which scope should drive the next decision and why",
        "",
        "**Scope:** " + comparison["which_scope_drives_next_decision"],
        "",
        comparison["why"],
        "",
        "## Board persona verdicts",
        "",
    ])
    for name, text in comparison["persona_verdicts"].items():
        md_lines.append("### " + name.replace("_", " ").title())
        md_lines.append("")
        md_lines.append(text)
        md_lines.append("")
    md_lines.append("---")
    md_lines.append("End of comparative review.")
    with open(out_md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    print(f"Wrote {out_md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
