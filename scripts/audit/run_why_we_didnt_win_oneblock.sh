#!/usr/bin/env bash
# WHY WE DIDN'T WIN — one-block run ON DROPLET. Fix trace↔attribution join, then full forensic.
# Usage: from repo root on droplet: bash scripts/audit/run_why_we_didnt_win_oneblock.sh [DATE]
set -euo pipefail

DATE="${1:-2026-03-09}"

echo "=== PHASE 0 (SRE): droplet preflight + required sources ==="
ls -lah reports/state/exit_decision_trace.jsonl 2>/dev/null || true
ls -lah logs/exit_attribution.jsonl 2>/dev/null || true
ls -lah state/blocked_trades.jsonl 2>/dev/null || true
ls -lah logs/gate.jsonl 2>/dev/null || true

echo "=== PHASE 1 (SRE): diagnose trade_id mismatch ==="
python3 - <<PY
import json, itertools, re
from collections import Counter

def head_jsonl(path, n=50):
    out = []
    try:
        with open(path, "r") as f:
            for line in itertools.islice(f, n):
                line = line.strip()
                if not line: continue
                out.append(json.loads(line))
    except FileNotFoundError:
        pass
    return out

trace_path = "reports/state/exit_decision_trace.jsonl"
attr_path = "logs/exit_attribution.jsonl"
trace = head_jsonl(trace_path, 200)
attr = head_jsonl(attr_path, 200)

def pick_id(obj):
    for k in ("trade_id", "master_trade_id", "position_id", "id"):
        if k in obj and obj[k]:
            return str(obj[k])
    return None

trace_ids = [pick_id(x) for x in trace if pick_id(x)]
attr_ids = [pick_id(x) for x in attr if pick_id(x)]

def norm(s):
    if s is None: return None
    s = str(s).replace("+00:00", "Z")
    s = re.sub(r"\.([0-9]{1,6})Z$", "Z", s) if s.endswith("Z") else s
    return s

trace_norm = [norm(x) for x in trace_ids]
attr_norm = [norm(x) for x in attr_ids]
overlap = set(trace_norm).intersection(set(attr_norm))
print("trace sample ids:", trace_ids[:5])
print("attr  sample ids:", attr_ids[:5])
print("normalized overlap count (sampled):", len(overlap))
def prefix(s):
    return (s or "").split("_", 1)[0] or "NONE"
print("trace prefixes:", Counter(prefix(x) for x in trace_ids).most_common(10))
print("attr  prefixes:", Counter(prefix(x) for x in attr_ids).most_common(10))
PY

echo "=== PHASE 2+3: run full forensic (join + counterfactuals) ==="
python3 scripts/audit/run_why_we_didnt_win_forensic.py --date "$DATE" --fail-if-no-trace-above 0.20

echo "=== PHASE 4 (SRE): verify artifacts ==="
ls -lah reports/audit/INTRADAY_PORTFOLIO_UNREALIZED_CURVE_${DATE}.json
ls -lah reports/audit/INTRADAY_EXIT_LAG_AND_GIVEBACK_${DATE}.json
ls -lah reports/audit/INTRADAY_BLOCKED_COUNTERFACTUALS_${DATE}.json
ls -lah reports/audit/INTRADAY_JOIN_DIAGNOSTICS_${DATE}.json
ls -lah reports/audit/INTRADAY_FORENSIC_FULL_${DATE}.md
ls -lah reports/board/INTRADAY_BOARD_PACKET_${DATE}.md
ls -lah reports/audit/CSA_INTRADAY_VERDICT_${DATE}.json

echo "=== PHASE 6 (BOARD): board packet + forensic narrative ==="
sed -n '1,200p' reports/board/INTRADAY_BOARD_PACKET_${DATE}.md
sed -n '1,200p' reports/audit/INTRADAY_FORENSIC_FULL_${DATE}.md

echo "DONE: Join fixed, forensic interpretable, CSA verdict actionable."
