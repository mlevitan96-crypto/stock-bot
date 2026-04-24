#!/usr/bin/env python3
"""Pull latest on droplet, run dashboard accuracy audit, fetch JSON and write report."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from droplet_client import DropletClient


def main() -> int:
    c = DropletClient()
    # Ensure droplet has latest (script we just pushed)
    c._execute_with_cd("git fetch origin main && git reset --hard origin/main", timeout=30)
    # Run audit (no --local: use droplet cwd as base)
    out, err, rc = c._execute_with_cd("python3 scripts/audit/run_dashboard_accuracy_audit_on_droplet.py", timeout=30)
    if rc != 0 and rc != 1:
        print("Audit script failed or not found on droplet.", file=sys.stderr)
        print(err or out, file=sys.stderr)
        return 1
    # Parse JSON from stdout (script prints one JSON object)
    text = out or ""
    try:
        # May have leading/trailing noise
        start = text.find("{")
        end = text.rfind("}") + 1
        if start < 0 or end <= start:
            print("No JSON in output.", file=sys.stderr)
            return 1
        data = json.loads(text[start:end])
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}", file=sys.stderr)
        return 1
    # Write JSON and report (canonical layout: STOCKBOT_REPORT_EVIDENCE_DIR → daily session evidence/)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")
    ev = os.environ.get("STOCKBOT_REPORT_EVIDENCE_DIR", "").strip()
    audit_dir = Path(ev) if ev else REPO / "reports" / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    json_path = audit_dir / f"DASHBOARD_ACCURACY_AUDIT_{ts}.json"
    json_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    print(f"Wrote {json_path}")
    # Write human-readable report for CSA/board/SRE
    report_path = audit_dir / f"DASHBOARD_ACCURACY_AUDIT_CSA_BOARD_SRE_{ts}.md"
    write_report(data, report_path)
    print(f"Wrote {report_path}")
    return 0 if not data.get("findings") else 1


def write_report(data: dict, path: Path) -> None:
    lines = [
        "# Dashboard Data Accuracy Audit — CSA / Board / SRE",
        "",
        "**Scope:** Every tab, every number. Accuracy = real and consistent with source of truth; no stale-but-matching numbers.",
        "",
        f"**Audit time (UTC):** {data.get('audit_ts_utc', '—')}",
        f"**Today (UTC):** {data.get('today_utc', '—')}",
        f"**Environment:** Droplet (`{data.get('base_dir', '')}`)",
        "",
        "---",
        "",
        "## 1. Source of truth (per metric)",
        "",
        "| Dashboard surface | Source of truth | What dashboard reads | Real? |",
        "|-------------------|-----------------|----------------------|-------|",
    ]
    sources = data.get("sources") or {}
    # Learning & Readiness: direction_readiness.json (from cron) + exit_attribution.jsonl
    dr = sources.get("state/direction_readiness.json") or {}
    ex = sources.get("logs/exit_attribution.jsonl") or {}
    dr_fresh = "Yes" if dr.get("fresh_within_24h") else ("No (stale)" if dr.get("exists") else "N/A")
    lines.append(f"| Learning & Readiness (X/100, all-time exits) | `logs/exit_attribution.jsonl` (cron writes `state/direction_readiness.json`) | `state/direction_readiness.json` | {dr_fresh} |")
    # Profitability & Learning: TRADE_CSA_STATE, CSA_VERDICT, cockpit
    csa_path = data.get("dashboard_csa_path_used") or "—"
    csa_ok = "Yes" if data.get("cross_checks", {}).get("csa_state_is_production_not_test") else "No (test path)"
    lines.append(f"| Profitability & Learning (trade count, CSA) | `reports/state/TRADE_CSA_STATE.json` + `reports/audit/CSA_VERDICT_LATEST.json` | {csa_path} | {csa_ok} |")
    # Closed Trades
    att = sources.get("logs/attribution.jsonl") or {}
    lines.append(f"| Closed Trades | `logs/attribution.jsonl` + `logs/exit_attribution.jsonl` | Same | Yes if files exist |")
    # Situation strip / promotion
    comb = sources.get(f"reports/{data.get('today_utc','')}_stock-bot_combined.json") or {}
    comb_ok = "Yes" if comb.get("exists") else "No (missing today's combined)"
    lines.append(f"| Situation strip / Strategy comparison (today) | `reports/{{today}}_stock-bot_combined.json` | Same | {comb_ok} |")
    lines.extend([
        "",
        "---",
        "",
        "## 2. Cross-checks (consistency)",
        "",
    ])
    cc = data.get("cross_checks") or {}
    for k, v in cc.items():
        label = k.replace("_", " ").title()
        status = "✓ Pass" if v is True else ("✗ Fail" if v is False else "— N/A")
        lines.append(f"- **{label}:** {status}")
    lines.extend([
        "",
        "---",
        "",
        "## 3. Data source details (droplet)",
        "",
    ])
    for name, info in sources.items():
        if not isinstance(info, dict):
            continue
        exists = info.get("exists", False)
        lines.append(f"### `{name}`")
        lines.append(f"- **Exists:** {exists}")
        if info.get("mtime_iso"):
            lines.append(f"- **Last modified (UTC):** {info['mtime_iso']}")
        if "line_count" in info:
            lines.append(f"- **Line count:** {info['line_count']}")
        for key in ("all_time_exits", "total_trades", "telemetry_trades", "total_trade_events", "last_csa_mission_id", "mission_id", "verdict"):
            if key in info and info[key] is not None:
                lines.append(f"- **{key}:** {info[key]}")
        if info.get("fresh_within_24h") is not None:
            lines.append(f"- **Fresh within 24h:** {info['fresh_within_24h']}")
        lines.append("")
    lines.extend([
        "---",
        "",
        "## 4. Findings (action required if any)",
        "",
    ])
    findings = data.get("findings") or []
    if not findings:
        lines.append("- No issues found. Numbers are consistent and from canonical sources.")
    else:
        for f in findings:
            lines.append(f"- **{f}**")
    lines.extend([
        "",
        "---",
        "",
        "## 5. SRE / Eng oversight checklist",
        "",
        "- [ ] direction_readiness cron installed and running (9–21 UTC Mon–Fri): `scripts/governance/install_direction_readiness_cron_on_droplet.py`",
        "- [ ] TRADE_CSA_STATE is production path (not test_csa_100) on droplet",
        "- [ ] exit_attribution.jsonl is appended by live trading (not a static copy)",
        "- [ ] Today's combined report exists when strategy comparison / situation is needed: `reports/{today}_stock-bot_combined.json`",
        "- [ ] Dashboard auth exemption list includes only read-only, non-sensitive endpoints",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
