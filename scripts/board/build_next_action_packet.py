#!/usr/bin/env python3
"""
Build NEXT_ACTION_PACKET_C1_PROMOTED_A3_SHADOW.md and .json.
Reads C1 proof (optional), A3 shadow state; includes promotion gate for A3 live test and persona verdicts.
Run on droplet after C1 proof and A3 shadow artifacts exist.
Includes Automation Status subsection (governance integrity + weekly summary) for board-grade artifacts.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from datetime import datetime, timezone


def _automation_status(base: Path) -> dict:
    """Read governance automation status and recent weekly summary for board packet. No dependency on CSA module."""
    out = {
        "last_governance_integrity_ts": None,
        "last_weekly_summary_date": None,
        "automation_anomalies_open": False,
    }
    status_path = base / "reports" / "audit" / "GOVERNANCE_AUTOMATION_STATUS.json"
    if status_path.exists():
        try:
            data = json.loads(status_path.read_text(encoding="utf-8"))
            out["last_governance_integrity_ts"] = data.get("run_ts_utc") or data.get("timestamp")
            out["automation_anomalies_open"] = data.get("anomalies_detected") or data.get("status") == "anomalies"
        except Exception:
            pass
    board_dir = base / "reports" / "board"
    if board_dir.exists():
        for f in sorted(board_dir.iterdir(), reverse=True):
            if f.name.startswith("WEEKLY_GOVERNANCE_SUMMARY_") and f.name.endswith(".md"):
                out["last_weekly_summary_date"] = f.stem.replace("WEEKLY_GOVERNANCE_SUMMARY_", "")
                break
    return out


def main() -> int:
    base = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    c1_proof_path = base / "reports" / "audit" / "C1_PROMOTION_PROOF.md"
    a3_state_path = base / "state" / "shadow" / "a3_expectancy_floor_shadow.json"
    out_dir = base / "reports" / "board"
    out_dir.mkdir(parents=True, exist_ok=True)
    basename = "NEXT_ACTION_PACKET_C1_PROMOTED_A3_SHADOW"
    out_json = out_dir / f"{basename}.json"
    out_md = out_dir / f"{basename}.md"

    what_changed = "C1 promoted (reporting only): counter-intelligence opportunity-cost ranking is first-class in board review output. No live gating or execution changes."
    a3_results = {}
    a3_confidence = "low"
    a3_proxy_label = "proxy"
    if a3_state_path.exists():
        try:
            a3_results = json.loads(a3_state_path.read_text(encoding="utf-8"))
            a3_proxy_label = a3_results.get("estimated_pnl_delta_label", "proxy")
            a3_confidence = "low (proxy PnL; no per-block outcome)"
        except Exception:
            a3_results = {"error": "failed to load A3 shadow state"}

    # Pre-declared promotion gate for A3 LIVE TEST (not deployment yet)
    promotion_gate = {
        "min_shadow_sample_size_blocked_events": 20,
        "min_expected_improvement_threshold_usd": -10,
        "max_tolerated_tail_risk_signal": "no single block reason >80% of would-admit count without backtest",
        "rollback_condition_if_live_approved": "If live paper test shows win_rate_delta < 0 or drawdown exceeds 1.5x baseline, rollback MIN_EXEC_SCORE to baseline_floor within 24h.",
    }
    # Explicit gate: Promote / Hold / Rollback (single line for board)
    promote_hold_rollback_gate = {
        "C1": "Promote (done): reporting only; no behavior change.",
        "A3_live_test": "Hold until shadow sample ≥20 and promotion_gate satisfied; then Test in paper. Rollback: MIN_EXEC_SCORE to 2.5 if win_rate_delta < 0 or drawdown > 1.5x baseline.",
    }

    persona_verdicts = {
        "adversarial": "Proceed to live paper test? Conditional yes. Shadow shows would-admit count and proxy PnL; we have not observed actual outcomes for those blocks. Run live paper with MIN_EXEC_SCORE at effective_floor for 1 week; if win rate of admitted band is below baseline, discard. Watch: win rate of score band [effective_floor, baseline_floor].",
        "quant": "Proceed to live paper test? Yes, with sample-size gate. Shadow gives expected direction; validate with live paper. Watch: expectancy of admitted band vs baseline; if negative, rollback.",
        "product_operator": "Proceed to live paper test? Yes, after shadow sample ≥20 and proxy PnL delta not severely negative. Watch: volume of new admits and fill rate.",
        "risk": "Proceed to live paper test? Hold until shadow sample size and tail-risk note are satisfied. Prefer B1/B3 (exit behavior) before lowering floor. Watch: concentration of losses in new band.",
        "execution_sre": "Proceed to live paper test? Test only after rollback procedure is documented and dashboard shows MIN_EXEC_SCORE. No config change until tests pass. Watch: logs for any unintended gate bypass.",
    }

    auto_status = _automation_status(base)
    payload = {
        "generated_ts": datetime.now(timezone.utc).isoformat(),
        "what_changed": what_changed,
        "a3_shadow_results": a3_results,
        "a3_confidence_level": a3_confidence,
        "a3_proxy_label": a3_proxy_label,
        "promotion_gate_for_a3_live_test": promotion_gate,
        "promote_hold_rollback_gate": promote_hold_rollback_gate,
        "persona_verdicts": persona_verdicts,
        "automation_status": auto_status,
    }
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)
    print(f"Wrote {out_json}")

    md_lines = [
        "# Next action packet: C1 promoted + A3 shadow",
        "",
        f"**Generated (UTC):** {payload['generated_ts']}",
        "",
        "## What changed",
        "",
        what_changed,
        "",
        "## A3 shadow results",
        "",
        f"- **Confidence:** {a3_confidence}",
        f"- **Proxy label:** {a3_proxy_label}",
        "",
    ]
    for k, v in (a3_results if isinstance(a3_results, dict) and "error" not in a3_results else {}).items():
        if k in ("run_ts", "additional_admitted_trades", "estimated_pnl_delta_usd", "effective_floor_shadow", "floor_breach_count", "tail_risk_notes"):
            md_lines.append(f"- **{k}:** {v}")
    md_lines.extend([
        "",
        "## Promotion gate for A3 live test (pre-declared)",
        "",
    ])
    for k, v in promotion_gate.items():
        md_lines.append(f"- **{k}:** {v}")
    md_lines.extend([
        "",
        "## Promote / Hold / Rollback (explicit gate)",
        "",
    ])
    for k, v in promote_hold_rollback_gate.items():
        md_lines.append(f"- **{k}:** {v}")
    md_lines.extend([
        "",
        "## Persona verdicts (proceed to live paper test? what to watch)",
        "",
    ])
    for persona, text in persona_verdicts.items():
        md_lines.append(f"### {persona.replace('_', ' ').title()}")
        md_lines.append("")
        md_lines.append(text)
        md_lines.append("")
    md_lines.extend([
        "## Automation Status",
        "",
        "Cursor Automations governance layer (first-class evidence in CSA/SRE).",
        "",
        f"- **Last governance-integrity run (UTC):** {auto_status.get('last_governance_integrity_ts') or 'unknown'}",
        f"- **Last weekly governance summary date:** {auto_status.get('last_weekly_summary_date') or 'none'}",
        f"- **Automation anomalies currently open:** {auto_status.get('automation_anomalies_open', False)}",
        "",
    ])
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    print(f"Wrote {out_md}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
