#!/usr/bin/env python3
"""
Alpaca Promotion Gate — advisory gate status from convergence, Tier 2/3, shadow, SRE.

Reads convergence state, Tier 2/3 packets (or board fallbacks), shadow comparison,
and SRE status; writes state/alpaca_promotion_gate_state.json with gate_ready and blockers.
Advisory only; no auto-promotion. Human approval required for any promotion.

Alpaca-native only. No Kraken references.

Usage:
  python scripts/run_alpaca_promotion_gate.py [--base-dir PATH] [--force] [--dry-run]
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


def _resolve_packet_dir(base: Path, packet_dir: str) -> Path:
    if Path(packet_dir).is_absolute():
        return Path(packet_dir)
    return base / packet_dir


def _tier2_ok(base: Path, board_state: dict[str, Any]) -> bool:
    """Tier 2 packet or board 7d/30d/last100 present with total_pnl_attribution_usd."""
    packet_dir = board_state.get("tier2_last_packet_dir")
    if packet_dir:
        p = _resolve_packet_dir(base, packet_dir)
        tier2 = _load_json(p / "TIER2_REVIEW.json")
        if tier2:
            summary = tier2.get("tier2_summary") or {}
            for scope in ("7d", "30d", "last100"):
                block = summary.get(scope) or {}
                if block.get("present") and "total_pnl_attribution_usd" in block:
                    return True
    board = base / "reports" / "board"
    for name in ("7d_comprehensive_review.json", "30d_comprehensive_review.json", "last100_comprehensive_review.json"):
        rev = _load_json(board / name)
        if rev and (rev.get("pnl") or {}).get("total_pnl_attribution_usd") is not None:
            return True
    return False


def _tier3_ok(base: Path, board_state: dict[str, Any]) -> bool:
    """Tier 3 packet or last387 review present with total_pnl_attribution_usd."""
    packet_dir = board_state.get("last_packet_dir")
    if packet_dir:
        p = _resolve_packet_dir(base, packet_dir)
        tier3 = _load_json(p / "BOARD_REVIEW.json")
        if tier3:
            summary = tier3.get("tier3_summary") or {}
            if summary.get("total_pnl_attribution_usd") is not None:
                return True
    rev = _load_json(base / "reports" / "board" / "last387_comprehensive_review.json")
    if rev and (rev.get("pnl") or {}).get("total_pnl_attribution_usd") is not None:
        return True
    return False


def _shadow_nomination(base: Path) -> str | None:
    """Nomination from SHADOW_COMPARISON_LAST387.json or None if missing."""
    shadow = _load_json(base / "reports" / "board" / "SHADOW_COMPARISON_LAST387.json")
    if not shadow:
        return None
    nom = shadow.get("nomination")
    if not nom or not isinstance(nom, str) or not nom.strip():
        return None
    nom = nom.strip()
    if nom.startswith("Advance") or nom in ("Hold", "Discard"):
        return nom
    return None


def _sre_anomaly(base: Path) -> bool:
    """True if SRE reports anomaly (same as Phase 3)."""
    sre = _load_json(base / "reports" / "audit" / "SRE_STATUS.json")
    if not sre:
        return False
    status = (sre.get("overall_status") or "").strip().upper()
    if status not in ("OK", "HEALTHY"):
        return True
    if sre.get("automation_anomalies_present") is True:
        return True
    return False


def run(base: Path, dry_run: bool) -> dict[str, Any]:
    conv_path = base / "state" / "alpaca_convergence_state.json"
    board_path = base / "state" / "alpaca_board_review_state.json"
    conv = _load_json(conv_path) or {}
    board_state = _load_json(board_path) or {}

    divergence_class = conv.get("divergence_class") or "unknown"
    convergence_severe = divergence_class == "severe"

    tier2_ok = _tier2_ok(base, board_state)
    tier3_ok = _tier3_ok(base, board_state)
    shadow_nom = _shadow_nomination(base)
    shadow_ok = shadow_nom is not None
    sre_anom = _sre_anomaly(base)

    blockers: list[str] = []
    if not tier2_ok:
        blockers.append("tier2_missing")
    if not tier3_ok:
        blockers.append("tier3_missing")
    if convergence_severe:
        blockers.append("severe_divergence")
    if not shadow_ok:
        blockers.append("missing_shadow_comparison")
    if sre_anom:
        blockers.append("sre_anomaly")

    gate_ready = tier2_ok and tier3_ok and not convergence_severe and shadow_ok and not sre_anom

    if gate_ready:
        one_liner = f"Gate ready (advisory). Shadow nomination: {shadow_nom}. Human approval required for promotion."
    else:
        one_liner = f"Gate blocked: {', '.join(blockers)}. Human review required."

    out = {
        "last_run_ts": datetime.now(timezone.utc).isoformat(),
        "gate_ready": gate_ready,
        "blockers": blockers,
        "convergence_divergence_class": divergence_class,
        "shadow_nomination": shadow_nom,
        "sre_anomaly": sre_anom,
        "tier2_ok": tier2_ok,
        "tier3_ok": tier3_ok,
        "one_liner": one_liner,
    }

    if dry_run:
        print("gate_ready:", gate_ready)
        print("blockers:", blockers)
        print("one_liner:", one_liner)
        return out

    state_out_path = base / "state" / "alpaca_promotion_gate_state.json"
    try:
        state_out_path.parent.mkdir(parents=True, exist_ok=True)
        state_out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"Failed to write {state_out_path}: {e}", file=sys.stderr)
        sys.exit(1)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Alpaca promotion gate (advisory; human approval required).")
    ap.add_argument("--base-dir", type=Path, default=DEFAULT_BASE, help="Repo root")
    ap.add_argument("--force", action="store_true", help="Run even if state exists")
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
            send_governance_telegram(f"Alpaca Gate: {out.get('one_liner', '')}", script_name="promotion_gate")
        except Exception:
            pass


if __name__ == "__main__":
    main()
