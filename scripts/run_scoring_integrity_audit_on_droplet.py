#!/usr/bin/env python3
"""Run scoring integrity audits on droplet: systemd, gate logs, cache, score snapshot."""
from __future__ import annotations

import json
import sys
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

        # Systemd: list units matching stock/trading/uw/dashboard
        units_out, _ = run(c, "systemctl list-units --all --no-pager 2>/dev/null | grep -E 'stock|trading|uw|dashboard' || true", 15)
        status_lines = []
        for unit in ["trading-bot.service", "stock-bot.service", "stockbot.service", "uw-flow-daemon.service", "stock-bot-dashboard.service"]:
            s, _ = run(c, f"systemctl is-active {unit} 2>/dev/null || echo not-found", 5)
            j, _ = run(c, f"journalctl -u {unit} -n 15 --no-pager 2>/dev/null || true", 10)
            status_lines.append(f"## {unit}\nactive: {s}\n--- journalctl -n 15 ---\n{j[:2000]}\n")
        (out_dir / "systemd_audit.md").write_text(
            "# Systemd Audit (Droplet)\n\n## Listed units (stock/trading/uw/dashboard)\n```\n" + units_out + "\n```\n\n" + "\n".join(status_lines),
            encoding="utf-8",
        )

        # Gate: last 50 lines of gate.jsonl for cycle_summary
        gate_out, _ = run(c, f"{cd} && tail -50 logs/gate.jsonl 2>/dev/null")
        cycles = []
        for line in gate_out.splitlines():
            try:
                e = json.loads(line.strip())
                if e.get("msg") == "cycle_summary" or (e.get("event") == "gate" and "considered" in e):
                    cycles.append(e)
            except Exception:
                pass
        gate_audit = "# Gate audit (recent)\n\n" + "\n".join(json.dumps(c) for c in cycles[-10:])
        (out_dir / "gate_sample.jsonl").write_text("\n".join(line for line in gate_out.splitlines()[-20:]), encoding="utf-8")

        # Score snapshot: last 30 lines
        snap_out, _ = run(c, f"{cd} && tail -30 state/score_snapshot.jsonl 2>/dev/null || tail -30 logs/score_snapshot.jsonl 2>/dev/null || echo '[]'")
        (out_dir / "score_snapshot_sample.txt").write_text(snap_out[:5000], encoding="utf-8")

        # Cache: uw_flow_cache presence and keys count
        cache_out, _ = run(c, f"{cd} && ls -la data/uw_flow_cache.json 2>/dev/null; python3 -c \"import json; d=json.load(open('data/uw_flow_cache.json')); print('keys:', len(d))\" 2>/dev/null || echo 'cache missing or invalid'")
        (out_dir / "cache_check.txt").write_text(cache_out, encoding="utf-8")

    return 0


if __name__ == "__main__":
    sys.exit(main())
