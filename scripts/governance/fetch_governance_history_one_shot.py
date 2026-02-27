#!/usr/bin/env python3
"""One-shot: run a script on droplet that outputs governance history JSON; print summary."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

def main() -> int:
    from droplet_client import DropletClient

    # Single SSH: list run dirs and for each output decision + overlay (parse with --- markers)
    with DropletClient() as c:
        cmd = (
            "cd /root/stock-bot && for d in $(ls -td reports/equity_governance/equity_governance_* 2>/dev/null | head -15); do "
            "echo DIR:$d; cat \"$d/lock_or_revert_decision.json\" 2>/dev/null || echo '{}'; "
            "echo '---OV---'; cat \"$d/overlay_config.json\" 2>/dev/null || echo '{}'; echo '---END---'; done"
        )
        out, err, rc = c._execute(cmd, timeout=45)
    if rc != 0:
        print("Droplet command failed:", err or out)
        return 1

    # Parse DIR:... {...} ---OV--- {...} ---END--- blocks (decision JSON can be multiline)
    runs = []
    raw = (out or "").strip()
    for blk in raw.split("---END---"):
        blk = blk.strip()
        if not blk or "DIR:" not in blk:
            continue
        run_tag = "?"
        if "DIR:" in blk:
            first = blk.split("\n")[0]
            if first.startswith("DIR:"):
                run_tag = first[4:].strip().split("/")[-1]
        if "---OV---" not in blk:
            continue
        pre, rest = blk.split("---OV---", 1)
        pre_lines = pre.strip().split("\n")
        dec_json = "\n".join(pre_lines[1:]).strip() if len(pre_lines) > 1 else "{}"
        ov_json = rest.split("---")[0].strip() if "---" in rest else rest.strip()
        try:
            decision = json.loads(dec_json) if dec_json else {}
            overlay = json.loads(ov_json) if ov_json else {}
        except Exception:
            decision = {}
            overlay = {}
        ch = overlay.get("change") or {}
        sig_delta = ch.get("signal_weight_delta") or {}
        runs.append({
            "run": run_tag,
            "decision": decision.get("decision", ""),
            "lever": overlay.get("lever", ""),
            "min_exec_score": ch.get("min_exec_score"),
            "signal_weight_delta": list(sig_delta.keys()) if sig_delta else [],
            "base_expectancy": (decision.get("baseline") or {}).get("expectancy_per_trade"),
            "cand_expectancy": (decision.get("candidate") or {}).get("expectancy_per_trade"),
            "base_win_rate": (decision.get("baseline") or {}).get("win_rate"),
            "cand_win_rate": (decision.get("candidate") or {}).get("win_rate"),
        })

    # Fetch signal_effectiveness in second call
    sig_eff = {}
    with DropletClient() as c:
        out2, _, _ = c._execute("cat /root/stock-bot/reports/effectiveness_baseline_blame/signal_effectiveness.json 2>/dev/null", timeout=10)
        if out2 and out2.strip():
            try:
                sig_eff = json.loads(out2.strip())
            except Exception:
                pass

    print("=== GOVERNANCE RUN HISTORY (newest first) ===\n")
    locked = []
    reverted = []
    for r in runs:
        tag = (r.get("run") or "")[:36]
        dec = r.get("decision", "")
        lev = r.get("lever", "")
        sigs = r.get("signal_weight_delta") or []
        min_sc = r.get("min_exec_score")
        if sigs:
            lever_desc = f"entry(down_weight:{sigs})"
        elif min_sc is not None:
            lever_desc = f"entry(min_exec_score={min_sc})"
        elif lev == "exit":
            lever_desc = "exit"
        else:
            lever_desc = lev or "entry"
        b_exp = r.get("base_expectancy")
        c_exp = r.get("cand_expectancy")
        b_wr = r.get("base_win_rate")
        c_wr = r.get("cand_win_rate")
        print(f"{tag} | {dec} | {lever_desc} | base_exp={b_exp} cand_exp={c_exp} | base_wr={b_wr} cand_wr={c_wr}")
        if dec == "LOCK":
            locked.append(r)
        elif dec == "REVERT":
            reverted.append(r)

    print("\n=== SUMMARY ===")
    print(f"Runs with decision: {len([r for r in runs if r.get('decision')])}")
    print(f"LOCK (passed): {len(locked)}")
    print(f"REVERT (dismissed): {len(reverted)}")

    print("\n=== DISMISSED (REVERT) — levers that worsened metrics ===")
    for r in reverted:
        sigs = r.get("signal_weight_delta") or []
        if sigs:
            desc = f"down_weight {sigs}"
        elif r.get("min_exec_score") is not None:
            desc = f"min_exec_score={r.get('min_exec_score')}"
        else:
            desc = "exit_tweak"
        print(f"  - {desc} (cand_exp={r.get('cand_expectancy')}, base_exp={r.get('base_expectancy')})")

    print("\n=== PASSED (LOCK) — levers that met stopping checks ===")
    if not locked:
        print("  (none yet)")
    else:
        for r in locked:
            sigs = r.get("signal_weight_delta") or []
            if sigs:
                desc = f"down_weight {sigs}"
            elif r.get("min_exec_score") is not None:
                desc = f"min_exec_score={r.get('min_exec_score')}"
            else:
                desc = "exit_tweak"
            print(f"  - {desc}")

    print("\n=== CURRENT BASELINE: TOP HARMFUL SIGNALS (worst win_rate / pnl) ===")
    if sig_eff and isinstance(sig_eff, dict):
        as_list = [
            (sid, v.get("trade_count"), v.get("win_rate"), v.get("avg_pnl"), v.get("avg_profit_giveback"))
            for sid, v in sig_eff.items()
            if isinstance(v, dict) and (v.get("trade_count") or 0) >= 3
        ]
        as_list.sort(key=lambda x: (x[2] or 1, (x[3] or 0)))
        for sid, tc, wr, pnl, gb in as_list[:15]:
            print(f"  {sid}: trades={tc} win_rate={wr} avg_pnl={pnl} giveback={gb}")
    else:
        print("  (no signal_effectiveness)")

    print("\n=== POSITIVE IMPACT (best win_rate / pnl in baseline) ===")
    if sig_eff and isinstance(sig_eff, dict):
        as_list = [
            (sid, v.get("trade_count"), v.get("win_rate"), v.get("avg_pnl"))
            for sid, v in sig_eff.items()
            if isinstance(v, dict) and (v.get("trade_count") or 0) >= 3
        ]
        as_list.sort(key=lambda x: (-(x[2] or 0), -((x[3]) or 0)))
        for sid, tc, wr, pnl in as_list[:10]:
            print(f"  {sid}: trades={tc} win_rate={wr} avg_pnl={pnl}")
    else:
        print("  (no data)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
