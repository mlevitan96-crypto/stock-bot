#!/usr/bin/env python3
"""
Alpaca End-to-End Governance Audit — single entry point.

Runs Step 0 (env check) then Steps 1–3 (trigger, full chain with --telegram, direct Telegram test).
Does NOT run Steps 4–6 (CSA/SRE reviews and MEMORY_BANK are written separately after human
confirms Telegram received).

Usage:
  Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID, then:
  python scripts/run_alpaca_e2e_governance_audit.py [--base-dir PATH]

Exit 0 only if env present, all scripts succeed, and direct Telegram send returns True.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _load_dotenv(base: Path) -> None:
    env_file = base / ".env"
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
        except ImportError:
            pass


def step0_verify_env(base: Path) -> bool:
    """Return True if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are set."""
    _load_dotenv(base)
    import os
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    return bool(token and str(token).strip() and chat and str(chat).strip())


def step1_trigger(base: Path) -> None:
    trigger_path = base / "state" / "alpaca_synthetic_audit_trigger.json"
    trigger_path.parent.mkdir(parents=True, exist_ok=True)
    trigger_path.write_text(json.dumps({
        "reason": "end_to_end_audit",
        "ts": datetime.now(timezone.utc).isoformat(),
        "note": "no live trading impact",
    }, indent=2), encoding="utf-8")
    doc = base / "reports" / "audit" / "ALPACA_E2E_TRIGGER.md"
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text(
        "# Alpaca E2E audit trigger\n\n"
        "**Method:** Synthetic governance marker.\n\n"
        f"- **File:** `state/alpaca_synthetic_audit_trigger.json`\n"
        f"- **Reason:** end_to_end_audit\n"
        f"- **Note:** no live trading impact\n\n"
        "Governance chain invoked with `--force` and `--telegram`.\n",
        encoding="utf-8",
    )


def run_cmd(cmd: list[str], cwd: Path) -> tuple[int, str, str]:
    r = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, timeout=300)
    return r.returncode, r.stdout or "", r.stderr or ""


def step2_chain(base: Path) -> tuple[bool, list[dict]]:
    import sys
    py = sys.executable
    scripts = [
        ("tier1", [py, "scripts/run_alpaca_board_review_tier1.py", "--force", "--telegram"]),
        ("tier2", [py, "scripts/run_alpaca_board_review_tier2.py", "--force", "--telegram"]),
        ("tier3", [py, "scripts/run_alpaca_board_review_tier3.py", "--force", "--telegram"]),
        ("convergence", [py, "scripts/run_alpaca_convergence_check.py", "--force", "--telegram"]),
        ("promotion_gate", [py, "scripts/run_alpaca_promotion_gate.py", "--force", "--telegram"]),
        ("heartbeat", [py, "scripts/run_alpaca_board_review_heartbeat.py", "--force", "--telegram"]),
    ]
    results = []
    for name, cmd in scripts:
        code, out, err = run_cmd(cmd, base)
        results.append({"step": name, "exit_code": code, "stdout": out, "stderr": err})
        if code != 0:
            return False, results
    return True, results


def step3_telegram_test(base: Path) -> bool:
    if str(base) not in sys.path:
        sys.path.insert(0, str(base))
    from scripts.alpaca_telegram import send_governance_telegram
    return send_governance_telegram(
        "ALPACA E2E AUDIT: Telegram transport verified. Governance chain completed successfully.",
        script_name="e2e_audit",
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Alpaca E2E governance audit (Steps 0–3).")
    ap.add_argument("--base-dir", type=Path, default=REPO, help="Repo root")
    args = ap.parse_args()
    base = args.base_dir.resolve()

    # Step 0
    if not step0_verify_env(base):
        missing = base / "reports" / "audit" / "TELEGRAM_ENV_MISSING.md"
        missing.parent.mkdir(parents=True, exist_ok=True)
        missing.write_text(
            "# Telegram environment missing — E2E audit blocked\n\n"
            "TELEGRAM_BOT_TOKEN and/or TELEGRAM_CHAT_ID not set at runtime.\n"
            "Set both, then re-run: `python scripts/verify_telegram_env.py`\n",
            encoding="utf-8",
        )
        print("Step 0 FAILED: Telegram env missing. Wrote", missing, file=sys.stderr)
        return 1
    print("Step 0: Telegram env present.")

    # Step 1
    step1_trigger(base)
    print("Step 1: Synthetic trigger written.")

    # Step 2
    ok, run_results = step2_chain(base)
    log_path = base / "reports" / "audit" / "ALPACA_E2E_RUN_LOG.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Alpaca E2E governance run log",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "| Step | Exit code |",
        "|------|-----------|",
    ]
    for r in run_results:
        lines.append(f"| {r['step']} | {r['exit_code']} |")
    lines.extend(["", "## Details", ""])
    for r in run_results:
        lines.append(f"### {r['step']}")
        lines.append(f"- Exit: {r['exit_code']}")
        if r["stdout"]:
            lines.append("```")
            lines.append(r["stdout"].strip()[:2000])
            lines.append("```")
        if r["stderr"]:
            lines.append("stderr: " + r["stderr"].strip()[:500])
        lines.append("")
    log_path.write_text("\n".join(lines), encoding="utf-8")
    print("Step 2: Chain run. Log:", log_path)

    if not ok:
        print("Step 2 FAILED: one or more scripts exited non-zero.", file=sys.stderr)
        return 1

    # Step 3
    if not step3_telegram_test(base):
        print("Step 3 FAILED: Direct Telegram send returned False. Check TELEGRAM_NOTIFICATION_LOG.md", file=sys.stderr)
        return 1
    print("Step 3: Telegram transport verified.")

    print("E2E audit (Steps 0–3) completed. Complete Steps 4–6 (CSA/SRE reviews, MEMORY_BANK) after confirming message received.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
