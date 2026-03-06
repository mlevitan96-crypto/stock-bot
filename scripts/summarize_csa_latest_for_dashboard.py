#!/usr/bin/env python3
"""
Summarize latest CSA verdict and trade-count state for dashboard.
Reads CSA_VERDICT_LATEST.json and reports/state/TRADE_CSA_STATE.json;
writes a short Markdown summary to reports/board/CSA_DASHBOARD_LATEST.md.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
AUDIT_DIR = REPO / "reports" / "audit"
STATE_DIR = REPO / "reports" / "state"
STATE_FILE = STATE_DIR / "TRADE_CSA_STATE.json"
BOARD_DIR = REPO / "reports" / "board"
OUT_PATH = BOARD_DIR / "CSA_DASHBOARD_LATEST.md"


def main() -> int:
    verdict_path = AUDIT_DIR / "CSA_VERDICT_LATEST.json"
    lines = [
        "# CSA Dashboard — Latest",
        "",
        f"**Updated:** (run `scripts/summarize_csa_latest_for_dashboard.py` to refresh)",
        "",
    ]
    # Trade count from state
    last_csa_trade_count = None
    total_trade_events = None
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            last_csa_trade_count = state.get("last_csa_trade_count")
            total_trade_events = state.get("total_trade_events")
            lines.append(f"- **Total trade events:** {total_trade_events}")
            lines.append(f"- **Last CSA at trade count:** {last_csa_trade_count}")
            lines.append("")
        except Exception:
            pass
    if verdict_path.exists():
        try:
            v = json.loads(verdict_path.read_text(encoding="utf-8"))
            mission_id = v.get("mission_id", "N/A")
            overall = v.get("verdict", "N/A")
            confidence = v.get("confidence", "N/A")
            rec = v.get("recommendation", "N/A")
            lines.extend([
                "## Latest verdict",
                "",
                f"- **Mission ID:** {mission_id}",
                f"- **Verdict:** {overall} ({confidence})",
                f"- **Recommendation:** {rec}",
                "",
                "### Top findings",
                "",
            ])
            findings = v.get("missing_data", [])[:3]
            if not findings and v.get("assumptions"):
                findings = v.get("assumptions", [])[:3]
            for i, f in enumerate(findings, 1):
                lines.append(f"{i}. {f}" if isinstance(f, str) else f"{i}. {json.dumps(f)}")
            lines.append("")
        except Exception:
            lines.append("(Could not read verdict JSON.)\n")
    else:
        lines.append("No CSA_VERDICT_LATEST.json found. Run CSA (e.g. every-100-trades) to generate.\n")
    BOARD_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
