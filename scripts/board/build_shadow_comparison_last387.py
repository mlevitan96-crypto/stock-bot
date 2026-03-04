#!/usr/bin/env python3
"""
Build SHADOW_COMPARISON_LAST387.md and .json from all state/shadow/*.json (last-387 cohort).
Ranking by expected improvement, risk flags, nomination (Advance / Hold / Discard), persona verdicts.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

SHADOW_IDS = ["A1_shadow", "A2_shadow", "A3_shadow", "B1_shadow", "B2_shadow", "C2_shadow"]


def main() -> int:
    base = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    state_shadow = base / "state" / "shadow"
    board = base / "reports" / "board"
    board.mkdir(parents=True, exist_ok=True)
    out_json = board / "SHADOW_COMPARISON_LAST387.json"
    out_md = board / "SHADOW_COMPARISON_LAST387.md"

    baseline = {}
    review_path = base / "reports" / "board" / "last387_comprehensive_review.json"
    if review_path.exists():
        try:
            baseline = json.loads(review_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    shadows = {}
    for sid in SHADOW_IDS:
        path = state_shadow / f"{sid}.json"
        if not path.exists() and sid == "A3_shadow":
            path = state_shadow / "a3_expectancy_floor_shadow.json"
        if not path.exists():
            shadows[sid] = {"error": "missing"}
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            shadows[sid] = {"error": str(e)}
            continue
        if sid == "A3_shadow" and "would_admit_count" not in data:
            data["shadow_id"] = "A3_shadow"
            data["would_admit_count"] = data.get("additional_admitted_trades", 0)
            data["proxy_pnl_delta"] = data.get("estimated_pnl_delta_usd")
            data["proxy_pnl_delta_label"] = data.get("estimated_pnl_delta_label", "proxy")
        shadows[sid] = data

    # Rank by expected improvement (less negative proxy_pnl_delta = better)
    def rank_key(sid):
        s = shadows.get(sid) or {}
        if s.get("error"):
            return (999, 0)
        delta = s.get("proxy_pnl_delta")
        if delta is None:
            return (1, 0)
        return (0, delta)
    ranked = sorted(SHADOW_IDS, key=rank_key)

    risk_flags = {
        "A1_shadow": "Displacement relaxation increases exposure.",
        "A2_shadow": "Max positions increase concentration risk.",
        "A3_shadow": "Lower score floor may admit worse entries.",
        "B1_shadow": "Min hold extension may increase drawdown in fast reversals.",
        "B2_shadow": "Removing early signal_decay may hold losers longer.",
        "C2_shadow": "Full C2 requires per-block outcome; proxy only.",
    }

    # Nomination: best proxy delta that is least negative, or Hold/Discard
    nomination = "Hold and accumulate more shadow data"
    best = ranked[0] if ranked else None
    if best and not (shadows.get(best) or {}).get("error"):
        delta = (shadows.get(best) or {}).get("proxy_pnl_delta")
        if delta is not None and delta > -5:
            nomination = "Advance to live paper test"
        elif delta is not None and delta < -50:
            nomination = "Discard"
        else:
            nomination = "Hold and accumulate more shadow data"

    advance_candidate = best if nomination == "Advance to live paper test" else None

    persona_verdicts = {
        "adversarial": f"SHADOW_COMPARISON_LAST387 ranks shadows by proxy delta. Recommend advancing {advance_candidate or 'none'} only if shadow is least negative and tail-risk acceptable. Others: wait or discard.",
        "quant": f"Ranking by expected improvement (proxy). Advance {advance_candidate or 'one shadow'} to live paper test; validate with backtest. Others hold until more data.",
        "product_operator": f"Use comparison to pick ONE shadow for next live paper test: {advance_candidate or 'hold'}. Others wait for product prioritization.",
        "risk": f"Risk flags per shadow in comparison. Advance only {advance_candidate or 'none'} if risk signs off. Others hold or discard.",
        "execution_sre": f"Advance {advance_candidate or 'one shadow'} only after SRE confirms rollback procedure. Others: hold.",
    }

    payload = {
        "generated_ts": datetime.now(timezone.utc).isoformat(),
        "baseline_scope": "last-387",
        "shadows": shadows,
        "ranked_by_expected_improvement": ranked,
        "risk_flags": risk_flags,
        "nomination": nomination,
        "advance_to_live_paper_test_candidate": advance_candidate,
        "stability_notes": "Signal consistency across time windows TBD; last-387 is governing cohort.",
        "persona_verdicts": persona_verdicts,
    }
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)
    print(f"Wrote {out_json}")

    md_lines = [
        "# Shadow comparison (last-387)",
        "",
        f"**Generated (UTC):** {payload['generated_ts']}",
        "",
        "## Baseline vs each shadow delta",
        "",
    ]
    for sid in SHADOW_IDS:
        s = shadows.get(sid) or {}
        if s.get("error"):
            md_lines.append(f"- **{sid}:** {s['error']}")
        else:
            md_lines.append(f"- **{sid}:** would_admit={s.get('would_admit_count')}, proxy_pnl_delta={s.get('proxy_pnl_delta')} ({s.get('proxy_pnl_delta_label', 'proxy')})")
    md_lines.extend([
        "",
        "## Ranking by expected improvement",
        "",
    ] + [f"{i+1}. {s}" for i, s in enumerate(ranked)] + [
        "",
        "## Risk flags per shadow",
        "",
    ] + [f"- **{k}:** {v}" for k, v in risk_flags.items()] + [
        "",
        "## Stability notes",
        "",
        payload["stability_notes"],
        "",
        "## Nomination",
        "",
        f"- **{nomination}**",
        f"- Advance to live paper test candidate: {advance_candidate or 'none'}",
        "",
        "## Board persona verdicts",
        "",
    ])
    for persona, text in persona_verdicts.items():
        md_lines.append(f"### {persona.replace('_', ' ').title()}")
        md_lines.append("")
        md_lines.append(text)
        md_lines.append("")
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    print(f"Wrote {out_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
