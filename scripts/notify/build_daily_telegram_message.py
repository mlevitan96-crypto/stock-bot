#!/usr/bin/env python3
"""
Build daily executive governance summary for Telegram.
Uses TOP_3_PROMOTABLE_IDEAS and promotion overlay details (read-only, output-only).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

# Ensure UTF-8 for emoji when stdout is a pipe or Windows console
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("Usage: build_daily_telegram_message.py <date>")
    date = sys.argv[1]
    root = Path(os.getcwd())
    top_path = root / "reports" / "rolling" / f"TOP_3_PROMOTABLE_IDEAS_{date}.json"

    if not top_path.exists():
        print("📊 Daily Trading Governance Update")
        print(f"Date: {date}\n")
        print("No rolling review data for this date.")
        return

    with open(top_path, encoding="utf-8") as f:
        top = json.load(f)
    configs = top.get("configs") or top.get("ideas", [])
    if not configs:
        print("📊 Daily Trading Governance Update")
        print(f"Date: {date}\n")
        print("No promotable ideas for this date.")
        return

    active = configs[0]["config_id"]
    try:
        out = subprocess.run(
            [sys.executable, "scripts/notify/extract_promotion_details.py", active],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=10,
        )
        details = json.loads(out.stdout) if out.returncode == 0 and out.stdout.strip() else {"active": False}
    except (FileNotFoundError, json.JSONDecodeError, subprocess.TimeoutExpired):
        details = {"active": False}

    msg = []
    msg.append("📊 Daily Trading Governance Update")
    msg.append(f"Date: {date}\n")
    msg.append("🧠 Promotion Status")
    msg.append(f"• Active promotion: {active} (paper)")
    if details.get("active"):
        msg.append(f"• Focus: {details['focus']}")
        msg.append("• Key changes:")
        for k in details["key_changes"]:
            msg.append(f"  - {k}")
        msg.append("• Expected impact:")
        for k, v in details["expected_impact"].items():
            msg.append(f"  - {k.replace('_', ' ')}: {v}")
    else:
        msg.append("• Overlay not yet applied or not found.")
    msg.append("\n🏆 Top Promotable Ideas")
    for i, c in enumerate(configs, 1):
        score = c.get("csa_board_score", "—")
        msg.append(f"{i}) {c['config_id']} — CSA score {score}")
    msg.append("\n🛡️ CSA / Board Verdict")
    msg.append("• Recommendation: PROMOTE & WATCH")
    msg.append("• Mode: learning promotion")

    text = "\n".join(msg)
    if hasattr(sys.stdout, "buffer"):
        sys.stdout.buffer.write((text + "\n").encode("utf-8"))
    else:
        print(text)


if __name__ == "__main__":
    main()
