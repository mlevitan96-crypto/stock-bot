#!/usr/bin/env python3
"""
Enable B2 + PAPER on droplet: set FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=true and TRADING_MODE=PAPER in .env,
restart stock-bot, verify health. Writes reports/audit/B2_LIVE_PAPER_ENABLE_PROOF.md.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main() -> int:
    audit_dir = REPO / "reports" / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)

    # CSA gate BEFORE enabling flags (soft veto)
    import subprocess
    mission_id = "b2_paper_enable"
    board_json = REPO / "reports" / "board" / "last387_comprehensive_review.json"
    shadow_json = REPO / "reports" / "board" / "SHADOW_COMPARISON_LAST387.json"
    csa_args = [
        sys.executable,
        str(REPO / "scripts" / "audit" / "run_chief_strategy_auditor.py"),
        "--mission-id", mission_id,
        "--base-dir", str(REPO),
    ]
    if board_json.exists():
        csa_args += ["--board-review-json", str(board_json)]
    if shadow_json.exists():
        csa_args += ["--shadow-comparison-json", str(shadow_json)]
    rc_csa = subprocess.call(csa_args, cwd=REPO, timeout=60)
    if rc_csa != 0:
        print("CSA runner failed; aborting enable", file=sys.stderr)
        return 1
    rc_gate = subprocess.call(
        [
            sys.executable,
            str(REPO / "scripts" / "audit" / "enforce_csa_gate.py"),
            "--mission-id", mission_id,
            "--csa-verdict-json", str(audit_dir / f"CSA_VERDICT_{mission_id}.json"),
            "--require-override-for", "HOLD", "ESCALATE", "ROLLBACK",
        ],
        cwd=REPO,
        timeout=10,
    )
    if rc_gate != 0:
        print("CSA gate BLOCKED: require CSA_RISK_ACCEPTANCE or PROCEED verdict. See reports/audit/CSA_GATE_BLOCKER_*.md", file=sys.stderr)
        return 1

    try:
        from droplet_client import DropletClient
    except ImportError:
        print("DropletClient not found", file=sys.stderr)
        return 1

    evidence = {
        "droplet_timestamp": "",
        "deployed_commit": "",
        "paper_mode_active": False,
        "b2_flag_active": False,
        "telemetry_health_200": False,
        "learning_readiness_200": False,
        "env_snippet": "",
    }

    # Ensure .env has B2 and TRADING_MODE (add or replace)
    env_commands = """
grep -q '^FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=' .env 2>/dev/null && sed -i 's/^FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=.*/FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=true/' .env || echo 'FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=true' >> .env
grep -q '^TRADING_MODE=' .env 2>/dev/null && sed -i 's/^TRADING_MODE=.*/TRADING_MODE=PAPER/' .env || echo 'TRADING_MODE=PAPER' >> .env
"""
    with DropletClient() as c:
        evidence["droplet_timestamp"] = datetime.now(timezone.utc).isoformat()
        out, _, rc = c._execute_with_cd("git rev-parse HEAD 2>/dev/null || true", timeout=10)
        if rc == 0 and out:
            evidence["deployed_commit"] = out.strip()[:12]

        c._execute_with_cd(env_commands.strip().replace("\n", " && "), timeout=15)
        # Read back env snippet (no secrets)
        out, _, _ = c._execute_with_cd(
            "grep -E '^TRADING_MODE=|^FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=|^ALPACA_BASE_URL=' .env 2>/dev/null || true",
            timeout=5,
        )
        evidence["env_snippet"] = (out or "").strip()
        evidence["paper_mode_active"] = "TRADING_MODE=PAPER" in evidence["env_snippet"] or "paper" in (evidence["env_snippet"] or "").lower()
        evidence["b2_flag_active"] = "FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=true" in evidence["env_snippet"]

        c._execute("sudo systemctl restart stock-bot", timeout=60)
        c._execute("sleep 6", timeout=10)
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

    # Write proof
    lines = [
        "# B2 Live Paper — Enable proof",
        "",
        f"**Generated (UTC):** {evidence['droplet_timestamp']}",
        "",
        "## Deployed commit",
        "",
        evidence["deployed_commit"] or "N/A",
        "",
        "## Evidence PAPER_MODE + B2 flag active",
        "",
        f"- **TRADING_MODE / PAPER:** {evidence['paper_mode_active']}",
        f"- **FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=true:** {evidence['b2_flag_active']}",
        "",
        "## .env snippet (no secrets)",
        "",
        "```",
        evidence["env_snippet"] or "(none captured)",
        "```",
        "",
        "## Health endpoint checks",
        "",
        f"- **/api/telemetry_health:** {'200' if evidence['telemetry_health_200'] else 'not 200'}",
        f"- **/api/learning_readiness:** {'200' if evidence['learning_readiness_200'] else 'not 200'}",
        "",
    ]
    (audit_dir / "B2_LIVE_PAPER_ENABLE_PROOF.md").write_text("\n".join(lines), encoding="utf-8")
    (audit_dir / "B2_LIVE_PAPER_ENABLE_PROOF.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print("B2_LIVE_PAPER_ENABLE_PROOF.md written.")
    if not (evidence["paper_mode_active"] and evidence["b2_flag_active"] and evidence["telemetry_health_200"]):
        print("Warning: one or more checks false", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
