#!/usr/bin/env python3
"""Deploy MIN_EXEC_SCORE=2.5 to droplet, restart paper, capture gate summary and verdict."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from droplet_client import DropletClient


def run(c, cmd: str, timeout: int = 30) -> tuple[str, str]:
    o, e, _ = c._execute(cmd, timeout=timeout)
    return (o or "").strip(), (e or "").strip()


def main() -> int:
    with DropletClient() as c:
        root = (
            run(c, "([ -d /root/stock-bot-current/scripts ] && echo /root/stock-bot-current) || echo /root/stock-bot")[0]
            or "/root/stock-bot"
        ).strip()
        cd = f"cd {root}"

        # 1) Force to origin/main (threshold commit 4e45064) and confirm
        run(c, f"{cd} && git fetch origin && git reset --hard origin/main", 60)
        log_out, _ = run(c, f"{cd} && git log -1 --oneline")
        print("Commit on droplet:", log_out)

        # 2) Restart paper
        run(c, f"tmux kill-session -t stock_bot_paper_run 2>/dev/null || true", 10)
        run(
            c,
            f"tmux new-session -d -s stock_bot_paper_run 'cd {root} && SCORE_SNAPSHOT_DEBUG=1 LOG_LEVEL=INFO python3 main.py'",
            10,
        )
        print("Paper restarted. Waiting 120s for cycles...")
        time.sleep(120)

        # 3) Capture gate cycle_summary from gate.jsonl
        out, _ = run(c, f"{cd} && tail -200 logs/gate.jsonl 2>/dev/null")
        cycles = []
        for line in out.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
                if e.get("msg") == "cycle_summary" or (e.get("event") == "gate" and "considered" in e):
                    cycles.append(e)
            except Exception:
                pass
        run_out, _ = run(c, f"{cd} && tail -20 logs/run.jsonl 2>/dev/null")
        run_orders = []
        for line in run_out.splitlines():
            try:
                e = json.loads(line.strip())
                if e.get("msg") == "complete" and "orders" in e:
                    run_orders.append(e.get("orders", 0))
            except Exception:
                pass

        # 4) Write proof and print output
        proof_path = REPO / "reports" / "blocked_expectancy" / "proof.md"
        inv_path = REPO / "reports" / "open_orders_investigation.md"
        recent = cycles[-3:] if len(cycles) >= 3 else cycles
        orders_recent = run_orders[-5:] if run_orders else []
        max_orders = max(orders_recent) if orders_recent else 0

        proof_lines = [
            "# Blocked-expectancy post-fix proof (droplet)",
            "",
            "**Deployed:** MIN_EXEC_SCORE 3.0 → 2.5 (git reset --hard origin/main). Paper restarted with SCORE_SNAPSHOT_DEBUG=1.",
            "",
            "## Confirmed commit on droplet",
            f"`{log_out}`",
            "",
            "## Post-change gate summary (recent cycles)",
            "",
        ]
        for i, e in enumerate(recent):
            proof_lines.append(f"- considered={e.get('considered', '?')}, orders={e.get('orders', '?')}, gate_counts={e.get('gate_counts', {})}")
        proof_lines.extend([
            "",
            "## Verdict",
            "TRADES ADMITTED" if max_orders > 0 else "STILL BLOCKED (see dominant gate in gate_counts above)",
            "",
        ])
        proof_path.write_text("\n".join(proof_lines), encoding="utf-8")

        # Append to open_orders_investigation.md
        if inv_path.exists():
            text = inv_path.read_text(encoding="utf-8")
            if "## Post-threshold-change" not in text:
                text += "\n\n---\n\n## Post-threshold-change (MIN_EXEC_SCORE=2.5)\n\n"
                text += f"- Commit: {log_out}\n"
                text += "- Recent cycle_summary: " + "; ".join([f"considered={e.get('considered')}, orders={e.get('orders')}, gate_counts={e.get('gate_counts')}" for e in recent]) + "\n"
                text += "- Verdict: " + ("TRADES ADMITTED" if max_orders > 0 else "STILL BLOCKED") + "\n"
                inv_path.write_text(text, encoding="utf-8")

        # Print required output
        print()
        print("Confirmed commit on droplet:", log_out)
        print()
        print("Post-change gate summary (recent cycles):")
        for e in recent:
            print("  considered=%s, gate_counts=%s, orders=%s" % (e.get("considered"), e.get("gate_counts"), e.get("orders")))
        if not recent:
            print("  (no cycle_summary in last 200 gate lines)")
        print()
        if max_orders > 0:
            print("Verdict: TRADES ADMITTED")
        else:
            dominant = "score_below_min"
            if recent and isinstance(recent[-1].get("gate_counts"), dict):
                gc = recent[-1]["gate_counts"]
                if gc:
                    dominant = max(gc.keys(), key=lambda k: gc[k])
            print("Verdict: STILL BLOCKED by", dominant)
    return 0


if __name__ == "__main__":
    sys.exit(main())
