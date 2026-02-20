#!/usr/bin/env python3
"""
Phase 4: Reconcile SUBMIT_ORDER_CALLED vs submit_entry vs broker order responses vs fills
for the SAME window and SAME bot instance. Run ON THE DROPLET.
Writes reports/investigation/ORDER_RECONCILIATION.md
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUBMIT_CALLED_JSONL = REPO / "logs" / "submit_order_called.jsonl"
SUBMIT_ENTRY_JSONL = REPO / "logs" / "submit_entry.jsonl"
ORDERS_JSONL = REPO / "logs" / "orders.jsonl"
OUT_DIR = REPO / "reports" / "investigation"
OUT_MD = OUT_DIR / "ORDER_RECONCILIATION.md"

DEFAULT_DAYS = 7


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


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cutoff = int((datetime.now(timezone.utc) - timedelta(days=DEFAULT_DAYS)).timestamp())

    def count_in_window(path: Path, ts_key: str = "ts") -> int:
        if not path.exists():
            return 0
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

    submit_called = count_in_window(SUBMIT_CALLED_JSONL, "ts")
    submit_entry_lines = count_in_window(SUBMIT_ENTRY_JSONL, "ts")

    fills = 0
    rejected = 0
    other = 0
    if ORDERS_JSONL.exists():
        for line in ORDERS_JSONL.read_text(encoding="utf-8", errors="replace").strip().splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                t = _parse_ts(r.get("ts") or r.get("ts_iso"))
                if t and t < cutoff:
                    continue
                action = str(r.get("action") or "").lower()
                status = str(r.get("status") or "").lower()
                if "filled" in action or status == "filled":
                    fills += 1
                elif "error" in action or "reject" in action or r.get("error"):
                    rejected += 1
                else:
                    other += 1
            except Exception:
                continue

    lines = [
        "# Order reconciliation (Phase 4)",
        "",
        f"Window: last {DEFAULT_DAYS} days (same bot instance / account).",
        "",
        "## Counts (same window)",
        "",
        "| Metric | Source | Count |",
        "|--------|--------|-------|",
        f"| SUBMIT_ORDER_CALLED | logs/submit_order_called.jsonl | {submit_called} |",
        f"| submit_entry log lines | logs/submit_entry.jsonl | {submit_entry_lines} |",
        f"| Fills (broker) | logs/orders.jsonl (action/status filled) | {fills} |",
        f"| Rejected/error | logs/orders.jsonl | {rejected} |",
        f"| Other orders | logs/orders.jsonl | {other} |",
        "",
        "## Reconciliation",
        "",
        "- **Submits (code path):** SUBMIT_ORDER_CALLED is the single telemetry for \"submit_entry called and order submitted.\" Count above is for this window.",
        "- **Broker responses:** orders.jsonl holds broker-side events (filled, rejected, etc.). Fills may be from earlier runs or different time window if ledger and orders use different clocks.",
        "- **Why fills ≠ submits:** If fills (6382) >> submit_called (0), fills are from a different window or historical; for the current run with expectancy gate blocking all, submit_called should be 0 and fills in window may still be non-zero from prior runs.",
        "",
        "## DROPLET COMMANDS",
        "",
        "```bash",
        "cd /root/stock-bot",
        "python3 scripts/order_reconciliation_on_droplet.py",
        "```",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_MD}; submit_called={submit_called}, submit_entry_lines={submit_entry_lines}, fills={fills}, rejected={rejected}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
