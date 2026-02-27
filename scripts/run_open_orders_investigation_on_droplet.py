#!/usr/bin/env python3
"""Run open-orders investigation on droplet via DropletClient. Market should be open for meaningful logs."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from droplet_client import DropletClient


def run(c, cmd: str, timeout: int = 15) -> tuple[str, str]:
    o, e, _ = c._execute(cmd, timeout=timeout)
    return (o or "").strip(), (e or "").strip()


def main() -> int:
    with DropletClient() as c:
        out, _ = run(c, "([ -d /root/stock-bot-current/scripts ] && echo /root/stock-bot-current) || echo /root/stock-bot")
        root = out.strip() or "/root/stock-bot"
        cd = f"cd {root}"

        print("=== Open orders investigation (droplet) ===\n")
        print("Repo root:", root)
        print()

        # Recent run completion
        out, _ = run(c, cd + " && tail -30 logs/run.jsonl 2>/dev/null")
        print("--- Recent run completion (logs/run.jsonl, last 30) ---")
        completes = []
        for line in out.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
                if e.get("msg") == "complete" or "clusters" in e:
                    completes.append(e)
            except Exception:
                pass
        for e in completes[-5:]:
            print(
                "  clusters=%s, orders=%s, risk_freeze=%s, market_open=%s"
                % (e.get("clusters", "?"), e.get("orders", "?"), e.get("risk_freeze") or "—", e.get("market_open", ""))
            )
        if not completes:
            print("  (no completion events)")
        print()

        # Skip-entry events
        out2, _ = run(
            c,
            cd
            + " && (tail -50 logs/run_once.jsonl 2>/dev/null; tail -50 logs/run.jsonl 2>/dev/null; tail -100 logs/gate.jsonl 2>/dev/null)",
            timeout=20,
        )
        skip = []
        for line in out2.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
                m = e.get("msg") or e.get("event")
                if m in ("not_armed_skip_entries", "not_reconciled_skip_entries", "reduce_only_broker_degraded"):
                    skip.append(e)
            except Exception:
                pass
        print("--- Skip-entry events ---")
        if not skip:
            print("  (none found)")
        else:
            for e in skip[-10:]:
                print("  ", e.get("msg") or e.get("event"), e.get("base_url", ""), e.get("action", ""))
        print()

        # Gate cycle_summary
        out3, _ = run(c, cd + " && tail -150 logs/gate.jsonl 2>/dev/null")
        cycles = []
        for line in out3.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
                if e.get("msg") == "cycle_summary" or (e.get("event") == "gate" and "considered" in e):
                    cycles.append(e)
            except Exception:
                pass
        print("--- Gate cycle_summary (last 5) ---")
        for e in cycles[-5:]:
            print(
                "  considered=%s, orders=%s, reason=%s"
                % (e.get("considered", "?"), e.get("orders", "?"), e.get("reason") or "—")
            )
            if e.get("gate_counts"):
                print("    gate_counts:", e.get("gate_counts"))
        if not cycles:
            print("  (none found)")
        print()

        # Worker debug
        out4, _ = run(c, cd + " && tail -60 logs/worker_debug.log 2>/dev/null")
        print("--- Worker debug (last 60 lines, filtered) ---")
        for line in (out4 or "").splitlines():
            line = line.rstrip()
            if "Market" in line or "run_once" in line or "decide_and_execute" in line or "orders" in line:
                print(" ", line[:120])
        print()

        # ALPACA_BASE_URL from .env (redact value)
        out5, _ = run(c, cd + " && grep ALPACA_BASE_URL .env 2>/dev/null | head -1 || echo '(not found)'")
        print("--- .env ALPACA_BASE_URL ---")
        if out5 and "=" in out5:
            key, _ = out5.split("=", 1)
            print("  ", key + "=*** (set)")
        else:
            print("  ", out5 or "(not found)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
