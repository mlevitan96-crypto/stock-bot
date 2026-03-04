#!/usr/bin/env python3
"""C2 shadow: classify good vetoes vs missed winners (counter-intel). Read-only; uses last387 blocked + PnL; writes state/shadow/C2_shadow.json and reports/audit/C2_SHADOW_RESULTS.md."""
from __future__ import annotations
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

def main() -> int:
    base = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    baseline_path = base / "reports" / "board" / "last387_comprehensive_review.json"
    if not baseline_path.exists():
        (base / "state" / "shadow").mkdir(parents=True, exist_ok=True)
        payload = {"shadow_id": "C2_shadow", "name": "Good vetoes vs missed winners", "error": "No last387 review", "would_admit_count": 0, "proxy_pnl_delta": None, "cohort": "last-387"}
        (base / "state" / "shadow" / "C2_shadow.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return 0
    data = json.loads(baseline_path.read_text(encoding="utf-8"))
    blocked_dist = data.get("blocked_trade_distribution") or {}
    pnl = data.get("pnl") or {}
    total_exits = pnl.get("total_exits") or 1
    total_pnl = pnl.get("total_pnl_attribution_usd") or 0
    avg = total_pnl / total_exits if total_exits else 0
    # C2: good vetoes = blocks that would have lost (we don't have per-block outcome); missed winners = blocks that would have won. Proxy: rank by count; opportunity cost proxy per reason.
    block_reason_counts = list(blocked_dist.items())
    opportunity_cost_proxy = {k: round(v * avg, 2) for k, v in block_reason_counts}
    payload = {
        "shadow_id": "C2_shadow",
        "name": "Good vetoes vs missed winners",
        "run_ts": datetime.now(timezone.utc).isoformat(),
        "would_admit_count": sum(blocked_dist.values()),
        "proxy_pnl_delta": round(sum(blocked_dist.values()) * avg, 2),
        "proxy_pnl_delta_label": "proxy",
        "win_rate_delta": None,
        "tail_risk_notes": ["Full C2 requires estimate_blocked_outcome per block; this is proxy by reason count * baseline avg PnL."],
        "cohort": "last-387",
        "block_reason_counts": blocked_dist,
        "opportunity_cost_proxy_by_reason": opportunity_cost_proxy,
    }
    (base / "state" / "shadow").mkdir(parents=True, exist_ok=True)
    (base / "state" / "shadow" / "C2_shadow.json").write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    (base / "reports" / "audit").mkdir(parents=True, exist_ok=True)
    (base / "reports" / "audit" / "C2_SHADOW_RESULTS.md").write_text(
        f"# C2 shadow results\n\nwould_admit_count (total blocked)={payload['would_admit_count']}\nproxy_pnl_delta={payload['proxy_pnl_delta']} (proxy)\nwin_rate_delta=N/A\ntail_risk: {payload['tail_risk_notes'][0]}\n",
        encoding="utf-8",
    )
    return 0

if __name__ == "__main__":
    sys.exit(main())
