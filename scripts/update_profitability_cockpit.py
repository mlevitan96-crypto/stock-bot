#!/usr/bin/env python3
"""
Update the Profitability Cockpit dashboard.
Ingests CSA, trade state, governance, SRE, and board artifacts; overwrites reports/board/PROFITABILITY_COCKPIT.md.
No trading logic; read-only summarization.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
AUDIT = REPO / "reports" / "audit"
BOARD = REPO / "reports" / "board"
STATE = REPO / "reports" / "state"
COCKPIT_PATH = BOARD / "PROFITABILITY_COCKPIT.md"

# How recent (seconds) CSA_VERDICT_LATEST must be to consider CSA "live"
CSA_RECENT_SECONDS = 7 * 24 * 3600  # 7 days


def _load_json(path: Path, default: dict | None = None) -> dict:
    if default is None:
        default = {}
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _load_text(path: Path, default: str = "") -> str:
    if not path.exists():
        return default
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return default


def _ingest() -> dict:
    """Phase 1: load all artifacts and compute derived flags."""
    data = {
        "csa_verdict_latest": {},
        "csa_verdicts": [],
        "csa_findings_md": "",
        "csa_board_mds": [],
        "trade_csa_state": {},
        "governance": {},
        "sre_status": {},
        "shadow_comparison": {},
        "board_review": {},
    }

    # CSA verdict latest
    latest = AUDIT / "CSA_VERDICT_LATEST.json"
    data["csa_verdict_latest"] = _load_json(latest)

    # All CSA verdict JSONs (for mission list)
    for f in AUDIT.glob("CSA_VERDICT_*.json"):
        if f.name == "CSA_VERDICT_LATEST.json":
            continue
        try:
            data["csa_verdicts"].append(_load_json(f))
        except Exception:
            pass

    # Latest CSA findings (match mission_id from verdict latest)
    mission_id = data["csa_verdict_latest"].get("mission_id", "")
    if mission_id:
        findings_path = AUDIT / f"CSA_FINDINGS_{mission_id}.md"
        data["csa_findings_md"] = _load_text(findings_path)
    if not data["csa_findings_md"]:
        # Fallback: any CSA_FINDINGS_*.md (most recent by name)
        for f in sorted(AUDIT.glob("CSA_FINDINGS_*.md"), reverse=True):
            data["csa_findings_md"] = _load_text(f)
            break

    # CSA board markdowns
    for f in BOARD.glob("CSA_*.md"):
        data["csa_board_mds"].append({"name": f.name, "content": _load_text(f)})

    # Trade CSA state: production (reports/state/TRADE_CSA_STATE.json) first, then test subdir
    state_file = STATE / "TRADE_CSA_STATE.json"
    if state_file.exists():
        data["trade_csa_state"] = _load_json(state_file)
    else:
        test_state = STATE / "test_csa_100" / "TRADE_CSA_STATE.json"
        if test_state.exists():
            data["trade_csa_state"] = _load_json(test_state)

    # Governance
    data["governance"] = _load_json(AUDIT / "GOVERNANCE_AUTOMATION_STATUS.json")
    # SRE
    data["sre_status"] = _load_json(AUDIT / "SRE_STATUS.json")
    # Shadow comparison (promotable / nomination)
    data["shadow_comparison"] = _load_json(BOARD / "SHADOW_COMPARISON_LAST387.json")
    # Board review (blocked distribution, etc.)
    for name in ["last387_comprehensive_review.json", "30d_comprehensive_review.json"]:
        p = BOARD / name
        if p.exists():
            data["board_review"] = _load_json(p)
            break

    # Derived: CSA live?
    gen_ts = data["csa_verdict_latest"].get("generated_ts") or ""
    csa_live = False
    try:
        if gen_ts:
            # Parse ISO8601 with optional Z or +00:00
            ts = gen_ts.replace("Z", "+00:00")
            if "+" in ts or ts.count("-") > 2:
                dt = datetime.fromisoformat(ts)
            else:
                dt = datetime.fromisoformat(ts + "+00:00")
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            age = (datetime.now(timezone.utc) - dt).total_seconds()
            csa_live = age >= 0 and age <= CSA_RECENT_SECONDS
    except Exception:
        csa_live = bool(data["csa_verdict_latest"].get("mission_id"))
    data["csa_live"] = csa_live

    # Derived: 100-trade trigger wired?
    state = data["trade_csa_state"]
    total = state.get("total_trade_events", 0)
    last_csa = state.get("last_csa_trade_count", 0)
    data["trigger_wired"] = total >= 0 and (last_csa % 100 == 0 or last_csa == 0)
    data["total_trade_events"] = total
    data["last_csa_trade_count"] = last_csa
    data["trades_until_next"] = (100 - (total % 100)) if total > 0 else 100
    data["trades_since_last_csa"] = total - last_csa if last_csa else total

    # Weekly review (latest weekly ledger summary + packet)
    weekly_date = ""
    ledger_glob = sorted(AUDIT.glob("WEEKLY_TRADE_DECISION_LEDGER_SUMMARY_*.json"), reverse=True)
    if ledger_glob:
        try:
            weekly_ledger = json.loads(ledger_glob[0].read_text(encoding="utf-8"))
            weekly_date = weekly_ledger.get("date", "")
            data["weekly_review"] = {
                "date": weekly_date,
                "executed_count": weekly_ledger.get("executed_count"),
                "blocked_count": weekly_ledger.get("blocked_count"),
                "counter_intel_blocked_count": weekly_ledger.get("counter_intel_blocked_count"),
                "board_packet_path": f"reports/board/CSA_WEEKLY_REVIEW_{weekly_date}_BOARD_PACKET.md",
                "top_promotable": (data.get("shadow_comparison") or {}).get("ranked_by_expected_improvement") or [],
                "top_profit_leaks": (data.get("csa_verdict_latest") or {}).get("value_leaks") or [],
            }
        except Exception:
            data["weekly_review"] = {}
    else:
        data["weekly_review"] = {}

    return data


def _render_cockpit(data: dict) -> str:
    """Phase 2: render PROFITABILITY_COCKPIT.md content."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    v = data["csa_verdict_latest"]
    mission_id = v.get("mission_id", "—")
    gen_ts = v.get("generated_ts", "—")
    verdict = v.get("verdict", "—")
    confidence = v.get("confidence", "—")
    csa_status = "ok" if data["csa_live"] and verdict in ("PROCEED", "HOLD") else ("degraded" if data["csa_live"] else "failed")

    lines = [
        f"# Profitability Cockpit — {now}",
        "",
        "## 1. CSA Status",
        f"- **Last CSA mission:** {mission_id}",
        f"- **Last CSA run:** {gen_ts}",
        f"- **CSA overall status:** {csa_status}",
        f"- **Trades since last CSA:** {data['trades_since_last_csa']}",
        f"- **Trades until next CSA review:** {data['trades_until_next']}",
        f"- **100-trade trigger wired:** " + ("yes" if data["trigger_wired"] else "no (or state missing)"),
        "",
        "## 2. Promotable Items",
        "",
    ]

    # Promotable from shadow comparison
    shadow = data["shadow_comparison"]
    advance_candidate = shadow.get("advance_to_live_paper_test_candidate") or shadow.get("nomination") or ""
    ranked = shadow.get("ranked_by_expected_improvement") or []
    if advance_candidate or ranked:
        if advance_candidate:
            lines.append(f"- **Advance to live paper test candidate:** {advance_candidate}")
        if ranked:
            lines.append("- **Shadow ranking (by expected improvement):** " + ", ".join(ranked[:6]))
        shadows = shadow.get("shadows") or {}
        for sid in ranked[:3]:
            s = shadows.get(sid, {})
            name = s.get("name") or sid
            delta = s.get("proxy_pnl_delta")
            lines.append(f"  - {sid}: {name}" + (f" (proxy_pnl_delta={delta})" if delta is not None else ""))
    else:
        lines.append("- (No shadow nomination in SHADOW_COMPARISON_LAST387.json; run board/shadow comparison to populate.)")
    lines.append("")

    # Not promotable / needs more evidence
    lines.extend([
        "## 3. Not Promotable / Needs More Evidence",
        "",
    ])
    missing = v.get("missing_data") or []
    counter = v.get("counterfactuals_not_tested") or []
    for m in missing:
        lines.append(f"- {m}")
    if not missing:
        lines.append("- (No missing_data from CSA.)")
    lines.append("")
    lines.append("**Counterfactuals not tested:**")
    for c in counter[:5]:
        lines.append(f"- {c}")
    if not counter:
        lines.append("- (None listed.)")
    lines.append("")

    # Blocked & counter-intel
    lines.extend([
        "## 4. Blocked & Counter-Intelligence Summary",
        "",
    ])
    board = data["board_review"]
    blocked_dist = board.get("blocked_trade_distribution") or {}
    blocked_total = board.get("blocked_total")
    if blocked_dist or blocked_total is not None:
        lines.append(f"- **Blocked total (board cohort):** {blocked_total}")
        for k, val in list(blocked_dist.items())[:10]:
            lines.append(f"- **{k}:** {val}")
    else:
        lines.append("- (No blocked_trade_distribution in board review; run comprehensive review to populate.)")
    lines.append("")
    esc = v.get("escalation_triggers") or []
    if esc:
        lines.append("**CSA escalation triggers:**")
        for e in esc[:4]:
            lines.append(f"- {e}")
    lines.append("")

    # Expectancy & learning
    lines.extend([
        "## 5. Expectancy & Learning",
        "",
    ])
    rec = v.get("recommendation") or ""
    next_exp = v.get("required_next_experiments") or []
    sre_interp = v.get("sre_interpretation") or {}
    lines.append(f"- **Recommendation:** {rec}")
    lines.append("- **Required next experiments:**")
    for ex in next_exp[:5]:
        lines.append(f"  - {ex}")
    lines.append(f"- **SRE breaking assumption:** " + (sre_interp.get("breaking_assumption") or "(none)"))
    lines.append("")

    # Governance & SRE
    lines.extend([
        "## 6. Governance & SRE Health",
        "",
    ])
    gov = data["governance"]
    sre = data["sre_status"]
    auto = v.get("automation_evidence") or {}
    lines.append(f"- **Governance status:** {gov.get('status') or auto.get('governance_status') or '—'}")
    lines.append(f"- **Governance timestamp:** {gov.get('timestamp') or auto.get('governance_timestamp') or '—'}")
    lines.append(f"- **Anomalies detected (governance):** {gov.get('anomalies_detected', '—')}")
    lines.append(f"- **SRE overall_status:** {sre.get('overall_status', '—')}")
    lines.append(f"- **SRE event_count:** {sre.get('event_count', '—')}")
    lines.append(f"- **SRE automation_anomalies_present:** {sre.get('automation_anomalies_present', '—')}")
    lines.append("")

    # Next actions
    lines.extend([
        "## 7. Next Actions (Owner View)",
        "",
    ])
    if advance_candidate:
        lines.append(f"- **Ready for promotion (shadow):** {advance_candidate} — advance to live paper test only after SRE/rollback and risk sign-off.")
    if next_exp:
        lines.append("- **Close:** Run required next experiments (see Section 5) before changing runtime behavior.")
    if missing:
        lines.append("- **Needs investigation:** Address missing_data before relying on CSA for gate decisions.")
    lines.append("- **CSA will evaluate at next 100-trade review:** Verdict, confidence, missing_data, shadow comparison, and governance/SRE evidence.")
    lines.append("")

    # Weekly review (last 7d) — from latest weekly ledger + board packet
    weekly = data.get("weekly_review") or {}
    weekly_date = weekly.get("date", "")
    if weekly_date:
        lines.extend([
            "## 8. Weekly Review (last 7d) — " + weekly_date,
            "",
            "- **Link to latest weekly board packet:** " + (weekly.get("board_packet_path") or "reports/board/CSA_WEEKLY_REVIEW_" + weekly_date + "_BOARD_PACKET.md"),
            "- **Top 3 promotable:** " + "; ".join((weekly.get("top_promotable") or [])[:3]) or "(see shadow nomination above)",
            "- **Top 3 profit leaks:** " + "; ".join((weekly.get("top_profit_leaks") or [])[:3]) or "(see CSA value_leaks / required_next_experiments)",
            "- **Trades this week:** executed " + str(weekly.get("executed_count", "—")) + ", blocked " + str(weekly.get("blocked_count", "—")) + ", CI-blocked " + str(weekly.get("counter_intel_blocked_count", "—")) + ".",
            "- **Trades until next CSA:** " + str(data.get("trades_until_next", "—")),
            "",
        ])
    else:
        lines.append("## 8. Weekly Review (last 7d)")
        lines.append("")
        lines.append("- Run weekly board audit to populate. See reports/board/WEEKLY_DECISION_PACKET_*.md and scripts/audit/collect_weekly_droplet_evidence.py.")
        lines.append("")

    lines.append("---")
    lines.append("*Generated by scripts/update_profitability_cockpit.py. Do not edit by hand.*")
    return "\n".join(lines)


def main() -> int:
    data = _ingest()
    body = _render_cockpit(data)
    BOARD.mkdir(parents=True, exist_ok=True)
    COCKPIT_PATH.write_text(body, encoding="utf-8")
    print("Profitability Cockpit updated:", COCKPIT_PATH)
    print("  CSA live:", data["csa_live"])
    print("  100-trade trigger wired:", data["trigger_wired"])
    print("  Total trade events:", data["total_trade_events"])
    print("  Trades until next CSA:", data["trades_until_next"])
    print("  Last mission:", data["csa_verdict_latest"].get("mission_id", "—"))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
