#!/usr/bin/env python3
"""
Phase 5 verification: on droplet run SRE scan, then CSA consuming SRE output.
Writes reports/audit/SRE_CSA_INTEGRATION_PROOF.md (deployed_commit, sample SRE events, CSA verdict ref, scheduler confirmation).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROJ = "/root/stock-bot"


def main() -> int:
    audit_dir = REPO / "reports" / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)

    try:
        from droplet_client import DropletClient
    except ImportError:
        (audit_dir / "SRE_IMPLEMENTATION_BLOCKERS.md").write_text(
            "SRE/CSA verify: DropletClient not found.\n",
            encoding="utf-8",
        )
        print("DropletClient not found", file=sys.stderr)
        return 1

    evidence = {
        "deployed_commit": "",
        "telemetry_health_200": False,
        "learning_readiness_200": False,
        "sre_scan_ran": False,
        "sre_status": None,
        "sample_sre_events": [],
        "csa_ran": False,
        "csa_verdict_ref": "",
        "scheduler_active": False,
        "generated_ts": datetime.now(timezone.utc).isoformat(),
    }

    with DropletClient() as c:
        out, _, rc = c._execute(f"cd {PROJ} && git rev-parse HEAD 2>/dev/null || true", timeout=10)
        if rc == 0 and out:
            evidence["deployed_commit"] = out.strip()[:12]

        code_out, _, _ = c._execute(
            "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5000/api/telemetry_health 2>/dev/null || echo 000",
            timeout=10,
        )
        evidence["telemetry_health_200"] = (code_out or "").strip() == "200"
        code_out2, _, _ = c._execute(
            "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5000/api/learning_readiness 2>/dev/null || echo 000",
            timeout=10,
        )
        evidence["learning_readiness_200"] = (code_out2 or "").strip() == "200"

        if not (evidence["telemetry_health_200"] and evidence["learning_readiness_200"]):
            (audit_dir / "SRE_IMPLEMENTATION_BLOCKERS.md").write_text(
                "SRE/CSA verify: health endpoints not 200.\n",
                encoding="utf-8",
            )
            print("Health check failed", file=sys.stderr)
            return 1

        rc_sre = c._execute(
            f"cd {PROJ} && python3 scripts/sre/run_sre_anomaly_scan.py --base-dir . 2>&1",
            timeout=90,
        )[2]
        evidence["sre_scan_ran"] = rc_sre == 0

        content, _, _ = c._execute(f"cat {PROJ}/reports/audit/SRE_STATUS.json 2>/dev/null || true", timeout=5)
        if content and content.strip():
            try:
                evidence["sre_status"] = json.loads(content)
            except Exception:
                pass

        content_ev, _, _ = c._execute(f"tail -n 20 {PROJ}/reports/audit/SRE_EVENTS.jsonl 2>/dev/null || true", timeout=5)
        if content_ev and content_ev.strip():
            for line in content_ev.strip().splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    evidence["sample_sre_events"].append(json.loads(line))
                except json.JSONDecodeError:
                    pass
            evidence["sample_sre_events"] = evidence["sample_sre_events"][-5:]

        mission_id = "sre_csa_smoke"
        rc_csa = c._execute(
            f"cd {PROJ} && python3 scripts/audit/run_chief_strategy_auditor.py --mission-id {mission_id} "
            f"--sre-status-json reports/audit/SRE_STATUS.json --sre-events-jsonl reports/audit/SRE_EVENTS.jsonl "
            f"--board-review-json reports/board/last387_comprehensive_review.json --base-dir . 2>&1",
            timeout=90,
        )[2]
        evidence["csa_ran"] = rc_csa == 0

        csa_content, _, _ = c._execute(f"cat {PROJ}/reports/audit/CSA_VERDICT_{mission_id}.json 2>/dev/null || true", timeout=5)
        if csa_content and csa_content.strip():
            try:
                csa_data = json.loads(csa_content)
                evidence["csa_verdict_ref"] = f"verdict={csa_data.get('verdict')} confidence={csa_data.get('confidence')} sre_high_impact_block={csa_data.get('sre_high_impact_block')}"
            except Exception:
                evidence["csa_verdict_ref"] = "CSA verdict present"
        else:
            evidence["csa_verdict_ref"] = "CSA verdict file not found"

        crontab_out, _, _ = c._execute("crontab -l 2>/dev/null | grep -c run_sre_anomaly_scan || echo 0", timeout=5)
        evidence["scheduler_active"] = (crontab_out or "").strip() not in ("0", "")

    lines = [
        "# SRE–CSA integration proof",
        "",
        f"**Generated (UTC):** {evidence['generated_ts']}",
        "",
        "## Deployed commit",
        "",
        evidence["deployed_commit"] or "N/A",
        "",
        "## Health",
        "",
        f"- /api/telemetry_health: {'200' if evidence['telemetry_health_200'] else 'not 200'}",
        f"- /api/learning_readiness: {'200' if evidence['learning_readiness_200'] else 'not 200'}",
        "",
        "## SRE scan",
        "",
        f"- SRE scan ran: {evidence['sre_scan_ran']}",
        f"- SRE status: {(evidence.get('sre_status') or {}).get('overall_status', 'N/A')}",
        "",
        "## Sample SRE events (if any)",
        "",
    ]
    for ev in evidence.get("sample_sre_events", []):
        lines.append(f"- `{ev.get('event_id', '')}` {ev.get('event_type', '')} {ev.get('metric_name', '')} (confidence={ev.get('confidence')})")
    if not evidence.get("sample_sre_events"):
        lines.append("- (none in tail)")
    lines.extend([
        "",
        "## CSA verdict referencing SRE",
        "",
        evidence["csa_verdict_ref"],
        "",
        "## Scheduler",
        "",
        f"SRE cron every 10 min active: {evidence['scheduler_active']}",
        "",
    ])
    (audit_dir / "SRE_CSA_INTEGRATION_PROOF.md").write_text("\n".join(lines), encoding="utf-8")
    (audit_dir / "SRE_CSA_INTEGRATION_PROOF.json").write_text(json.dumps(evidence, indent=2, default=str), encoding="utf-8")
    print("SRE_CSA_INTEGRATION_PROOF.md written.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
