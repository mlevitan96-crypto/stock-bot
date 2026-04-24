#!/usr/bin/env python3
"""
Alpaca Tier 2 (medium-horizon) Board Review — packet generation.

Reads existing 7d/30d/last100 comprehensive reviews and optional CSA_BOARD_REVIEW;
produces Tier 2 Board Review packet (MD + JSON).
Updates state/alpaca_board_review_state.json (merge: adds tier2_* keys).

Alpaca US equities only. No cron, no promotion logic, no heartbeat.
Phase 2. Read-only: does not invoke build_30d_comprehensive_review.

Usage:
  python scripts/run_alpaca_board_review_tier2.py [--base-dir PATH] [--date YYYY-MM-DD] [--force] [--dry-run]
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


def _find_latest_csa_board_review(base: Path) -> Path | None:
    board = base / "reports" / "board"
    if not board.exists():
        return None
    candidates = list(board.glob("CSA_BOARD_REVIEW_*.json"))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def load_tier2_inputs(base: Path) -> dict[str, Any]:
    """Load 7d, 30d, last100 comprehensive reviews and latest CSA_BOARD_REVIEW."""
    board = base / "reports" / "board"
    review_7d = _load_json(board / "7d_comprehensive_review.json")
    review_30d = _load_json(board / "30d_comprehensive_review.json")
    review_last100 = _load_json(board / "last100_comprehensive_review.json")
    csa_board_path = _find_latest_csa_board_review(base)
    csa_board = _load_json(csa_board_path) if csa_board_path else None
    return {
        "review_7d": review_7d,
        "review_30d": review_30d,
        "review_last100": review_last100,
        "csa_board_review": csa_board,
        "csa_board_review_path": str(csa_board_path) if csa_board_path else None,
    }


def build_tier2_payload(sources: dict[str, Any], generated_ts: str, base_dir: str) -> dict[str, Any]:
    """Build TIER2_REVIEW.json payload."""
    r7 = sources.get("review_7d")
    r30 = sources.get("review_30d")
    r100 = sources.get("review_last100")
    csa_board = sources.get("csa_board_review")

    inputs_present = {
        "7d_review": r7 is not None,
        "30d_review": r30 is not None,
        "last100_review": r100 is not None,
        "csa_board_review": csa_board is not None,
    }

    cover = {
        "title": "Alpaca Tier 2 Board Review",
        "generated_ts": generated_ts,
        "base_dir": base_dir,
        "inputs_present": inputs_present,
    }

    def _scope_summary(review: dict | None, label: str) -> dict[str, Any]:
        if not review:
            return {"scope": label, "present": False}
        pnl = review.get("pnl") or {}
        return {
            "scope": label,
            "present": True,
            "window_start": review.get("window_start"),
            "window_end": review.get("window_end"),
            "total_pnl_attribution_usd": pnl.get("total_pnl_attribution_usd"),
            "win_rate": pnl.get("win_rate"),
            "total_exits": pnl.get("total_exits"),
            "blocked_total": review.get("blocked_total"),
            "learning_telemetry": review.get("learning_telemetry"),
            "how_to_proceed": review.get("how_to_proceed"),
        }

    tier2_summary = {
        "7d": _scope_summary(r7, "7d"),
        "30d": _scope_summary(r30, "30d"),
        "last100": _scope_summary(r100, "last100"),
    }

    # Counter-intelligence from first available review
    first_review = r7 or r30 or r100
    counter_intel: dict[str, Any] = {}
    if first_review:
        ci = first_review.get("counter_intelligence") or {}
        counter_intel["blocking_patterns"] = dict(list((ci.get("blocking_patterns") or {}).items())[:10])
        counter_intel["opportunity_cost_ranked_reasons"] = (ci.get("opportunity_cost_ranked_reasons") or [])[:10]
    else:
        counter_intel["note"] = "No comprehensive review data."

    rolling_promotion: dict[str, Any] = {}
    if csa_board:
        ranked = csa_board.get("ranked_configs") or []
        rolling_promotion["ranked_configs_count"] = len(ranked)
        rolling_promotion["scope"] = csa_board.get("scope", "shadow_only")
    else:
        rolling_promotion["note"] = "CSA_BOARD_REVIEW not found."

    appendices_paths = [
        "reports/board/7d_comprehensive_review.json",
        "reports/board/30d_comprehensive_review.json",
        "reports/board/last100_comprehensive_review.json",
        "reports/board/CSA_BOARD_REVIEW_*.json",
    ]

    return {
        "cover": cover,
        "tier2_summary": tier2_summary,
        "counter_intelligence": counter_intel,
        "rolling_promotion": rolling_promotion,
        "appendices_paths": appendices_paths,
    }


def payload_to_md(payload: dict[str, Any]) -> str:
    """Render TIER2_REVIEW.md from payload."""
    lines: list[str] = []
    cover = payload.get("cover") or {}
    lines.append("# Alpaca Tier 2 Board Review")
    lines.append("")
    lines.append(f"**Generated:** {cover.get('generated_ts')}")
    lines.append(f"**Base dir:** {cover.get('base_dir')}")
    lines.append("")
    lines.append("## 1. Cover — inputs loaded")
    lines.append("")
    for k, v in (cover.get("inputs_present") or {}).items():
        lines.append(f"- **{k}:** {'yes' if v else 'no'}")
    lines.append("")
    lines.append("---")
    lines.append("")

    t2 = payload.get("tier2_summary") or {}
    lines.append("## 2. Tier 2 summary")
    lines.append("")
    for scope_key in ("7d", "30d", "last100"):
        s = t2.get(scope_key) or {}
        lines.append(f"### {scope_key}")
        if not s.get("present"):
            lines.append("- Not found.")
            lines.append("")
            continue
        lines.append(f"- Window: {s.get('window_start')} to {s.get('window_end')}")
        lines.append(f"- Total PnL (attribution): {s.get('total_pnl_attribution_usd')}")
        lines.append(f"- Win rate: {s.get('win_rate')}")
        lines.append(f"- Total exits: {s.get('total_exits')}")
        lines.append(f"- Blocked total: {s.get('blocked_total')}")
        if s.get("how_to_proceed"):
            for rec in (s["how_to_proceed"] or [])[:5]:
                lines.append(f"- {rec}")
        lines.append("")
    lines.append("---")
    lines.append("")

    ci = payload.get("counter_intelligence") or {}
    lines.append("## 3. Counter-intelligence")
    lines.append("")
    if ci.get("note"):
        lines.append(ci["note"])
    else:
        for reason, count in (ci.get("blocking_patterns") or {}).items():
            lines.append(f"- `{reason}`: {count}")
        for item in (ci.get("opportunity_cost_ranked_reasons") or [])[:5]:
            lines.append(f"- Opportunity cost: {item.get('reason')} (count={item.get('blocked_count')}, est_cost={item.get('estimated_opportunity_cost_usd')})")
    lines.append("")
    lines.append("---")
    lines.append("")

    rp = payload.get("rolling_promotion") or {}
    lines.append("## 4. Rolling promotion (CSA_BOARD_REVIEW)")
    lines.append("")
    if rp.get("note"):
        lines.append(rp["note"])
    else:
        lines.append(f"- Ranked configs count: {rp.get('ranked_configs_count')}")
        lines.append(f"- Scope: {rp.get('scope')}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 5. Appendices (paths)")
    lines.append("")
    for p in payload.get("appendices_paths") or []:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("*End of Alpaca Tier 2 Board Review.*")
    return "\n".join(lines)


def _read_state(base: Path) -> dict[str, Any]:
    p = base / "state" / "alpaca_board_review_state.json"
    if not p.exists():
        return {}
    return _load_json(p) or {}


def _write_state(base: Path, tier2_run_ts: str, tier2_packet_dir: str) -> None:
    state = _read_state(base)
    state["tier2_last_run_ts"] = tier2_run_ts
    state["tier2_last_packet_dir"] = tier2_packet_dir
    state_path = base / "state" / "alpaca_board_review_state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Alpaca Tier 2 Board Review — generate Tier 2 packet (MD + JSON)")
    ap.add_argument("--base-dir", default="", help="Repo root (default: script repo parent)")
    ap.add_argument("--date", default="", help="Unused; for CLI compatibility")
    ap.add_argument("--force", action="store_true", help="Allow run")
    ap.add_argument("--dry-run", action="store_true", help="Build payload only; do not write")
    ap.add_argument("--telegram", action="store_true", help="Send one-line summary to Telegram (best-effort; failures logged)")
    args = ap.parse_args()

    base = Path(args.base_dir).resolve() if args.base_dir else DEFAULT_BASE
    if not base.is_dir():
        print(f"Base dir not found: {base}", file=sys.stderr)
        return 1

    generated_ts = datetime.now(timezone.utc).isoformat()
    sources = load_tier2_inputs(base)
    payload = build_tier2_payload(sources, generated_ts, str(base))

    if args.dry_run:
        print("DRY RUN — no files written")
        print(f"  Inputs present: {payload['cover'].get('inputs_present')}")
        print(f"  Payload keys: {list(payload.keys())}")
        return 0

    reports_dir = base / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    ts_dir = f"ALPACA_TIER2_REVIEW_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}"
    packet_dir = reports_dir / ts_dir
    packet_dir.mkdir(parents=True, exist_ok=True)
    md_path = packet_dir / "TIER2_REVIEW.md"
    json_path = packet_dir / "TIER2_REVIEW.json"

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

    try:
        _write_state(base, generated_ts, str(packet_dir))
    except Exception as e:
        print(f"Failed to write state: {e}", file=sys.stderr)
        return 1

    print(f"Tier 2 packet written: {packet_dir}")
    print(f"  {md_path.name}")
    print(f"  {json_path.name}")
    if args.telegram:
        try:
            if str(base) not in sys.path:
                sys.path.insert(0, str(base))
            from scripts.alpaca_telegram import send_governance_telegram
            send_governance_telegram(f"Alpaca Tier2 review: {packet_dir}", script_name="tier2")
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
