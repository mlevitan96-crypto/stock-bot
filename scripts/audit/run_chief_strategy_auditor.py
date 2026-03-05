#!/usr/bin/env python3
"""
Chief Strategy Auditor (CSA): adversarial governance reviewer.
Runs for every mission; produces findings and verdict (PROCEED | HOLD | ESCALATE | ROLLBACK).
Outputs: reports/audit/CSA_FINDINGS_<mission-id>.md, reports/audit/CSA_VERDICT_<mission-id>.json.
Also writes CSA_SUMMARY_LATEST.md and CSA_VERDICT_LATEST.json for Cursor block enforcement.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
# Allow loading from repo root (src.contracts) or with src on path
try:
    from src.contracts.csa_verdict_schema import (
        CSA_VERDICT_SCHEMA_VERSION,
        build_verdict,
        validate_csa_verdict,
    )
except ImportError:
    sys.path.insert(0, str(REPO / "src"))
    from contracts.csa_verdict_schema import (
        CSA_VERDICT_SCHEMA_VERSION,
        build_verdict,
        validate_csa_verdict,
    )


def _load_json(path: Path) -> dict | None:
    if not path or not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _gather_context(base: Path, args: argparse.Namespace) -> dict:
    """Gather mission context from args and available artifacts."""
    ctx = {
        "mission_id": getattr(args, "mission_id", "unknown"),
        "context_json": None,
        "board_review": None,
        "shadow_comparison": None,
        "baseline_snapshot": None,
        "board_files": [],
        "audit_files": [],
        "shadow_files": [],
    }
    if getattr(args, "context_json", None):
        p = base / args.context_json if not Path(args.context_json).is_absolute() else Path(args.context_json)
        ctx["context_json"] = _load_json(p)
    if getattr(args, "board_review_json", None):
        p = base / args.board_review_json if not Path(args.board_review_json).is_absolute() else Path(args.board_review_json)
        ctx["board_review"] = _load_json(p)
    if getattr(args, "shadow_comparison_json", None):
        p = base / args.shadow_comparison_json if not Path(args.shadow_comparison_json).is_absolute() else Path(args.shadow_comparison_json)
        ctx["shadow_comparison"] = _load_json(p)
    if getattr(args, "baseline_snapshot", None):
        p = base / args.baseline_snapshot if not Path(args.baseline_snapshot).is_absolute() else Path(args.baseline_snapshot)
        ctx["baseline_snapshot"] = _load_json(p)

    board_dir = base / "reports" / "board"
    if board_dir.exists():
        ctx["board_files"] = [f.name for f in board_dir.iterdir() if f.suffix in (".json", ".md")]
    audit_dir = base / "reports" / "audit"
    if audit_dir.exists():
        ctx["audit_files"] = [f.name for f in audit_dir.iterdir() if f.suffix in (".json", ".md")]
    shadow_dir = base / "state" / "shadow"
    if shadow_dir.exists():
        ctx["shadow_files"] = [f.name for f in shadow_dir.iterdir() if f.suffix == ".json"]

    return ctx


def _audit_assumptions(ctx: dict) -> list[str]:
    """Assumption audit: what are we assuming that could be wrong?"""
    assumptions = [
        "Board review and shadow data reflect current production behavior.",
        "Last-387 (or chosen cohort) is representative for promotion decisions.",
        "Telemetry and attribution paths are complete for in-scope exits.",
        "No unmeasured regime shift between review window and deploy.",
    ]
    if ctx.get("shadow_comparison"):
        assumptions.append("Shadow comparison ranking (proxy_pnl_delta) is sufficient for advance decisions.")
    if ctx.get("board_review"):
        assumptions.append("Board opportunity_cost / scenario logic is stable across runs.")
    return assumptions


def _audit_missing_data(ctx: dict) -> list[str]:
    """Data sufficiency: what is missing that could change the verdict?"""
    missing = []
    if not ctx.get("board_review"):
        missing.append("Board review JSON not provided; cannot validate scenario alignment.")
    if not ctx.get("shadow_comparison"):
        missing.append("Shadow comparison not provided; advance candidate may be unvalidated.")
    br = ctx.get("board_review")
    if br and isinstance(br, dict):
        if not br.get("exits_in_scope") and not br.get("opportunity_cost_ranked_reasons"):
            missing.append("Board review lacks exits_in_scope or opportunity_cost_ranked_reasons.")
    sc = ctx.get("shadow_comparison")
    if sc and isinstance(sc, dict):
        shadows = sc.get("shadows") or {}
        if not shadows or all((s or {}).get("error") for s in shadows.values()):
            missing.append("Shadow comparison has no valid shadow results.")
    if not ctx.get("audit_files"):
        missing.append("No audit artifacts found; deploy/verification proof unknown.")
    return missing


def _audit_counterfactuals(ctx: dict) -> list[str]:
    """Counterfactuals not tested."""
    cf = [
        "Alternative time windows (7d, 14d) not compared in this run.",
        "Rollback impact (reverting B2/paper flags) not re-measured post-enable.",
        "Different exit-count cohorts (e.g. last750) not compared for stability.",
    ]
    if ctx.get("shadow_comparison"):
        cf.append("Shadow advance: live paper outcome vs shadow proxy not yet observed.")
    return cf


def _audit_value_leaks(ctx: dict) -> list[str]:
    """Value leakage scan: future or out-of-scope info leaking into decisions."""
    leaks = [
        "Ensure board review uses only in-scope exits; no post-cutoff data.",
        "Shadow runs must not use post-decision execution data.",
    ]
    return leaks


def _risk_asymmetry(ctx: dict) -> str:
    """Worst plausible downside vs upside."""
    sc = ctx.get("shadow_comparison")
    if sc and isinstance(sc, dict):
        nomination = (sc.get("nomination") or "").lower()
        if "advance" in nomination or "discard" in nomination:
            return "Asymmetry: advancing a shadow has unbounded downside (live paper loss); holding has bounded opportunity cost. Rollback cost non-zero."
    return "Default: downside (bad live paper / production impact) exceeds upside (marginal PnL gain) until proven in shadow and paper."


def _escalation_triggers(ctx: dict) -> list[str]:
    """When to escalate to human."""
    return [
        "Verdict is HOLD, ESCALATE, or ROLLBACK and no CSA_RISK_ACCEPTANCE artifact exists.",
        "Confidence is LOW on a PROCEED verdict.",
        "Missing data list is non-empty and mission changes runtime behavior.",
        "Risk asymmetry note indicates unbounded downside.",
    ]


def _required_next_experiments(ctx: dict) -> list[str]:
    """Ranked next experiments."""
    experiments = [
        "Run parallel reviews (7d, 14d, 30d, last387) and compare nomination stability.",
        "Run shadow comparison after every board review; gate enable on CSA + shadow.",
        "Document rollback procedure and run rollback drill before enabling new flags.",
    ]
    if not ctx.get("shadow_comparison"):
        experiments.insert(0, "Produce shadow comparison (build_shadow_comparison_last387) before any promotion.")
    return experiments


def _recommendation(verdict: str, confidence: str, missing: list[str]) -> str:
    if verdict == "PROCEED":
        return "CSA does not block. Proceed only if other gates pass; prefer HIGH confidence."
    if verdict == "HOLD":
        return "Do not promote until missing data is addressed or explicit CSA_RISK_ACCEPTANCE override is written."
    if verdict == "ESCALATE":
        return "Escalate to human; do not auto-promote. Human may override with CSA_RISK_ACCEPTANCE."
    if verdict == "ROLLBACK":
        return "Recommend rollback or do not enable. Override only with explicit risk acceptance and rollback plan."
    return "Unknown verdict; treat as HOLD."


def _choose_verdict(ctx: dict, missing: list[str]) -> tuple[str, str]:
    """Choose verdict and confidence from context and findings."""
    has_board = bool(ctx.get("board_review"))
    has_shadow = bool(ctx.get("shadow_comparison"))
    shadow_ok = False
    if has_shadow and isinstance(ctx.get("shadow_comparison"), dict):
        shadows = (ctx["shadow_comparison"] or {}).get("shadows") or {}
        shadow_ok = any(not (s or {}).get("error") for s in shadows.values())

    if not has_board and not has_shadow:
        return "HOLD", "LOW"
    if len(missing) > 3:
        return "HOLD", "LOW"
    if has_board and has_shadow and shadow_ok and len(missing) <= 1:
        return "PROCEED", "MED"
    if "advance" in ((ctx.get("shadow_comparison") or {}).get("nomination") or "").lower() and not shadow_ok:
        return "ESCALATE", "MED"
    if len(missing) >= 2:
        return "HOLD", "MED"
    return "PROCEED", "LOW"


def main() -> int:
    ap = argparse.ArgumentParser(description="Chief Strategy Auditor: run for every mission")
    ap.add_argument("--mission-id", required=True, help="Mission identifier")
    ap.add_argument("--context-json", default="", help="Path to context JSON (what changed, flags, scope)")
    ap.add_argument("--baseline-snapshot", default="", help="Optional baseline snapshot path")
    ap.add_argument("--board-review-json", default="", help="Optional board review JSON path")
    ap.add_argument("--shadow-comparison-json", default="", help="Optional shadow comparison JSON path")
    ap.add_argument("--base-dir", default="", help="Repo base dir (default: cwd)")
    args = ap.parse_args()

    base = Path(args.base_dir).resolve() if args.base_dir else REPO
    audit_dir = base / "reports" / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)

    ctx = _gather_context(base, args)
    mission_id = args.mission_id

    assumptions = _audit_assumptions(ctx)
    missing_data = _audit_missing_data(ctx)
    counterfactuals_not_tested = _audit_counterfactuals(ctx)
    value_leaks = _audit_value_leaks(ctx)
    risk_asymmetry = _risk_asymmetry(ctx)
    escalation_triggers = _escalation_triggers(ctx)
    required_next_experiments = _required_next_experiments(ctx)

    verdict, confidence = _choose_verdict(ctx, missing_data)
    recommendation = _recommendation(verdict, confidence, missing_data)

    payload = build_verdict(
        verdict=verdict,
        confidence=confidence,
        assumptions=assumptions,
        missing_data=missing_data,
        counterfactuals_not_tested=counterfactuals_not_tested,
        value_leaks=value_leaks,
        risk_asymmetry=risk_asymmetry,
        recommendation=recommendation,
        escalation_triggers=escalation_triggers,
        required_next_experiments=required_next_experiments,
        override_allowed=True,
        override_requirements=["reports/audit/CSA_RISK_ACCEPTANCE_<mission-id>.md"],
        mission_id=mission_id,
    )
    payload["generated_ts"] = datetime.now(timezone.utc).isoformat()

    ok, issues = validate_csa_verdict(payload)
    if not ok:
        blocker_path = audit_dir / "CSA_IMPLEMENTATION_BLOCKERS.md"
        blocker_path.write_text(
            "CSA verdict contract validation failed: " + "; ".join(issues) + "\n",
            encoding="utf-8",
        )
        print("CSA contract validation failed:", issues, file=sys.stderr)
        return 1

    verdict_path = audit_dir / f"CSA_VERDICT_{mission_id}.json"
    verdict_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    # Findings markdown
    md_lines = [
        "# CSA Findings",
        "",
        f"**Mission ID:** {mission_id}",
        f"**Generated (UTC):** {payload['generated_ts']}",
        f"**Verdict:** {verdict} (**{confidence}** confidence)",
        "",
        "## Assumption audit",
        "",
    ]
    for a in assumptions:
        md_lines.append(f"- {a}")
    md_lines.extend([
        "",
        "## Missing data",
        "",
    ])
    for m in missing_data:
        md_lines.append(f"- {m}")
    if not missing_data:
        md_lines.append("- (none identified)")
    md_lines.extend([
        "",
        "## Counterfactuals not tested",
        "",
    ])
    for c in counterfactuals_not_tested:
        md_lines.append(f"- {c}")
    md_lines.extend([
        "",
        "## Value leakage scan",
        "",
    ])
    for v in value_leaks:
        md_lines.append(f"- {v}")
    md_lines.extend([
        "",
        "## Risk asymmetry",
        "",
        risk_asymmetry,
        "",
        "## Escalation triggers",
        "",
    ])
    for e in escalation_triggers:
        md_lines.append(f"- {e}")
    md_lines.extend([
        "",
        "## Required next experiments (ranked)",
        "",
    ])
    for i, ex in enumerate(required_next_experiments, 1):
        md_lines.append(f"{i}. {ex}")
    md_lines.extend([
        "",
        "## Recommendation",
        "",
        recommendation,
        "",
        "## Override",
        "",
        "Override allowed: **yes** (soft veto). To override HOLD/ESCALATE/ROLLBACK, create:",
        "",
        f"`reports/audit/CSA_RISK_ACCEPTANCE_{mission_id}.md`",
        "",
        "with required sections (verdict summary, why override, risk accepted, rollback plan, sign-off).",
        "",
    ])

    findings_path = audit_dir / f"CSA_FINDINGS_{mission_id}.md"
    findings_path.write_text("\n".join(md_lines), encoding="utf-8")

    # Phase 4: always-on — write latest for Cursor block enforcement
    latest_md = audit_dir / "CSA_SUMMARY_LATEST.md"
    latest_json = audit_dir / "CSA_VERDICT_LATEST.json"
    latest_md.write_text("\n".join(md_lines), encoding="utf-8")
    latest_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    print(f"CSA verdict: {verdict} ({confidence})")
    print(f"Wrote {findings_path}")
    print(f"Wrote {verdict_path}")
    print(f"Wrote {latest_md} and {latest_json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
