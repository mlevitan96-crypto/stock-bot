#!/usr/bin/env python3
"""On droplet: inventory Alpaca telemetry files. Writes reports/audit/ALPACA_TELEMETRY_INVENTORY.md"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
AUDIT = REPO / "reports" / "audit"
LOGS = REPO / "logs"
STATE = REPO / "state"

FILES = [
    ("logs/alpaca_unified_events.jsonl", "unified"),
    ("logs/alpaca_entry_attribution.jsonl", "entry_attr"),
    ("logs/alpaca_exit_attribution.jsonl", "exit_attr_emit"),
    ("logs/exit_attribution.jsonl", "exit_attribution"),
    ("logs/master_trade_log.jsonl", "master_trade"),
    ("logs/attribution.jsonl", "attribution"),
    ("state/blocked_trades.jsonl", "blocked"),
]


def stat_path(p: Path) -> dict:
    out = {"exists": p.exists(), "bytes": 0, "mtime_utc": "", "lines": 0}
    if not p.exists():
        return out
    try:
        st = p.stat()
        out["bytes"] = st.st_size
        out["mtime_utc"] = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat()
        if st.st_size > 0 and st.st_size < 500_000_000:
            with open(p, "rb") as f:
                out["lines"] = sum(1 for _ in f)
    except OSError:
        pass
    return out


def main() -> int:
    AUDIT.mkdir(parents=True, exist_ok=True)
    rows = []
    for rel, name in FILES:
        p = REPO / rel
        s = stat_path(p)
        if not s["exists"]:
            status = "MISSING"
        elif s["bytes"] == 0:
            status = "EMPTY"
        else:
            status = "OK"
        rows.append((name, rel, status, s))

    # Rotated variants
    rot = []
    for pat in ("logs/alpaca_unified_events.jsonl.*", "logs/*.gz"):
        try:
            r = subprocess.run(
                f"ls -la {REPO}/logs/*.gz 2>/dev/null | head -5; ls {REPO}/logs/alpaca*.jsonl* 2>/dev/null | head -10",
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
            rot.append(r.stdout or r.stderr or "(none)")
        except Exception as e:
            rot.append(str(e))

    lines_out = [
        "# Alpaca Telemetry Inventory (Droplet)",
        "",
        f"**UTC:** {datetime.now(timezone.utc).isoformat()}",
        "",
        "| Stream | Path | Status | Bytes | Lines | mtime_utc |",
        "|--------|------|--------|-------|-------|-----------|",
    ]
    for name, rel, status, s in rows:
        lines_out.append(
            f"| {name} | `{rel}` | **{status}** | {s['bytes']} | {s['lines']} | {s['mtime_utc']} |"
        )
    lines_out.extend(
        [
            "",
            "## Schema version (sample)",
            "",
        ]
    )
    exit_p = REPO / "logs" / "exit_attribution.jsonl"
    schema_exit = ""
    if exit_p.exists():
        try:
            with open(exit_p, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        r = json.loads(line)
                        schema_exit = str(r.get("attribution_schema_version") or r.get("schema_version") or "")
                        break
                    except json.JSONDecodeError:
                        continue
        except OSError:
            pass
    lines_out.append(f"- Last line schema hint (exit_attribution): `{schema_exit or 'n/a'}`")
    lines_out.append("- Emitter schema: `src/telemetry/alpaca_attribution_schema.py` SCHEMA_VERSION **1.2.0**")
    lines_out.append("")
    lines_out.append("## Rotated / archived (sample ls)")
    lines_out.append("```")
    lines_out.append(rot[0][:4000] if rot else "")
    lines_out.append("```")
    lines_out.append("")
    lines_out.append("## Append-only policy")
    lines_out.append("Per MEMORY_BANK: `exit_attribution.jsonl`, `attribution.jsonl`, `master_trade_log.jsonl` must not be truncated by rotation.")

    (AUDIT / "ALPACA_TELEMETRY_INVENTORY.md").write_text("\n".join(lines_out), encoding="utf-8")
    print("Wrote reports/audit/ALPACA_TELEMETRY_INVENTORY.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
