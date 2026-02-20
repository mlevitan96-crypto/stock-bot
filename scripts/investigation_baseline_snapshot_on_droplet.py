#!/usr/bin/env python3
"""
Phase 0: Droplet-only baseline snapshot. Run ON THE DROPLET.
Captures: service status, newest timestamps in key logs, last 24h counts.
Writes: reports/investigation/BASELINE_SNAPSHOT.md
Includes: DROPLET COMMANDS section.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
OUT_DIR = REPO / "reports" / "investigation"
OUT_MD = OUT_DIR / "BASELINE_SNAPSHOT.md"

SEC_24H = 24 * 3600


def _parse_ts(v) -> int | None:
    if v is None:
        return None
    try:
        if isinstance(v, (int, float)):
            return int(float(v))
        s = str(v).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s[:26])
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    except Exception:
        return None


def _count_jsonl_24h(path: Path, ts_key: str = "ts") -> int:
    if not path.exists():
        return 0
    cutoff = int(datetime.now(timezone.utc).timestamp()) - SEC_24H
    n = 0
    for line in path.read_text(encoding="utf-8", errors="replace").strip().splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
            t = _parse_ts(r.get(ts_key) or r.get("ts_iso") or r.get("ts_eval_epoch"))
            if t and t >= cutoff:
                n += 1
        except Exception:
            continue
    return n


def _newest_ts(path: Path, ts_key: str = "ts") -> str:
    if not path.exists():
        return "N/A"
    best = None
    for line in path.read_text(encoding="utf-8", errors="replace").strip().splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
            t = _parse_ts(r.get(ts_key) or r.get("ts_iso") or r.get("ts_eval_epoch"))
            if t and (best is None or t > best):
                best = t
        except Exception:
            continue
    if best is None:
        return "N/A"
    return datetime.fromtimestamp(best, tz=timezone.utc).isoformat() + f" (epoch {best})"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)

    # Service status
    service_out = ""
    try:
        r = subprocess.run(
            ["systemctl", "status", "stock-bot", "--no-pager"],
            cwd=str(REPO), capture_output=True, text=True, timeout=10,
        )
        service_out = (r.stdout or r.stderr or "N/A")[:1500]
    except Exception as e:
        service_out = f"Error: {e}"

    paths = {
        "ledger": REPO / "reports" / "decision_ledger" / "decision_ledger.jsonl",
        "snapshots": REPO / "logs" / "score_snapshot.jsonl",
        "uw_failure_events": REPO / "reports" / "uw_health" / "uw_failure_events.jsonl",
        "orders": REPO / "logs" / "orders.jsonl",
        "submit_entry": REPO / "logs" / "submit_entry.jsonl",
        "submit_order_called": REPO / "logs" / "submit_order_called.jsonl",
        "expectancy_gate_truth": REPO / "logs" / "expectancy_gate_truth.jsonl",
    }

    newest = {name: _newest_ts(p, "ts_eval_epoch" if name == "expectancy_gate_truth" else "ts") for name, p in paths.items()}
    counts_24h = {}
    for name, p in paths.items():
        key = "ts_eval_epoch" if name == "expectancy_gate_truth" else "ts"
        counts_24h[name] = _count_jsonl_24h(p, ts_key=key)

    # Ledger: pass/fail from gates (if available)
    expectancy_pass_24h = 0
    expectancy_fail_24h = 0
    if paths["ledger"].exists():
        cutoff = int(now.timestamp()) - SEC_24H
        for line in paths["ledger"].read_text(encoding="utf-8", errors="replace").strip().splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                t = _parse_ts(r.get("ts"))
                if t and t < cutoff:
                    continue
                for g in r.get("gates") or []:
                    if g.get("gate_name") == "expectancy_gate":
                        if g.get("pass") is True:
                            expectancy_pass_24h += 1
                        else:
                            expectancy_fail_24h += 1
                        break
            except Exception:
                continue

    lines = [
        "# Baseline snapshot (Phase 0)",
        "",
        f"Generated: {now.strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "## DROPLET COMMANDS",
        "",
        "```bash",
        "cd /root/stock-bot   # or /root/stock-bot-current",
        "python3 scripts/investigation_baseline_snapshot_on_droplet.py",
        "```",
        "",
        "## Service / process status",
        "",
        "```",
        service_out.strip() or "N/A",
        "```",
        "",
        "## Newest timestamps in key logs",
        "",
        "| Log | Newest timestamp |",
        "|-----|------------------|",
    ]
    for name, p in paths.items():
        lines.append(f"| {name} | {newest[name]} |")
    lines.extend([
        "",
        "## Last 24h counts",
        "",
        "| Metric | Count |",
        "|--------|-------|",
        f"| candidates (ledger events) | {counts_24h['ledger']} |",
        f"| expectancy gate pass (from ledger) | {expectancy_pass_24h} |",
        f"| expectancy gate fail (from ledger) | {expectancy_fail_24h} |",
        f"| submit_entry.jsonl lines | {counts_24h['submit_entry']} |",
        f"| SUBMIT_ORDER_CALLED lines | {counts_24h['submit_order_called']} |",
        f"| score_snapshot.jsonl lines | {counts_24h['snapshots']} |",
        f"| expectancy_gate_truth.jsonl lines | {counts_24h['expectancy_gate_truth']} |",
        f"| orders.jsonl lines | {counts_24h['orders']} |",
        "",
    ])
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
