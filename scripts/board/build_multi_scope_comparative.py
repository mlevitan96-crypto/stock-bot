#!/usr/bin/env python3
"""
Build MULTI_SCOPE_COMPARATIVE_REVIEW.md and .json from all scope comprehensive reviews and A3 shadows.
Run on droplet after run_parallel_reviews_on_droplet.py.
Includes: learning/telemetry by scope, PnL by scope, blocked by scope, A3 deltas, stability vs regime, recommendation, persona verdicts.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

SCOPES = ["7d", "14d", "30d", "last100", "last387", "last750"]


def main() -> int:
    base = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    board = base / "reports" / "board"
    scenarios = board / "scenarios"
    out_json = board / "MULTI_SCOPE_COMPARATIVE_REVIEW.json"
    out_md = board / "MULTI_SCOPE_COMPARATIVE_REVIEW.md"
    board.mkdir(parents=True, exist_ok=True)

    by_scope = {}
    for scope in SCOPES:
        j = board / f"{scope}_comprehensive_review.json"
        a3 = scenarios / f"{scope}_A3_shadow.json"
        if not j.exists():
            by_scope[scope] = {"error": "missing comprehensive_review"}
            continue
        try:
            data = json.loads(j.read_text(encoding="utf-8"))
            learning = data.get("learning_telemetry") or {}
            pnl = data.get("pnl") or {}
            blocked = data.get("blocked_total") or 0
            blocked_dist = data.get("blocked_trade_distribution") or {}
            row = {
                "learning_telemetry": learning,
                "pnl": pnl,
                "blocked_total": blocked,
                "blocked_trade_distribution": blocked_dist,
                "scope_label": data.get("scope", scope),
            }
            if a3.exists():
                try:
                    a3_data = json.loads(a3.read_text(encoding="utf-8"))
                    row["a3_shadow"] = {
                        "additional_admitted_trades": a3_data.get("additional_admitted_trades"),
                        "estimated_pnl_delta_usd": a3_data.get("estimated_pnl_delta_usd"),
                        "estimated_pnl_delta_label": a3_data.get("estimated_pnl_delta_label", "proxy"),
                    }
                except Exception:
                    row["a3_shadow"] = None
            else:
                row["a3_shadow"] = None
            by_scope[scope] = row
        except Exception as e:
            by_scope[scope] = {"error": str(e)}

    # Which scope governs NEXT live decision: recommend last387 as baseline (board-grade)
    governing_scope = "last387"
    context_only = [s for s in SCOPES if s != governing_scope]
    recommendation = {
        "governing_scope_for_next_live_decision": governing_scope,
        "context_only_scopes": context_only,
        "rationale": "last387 is the agreed learning baseline; other scopes provide regime sensitivity and stability context.",
    }

    persona_verdicts = {
        "adversarial": "MULTI_SCOPE_COMPARATIVE_REVIEW shows A3 shadow deltas by scope; 7d/14d may be regime-sensitive. Recommend Hold A3 until 30d or last387 shadow is stable; do not advance to live paper test on 7d alone.",
        "quant": "Compare PnL and A3 estimated_pnl_delta across scopes; if last387 and 30d align, A3 is stable. Promote A3 to live paper test only if governing scope (last387) and 30d both show acceptable proxy delta.",
        "product_operator": "Use multi-scope view to prioritize which scope drives the next feature (e.g. exit vs gate). A3: Hold until Product agrees which scope is the success metric; then advance to live paper test.",
        "risk": "Stability vs regime: 7d/14d can swing; last387 and 30d are more stable. Discard A3 for live if any scope shows tail-risk note or large negative delta. Hold A3 until Risk signs off on governing scope.",
        "execution_sre": "Verify all scope artifacts exist on droplet and synthesis ran. Promote A3 only after SRE confirms no config/restart drift. Advance to live paper test only with rollback procedure documented.",
    }

    payload = {
        "generated_ts": datetime.now(timezone.utc).isoformat(),
        "by_scope": by_scope,
        "recommendation": recommendation,
        "persona_verdicts": persona_verdicts,
    }
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)
    print(f"Wrote {out_json}")

    md_lines = [
        "# Multi-scope comparative review",
        "",
        f"**Generated (UTC):** {payload['generated_ts']}",
        "",
        "## Learning & telemetry by scope",
        "",
    ]
    for scope in SCOPES:
        r = by_scope.get(scope) or {}
        if "error" in r:
            md_lines.append(f"- **{scope}:** {r['error']}")
        else:
            lt = r.get("learning_telemetry") or {}
            md_lines.append(f"- **{scope}:** telemetry_backed={lt.get('telemetry_backed')}, ready_for_replay={lt.get('ready_for_replay')}")
    md_lines.extend(["", "## PnL by scope", ""])
    for scope in SCOPES:
        r = by_scope.get(scope) or {}
        if "error" in r:
            continue
        pnl = r.get("pnl") or {}
        md_lines.append(f"- **{scope}:** total_pnl_attribution_usd={pnl.get('total_pnl_attribution_usd')}, total_exits={pnl.get('total_exits')}, win_rate={pnl.get('win_rate')}")
    md_lines.extend(["", "## Blocked trades by scope", ""])
    for scope in SCOPES:
        r = by_scope.get(scope) or {}
        if "error" in r:
            continue
        md_lines.append(f"- **{scope}:** blocked_total={r.get('blocked_total')}")
    md_lines.extend(["", "## A3 shadow deltas by scope", ""])
    for scope in SCOPES:
        r = by_scope.get(scope) or {}
        if "error" in r:
            continue
        a3 = r.get("a3_shadow")
        if a3:
            md_lines.append(f"- **{scope}:** additional_admitted={a3.get('additional_admitted_trades')}, estimated_pnl_delta_usd={a3.get('estimated_pnl_delta_usd')} ({a3.get('estimated_pnl_delta_label')})")
        else:
            md_lines.append(f"- **{scope}:** (no A3 shadow)")
    md_lines.extend([
        "",
        "## Stability vs regime sensitivity",
        "",
        "Time windows (7d, 14d, 30d) can be regime-sensitive; exit-count scopes (last100, last387, last750) smooth over time. Use last387 as governing baseline; 7d/14d as context for recent regime.",
        "",
        "## Recommendation",
        "",
        f"- **Scope governing NEXT live decision:** {recommendation['governing_scope_for_next_live_decision']}",
        f"- **Context-only scopes:** {', '.join(recommendation['context_only_scopes'])}",
        f"- **Rationale:** {recommendation['rationale']}",
        "",
        "## Board persona verdicts (A3: Promote / Hold / Discard; advance to live paper test?)",
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
