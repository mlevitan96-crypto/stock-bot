#!/usr/bin/env python3
"""A1 shadow: relax displacement_blocked. Read-only; writes state/shadow/A1_shadow.json and reports/audit/A1_SHADOW_RESULTS.md."""
from __future__ import annotations
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

def main() -> int:
    base = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    baseline_path = base / "reports" / "board" / "last387_comprehensive_review.json"
    if not baseline_path.exists():
        print("last387_comprehensive_review.json not found", file=sys.stderr)
        return 1
    data = json.loads(baseline_path.read_text(encoding="utf-8"))
    blocked = data.get("blocked_trade_distribution") or {}
    pnl = data.get("pnl") or {}
    n = blocked.get("displacement_blocked", 0)
    total_exits = pnl.get("total_exits") or 1
    total_pnl = pnl.get("total_pnl_attribution_usd") or 0
    avg = total_pnl / total_exits if total_exits else 0
    payload = {
        "shadow_id": "A1_shadow",
        "name": "Relax displacement_blocked",
        "run_ts": datetime.now(timezone.utc).isoformat(),
        "would_admit_count": n,
        "proxy_pnl_delta": round(n * avg, 2),
        "proxy_pnl_delta_label": "proxy",
        "win_rate_delta": None,
        "tail_risk_notes": ["Relaxing displacement may increase drawdown; capacity unchanged."],
        "cohort": "last-387",
    }
    (base / "state" / "shadow").mkdir(parents=True, exist_ok=True)
    (base / "state" / "shadow" / "A1_shadow.json").write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    audit = base / "reports" / "audit"
    audit.mkdir(parents=True, exist_ok=True)
    audit.joinpath("A1_SHADOW_RESULTS.md").write_text(
        f"# A1 shadow results\n\nwould_admit_count={n}\nproxy_pnl_delta={payload['proxy_pnl_delta']} (proxy)\nwin_rate_delta=N/A\ntail_risk: {payload['tail_risk_notes'][0]}\n",
        encoding="utf-8",
    )
    return 0

if __name__ == "__main__":
    sys.exit(main())
