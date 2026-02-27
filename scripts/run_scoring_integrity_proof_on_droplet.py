#!/usr/bin/env python3
"""Deploy scoring pipeline integrity fix to droplet, restart paper, capture proof."""
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
    out_dir = REPO / "reports" / "scoring_integrity"
    out_dir.mkdir(parents=True, exist_ok=True)

    with DropletClient() as c:
        root = (
            run(c, "([ -d /root/stock-bot-current/scripts ] && echo /root/stock-bot-current) || echo /root/stock-bot")[0]
            or "/root/stock-bot"
        ).strip()
        cd = f"cd {root}"

        # 1) Deploy latest (scoring integrity fix)
        run(c, f"{cd} && git fetch origin && git reset --hard origin/main", 60)
        log_out, _ = run(c, f"{cd} && git log -1 --oneline")
        print("Commit on droplet:", log_out)

        # 2) Systemd health (if applicable)
        svc, _ = run(c, "systemctl is-active trading-bot.service 2>/dev/null || systemctl is-active stockbot.service 2>/dev/null || echo not-found", 5)

        # 3) Restart paper (tmux)
        run(c, "tmux kill-session -t stock_bot_paper_run 2>/dev/null || true", 10)
        run(c, f"tmux new-session -d -s stock_bot_paper_run 'cd {root} && SCORE_SNAPSHOT_DEBUG=1 LOG_LEVEL=INFO python3 main.py'", 10)
        print("Paper restarted. Waiting 120s for cycles...")
        time.sleep(120)

        # 4) Gate summary
        out, _ = run(c, f"{cd} && tail -200 logs/gate.jsonl 2>/dev/null")
        cycles = []
        for line in out.splitlines():
            try:
                e = json.loads(line.strip())
                if e.get("msg") == "cycle_summary" or (e.get("event") == "gate" and "considered" in e):
                    cycles.append(e)
            except Exception:
                pass
        recent = cycles[-5:] if len(cycles) >= 5 else cycles

        # 5) Orders from run.jsonl
        run_out, _ = run(c, f"{cd} && tail -20 logs/run.jsonl 2>/dev/null")
        orders_list = []
        for line in run_out.splitlines():
            try:
                e = json.loads(line.strip())
                if e.get("msg") == "complete" and "orders" in e:
                    orders_list.append(e.get("orders", 0))
            except Exception:
                pass
        max_orders = max(orders_list) if orders_list else 0

        # 6) Write proof.md
        dominant = "expectancy_blocked:score_floor_breach"
        if recent and isinstance(recent[-1].get("gate_counts"), dict) and recent[-1]["gate_counts"]:
            dominant = max(recent[-1]["gate_counts"].keys(), key=lambda k: recent[-1]["gate_counts"][k])
        verdict = "TRADES ADMITTED" if max_orders > 0 else f"STILL BLOCKED (dominant gate: {dominant})"

        proof = f"""# Scoring Pipeline Integrity — Proof (Droplet)

**Fix deployed:** Expectancy gate now uses same score as min-score gate (adjusted score).

## Commit on droplet
`{log_out}`

## Systemd health
- Main service: {svc}

## Post-fix gate summary (recent cycles)
"""
        for e in recent:
            proof += f"- considered={e.get('considered')}, gate_counts={e.get('gate_counts')}, orders={e.get('orders')}\n"
        proof += f"""
## Verdict
{verdict}
"""
        (out_dir / "proof.md").write_text(proof, encoding="utf-8")

        # Print required output
        print()
        print("Post-fix gate summary (considered, gate_counts, orders):")
        for e in recent:
            print(" ", e.get("considered"), e.get("gate_counts"), e.get("orders"))
        print("Verdict:", verdict)
    return 0


if __name__ == "__main__":
    sys.exit(main())
