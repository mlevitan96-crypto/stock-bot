#!/usr/bin/env python3
"""
Read reports/uw_health/uw_api_errors.jsonl and write reports/uw_health/uw_api_integrity_summary.md.
Counts by error type, top endpoints, top symbols (from params), first/last seen, remediation notes.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
ERRORS_JSONL = REPO / "reports" / "uw_health" / "uw_api_errors.jsonl"
OUT_MD = REPO / "reports" / "uw_health" / "uw_api_integrity_summary.md"


def _remediation(error_type: str) -> str:
    m = {
        "401": "Check UW_API_KEY; rotate if expired or invalid.",
        "403": "Forbidden: check API plan and endpoint access.",
        "404": "Endpoint path may have changed; verify OpenAPI spec.",
        "rate_limit": "Reduce call frequency or increase quota; respect Retry-After.",
        "5xx": "Upstream UW service issue; retry with backoff; check status page.",
        "http_error": "Check status code and response body; retry if transient.",
        "schema": "Response missing required structure; log response_body_truncated and fix parser.",
        "empty": "API returned 200 but empty data; check params (symbol, date range).",
        "exception": "Network/timeout or client error; check connectivity and timeout_s.",
    }
    return m.get(error_type, "Inspect response_body_truncated and caller; add remediation if recurring.")


def main() -> int:
    if not ERRORS_JSONL.exists():
        OUT_MD.parent.mkdir(parents=True, exist_ok=True)
        OUT_MD.write_text(
            "# UW API integrity summary\n\nNo UW API errors recorded (reports/uw_health/uw_api_errors.jsonl missing or empty).\n",
            encoding="utf-8",
        )
        print("No uw_api_errors.jsonl; wrote empty summary.")
        return 0

    records = []
    for line in ERRORS_JSONL.read_text(encoding="utf-8", errors="replace").strip().splitlines():
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except Exception:
            continue

    if not records:
        OUT_MD.parent.mkdir(parents=True, exist_ok=True)
        OUT_MD.write_text(
            "# UW API integrity summary\n\nNo UW API errors in log (file empty or unparseable).\n",
            encoding="utf-8",
        )
        print("No records in uw_api_errors.jsonl; wrote empty summary.")
        return 0

    by_type = Counter(r.get("uw_api_error_type") or "unknown" for r in records)
    by_endpoint = Counter(r.get("endpoint") or "?" for r in records)
    by_symbol: Counter[str] = Counter()
    for r in records:
        params = r.get("request_params") or {}
        sym = params.get("symbol") or params.get("symbols")
        if isinstance(sym, list):
            for s in sym:
                by_symbol[str(s)] += 1
        elif sym:
            by_symbol[str(sym)] += 1

    first_ts = min(float(r.get("ts") or 0) for r in records)
    last_ts = max(float(r.get("ts") or 0) for r in records)
    first_seen = datetime.fromtimestamp(first_ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    last_seen = datetime.fromtimestamp(last_ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        "# UW API integrity summary",
        "",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"Total errors: **{len(records)}**",
        f"First seen: {first_seen}",
        f"Last seen: {last_seen}",
        "",
        "## Counts by error type",
        "",
    ]
    for etype, count in by_type.most_common():
        lines.append(f"- **{etype}**: {count} — {_remediation(etype)}")
    lines.extend(["", "## Top endpoints (by error count)", ""])
    for ep, count in by_endpoint.most_common(10):
        lines.append(f"- `{ep}`: {count}")
    lines.extend(["", "## Top symbols (from request params)", ""])
    for sym, count in by_symbol.most_common(10):
        lines.append(f"- {sym}: {count}")
    lines.append("")
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_MD} ({len(records)} errors)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
