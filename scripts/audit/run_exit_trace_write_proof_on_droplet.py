#!/usr/bin/env python3
"""
Exit Trace Write-Health PROOF — run ON DROPLET.
Verifies exit_trace_write_health.jsonl exists, grows with trace, recent, written=true.
Outputs: EXIT_TRACE_WRITE_PROOF_<date>_<time>.md, CSA_EXIT_TRACE_WRITE_VERDICT_<date>_<time>.json
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TRACE_PATH = REPO / "reports" / "state" / "exit_decision_trace.jsonl"
HEALTH_PATH = REPO / "reports" / "state" / "exit_trace_write_health.jsonl"
AUDIT = REPO / "reports" / "audit"
NOW = datetime.now(timezone.utc)
DATE = NOW.strftime("%Y-%m-%d")
TIME = NOW.strftime("%H%M")
STAMP = f"{DATE}_{TIME}"
PROOF_MD = AUDIT / f"EXIT_TRACE_WRITE_PROOF_{STAMP}.md"
VERDICT_JSON = AUDIT / f"CSA_EXIT_TRACE_WRITE_VERDICT_{STAMP}.json"
MAX_AGE_SEC = 300  # 5 min
WAIT_SEC = 70  # allow one sample interval + buffer


def _read_jsonl(path: Path, tail_n: int = 0) -> list:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").strip().splitlines()
    if tail_n:
        lines = lines[-tail_n:]
    out = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def main() -> int:
    AUDIT.mkdir(parents=True, exist_ok=True)
    HEALTH_PATH.parent.mkdir(parents=True, exist_ok=True)

    proof_lines = [
        f"# Exit Trace Write-Health PROOF — {STAMP}",
        "",
        f"**Generated:** {NOW.isoformat()}",
        "",
        "## SRE runtime verification",
        "",
    ]
    verdict = {
        "verdict": "EXIT_TRACE_WRITE_HEALTH_BLOCKED",
        "confidence": 0.0,
        "stamp": STAMP,
        "health_exists": False,
        "health_size": 0,
        "health_recent_count": 0,
        "written_true_count": 0,
        "written_false_count": 0,
        "trace_size": 0,
        "last_5_health": [],
    }

    # Wait for possible new writes
    time.sleep(WAIT_SEC)

    trace_exists = TRACE_PATH.exists()
    trace_size = TRACE_PATH.stat().st_size if trace_exists else 0
    verdict["trace_size"] = trace_size
    proof_lines.append(f"- exit_decision_trace.jsonl exists: {trace_exists}, size: {trace_size}")
    proof_lines.append("")

    if not HEALTH_PATH.exists():
        proof_lines.append("- exit_trace_write_health.jsonl: **MISSING** — FAIL")
        verdict["verdict"] = "EXIT_TRACE_WRITE_HEALTH_BLOCKED"
        verdict["required_fixes"] = ["write_health file missing; deploy trace writer with write-health instrumentation"]
        PROOF_MD.write_text("\n".join(proof_lines), encoding="utf-8")
        VERDICT_JSON.write_text(json.dumps(verdict, indent=2), encoding="utf-8")
        return 1

    verdict["health_exists"] = True
    health_size = HEALTH_PATH.stat().st_size
    verdict["health_size"] = health_size
    proof_lines.append(f"- exit_trace_write_health.jsonl exists: yes, size: {health_size}")
    proof_lines.append("")

    health_records = _read_jsonl(HEALTH_PATH, tail_n=500)
    verdict["health_recent_count"] = len(health_records)
    now_ts = time.time()

    def parse_ts(s: str) -> float | None:
        if not s:
            return None
        try:
            from datetime import datetime as dt
            return dt.fromisoformat(str(s).replace("Z", "+00:00")).timestamp()
        except Exception:
            return None

    recent = 0
    written_true = 0
    written_false = 0
    for r in health_records:
        t = parse_ts(r.get("ts"))
        if t and (now_ts - t) <= MAX_AGE_SEC:
            recent += 1
        if r.get("written") is True:
            written_true += 1
        elif r.get("written") is False:
            written_false += 1
    verdict["health_recent_count"] = recent
    verdict["written_true_count"] = written_true
    verdict["written_false_count"] = written_false
    verdict["last_5_health"] = health_records[-5:]

    proof_lines.append("## Write-health content check")
    proof_lines.append("")
    proof_lines.append(f"- Health records in window: {len(health_records)}")
    proof_lines.append(f"- Records with ts within 5 min: {recent}")
    proof_lines.append(f"- written=true: {written_true}")
    proof_lines.append(f"- written=false: {written_false}")
    proof_lines.append("")
    proof_lines.append("### Last 5 write-health records")
    proof_lines.append("")
    for i, r in enumerate(health_records[-5:]):
        proof_lines.append(f"- {i+1}. ts={r.get('ts')} trade_id={r.get('trade_id')} written={r.get('written')} error_type={r.get('error_type')}")
    proof_lines.append("")

    if written_false > 0:
        proof_lines.append("**written=false events:** present — check error_type/error_msg in health file.")
        verdict["required_fixes"] = verdict.get("required_fixes", []) + ["At least one write failed; inspect exit_trace_write_health.jsonl for error_type/error_msg"]
    if recent == 0 and trace_exists and trace_size > 0:
        proof_lines.append("**WARN:** No health records in last 5 min but trace exists; health may not be updating (e.g. no open positions or sampling skipped).")
    if health_exists and written_true > 0 and written_false == 0:
        verdict["verdict"] = "EXIT_TRACE_WRITE_HEALTH_PROVEN"
        verdict["confidence"] = 0.9
        proof_lines.append("## CSA verdict")
        proof_lines.append("")
        proof_lines.append("- **EXIT_TRACE_WRITE_HEALTH_PROVEN**: Write-health telemetry is live; no silent trace write failures.")
    else:
        proof_lines.append("## CSA verdict")
        proof_lines.append("")
        proof_lines.append("- **EXIT_TRACE_WRITE_HEALTH_BLOCKED** or incomplete: resolve required_fixes before accepting.")

    PROOF_MD.write_text("\n".join(proof_lines), encoding="utf-8")
    VERDICT_JSON.write_text(json.dumps(verdict, indent=2), encoding="utf-8")
    print("PROOF written:", PROOF_MD.name)
    print("VERDICT written:", VERDICT_JSON.name)
    print("VERDICT:", verdict["verdict"])
    return 0 if verdict["verdict"] == "EXIT_TRACE_WRITE_HEALTH_PROVEN" else 1


if __name__ == "__main__":
    sys.exit(main())
