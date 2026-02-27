#!/usr/bin/env python3
"""Fetch full governance run history from droplet: decisions, overlays, signals tried."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))


def main() -> int:
    from droplet_client import DropletClient

    with DropletClient() as c:
        out, _, _ = c._execute(
            "for d in /root/stock-bot/reports/equity_governance/equity_governance_*; do [ -d \"$d\" ] && echo \"$d\"; done | sort -r",
            timeout=15,
        )
        dirs = [x.strip() for x in (out or "").splitlines() if x.strip()]

        runs = []
        for d in dirs[:25]:
            dec_raw, _, _ = c._execute(f"cat \"{d}/lock_or_revert_decision.json\" 2>/dev/null", timeout=5)
            ov_raw, _, _ = c._execute(f"cat \"{d}/overlay_config.json\" 2>/dev/null", timeout=5)
            rec_raw, _, _ = c._execute(f"cat \"{d}/recommendation.json\" 2>/dev/null", timeout=5)
            try:
                decision = json.loads(dec_raw) if dec_raw and dec_raw.strip() else {}
            except Exception:
                decision = {}
            try:
                overlay = json.loads(ov_raw) if ov_raw and ov_raw.strip() else {}
            except Exception:
                overlay = {}
            try:
                recommendation = json.loads(rec_raw) if rec_raw and rec_raw.strip() else {}
            except Exception:
                recommendation = {}

            lever = overlay.get("lever", "")
            ch = overlay.get("change", {})
            sig_delta = ch.get("signal_weight_delta") or {}
            min_sc = ch.get("min_exec_score")
            dec_val = decision.get("decision", "")
            base_exp = decision.get("baseline", {}).get("expectancy_per_trade")
            cand_exp = decision.get("candidate", {}).get("expectancy_per_trade")
            base_wr = decision.get("baseline", {}).get("win_rate")
            cand_wr = decision.get("candidate", {}).get("win_rate")
            top5 = recommendation.get("top5_harmful") or []
            run_tag = d.split("/")[-1] if "/" in d else d
            runs.append({
                "run": run_tag,
                "decision": dec_val,
                "lever": lever,
                "min_exec_score": min_sc,
                "signal_weight_delta": sig_delta,
                "base_expectancy": base_exp,
                "cand_expectancy": cand_exp,
                "base_win_rate": base_wr,
                "cand_win_rate": cand_wr,
                "top5_harmful_signal_ids": [h.get("signal_id") for h in top5[:5] if isinstance(h, dict)],
            })

        # Current baseline effectiveness (for signal list with impact)
        base_dir = "/root/stock-bot/reports/effectiveness_baseline_blame"
        sig_eff_raw, _, _ = c._execute(f"cat \"{base_dir}/signal_effectiveness.json\" 2>/dev/null", timeout=5)
        try:
            signal_effectiveness = json.loads(sig_eff_raw) if sig_eff_raw and sig_eff_raw.strip() else {}
        except Exception:
            signal_effectiveness = {}

    # Print report
    print("=== GOVERNANCE RUN HISTORY (newest first) ===\n")
    locked = []
    reverted = []
    for r in runs:
        tag = r["run"][:36]
        dec = r["decision"]
        lev = r["lever"]
        lever_desc = lev
        if r.get("signal_weight_delta"):
            lever_desc = f"entry(down_weight:{list(r['signal_weight_delta'].keys())})"
        elif r.get("min_exec_score") is not None:
            lever_desc = f"entry(min_exec_score={r['min_exec_score']})"
        elif lev == "exit":
            lever_desc = "exit"
        b_exp = r.get("base_expectancy")
        c_exp = r.get("cand_expectancy")
        b_wr = r.get("base_win_rate")
        c_wr = r.get("cand_win_rate")
        print(f"{tag} | {dec} | {lever_desc} | baseline_exp={b_exp} cand_exp={c_exp} | base_wr={b_wr} cand_wr={c_wr}")
        if dec == "LOCK":
            locked.append(r)
        elif dec == "REVERT":
            reverted.append(r)

    print("\n=== SUMMARY ===")
    print(f"Runs with decision: {len([r for r in runs if r['decision']])}")
    print(f"LOCK (passed): {len(locked)}")
    print(f"REVERT (dismissed): {len(reverted)}")

    print("\n=== DISMISSED (REVERT) — levers that worsened metrics ===")
    for r in reverted:
        desc = r.get("signal_weight_delta") and f"down_weight {list(r['signal_weight_delta'].keys())}" or (
            f"min_exec_score={r.get('min_exec_score')}" if r.get("min_exec_score") is not None else "exit_tweak"
        )
        print(f"  - {desc} (cand_exp={r.get('cand_expectancy')}, base_exp={r.get('base_expectancy')})")

    print("\n=== PASSED (LOCK) — levers that met stopping checks ===")
    if not locked:
        print("  (none yet)")
    else:
        for r in locked:
            desc = r.get("signal_weight_delta") and f"down_weight {list(r['signal_weight_delta'].keys())}" or (
                f"min_exec_score={r.get('min_exec_score')}" if r.get("min_exec_score") is not None else "exit_tweak"
            )
            print(f"  - {desc}")

    print("\n=== CURRENT BASELINE: TOP HARMFUL SIGNALS (by win_rate / pnl) ===")
    if signal_effectiveness:
        as_list = [
            (sid, v.get("trade_count"), v.get("win_rate"), v.get("avg_pnl"), v.get("avg_profit_giveback"))
            for sid, v in (signal_effectiveness.items() if isinstance(signal_effectiveness, dict) else [])
            if isinstance(v, dict) and (v.get("trade_count") or 0) >= 3
        ]
        as_list.sort(key=lambda x: (x[2] or 1, (x[3] or 0)))
        for sid, tc, wr, pnl, gb in as_list[:15]:
            print(f"  {sid}: trades={tc} win_rate={wr} avg_pnl={pnl} giveback={gb}")
    else:
        print("  (no signal_effectiveness.json)")

    print("\n=== POSITIVE IMPACT (signals with best win_rate / pnl in current baseline) ===")
    if signal_effectiveness and isinstance(signal_effectiveness, dict):
        as_list = [
            (sid, v.get("trade_count"), v.get("win_rate"), v.get("avg_pnl"))
            for sid, v in signal_effectiveness.items()
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
