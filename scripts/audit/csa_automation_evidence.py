#!/usr/bin/env python3
"""
CSA Automation Evidence: load Cursor Automations outputs for use in CSA.
Ingests GOVERNANCE_AUTOMATION_STATUS.json and optional weekly summaries.
Does not depend on automations to run; returns empty evidence if files are missing.
"""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone


def load_governance_status(base: Path) -> dict | None:
    """Load reports/audit/GOVERNANCE_AUTOMATION_STATUS.json. Returns None if missing or invalid."""
    path = base / "reports" / "audit" / "GOVERNANCE_AUTOMATION_STATUS.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def load_recent_weekly_summaries(base: Path, max_files: int = 3) -> list[dict]:
    """
    Load recent reports/board/WEEKLY_GOVERNANCE_SUMMARY_*.md.
    Returns list of { "path": str, "date": str, "preview": str } (first 500 chars).
    """
    board_dir = base / "reports" / "board"
    if not board_dir.exists():
        return []
    out = []
    prefix = "WEEKLY_GOVERNANCE_SUMMARY_"
    suffix = ".md"
    for f in sorted(board_dir.iterdir(), reverse=True):
        if not f.name.startswith(prefix) or not f.name.endswith(suffix):
            continue
        try:
            date_str = f.name[len(prefix) : -len(suffix)]
            text = f.read_text(encoding="utf-8", errors="replace")
            preview = text.strip()[:500] + ("..." if len(text) > 500 else "")
            out.append({"path": str(f.relative_to(base)), "date": date_str, "preview": preview})
        except Exception:
            continue
        if len(out) >= max_files:
            break
    return out


def load_automation_evidence(base: Path) -> dict:
    """
    Load all automation evidence for CSA. Safe to call when automations are unavailable.
    Returns dict with:
      - governance_integrity: status dict or None
      - governance_status: "ok" | "anomalies" | "unavailable"
      - governance_timestamp: ISO str or None
      - anomalies: list of strings (from status details)
      - open_automation_issues_note: str (placeholder; GitHub issues are not fetched here)
      - recent_weekly_summaries: list of { path, date, preview }
      - unavailable_reason: str if governance status file missing
    """
    evidence = {
        "governance_integrity": None,
        "governance_status": "unavailable",
        "governance_timestamp": None,
        "anomalies": [],
        "open_automation_issues_note": "Open issues from Security Review or Governance Integrity are not loaded in this script; check GitHub for labels automation-anomaly, security-review.",
        "recent_weekly_summaries": [],
        "unavailable_reason": None,
    }

    status = load_governance_status(base)
    if status is None:
        evidence["unavailable_reason"] = "GOVERNANCE_AUTOMATION_STATUS.json missing or unreadable"
        evidence["recent_weekly_summaries"] = load_recent_weekly_summaries(base)
        return evidence

    evidence["governance_integrity"] = status
    evidence["governance_timestamp"] = status.get("run_ts_utc") or status.get("timestamp")
    anomalies_detected = status.get("anomalies_detected", False)
    details = status.get("details") or status.get("anomalies") or []
    if isinstance(details, list):
        evidence["anomalies"] = [str(d) for d in details]
    else:
        evidence["anomalies"] = []
    evidence["governance_status"] = "anomalies" if (anomalies_detected or evidence["anomalies"]) else "ok"
    evidence["recent_weekly_summaries"] = load_recent_weekly_summaries(base)
    evidence["unavailable_reason"] = None
    return evidence


def format_automation_evidence_section(evidence: dict) -> list[str]:
    """Format Automation Evidence as markdown lines for CSA findings."""
    lines = [
        "## Automation Evidence",
        "",
        "Cursor Automations governance layer (pre-merge/pre-deploy) outputs ingested as first-class evidence.",
        "",
    ]
    if evidence.get("unavailable_reason"):
        lines.append(f"- **Governance integrity:** Unavailable — {evidence['unavailable_reason']}")
        lines.append("- **Action:** Run `python scripts/automations/run_governance_integrity_once.py` or ensure Cursor Automation (Governance Integrity) has run.")
        lines.append("")
        if evidence.get("recent_weekly_summaries"):
            lines.append("**Recent weekly summaries:**")
            for s in evidence["recent_weekly_summaries"]:
                lines.append(f"- {s['path']} ({s['date']})")
            lines.append("")
        return lines

    lines.append(f"- **Governance integrity status:** {evidence.get('governance_status', 'unknown')}")
    lines.append(f"- **Last run (UTC):** {evidence.get('governance_timestamp') or 'unknown'}")
    if evidence.get("anomalies"):
        lines.append("- **Anomalies:**")
        for a in evidence["anomalies"]:
            lines.append(f"  - {a}")
        lines.append("")
    else:
        lines.append("- **Anomalies:** (none)")
        lines.append("")
    lines.append(f"- **Open automation-related issues:** {evidence.get('open_automation_issues_note', 'See GitHub.')}")
    lines.append("")
    if evidence.get("recent_weekly_summaries"):
        lines.append("**Recent weekly governance summaries:**")
        for s in evidence["recent_weekly_summaries"]:
            lines.append(f"- {s['path']} ({s['date']})")
        lines.append("")
    return lines


if __name__ == "__main__":
    import sys
    base = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]
    ev = load_automation_evidence(base)
    print(json.dumps({k: v for k, v in ev.items() if k != "recent_weekly_summaries" or ev["recent_weekly_summaries"]}, indent=2, default=str))
    for line in format_automation_evidence_section(ev):
        print(line, end="\n")
