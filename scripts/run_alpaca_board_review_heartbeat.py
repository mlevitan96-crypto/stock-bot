#!/usr/bin/env python3
"""
Alpaca Board Review Heartbeat — record last run and Tier 1/2/3 timestamps; optional staleness.

Reads alpaca_board_review_state.json and alpaca_convergence_state.json; writes
state/alpaca_heartbeat_state.json with last_heartbeat_ts, tier timestamps, and stale flag.
No decisions, no tuning, no promotion. Advisory only.

Alpaca US equities only.

Usage:
  python scripts/run_alpaca_board_review_heartbeat.py [--base-dir PATH] [--stale-hours 24] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone, timedelta
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


def _parse_ts(ts: str | None) -> datetime | None:
    if not ts or not isinstance(ts, str):
        return None
    ts = ts.strip()
    if not ts:
        return None
    try:
        # ISO8601 with Z or +00:00
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None


def run(base: Path, stale_hours: float, dry_run: bool) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    board_path = base / "state" / "alpaca_board_review_state.json"
    conv_path = base / "state" / "alpaca_convergence_state.json"
    board = _load_json(board_path) or {}
    conv = _load_json(conv_path) or {}

    tier1_ts = board.get("tier1_last_run_ts")
    tier2_ts = board.get("tier2_last_run_ts")
    tier3_ts = board.get("last_run_ts")
    conv_ts = conv.get("last_run_ts")

    tier1_dt = _parse_ts(tier1_ts)
    tier2_dt = _parse_ts(tier2_ts)
    tier3_dt = _parse_ts(tier3_ts)
    conv_dt = _parse_ts(conv_ts)

    cutoff = now - timedelta(hours=stale_hours)
    stale = False
    if tier1_dt is None or tier1_dt < cutoff:
        stale = True
    if tier2_dt is None or tier2_dt < cutoff:
        stale = True
    if tier3_dt is None or tier3_dt < cutoff:
        stale = True

    if stale:
        one_liner = f"Heartbeat: at least one tier stale (>{stale_hours}h) or missing."
    else:
        one_liner = "Heartbeat OK; all tiers fresh."

    out = {
        "last_heartbeat_ts": now.isoformat(),
        "tier1_last_run_ts": tier1_ts,
        "tier2_last_run_ts": tier2_ts,
        "tier3_last_run_ts": tier3_ts,
        "convergence_last_run_ts": conv_ts,
        "stale_interval_hours": stale_hours,
        "stale": stale,
        "one_liner": one_liner,
    }

    if dry_run:
        print("one_liner:", one_liner)
        print("stale:", stale)
        return out

    state_out_path = base / "state" / "alpaca_heartbeat_state.json"
    try:
        state_out_path.parent.mkdir(parents=True, exist_ok=True)
        state_out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"Failed to write {state_out_path}: {e}", file=sys.stderr)
        sys.exit(1)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Alpaca board review heartbeat (advisory).")
    ap.add_argument("--base-dir", type=Path, default=DEFAULT_BASE, help="Repo root")
    ap.add_argument("--stale-hours", type=float, default=24.0, help="Hours after which a tier is considered stale")
    ap.add_argument("--force", action="store_true", help="Allow run (no-op; for E2E CLI compatibility)")
    ap.add_argument("--dry-run", action="store_true", help="Print summary only; do not write state")
    ap.add_argument("--telegram", action="store_true", help="Send one-line summary to Telegram (best-effort; failures logged)")
    args = ap.parse_args()
    base = args.base_dir.resolve()
    out = run(base, stale_hours=args.stale_hours, dry_run=args.dry_run)
    if not args.dry_run and args.telegram:
        try:
            repo = base  # base is repo when from main()
            if str(repo) not in sys.path:
                sys.path.insert(0, str(repo))
            from scripts.alpaca_telegram import send_governance_telegram
            send_governance_telegram(f"Alpaca Heartbeat: {out.get('one_liner', '')}", script_name="heartbeat")
        except Exception:
            pass


if __name__ == "__main__":
    main()
