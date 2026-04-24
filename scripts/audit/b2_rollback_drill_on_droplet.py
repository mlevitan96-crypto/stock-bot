#!/usr/bin/env python3
"""
Phase 7: Rollback drill on droplet. Flip B2 OFF -> restart -> verify; flip B2 ON -> restart -> verify.
Writes reports/audit/B2_ROLLBACK_DRILL_PROOF.md or B2_ROLLBACK_BLOCKER.md on failure.
"""
from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main() -> int:
    audit_dir = REPO / "reports" / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)

    try:
        from droplet_client import DropletClient
    except ImportError:
        audit_dir / "B2_ROLLBACK_BLOCKER.md"
        (audit_dir / "B2_ROLLBACK_BLOCKER.md").write_text(
            "# B2 Rollback Blocker\n\nDropletClient not found; rollback drill could not run.\n",
            encoding="utf-8",
        )
        return 1

    steps = []
    now = datetime.now(timezone.utc).isoformat()

    with DropletClient() as c:
        def run(cmd: str, timeout: int = 15):
            out, err, rc = c._execute_with_cd(cmd, timeout=timeout)
            return (out or "").strip(), (err or "").strip(), rc

        # 1) B2 OFF
        run("sed -i 's/^FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=.*/FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=false/' .env 2>/dev/null || echo 'FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=false' >> .env")
        run("grep -q '^FEATURE_B2' .env || echo 'FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=false' >> .env")
        run("sed -i 's/^FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=.*/FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=false/' .env")
        c._execute("sudo systemctl restart stock-bot", timeout=60)
        c._execute("sleep 6", timeout=10)
        env_out, _, _ = run("grep '^FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=' .env 2>/dev/null || true")
        code, _, _ = c._execute("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5000/api/telemetry_health 2>/dev/null || echo 000", timeout=10)
        b2_off_ok = "FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=false" in env_out and (code or "").strip() == "200"
        steps.append({"step": "B2 OFF", "env_line": env_out, "health_200": (code or "").strip() == "200", "ok": b2_off_ok})

        if not b2_off_ok:
            (audit_dir / "B2_ROLLBACK_BLOCKER.md").write_text(
                f"# B2 Rollback Blocker\n\n**Generated:** {now}\n\n"
                "Rollback drill failed at step 'B2 OFF': flag not false or health not 200.\n"
                f"env_line: {env_out!r}\nhealth_code: {code!r}\n",
                encoding="utf-8",
            )
            return 1

        # 2) B2 ON again
        run("sed -i 's/^FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=.*/FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=true/' .env")
        c._execute("sudo systemctl restart stock-bot", timeout=60)
        c._execute("sleep 6", timeout=10)
        env_out2, _, _ = run("grep '^FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=' .env 2>/dev/null || true")
        code2, _, _ = c._execute("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5000/api/telemetry_health 2>/dev/null || echo 000", timeout=10)
        b2_on_ok = "FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=true" in env_out2 and (code2 or "").strip() == "200"
        steps.append({"step": "B2 ON", "env_line": env_out2, "health_200": (code2 or "").strip() == "200", "ok": b2_on_ok})

        if not b2_on_ok:
            (audit_dir / "B2_ROLLBACK_BLOCKER.md").write_text(
                f"# B2 Rollback Blocker\n\n**Generated:** {now}\n\n"
                "Rollback drill failed at step 'B2 ON' (re-enable): flag not true or health not 200.\n"
                f"env_line: {env_out2!r}\nhealth_code: {code2!r}\n",
                encoding="utf-8",
            )
            return 1

    # Success: write proof
    lines = [
        "# B2 Rollback Drill Proof",
        "",
        f"**Generated (UTC):** {now}",
        "",
        "## Drill steps",
        "",
        "1. **B2 OFF:** Set FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=false, restart stock-bot.",
        f"   - Env: `{steps[0].get('env_line', '')}`",
        f"   - Health 200: {steps[0].get('health_200', False)}",
        "",
        "2. **B2 ON:** Set FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=true, restart stock-bot.",
        f"   - Env: `{steps[1].get('env_line', '')}`",
        f"   - Health 200: {steps[1].get('health_200', False)}",
        "",
        "## Result",
        "",
        "Rollback drill passed. One-config flip + restart is verified; B2 is re-enabled for continued live paper test.",
        "",
    ]
    (audit_dir / "B2_ROLLBACK_DRILL_PROOF.md").write_text("\n".join(lines), encoding="utf-8")
    # Remove blocker if it existed from a prior run
    blocker = audit_dir / "B2_ROLLBACK_BLOCKER.md"
    if blocker.exists():
        blocker.unlink()
    print("B2_ROLLBACK_DRILL_PROOF.md written.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
