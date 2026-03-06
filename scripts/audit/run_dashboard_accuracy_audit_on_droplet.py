#!/usr/bin/env python3
"""
Dashboard data accuracy audit: run ON THE DROPLET (or with --local for dev).
Verifies every key data source is real, consistent, and not stale.
Outputs JSON to stdout for CSA/board/SRE report generation.

Checks:
- File existence, mtime, and key numbers for all dashboard data sources
- Cross-checks: exit_attribution line count vs direction_readiness; TRADE_CSA_STATE path (prod vs test)
- Staleness: direction_readiness mtime vs now; combined report date vs today
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _mtime_iso(p: Path) -> str | None:
    if not p.exists():
        return None
    try:
        return datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).isoformat()
    except Exception:
        return None


def _line_count(p: Path) -> int:
    if not p.exists():
        return 0
    try:
        return sum(1 for ln in p.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip())
    except Exception:
        return 0


def _read_json(p: Path, default: dict | None = None) -> dict:
    if default is None:
        default = {}
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def run_audit(base_dir: Path) -> dict:
    now = _now_utc()
    today = now.strftime("%Y-%m-%d")
    state_dir = base_dir / "state"
    logs_dir = base_dir / "logs"
    reports_dir = base_dir / "reports"
    audit_dir = reports_dir / "audit"
    board_dir = reports_dir / "board"
    state_csa = reports_dir / "state"
    state_csa_test = state_csa / "test_csa_100"

    # --- Primary sources ---
    direction_readiness_path = state_dir / "direction_readiness.json"
    direction_replay_path = state_dir / "direction_replay_status.json"
    exit_attribution_path = logs_dir / "exit_attribution.jsonl"
    attribution_path = logs_dir / "attribution.jsonl"

    trade_csa_prod = state_csa / "TRADE_CSA_STATE.json"
    trade_csa_test_file = state_csa_test / "TRADE_CSA_STATE.json"
    trade_events_log = state_csa / "trade_events.jsonl"

    csa_verdict_path = audit_dir / "CSA_VERDICT_LATEST.json"
    cockpit_path = board_dir / "PROFITABILITY_COCKPIT.md"
    combined_today_path = reports_dir / f"{today}_stock-bot_combined.json"

    # --- Read and compute ---
    exit_lines = _line_count(exit_attribution_path)
    attribution_lines = _line_count(attribution_path)
    trade_events_lines = _line_count(trade_events_log)

    direction_readiness = _read_json(direction_readiness_path)
    dr_all_time = int(direction_readiness.get("all_time_exits") or 0)
    dr_total_trades = int(direction_readiness.get("total_trades") or 0)
    dr_telemetry_trades = int(direction_readiness.get("telemetry_trades") or 0)
    dr_updated_ts = direction_readiness.get("updated_ts") or _mtime_iso(direction_readiness_path)

    # Which TRADE_CSA_STATE does the dashboard use? Prod exists => prod; else test.
    csa_prod_exists = trade_csa_prod.exists()
    csa_test_exists = trade_csa_test_file.exists()
    dashboard_uses_csa_path = "reports/state/TRADE_CSA_STATE.json" if csa_prod_exists else (
        "reports/state/test_csa_100/TRADE_CSA_STATE.json" if csa_test_exists else None
    )
    csa_state_path = trade_csa_prod if csa_prod_exists else (trade_csa_test_file if csa_test_exists else None)
    csa_state = _read_json(csa_state_path) if csa_state_path else {}
    csa_total_events = int(csa_state.get("total_trade_events") or 0)
    csa_last_mission = csa_state.get("last_csa_mission_id") or csa_state.get("mission_id") or ""

    csa_verdict = _read_json(csa_verdict_path)
    cockpit_exists = cockpit_path.exists()
    cockpit_mtime = _mtime_iso(cockpit_path)
    combined_exists = combined_today_path.exists()
    combined_mtime = _mtime_iso(combined_today_path)

    # Staleness: direction_readiness updated within last 24h?
    dr_fresh = False
    if dr_updated_ts:
        try:
            # Parse ISO
            ts = dr_updated_ts.replace("Z", "+00:00")[:26]
            if "+" in ts or ts.endswith("Z"):
                dt = datetime.fromisoformat(ts)
            else:
                dt = datetime.fromisoformat(ts[:19]).replace(tzinfo=timezone.utc)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            age_h = (now - dt).total_seconds() / 3600
            dr_fresh = age_h < 24
        except Exception:
            dr_fresh = False

    # Cross-checks
    # 1) direction_readiness.all_time_exits should equal exit_attribution line count (cron recomputes from file)
    all_time_matches_file = dr_all_time == exit_lines if (direction_readiness_path.exists() and exit_attribution_path.exists()) else None
    # 2) If we use test_csa_100, that's wrong for production
    csa_uses_production = csa_prod_exists and dashboard_uses_csa_path and "test_csa_100" not in (dashboard_uses_csa_path or "")
    # 3) trade_events.jsonl line count vs TRADE_CSA_STATE.total_trade_events (can differ if not reconciled)
    csa_log_reconciled = (trade_events_lines == csa_total_events) if (trade_events_log.exists() and csa_state) else None

    out = {
        "audit_ts_utc": now.isoformat(),
        "today_utc": today,
        "base_dir": str(base_dir),
        "sources": {
            "state/direction_readiness.json": {
                "exists": direction_readiness_path.exists(),
                "mtime_iso": _mtime_iso(direction_readiness_path),
                "all_time_exits": dr_all_time,
                "total_trades": dr_total_trades,
                "telemetry_trades": dr_telemetry_trades,
                "updated_ts": dr_updated_ts,
                "fresh_within_24h": dr_fresh,
            },
            "state/direction_replay_status.json": {
                "exists": direction_replay_path.exists(),
                "mtime_iso": _mtime_iso(direction_replay_path),
            },
            "logs/exit_attribution.jsonl": {
                "exists": exit_attribution_path.exists(),
                "mtime_iso": _mtime_iso(exit_attribution_path),
                "line_count": exit_lines,
            },
            "logs/attribution.jsonl": {
                "exists": attribution_path.exists(),
                "line_count": attribution_lines,
                "mtime_iso": _mtime_iso(attribution_path),
            },
            "reports/state/TRADE_CSA_STATE.json": {
                "exists": csa_prod_exists,
                "mtime_iso": _mtime_iso(trade_csa_prod),
                "total_trade_events": csa_total_events if csa_prod_exists else None,
                "last_csa_mission_id": csa_last_mission if csa_prod_exists else None,
            },
            "reports/state/test_csa_100/TRADE_CSA_STATE.json": {
                "exists": csa_test_exists,
                "mtime_iso": _mtime_iso(trade_csa_test_file),
                "used_only_if_prod_missing": not csa_prod_exists and csa_test_exists,
            },
            "reports/state/trade_events.jsonl": {
                "exists": trade_events_log.exists(),
                "line_count": trade_events_lines,
            },
            "reports/audit/CSA_VERDICT_LATEST.json": {
                "exists": csa_verdict_path.exists(),
                "mtime_iso": _mtime_iso(csa_verdict_path),
                "mission_id": csa_verdict.get("mission_id"),
                "verdict": csa_verdict.get("verdict"),
            },
            "reports/board/PROFITABILITY_COCKPIT.md": {
                "exists": cockpit_exists,
                "mtime_iso": cockpit_mtime,
            },
            f"reports/{today}_stock-bot_combined.json": {
                "exists": combined_exists,
                "mtime_iso": combined_mtime,
            },
        },
        "dashboard_csa_path_used": dashboard_uses_csa_path,
        "cross_checks": {
            "direction_readiness_all_time_matches_exit_attribution_lines": all_time_matches_file,
            "csa_state_is_production_not_test": csa_uses_production,
            "trade_events_log_matches_csa_total": csa_log_reconciled,
        },
        "findings": [],
    }

    # Append findings
    if all_time_matches_file is False:
        out["findings"].append("MISMATCH: direction_readiness.all_time_exits != exit_attribution.jsonl line count (stale or wrong number)")
    if not csa_uses_production and csa_test_exists:
        out["findings"].append("WRONG_SOURCE: Dashboard would use test_csa_100 TRADE_CSA_STATE (test data, not production)")
    if not dr_fresh and direction_readiness_path.exists():
        out["findings"].append("STALE: direction_readiness.json not updated in 24h (cron may not be running)")
    if not direction_readiness_path.exists():
        out["findings"].append("MISSING: state/direction_readiness.json (Learning & Readiness tab will show zeros or fallback)")
    if not exit_attribution_path.exists():
        out["findings"].append("MISSING: logs/exit_attribution.jsonl (no exit attribution data)")
    if csa_log_reconciled is False:
        out["findings"].append("MISMATCH: trade_events.jsonl line count != TRADE_CSA_STATE.total_trade_events (reconcile_state_from_log)")
    if not combined_exists:
        out["findings"].append(f"MISSING: reports/{today}_stock-bot_combined.json (Situation strip / strategy comparison may be empty for today)")

    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Dashboard data accuracy audit (run on droplet)")
    ap.add_argument("--local", action="store_true", help="Run against local repo (default: cwd)")
    ap.add_argument("--base-dir", type=Path, default=None, help="Repo root (default: auto)")
    args = ap.parse_args()
    base = args.base_dir or REPO
    if args.local:
        base = base.resolve()
    result = run_audit(base)
    print(json.dumps(result, indent=2, default=str))
    return 0 if not result.get("findings") else 1


if __name__ == "__main__":
    sys.exit(main())
