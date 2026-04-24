#!/usr/bin/env python3
"""
Alpaca Convergence Check — Tier1 vs Tier2 vs Tier3 sign consistency.

Reads Tier 1/2/3 packets (or board/state fallbacks) and SRE_STATUS; produces
state/alpaca_convergence_state.json with convergence_status and divergence_class.
Advisory only; no auto-block, no promotion logic.

Alpaca US equities only.

Usage:
  python scripts/run_alpaca_convergence_check.py [--base-dir PATH] [--force] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

REPO = Path(__file__).resolve().parents[1]
DEFAULT_BASE = REPO

Sign = Literal["positive", "negative", "zero", "missing"]
ConvergenceStatus = Literal["green", "yellow", "red"]
DivergenceClass = Literal["none", "mild", "moderate", "severe"]


def _load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _pnl_to_sign(pnl: float | None) -> Sign:
    if pnl is None:
        return "missing"
    if pnl > 0:
        return "positive"
    if pnl < 0:
        return "negative"
    return "zero"


def _resolve_packet_dir(base: Path, packet_dir: str) -> Path:
    if Path(packet_dir).is_absolute():
        return Path(packet_dir)
    return base / packet_dir


def _get_tier1_5d_sign(base: Path, state: dict[str, Any]) -> tuple[Sign, str]:
    """From Tier1 packet or reports/state/rolling_pnl_5d.jsonl. Returns (sign, source)."""
    packet_dir = state.get("tier1_last_packet_dir")
    if packet_dir:
        p = _resolve_packet_dir(base, packet_dir)
        tier1 = _load_json(p / "TIER1_REVIEW.json")
        if tier1:
            summary = tier1.get("tier1_summary") or {}
            r5 = summary.get("rolling_5d_last_point") or {}
            pnl = r5.get("pnl")
            if pnl is not None:
                return _pnl_to_sign(float(pnl)), "tier1_packet"
    jsonl = base / "reports" / "state" / "rolling_pnl_5d.jsonl"
    if jsonl.exists():
        lines = [ln.strip() for ln in jsonl.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()]
        if lines:
            try:
                last = json.loads(lines[-1])
                pnl = last.get("pnl") if isinstance(last, dict) else None
                if pnl is not None:
                    return _pnl_to_sign(float(pnl)), "rolling_5d"
            except Exception:
                pass
    return "missing", "none"


def _get_tier2_sign(base: Path, state: dict[str, Any]) -> tuple[Sign, str]:
    """From Tier2 packet or board 7d/30d/last100. Returns (sign, source)."""
    packet_dir = state.get("tier2_last_packet_dir")
    if packet_dir:
        p = _resolve_packet_dir(base, packet_dir)
        tier2 = _load_json(p / "TIER2_REVIEW.json")
        if tier2:
            summary = tier2.get("tier2_summary") or {}
            for scope in ("7d", "30d", "last100"):
                block = summary.get(scope) or {}
                if block.get("present") and "total_pnl_attribution_usd" in block:
                    pnl = block.get("total_pnl_attribution_usd")
                    return _pnl_to_sign(float(pnl) if pnl is not None else None), "tier2_packet"
    board = base / "reports" / "board"
    for name in ("7d_comprehensive_review.json", "30d_comprehensive_review.json", "last100_comprehensive_review.json"):
        rev = _load_json(board / name)
        if rev:
            pnl = (rev.get("pnl") or {}).get("total_pnl_attribution_usd")
            if pnl is not None:
                return _pnl_to_sign(float(pnl)), f"board_{name.replace('_comprehensive_review.json', '')}"
    return "missing", "none"


def _get_tier3_sign(base: Path, state: dict[str, Any]) -> tuple[Sign, str]:
    """From Tier3 packet or last387 comprehensive review. Returns (sign, source)."""
    packet_dir = state.get("last_packet_dir")
    if packet_dir:
        p = _resolve_packet_dir(base, packet_dir)
        tier3 = _load_json(p / "BOARD_REVIEW.json")
        if tier3:
            summary = tier3.get("tier3_summary") or {}
            pnl = summary.get("total_pnl_attribution_usd")
            if pnl is not None:
                return _pnl_to_sign(float(pnl)), "tier3_packet"
    rev = _load_json(base / "reports" / "board" / "last387_comprehensive_review.json")
    if rev:
        pnl = (rev.get("pnl") or {}).get("total_pnl_attribution_usd")
        if pnl is not None:
            return _pnl_to_sign(float(pnl)), "board_last387"
    return "missing", "none"


def _sre_anomaly(base: Path) -> bool:
    """True if SRE reports anomaly."""
    sre = _load_json(base / "reports" / "audit" / "SRE_STATUS.json")
    if not sre:
        return False
    status = (sre.get("overall_status") or "").strip().upper()
    if status not in ("OK", "HEALTHY"):
        return True
    if sre.get("automation_anomalies_present") is True:
        return True
    return False


def _classify(
    t1: Sign, t2: Sign, t3: Sign, sre_anomaly: bool
) -> tuple[ConvergenceStatus, DivergenceClass, str]:
    if t1 == "missing" and t2 == "missing" and t3 == "missing":
        return "yellow", "mild", "Missing Tier1/2/3 data; cannot assess convergence."
    signs = [s for s in (t1, t2, t3) if s != "missing"]
    if not signs:
        return "yellow", "mild", "Missing Tier1/2/3 data; cannot assess convergence."
    # Check contradiction: at least one positive and one negative
    has_pos = any(s == "positive" for s in signs)
    has_neg = any(s == "negative" for s in signs)
    if has_pos and has_neg and sre_anomaly:
        return "red", "severe", "Divergence plus SRE anomaly; human review required."
    if has_pos and has_neg:
        return "yellow", "moderate", "Short-term (5d) underperforming vs cohort (Tier2/Tier3)."
    if sre_anomaly:
        return "yellow", "moderate", "SRE anomaly; human review recommended."
    return "green", "none", "Tier1/Tier2/Tier3 signs consistent; no SRE anomaly."


def run(base: Path, dry_run: bool) -> dict[str, Any]:
    state_path = base / "state" / "alpaca_board_review_state.json"
    board_state = _load_json(state_path) or {}

    t1_sign, t1_src = _get_tier1_5d_sign(base, board_state)
    t2_sign, t2_src = _get_tier2_sign(base, board_state)
    t3_sign, t3_src = _get_tier3_sign(base, board_state)
    sre_anom = _sre_anomaly(base)

    status, div_class, one_liner = _classify(t1_sign, t2_sign, t3_sign, sre_anom)

    out = {
        "last_run_ts": datetime.now(timezone.utc).isoformat(),
        "tier1_5d_sign": t1_sign,
        "tier2_sign": t2_sign,
        "tier3_sign": t3_sign,
        "sre_anomaly": sre_anom,
        "convergence_status": status,
        "divergence_class": div_class,
        "one_liner": one_liner,
        "sources_used": {
            "tier1": t1_src,
            "tier2": t2_src,
            "tier3": t3_src,
            "sre_status": "reports/audit/SRE_STATUS.json",
        },
    }

    if dry_run:
        print("one_liner:", one_liner)
        print("convergence_status:", status)
        print("divergence_class:", div_class)
        return out

    state_out_path = base / "state" / "alpaca_convergence_state.json"
    try:
        state_out_path.parent.mkdir(parents=True, exist_ok=True)
        state_out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"Failed to write {state_out_path}: {e}", file=sys.stderr)
        sys.exit(1)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Alpaca convergence check (Tier1 vs Tier2 vs Tier3).")
    ap.add_argument("--base-dir", type=Path, default=DEFAULT_BASE, help="Repo root")
    ap.add_argument("--force", action="store_true", help="Run even if state exists (no-op for convergence)")
    ap.add_argument("--dry-run", action="store_true", help="Print summary only; do not write state")
    ap.add_argument("--telegram", action="store_true", help="Send one-line summary to Telegram (best-effort; failures logged)")
    args = ap.parse_args()
    base = args.base_dir.resolve()
    out = run(base, dry_run=args.dry_run)
    if not args.dry_run and args.telegram:
        try:
            if str(REPO) not in sys.path:
                sys.path.insert(0, str(REPO))
            from scripts.alpaca_telegram import send_governance_telegram
            send_governance_telegram(
                f"Alpaca Convergence: {out.get('convergence_status')} — {out.get('one_liner', '')}",
                script_name="convergence",
            )
        except Exception:
            pass


if __name__ == "__main__":
    main()
