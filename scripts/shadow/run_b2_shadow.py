#!/usr/bin/env python3
"""B2 shadow: remove early signal_decay exits. Read-only; last-387; writes state/shadow/B2_shadow.json and reports/audit/B2_SHADOW_RESULTS.md."""
from __future__ import annotations
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

def main() -> int:
    base = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    exit_path = base / "logs" / "exit_attribution.jsonl"
    if not exit_path.exists():
        (base / "state" / "shadow").mkdir(parents=True, exist_ok=True)
        payload = {"shadow_id": "B2_shadow", "name": "Remove early signal_decay", "error": "No exit_attribution", "would_admit_count": 0, "proxy_pnl_delta": None, "cohort": "last-387"}
        (base / "state" / "shadow" / "B2_shadow.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return 0
    lines = [ln for ln in exit_path.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()]
    recent = lines[-387:] if len(lines) >= 387 else lines
    early_decay_count = 0
    pnls = []
    for ln in recent:
        try:
            r = json.loads(ln)
        except json.JSONDecodeError:
            continue
        reason = str(r.get("exit_reason") or r.get("close_reason") or "")
        if "signal_decay" in reason:
            h = r.get("time_in_trade_minutes") or r.get("hold_minutes")
            if h is not None and float(h) < 30:
                early_decay_count += 1
        p = r.get("pnl_usd") or r.get("pnl") or r.get("realized_pnl_usd")
        if p is not None:
            try:
                pnls.append(float(p))
            except (TypeError, ValueError):
                pass
    pnl_avg = (sum(pnls) / len(pnls)) if pnls else 0
    proxy_delta = round(-early_decay_count * pnl_avg, 2) if pnls else None
    payload = {
        "shadow_id": "B2_shadow",
        "name": "Remove early signal_decay exits",
        "run_ts": datetime.now(timezone.utc).isoformat(),
        "would_admit_count": early_decay_count,
        "proxy_pnl_delta": proxy_delta,
        "proxy_pnl_delta_label": "proxy",
        "win_rate_delta": None,
        "tail_risk_notes": ["Removing early decay may hold losers longer."],
        "cohort": "last-387",
    }
    (base / "state" / "shadow").mkdir(parents=True, exist_ok=True)
    (base / "state" / "shadow" / "B2_shadow.json").write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    (base / "reports" / "audit").mkdir(parents=True, exist_ok=True)
    (base / "reports" / "audit" / "B2_SHADOW_RESULTS.md").write_text(
        f"# B2 shadow results\n\nwould_admit_count (early signal_decay <30min)={early_decay_count}\nproxy_pnl_delta={proxy_delta} (proxy)\nwin_rate_delta=N/A\ntail_risk: {payload['tail_risk_notes'][0]}\n",
        encoding="utf-8",
    )
    return 0

if __name__ == "__main__":
    sys.exit(main())
