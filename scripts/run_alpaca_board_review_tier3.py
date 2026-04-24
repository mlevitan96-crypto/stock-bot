#!/usr/bin/env python3
"""
Alpaca Tier 3 (long-horizon) Board Review — packet generation.

Reads existing Alpaca governance artifacts (last387/last750/30d comprehensive review,
shadow comparison, weekly ledger, CSA verdict, SRE status) and produces a Board Review
Packet (MD + JSON) under reports/ALPACA_BOARD_REVIEW_<YYYYMMDD>_<HHMM>/.
Updates state/alpaca_board_review_state.json on success.

Alpaca US equities only. No cron, no promotion logic, no heartbeat.
Phase 1: Tier 3 only.

Usage:
  python3 scripts/run_alpaca_board_review_tier3.py [--base-dir PATH] [--date YYYY-MM-DD] [--force] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
DEFAULT_BASE = REPO


def _load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _load_text(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return None


def _mtime_iso(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
    except Exception:
        return None


def _find_comprehensive_review(base: Path) -> tuple[Path | None, str]:
    """Return (path, scope_label). Prefer last387, then last750, then 30d."""
    board = base / "reports" / "board"
    for name, label in [
        ("last387_comprehensive_review.json", "last387"),
        ("last750_comprehensive_review.json", "last750"),
        ("30d_comprehensive_review.json", "30d"),
    ]:
        p = board / name
        if p.exists():
            return p, label
    return None, ""


def _find_latest_csa_board_review(base: Path) -> Path | None:
    """Return path to most recent CSA_BOARD_REVIEW_*.json by mtime."""
    board = base / "reports" / "board"
    if not board.exists():
        return None
    candidates = list(board.glob("CSA_BOARD_REVIEW_*.json"))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def _tail_jsonl(path: Path, n: int = 20) -> list[dict]:
    out: list[dict] = []
    if not path.exists() or n <= 0:
        return out
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").strip().splitlines()
        for line in lines[-n:]:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    except Exception:
        pass
    return out


def load_tier3_inputs(base: Path, date_str: str) -> tuple[dict[str, Any], dict[str, str | None]]:
    """Load all Tier 3 inputs. Returns (payload_sources, input_mtimes)."""
    audit = base / "reports" / "audit"
    board = base / "reports" / "board"

    review_path, scope_label = _find_comprehensive_review(base)
    comprehensive = _load_json(review_path) if review_path else None

    shadow_path = board / "SHADOW_COMPARISON_LAST387.json"
    shadow = _load_json(shadow_path)

    weekly_path = audit / f"WEEKLY_TRADE_DECISION_LEDGER_SUMMARY_{date_str}.json"
    weekly = _load_json(weekly_path)

    csa_verdict_path = audit / "CSA_VERDICT_LATEST.json"
    csa_verdict = _load_json(csa_verdict_path)

    csa_summary_path = audit / "CSA_SUMMARY_LATEST.md"
    csa_summary = _load_text(csa_summary_path)

    sre_status_path = audit / "SRE_STATUS.json"
    sre_status = _load_json(sre_status_path)

    sre_events_path = audit / "SRE_EVENTS.jsonl"
    sre_events_tail = _tail_jsonl(sre_events_path, 20)

    gov_path = base / "reports" / "audit" / "GOVERNANCE_AUTOMATION_STATUS.json"
    gov_status = _load_json(gov_path)

    csa_board_review_path = _find_latest_csa_board_review(base)
    csa_board_review = _load_json(csa_board_review_path) if csa_board_review_path else None

    input_mtimes: dict[str, str | None] = {}
    for name, p in [
        ("last_review", review_path),
        ("shadow_comparison", shadow_path),
        ("weekly_ledger", weekly_path),
        ("csa_verdict_latest", csa_verdict_path),
        ("sre_status", sre_status_path),
    ]:
        input_mtimes[name] = _mtime_iso(p) if p else None

    sources = {
        "comprehensive_review": comprehensive,
        "scope_label": scope_label,
        "review_path": str(review_path) if review_path else None,
        "shadow_comparison": shadow,
        "shadow_path": str(shadow_path),
        "weekly_ledger": weekly,
        "csa_verdict": csa_verdict,
        "csa_summary": csa_summary,
        "sre_status": sre_status,
        "sre_events_tail": sre_events_tail,
        "governance_automation": gov_status,
        "csa_board_review": csa_board_review,
        "csa_board_review_path": str(csa_board_review_path) if csa_board_review_path else None,
        "input_mtimes": input_mtimes,
    }
    return sources, input_mtimes


def build_payload(sources: dict[str, Any], generated_ts: str, base_dir: str) -> dict[str, Any]:
    """Build BOARD_REVIEW.json payload."""
    comprehensive = sources.get("comprehensive_review")
    shadow = sources.get("shadow_comparison")
    weekly = sources.get("weekly_ledger")
    csa_verdict = sources.get("csa_verdict")
    sre_status = sources.get("sre_status")
    gov = sources.get("governance_automation")
    scope_label = sources.get("scope_label") or "none"
    input_mtimes = sources.get("input_mtimes") or {}

    # Cover
    inputs_present = {
        "comprehensive_review": comprehensive is not None,
        "shadow_comparison": shadow is not None,
        "weekly_ledger": weekly is not None,
        "csa_verdict_latest": csa_verdict is not None,
        "sre_status": sre_status is not None,
    }
    cover = {
        "title": "Alpaca Tier 3 Board Review",
        "generated_ts": generated_ts,
        "base_dir": base_dir,
        "inputs_present": inputs_present,
        "input_mtimes_utc": input_mtimes,
    }

    # Tier 3 summary
    tier3: dict[str, Any] = {"scope": scope_label, "window_start": None, "window_end": None}
    if comprehensive:
        tier3["window_start"] = comprehensive.get("window_start")
        tier3["window_end"] = comprehensive.get("window_end")
        pnl = comprehensive.get("pnl") or {}
        tier3["total_pnl_attribution_usd"] = pnl.get("total_pnl_attribution_usd")
        tier3["total_pnl_exit_attribution_usd"] = pnl.get("total_pnl_exit_attribution_usd")
        tier3["win_rate"] = pnl.get("win_rate")
        tier3["total_exits"] = pnl.get("total_exits")
        tier3["total_trades"] = pnl.get("total_trades")
        tier3["blocked_total"] = comprehensive.get("blocked_total")
    if shadow:
        tier3["shadow_nomination"] = shadow.get("nomination")
        tier3["shadow_advance_candidate"] = shadow.get("advance_candidate")
    if weekly:
        tier3["weekly_ledger_note"] = "Weekly ledger summary loaded"
    if csa_verdict:
        tier3["csa_verdict"] = csa_verdict.get("verdict")
        tier3["csa_confidence"] = csa_verdict.get("confidence")

    # Executed / attribution (from comprehensive)
    executed: dict[str, Any] = {}
    if comprehensive:
        executed["pnl"] = comprehensive.get("pnl")
        executed["by_direction"] = comprehensive.get("by_direction")
        executed["canonical_logs"] = ["logs/exit_attribution.jsonl", "logs/attribution.jsonl"]
    else:
        executed["note"] = "No comprehensive review data."

    # Blocked / counter-intel
    blocked: dict[str, Any] = {}
    if comprehensive:
        blocked["blocked_total"] = comprehensive.get("blocked_total")
        counter = comprehensive.get("counter_intelligence") or {}
        blocked["blocking_patterns"] = dict(list((counter.get("blocking_patterns") or {}).items())[:10])
        blocked["opportunity_cost_ranked_reasons"] = (counter.get("opportunity_cost_ranked_reasons") or [])[:10]
    else:
        blocked["note"] = "No comprehensive review data."

    # Shadow comparison
    shadow_section: dict[str, Any] = {}
    if shadow:
        shadow_section["ranked_by_expected_improvement"] = shadow.get("ranked_by_expected_improvement")
        shadow_section["nomination"] = shadow.get("nomination")
        shadow_section["risk_flags"] = shadow.get("risk_flags")
        shadow_section["persona_verdicts"] = shadow.get("persona_verdicts")
    else:
        shadow_section["note"] = "Shadow comparison not run; required before promotion."

    # Learning / replay
    learning_section: dict[str, Any] = {}
    if comprehensive:
        learning_section["learning_telemetry"] = comprehensive.get("learning_telemetry")
        learning_section["how_to_proceed"] = comprehensive.get("how_to_proceed")
    else:
        learning_section["note"] = "N/A"

    # SRE and automation
    sre_section: dict[str, Any] = {}
    sre_section["sre_overall_status"] = (sre_status or {}).get("overall_status") if sre_status else "not available"
    sre_section["governance_anomalies_detected"] = (gov or {}).get("anomalies_detected") if gov else None
    sre_section["sre_events_path"] = "reports/audit/SRE_EVENTS.jsonl"
    sre_section["sre_events_tail_count"] = len(sources.get("sre_events_tail") or [])

    # Appendices (paths only)
    appendices_paths = [
        "reports/POSTMARKET_*.md",
        "reports/SHADOW_TRADING_CONFIRMATION_*.md",
    ]

    return {
        "cover": cover,
        "tier3_summary": tier3,
        "executed_attribution": executed,
        "blocked_counterintel": blocked,
        "shadow_comparison": shadow_section,
        "learning_replay": learning_section,
        "sre_automation": sre_section,
        "appendices_paths": appendices_paths,
    }


def payload_to_md(payload: dict[str, Any]) -> str:
    """Render BOARD_REVIEW.md from payload."""
    lines: list[str] = []
    cover = payload.get("cover") or {}
    lines.append("# Alpaca Tier 3 Board Review")
    lines.append("")
    lines.append(f"**Generated:** {cover.get('generated_ts', 'N/A')}")
    lines.append(f"**Base dir:** {cover.get('base_dir', 'N/A')}")
    lines.append("")
    lines.append("## 1. Cover — inputs loaded")
    lines.append("")
    for k, v in (cover.get("inputs_present") or {}).items():
        lines.append(f"- **{k}:** {'yes' if v else 'no'}")
    mtimes = cover.get("input_mtimes_utc") or {}
    if mtimes:
        lines.append("")
        lines.append("Input mtimes (UTC):")
        for k, t in mtimes.items():
            lines.append(f"- {k}: {t or 'N/A'}")
    lines.append("")
    lines.append("---")
    lines.append("")

    t3 = payload.get("tier3_summary") or {}
    lines.append("## 2. Tier 3 summary")
    lines.append("")
    lines.append(f"- **Scope:** {t3.get('scope') or 'none'}")
    lines.append(f"- **Window:** {t3.get('window_start')} to {t3.get('window_end')}")
    lines.append(f"- **Total PnL (attribution):** {t3.get('total_pnl_attribution_usd')}")
    lines.append(f"- **Total PnL (exit attribution):** {t3.get('total_pnl_exit_attribution_usd')}")
    lines.append(f"- **Win rate:** {t3.get('win_rate')}")
    lines.append(f"- **Total exits:** {t3.get('total_exits')}")
    lines.append(f"- **Blocked total:** {t3.get('blocked_total')}")
    lines.append(f"- **Shadow nomination:** {t3.get('shadow_nomination') or 'N/A'}")
    lines.append(f"- **CSA verdict:** {t3.get('csa_verdict') or 'N/A'}")
    lines.append(f"- **CSA confidence:** {t3.get('csa_confidence') or 'N/A'}")
    if t3.get("weekly_ledger_note"):
        lines.append(f"- **Weekly:** {t3['weekly_ledger_note']}")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## 3. Executed trades and attribution")
    lines.append("")
    ex = payload.get("executed_attribution") or {}
    if ex.get("note"):
        lines.append(ex["note"])
    else:
        pnl = ex.get("pnl") or {}
        lines.append(f"- Total PnL (attribution): {pnl.get('total_pnl_attribution_usd')}")
        lines.append(f"- Total exits: {pnl.get('total_exits')}")
        lines.append(f"- Canonical logs: {ex.get('canonical_logs', [])}")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## 4. Blocked trades and counter-intelligence")
    lines.append("")
    blk = payload.get("blocked_counterintel") or {}
    if blk.get("note"):
        lines.append(blk["note"])
    else:
        lines.append(f"- **Blocked total:** {blk.get('blocked_total')}")
        for reason, count in list((blk.get("blocking_patterns") or {}).items())[:10]:
            lines.append(f"  - `{reason}`: {count}")
        oc = blk.get("opportunity_cost_ranked_reasons") or []
        for item in oc[:5]:
            r = item.get("reason")
            c = item.get("blocked_count")
            cost = item.get("estimated_opportunity_cost_usd")
            lines.append(f"  - Opportunity cost: {r} (count={c}, est_cost={cost})")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## 5. Shadow comparison")
    lines.append("")
    sh = payload.get("shadow_comparison") or {}
    if sh.get("note"):
        lines.append(sh["note"])
    else:
        lines.append(f"- **Nomination:** {sh.get('nomination')}")
        lines.append(f"- **Ranked by expected improvement:** {sh.get('ranked_by_expected_improvement')}")
        risk = sh.get("risk_flags") or {}
        for k, v in list(risk.items())[:5]:
            lines.append(f"- Risk: {k}: {v}")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## 6. Learning and replay readiness")
    lines.append("")
    lr = payload.get("learning_replay") or {}
    if lr.get("note"):
        lines.append(lr["note"])
    else:
        lt = lr.get("learning_telemetry") or {}
        lines.append(f"- Exits in scope: {lt.get('total_exits_in_scope')}")
        lines.append(f"- Telemetry-backed: {lt.get('telemetry_backed')} ({lt.get('pct_telemetry')}%)")
        lines.append(f"- Ready for replay: {lt.get('ready_for_replay')}")
        for rec in (lr.get("how_to_proceed") or [])[:10]:
            lines.append(f"- {rec}")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## 7. SRE and automation")
    lines.append("")
    sre = payload.get("sre_automation") or {}
    lines.append(f"- **SRE overall status:** {sre.get('sre_overall_status')}")
    lines.append(f"- **Governance anomalies detected:** {sre.get('governance_anomalies_detected')}")
    lines.append(f"- **SRE events path:** {sre.get('sre_events_path')} (tail count: {sre.get('sre_events_tail_count')})")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## 8. Appendices (optional paths)")
    lines.append("")
    for p in payload.get("appendices_paths") or []:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("*End of Alpaca Tier 3 Board Review.*")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Alpaca Tier 3 Board Review — generate Board Review Packet (MD + JSON)"
    )
    ap.add_argument("--base-dir", default="", help="Repo root (default: script repo parent)")
    ap.add_argument("--date", default="", help="YYYY-MM-DD for weekly ledger (default: today UTC)")
    ap.add_argument("--force", action="store_true", help="Allow run even if state suggests recent run")
    ap.add_argument("--dry-run", action="store_true", help="Load inputs, build payload, print summary; do not write")
    ap.add_argument("--telegram", action="store_true", help="Send one-line summary to Telegram (best-effort; failures logged)")
    args = ap.parse_args()

    base = Path(args.base_dir).resolve() if args.base_dir else DEFAULT_BASE
    if not base.is_dir():
        print(f"Base dir not found: {base}", file=sys.stderr)
        return 1

    date_str = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    generated_ts = datetime.now(timezone.utc).isoformat()

    sources, input_mtimes = load_tier3_inputs(base, date_str)
    payload = build_payload(sources, generated_ts, str(base))
    scope_label = (sources.get("comprehensive_review") and sources.get("scope_label")) or "none"

    if args.dry_run:
        print("DRY RUN — no files written")
        print(f"  Scope: {scope_label}")
        print(f"  Inputs present: {payload['cover'].get('inputs_present')}")
        print(f"  Payload keys: {list(payload.keys())}")
        return 0

    reports_dir = base / "reports"
    state_dir = base / "state"
    reports_dir.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)

    ts_dir = f"ALPACA_BOARD_REVIEW_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}"
    packet_dir = reports_dir / ts_dir
    packet_dir.mkdir(parents=True, exist_ok=True)
    md_path = packet_dir / "BOARD_REVIEW.md"
    json_path = packet_dir / "BOARD_REVIEW.json"

    try:
        md_path.write_text(payload_to_md(payload), encoding="utf-8")
    except Exception as e:
        print(f"Failed to write {md_path}: {e}", file=sys.stderr)
        return 1

    try:
        json_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    except Exception as e:
        print(f"Failed to write {json_path}: {e}", file=sys.stderr)
        return 1

    state_data = {
        "last_run_ts": generated_ts,
        "last_packet_dir": str(packet_dir),
        "last_scope": scope_label,
        "inputs_present": payload["cover"].get("inputs_present"),
    }
    state_path = state_dir / "alpaca_board_review_state.json"
    try:
        state_path.write_text(json.dumps(state_data, indent=2, default=str), encoding="utf-8")
    except Exception as e:
        print(f"Failed to write state {state_path}: {e}", file=sys.stderr)
        return 1

    print(f"Packet written: {packet_dir}")
    print(f"  {md_path.name}")
    print(f"  {json_path.name}")
    print(f"State updated: {state_path}")
    if args.telegram:
        try:
            if str(base) not in sys.path:
                sys.path.insert(0, str(base))
            from scripts.alpaca_telegram import send_governance_telegram
            send_governance_telegram(f"Alpaca Tier3 review: {packet_dir} scope {scope_label}", script_name="tier3")
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
