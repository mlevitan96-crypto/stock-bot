#!/usr/bin/env python3
"""B1 shadow: extend minimum hold +15 min. Read-only; uses last-387 exits; writes state/shadow/B1_shadow.json and reports/audit/B1_SHADOW_RESULTS.md."""
from __future__ import annotations
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

def main() -> int:
    base = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    exit_path = base / "logs" / "exit_attribution.jsonl"
    baseline_path = base / "reports" / "board" / "last387_comprehensive_review.json"
    if not exit_path.exists():
        (base / "state" / "shadow").mkdir(parents=True, exist_ok=True)
        payload = {"shadow_id": "B1_shadow", "name": "Extend min hold +15 min", "error": "No exit_attribution", "would_admit_count": 0, "proxy_pnl_delta": None, "cohort": "last-387"}
        (base / "state" / "shadow" / "B1_shadow.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return 0
    lines = [ln for ln in exit_path.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()]
    recent = lines[-387:] if len(lines) >= 387 else lines
    exits = []
    for ln in recent:
        try:
            exits.append(json.loads(ln))
        except json.JSONDecodeError:
            continue
    hold_below_15 = 0
    pnls = []
    for r in exits:
        h = r.get("time_in_trade_minutes") or r.get("hold_minutes")
        if h is not None and float(h) < 15:
            hold_below_15 += 1
        p = r.get("pnl_usd") or r.get("pnl") or r.get("realized_pnl_usd")
        if p is not None:
            try:
                pnls.append(float(p))
            except (TypeError, ValueError):
                pass
    # Proxy: excluding those exits would change count; assume avg PnL of excluded = baseline avg
    pnl_avg = (sum(pnls) / len(pnls)) if pnls else 0
    proxy_delta = round(-hold_below_15 * pnl_avg, 2) if pnls else None
    payload = {
        "shadow_id": "B1_shadow",
        "name": "Extend minimum hold +15 min",
        "run_ts": datetime.now(timezone.utc).isoformat(),
        "would_admit_count": hold_below_15,
        "proxy_pnl_delta": proxy_delta,
        "proxy_pnl_delta_label": "proxy",
        "win_rate_delta": None,
        "tail_risk_notes": ["Extending min hold may increase drawdown in fast reversals."],
        "cohort": "last-387",
    }
    (base / "state" / "shadow").mkdir(parents=True, exist_ok=True)
    (base / "state" / "shadow" / "B1_shadow.json").write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    (base / "reports" / "audit").mkdir(parents=True, exist_ok=True)
    (base / "reports" / "audit" / "B1_SHADOW_RESULTS.md").write_text(
        f"# B1 shadow results\n\nwould_admit_count (exits below 15min)={hold_below_15}\nproxy_pnl_delta={proxy_delta} (proxy)\nwin_rate_delta=N/A\ntail_risk: {payload['tail_risk_notes'][0]}\n",
        encoding="utf-8",
    )
    return 0

if __name__ == "__main__":
    sys.exit(main())
