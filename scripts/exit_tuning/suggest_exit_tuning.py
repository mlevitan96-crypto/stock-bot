#!/usr/bin/env python3
"""
Suggest exit tuning from effectiveness v2 outputs.
Produces recommendations only; no automatic application. Board review required.

Outputs:
  reports/exit_review/exit_tuning_recommendations.md
  reports/exit_review/exit_tuning_patch.json (config-only patch)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "reports" / "exit_review"
EFFECTIVENESS_PATH = OUT_DIR / "exit_effectiveness_v2.json"


def main() -> int:
    if not EFFECTIVENESS_PATH.exists():
        rec = {
            "recommendations": ["Run exit effectiveness v2 first: python scripts/analysis/run_exit_effectiveness_v2.py"],
            "patch": {},
        }
    else:
        data = json.loads(EFFECTIVENESS_PATH.read_text(encoding="utf-8"))
        by_reason = data.get("by_exit_reason_code") or {}
        overall = data.get("overall") or {}
        recommendations = []
        patch = {"EXIT_PRESSURE_NORMAL": None, "EXIT_PRESSURE_URGENT": None, "component_weights": {}}

        # High giveback -> consider tightening profit protection or threshold
        avg_gb = overall.get("avg_profit_giveback")
        if avg_gb is not None and avg_gb > 0.25:
            recommendations.append(
                f"avg_profit_giveback={avg_gb:.2%} is high; consider increasing profit_protection weight or lowering EXIT_PRESSURE_NORMAL to exit earlier when giveback is building."
            )
        # Low saved_loss rate -> review stop/urgency
        for reason, v in by_reason.items():
            freq = v.get("frequency", 0)
            if freq < 5:
                continue
            slr = v.get("saved_loss_rate", 0) or 0
            lmr = v.get("left_money_rate", 0) or 0
            avg_pnl = v.get("avg_pnl") or v.get("avg_realized_pnl")
            if avg_pnl is not None and avg_pnl < 0 and slr < 20:
                recommendations.append(
                    f"exit_reason_code={reason}: saved_loss_rate={slr}%; consider earlier exit for this reason (e.g. lower threshold or higher weight)."
                )
            if lmr > 40:
                recommendations.append(
                    f"exit_reason_code={reason}: left_money_rate={lmr}%; consider holding longer or relaxing threshold for this bucket."
                )

        if not recommendations:
            recommendations.append("No strong tuning signals from current effectiveness v2; retain current thresholds and weights.")

        rec = {"recommendations": recommendations, "patch": patch}

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "exit_tuning_recommendations.md").write_text(
        "# Exit tuning recommendations\n\n" + "\n".join(f"- {r}" for r in rec["recommendations"]) + "\n\n*Board review required before applying any patch.*\n",
        encoding="utf-8",
    )
    (OUT_DIR / "exit_tuning_patch.json").write_text(json.dumps(rec["patch"], indent=2), encoding="utf-8")
    print("Wrote exit_tuning_recommendations.md and exit_tuning_patch.json to reports/exit_review/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
