#!/usr/bin/env python3
"""
Run CSA weekly review mission. Inputs: weekly ledger summary, shadow comparison, board review,
SRE status, governance. Outputs: CSA_VERDICT_CSA_WEEKLY_REVIEW_<date>.json,
CSA_FINDINGS_CSA_WEEKLY_REVIEW_<date>.md, reports/board/CSA_WEEKLY_REVIEW_<date>_BOARD_PACKET.md.

Usage:
  python scripts/audit/run_csa_weekly_review.py [--date YYYY-MM-DD] [--base-dir DIR]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))


def _load_json(p: Path) -> dict | None:
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Run CSA weekly review mission")
    ap.add_argument("--date", default=None, help="Date YYYY-MM-DD (default: today)")
    ap.add_argument("--base-dir", default=None, help="Repo root (default: REPO)")
    args = ap.parse_args()
    base = Path(args.base_dir).resolve() if args.base_dir else REPO
    if args.date:
        try:
            date_str = datetime.strptime(args.date, "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            print("Invalid --date", file=sys.stderr)
            return 1
    else:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    mission_id = f"CSA_WEEKLY_REVIEW_{date_str}"
    audit_dir = base / "reports" / "audit"
    board_dir = base / "reports" / "board"
    audit_dir.mkdir(parents=True, exist_ok=True)
    board_dir.mkdir(parents=True, exist_ok=True)

    ledger_summary_path = audit_dir / f"WEEKLY_TRADE_DECISION_LEDGER_SUMMARY_{date_str}.json"
    board_review_path = base / "reports" / "board" / "last387_comprehensive_review.json"
    shadow_path = base / "reports" / "board" / "SHADOW_COMPARISON_LAST387.json"
    stage = base / "reports" / "audit" / "weekly_evidence_stage"
    if not board_review_path.exists() and (stage / "reports" / "board" / "last387_comprehensive_review.json").exists():
        board_review_path = stage / "reports" / "board" / "last387_comprehensive_review.json"
    if not shadow_path.exists() and (stage / "reports" / "board" / "SHADOW_COMPARISON_LAST387.json").exists():
        shadow_path = stage / "reports" / "board" / "SHADOW_COMPARISON_LAST387.json"

    context = {
        "mission_type": "weekly_review",
        "date": date_str,
        "weekly_ledger_summary": _load_json(ledger_summary_path),
        "promotion_changes_this_week_note": "B2 live paper enable evidence if any; see reports/audit/B2_*.",
    }
    context_path = audit_dir / f"CSA_WEEKLY_CONTEXT_{date_str}.json"
    context_path.write_text(json.dumps(context, indent=2), encoding="utf-8")

    cmd = [
        sys.executable,
        str(base / "scripts" / "audit" / "run_chief_strategy_auditor.py"),
        "--mission-id", mission_id,
        "--context-json", str(context_path),
        "--base-dir", str(base),
    ]
    if board_review_path.exists():
        cmd.extend(["--board-review-json", str(board_review_path)])
    if shadow_path.exists():
        cmd.extend(["--shadow-comparison-json", str(shadow_path)])
    rc = subprocess.run(cmd, cwd=base, timeout=120)
    if rc.returncode != 0:
        print("CSA run failed:", rc.returncode, file=sys.stderr)
        return rc.returncode

    verdict_path = audit_dir / f"CSA_VERDICT_{mission_id}.json"
    findings_path = audit_dir / f"CSA_FINDINGS_{mission_id}.md"
    verdict = _load_json(verdict_path) or {}
    findings_text = findings_path.read_text(encoding="utf-8") if findings_path.exists() else ""

    # Board packet: synthesis for board (what happened, promotable, leaks, etc.)
    ledger_summary = context.get("weekly_ledger_summary") or {}
    packet_lines = [
        f"# CSA Weekly Review — Board Packet ({date_str})",
        "",
        f"**Mission:** {mission_id}",
        f"**Verdict:** {verdict.get('verdict', '—')} ({verdict.get('confidence', '—')} confidence)",
        "",
        "## 1. Week in numbers (from trade decision ledger)",
        f"- Executed: {ledger_summary.get('executed_count', '—')}",
        f"- Blocked: {ledger_summary.get('blocked_count', '—')}",
        f"- Counter-intel blocked: {ledger_summary.get('counter_intel_blocked_count', '—')}",
        f"- Validation failed: {ledger_summary.get('validation_failed_count', '—')}",
        f"- Validation failure rate: {ledger_summary.get('validation_failure_rate_pct', '—')}%",
        "",
        "## 2. CSA verdict summary",
        f"- **Recommendation:** {verdict.get('recommendation', '—')}",
        "- **Missing data:** " + ", ".join(verdict.get("missing_data", [])[:5]) or "(none)",
        "- **Required next experiments:** " + ", ".join(verdict.get("required_next_experiments", [])[:5]) or "(none)",
        "",
        "## 3. Entries / Exits / Sizing (CSA coverage)",
        "CSA explicitly covers: signal quality, gating, universe, regime; exit reasons, hold-time, early/decay/stop; sizing, concentration, max_positions, displacement blocks.",
        "See full findings: " + str(findings_path.relative_to(base)) if findings_path.exists() else "",
        "",
        "## 4. Blocked & CI",
        "What we're preventing, what it costs, what it saves — see ledger summary top_blocked_reasons and top_ci_reasons.",
        "",
        "## 5. Promotions (what to promote next)",
        "No promotions in this mission (read-only). CSA identifies what to promote next in findings; gate via enforce_csa_gate.",
        "",
        "---",
        "*Generated by scripts/audit/run_csa_weekly_review.py*",
    ]
    packet_path = board_dir / f"CSA_WEEKLY_REVIEW_{date_str}_BOARD_PACKET.md"
    packet_path.write_text("\n".join(packet_lines), encoding="utf-8")
    print("Board packet:", packet_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
