#!/usr/bin/env python3
"""
Synthesis: rank scenario reviews (last-387 baseline), add risk notes, Promote/Test/Discard, persona verdicts.
RUN ON DROPLET. Reads reports/board/scenarios/*_review.json; writes SCENARIO_COMPARISON_LAST387.json and .md.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

SCENARIO_IDS = ["A1", "A2", "A3", "B1", "B2", "B3", "C1", "C2"]

def main() -> int:
    base = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    scenarios_dir = base / "reports" / "board" / "scenarios"
    out_json = base / "reports" / "board" / "SCENARIO_COMPARISON_LAST387.json"
    out_md = base / "reports" / "board" / "SCENARIO_COMPARISON_LAST387.md"
    scenarios_dir.mkdir(parents=True, exist_ok=True)
    reports = {}
    for sid in SCENARIO_IDS:
        p = scenarios_dir / f"{sid}_review.json"
        if p.exists():
            try:
                reports[sid] = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                reports[sid] = {"scenario_id": sid, "error": "failed to load"}
        else:
            reports[sid] = {"scenario_id": sid, "error": "missing"}

    # Rank by expected improvement (qualitative; use proxy metrics where present)
    def rank_key(sid):
        r = reports.get(sid) or {}
        if r.get("error"):
            return (0, 0)
        proxy = r.get("counterfactual_pnl_proxy_usd")
        if proxy is not None and proxy > 0:
            return (2, proxy)
        if "moderate" in str(r.get("expected_improvement", "")):
            return (1, 0)
        return (0, proxy or 0)
    ranked = sorted(SCENARIO_IDS, key=lambda s: (-rank_key(s)[0], rank_key(s)[1]))

    recommendations = {}
    for sid in SCENARIO_IDS:
        r = reports.get(sid) or {}
        if r.get("error"):
            recommendations[sid] = "Discard (no data)"
        elif sid in ("A1", "A2"):
            recommendations[sid] = "Test (gate relaxation; run in paper first)"
        elif sid == "A3":
            recommendations[sid] = "Test (score floor; backtest recommended)"
        elif sid in ("B1", "B2", "B3"):
            recommendations[sid] = "Test (exit behavior; replay validation)"
        elif sid == "C1":
            recommendations[sid] = "Promote (re-rank informs which gate to relax first)"
        else:
            recommendations[sid] = "Test (C2 needs full counter-intel run)"

    payload = {
        "generated_ts": datetime.now(timezone.utc).isoformat(),
        "baseline": "last 387 exits",
        "scenarios": reports,
        "ranked_by_expected_improvement": ranked,
        "recommendations": recommendations,
        "risk_notes": {
            "A1": "Displacement relaxation increases exposure; monitor drawdown.",
            "A2": "Max positions increase concentration risk.",
            "A3": "Lower score floor may admit worse entries; validate with backtest.",
            "B1": "Min hold extension may increase drawdown in fast reversals.",
            "B2": "Removing early signal_decay may hold losers longer.",
            "B3": "TP favor requires rule change; test on replay.",
            "C1": "Opportunity cost is proxy; use for prioritization only.",
            "C2": "Full C2 requires estimate_blocked_outcome per block.",
        },
        "persona_verdicts": {
            "adversarial": "Test A3 first (lower score floor): if the blocked score band is profitable, we are over-blocking; if not, we keep the floor. No live change until backtest.",
            "quant": "Test C1 first: re-ranking by opportunity cost gives a clear order for which gate to relax; then validate with A1/A2/A3 tests.",
            "product_operator": "Test B2 first (remove early signal_decay): quickest exit-policy change to validate on replay; if early decay exits are net negative, removing them improves expectancy.",
            "risk": "Test A2 last; prioritize B1 or B3 (exit behavior) over gate relaxation to avoid concentration. Promote C1 for decision order.",
            "execution_sre": "Test B1 first (extend min hold): single parameter, easy rollback; then C1 for prioritization. No live config change until tests pass.",
        },
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)
    print(f"Wrote {out_json}")

    md = [
        "# Scenario Comparison (Last-387 Baseline)",
        "",
        f"**Generated (UTC):** {payload['generated_ts']}",
        "",
        "## Ranked by expected improvement",
        "",
    ]
    for i, sid in enumerate(ranked, 1):
        r = reports.get(sid) or {}
        name = r.get("name", sid)
        rec = recommendations.get(sid, "")
        md.append(f"{i}. **{sid}** — {name} → **{rec}**")
    md.extend(["", "## Recommendations (Promote / Test / Discard)", ""])
    for sid in SCENARIO_IDS:
        md.append(f"- **{sid}:** {recommendations.get(sid, '')}")
    md.extend(["", "## Risk notes", ""])
    for sid, note in payload["risk_notes"].items():
        md.append(f"- **{sid}:** {note}")
    md.extend(["", "## Board persona verdicts (which scenario to test first)", ""])
    for persona, text in payload["persona_verdicts"].items():
        md.append(f"### {persona.replace('_', ' ').title()}")
        md.append("")
        md.append(text)
        md.append("")
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print(f"Wrote {out_md}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
