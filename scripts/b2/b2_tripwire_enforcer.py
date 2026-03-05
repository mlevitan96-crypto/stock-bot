#!/usr/bin/env python3
"""
B2 tripwire enforcer. Run on droplet after b2_daily_evaluator.py.
Reads B2_LIVE_PAPER_TEST_PLAN.json and B2_DAILY_STATUS.json.
If tripwire breached: set FEATURE_B2=false, restart stock-bot, verify health, write B2_AUTO_ROLLBACK_PROOF.md.
Else: write B2_TRIPWIRE_CLEAR.md.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main() -> int:
    base = Path(os.getenv("B2_BASE_DIR", REPO))
    board_dir = base / "reports" / "board"
    audit_dir = base / "reports" / "audit"
    state_dir = base / "state"
    audit_dir.mkdir(parents=True, exist_ok=True)

    plan_path = board_dir / "B2_LIVE_PAPER_TEST_PLAN.json"
    status_path = board_dir / "B2_DAILY_STATUS.json"
    if not plan_path.exists() or not status_path.exists():
        print("B2_LIVE_PAPER_TEST_PLAN.json or B2_DAILY_STATUS.json not found", file=sys.stderr)
        return 1

    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    status = json.loads(status_path.read_text(encoding="utf-8"))
    tripwires = plan.get("tripwires") or []
    breaches: list[dict] = []

    # 1) paper_safety_violation > 0
    count = status.get("paper_safety_violation_count")
    if count is None:
        vpath = base / "state" / "paper_safety_violation.json"
        if vpath.exists():
            try:
                count = json.loads(vpath.read_text(encoding="utf-8")).get("count", 0)
            except Exception:
                count = 0
        else:
            count = 0
    if count > 0:
        breaches.append({"id": "paper_safety_violation", "detail": f"count={count} (immediate_rollback)"})

    # 2) tail_risk_breach: current worst 5% mean worse than baseline by > 20% relative
    tail = status.get("tail_risk_summary") or {}
    current_worst_5pct = tail.get("worst_5pct_mean_pnl_usd")
    baseline_worst_5pct = None
    for tw in tripwires:
        if tw.get("id") == "tail_risk_breach":
            baseline_worst_5pct = tw.get("baseline_worst_5pct_pnl_usd")
            break
    if current_worst_5pct is not None and baseline_worst_5pct is not None and baseline_worst_5pct < 0:
        # current worse than baseline by > 20% relative: current < baseline * 1.2 (e.g. baseline -15, 20% worse = -18)
        threshold = baseline_worst_5pct * 1.2
        if current_worst_5pct < threshold:
            breaches.append({
                "id": "tail_risk_breach",
                "detail": f"worst_5pct_mean={current_worst_5pct} vs baseline={baseline_worst_5pct} (threshold {threshold:.1f})",
            })

    # 3) sustained_negative_delta: expectancy below baseline by > 15% for 3+ consecutive days (last 3 history lines)
    history_path = state_dir / "b2_daily_history.jsonl"
    baseline_expectancy = status.get("baseline_expectancy_per_exit_usd")
    if baseline_expectancy is not None and baseline_expectancy < 0 and history_path.exists():
        lines = [ln.strip() for ln in history_path.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()]
        recent = lines[-3:]  # last 3 runs (consecutive days if run daily)
        threshold_exp = baseline_expectancy * 1.15  # 15% worse than baseline
        all_three_worse = True
        for line in recent:
            try:
                rec = json.loads(line)
                exp = rec.get("expectancy_per_exit_usd")
                if exp is None or exp >= threshold_exp:
                    all_three_worse = False
                    break
            except Exception:
                all_three_worse = False
                break
        if len(recent) >= 3 and all_three_worse:
            breaches.append({
                "id": "sustained_negative_delta",
                "detail": f"expectancy below baseline by >15% for 3+ consecutive runs (threshold {threshold_exp:.4f})",
            })

    if not breaches:
        clear_lines = [
            "# B2 Tripwire Clear",
            "",
            f"**Checked (UTC):** {datetime.now(timezone.utc).isoformat()}",
            "",
            "No tripwires breached. B2 remains enabled.",
            "",
        ]
        (audit_dir / "B2_TRIPWIRE_CLEAR.md").write_text("\n".join(clear_lines), encoding="utf-8")
        # Update recommendation in status to Hold (evaluator already set it; enforcer doesn't change to Promote)
        print("B2 tripwire: CLEAR")
        return 0

    # Rollback: set B2=false, restart, verify
    env_path = base / ".env"
    if not env_path.exists():
        (audit_dir / "B2_AUTO_ROLLBACK_PROOF.md").write_text(
            f"# B2 Auto-Rollback (failed)\n\n**Time:** {datetime.now(timezone.utc).isoformat()}\n\n"
            "Tripwires breached but .env not found; could not perform rollback.\n"
            f"Breaches: {breaches}\n",
            encoding="utf-8",
        )
        return 1

    # sed to set FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=false (Linux)
    try:
        if sys.platform == "win32":
            content = env_path.read_text(encoding="utf-8", errors="replace")
            new_lines = []
            for line in content.splitlines():
                if line.strip().startswith("FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT="):
                    new_lines.append("FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=false")
                else:
                    new_lines.append(line)
            env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        else:
            subprocess.run(
                ["sed", "-i", "s/^FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=.*/FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=false/", str(env_path)],
                check=True,
                timeout=5,
                cwd=base,
            )
    except Exception as e:
        (audit_dir / "B2_AUTO_ROLLBACK_PROOF.md").write_text(
            f"# B2 Auto-Rollback (failed)\n\n**Time:** {datetime.now(timezone.utc).isoformat()}\n\n"
            f"Could not update .env: {e}\nBreaches: {breaches}\n",
            encoding="utf-8",
        )
        return 1

    subprocess.run(["sudo", "systemctl", "restart", "stock-bot"], cwd=base, timeout=60, check=False)
    import time
    time.sleep(6)
    health_ok = True
    for path in ["/api/telemetry_health", "/api/learning_readiness"]:
        try:
            r = subprocess.run(
                ["curl", "-s", "-o", os.devnull, "-w", "%{http_code}", f"http://127.0.0.1:5000{path}"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if (r.stdout or "").strip() != "200":
                health_ok = False
                break
        except Exception:
            health_ok = False
            break

    proof_lines = [
        "# B2 Auto-Rollback Proof",
        "",
        f"**Executed (UTC):** {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Tripwires breached",
        "",
    ] + [f"- **{b['id']}:** {b['detail']}" for b in breaches] + [
        "",
        "## Actions taken",
        "",
        "1. Set FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=false in .env",
        "2. sudo systemctl restart stock-bot",
        f"3. Health endpoints 200: {health_ok}",
        "",
        "B2 is OFF. Do not re-enable until tripwire root cause is resolved.",
        "",
    ]
    (audit_dir / "B2_AUTO_ROLLBACK_PROOF.md").write_text("\n".join(proof_lines), encoding="utf-8")

    # Update B2_DAILY_STATUS recommendation to Rollback
    status["recommendation"] = "Rollback"
    status["reason_bullets"] = [f"Tripwire breach: {b['id']} — {b['detail']}" for b in breaches[:3]]
    status_path.write_text(json.dumps(status, indent=2, default=str), encoding="utf-8")
    md_path = board_dir / "B2_DAILY_STATUS.md"
    if md_path.exists():
        content = md_path.read_text(encoding="utf-8", errors="replace")
        if "## Recommendation" in content:
            new_section = "## Recommendation\n\n**Rollback**\n\n**Reason:**\n\n" + "\n".join(f"- {b}" for b in status["reason_bullets"]) + "\n"
            content = re.sub(r"## Recommendation\n\n.*?(?=\n## |\n---|\Z)", new_section + "\n", content, flags=re.DOTALL)
            md_path.write_text(content, encoding="utf-8")
        else:
            md_path.write_text(
                content.rstrip() + "\n\n## Recommendation\n\n**Rollback** (auto-executed). See B2_AUTO_ROLLBACK_PROOF.md.\n",
                encoding="utf-8",
            )
    if not health_ok:
        return 1
    print("B2 tripwire: BREACHED — rollback executed. See B2_AUTO_ROLLBACK_PROOF.md", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
