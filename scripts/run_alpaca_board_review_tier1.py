#!/usr/bin/env python3
"""
Alpaca Tier 1 (short-horizon) Board Review — packet generation.

Reads 1d/3d/5d rolling windows, 5d rolling PnL state, trade visibility (since-hours),
fast-lane ledger, and daily pack; produces Tier 1 Board Review packet (MD + JSON).
Updates state/alpaca_board_review_state.json (merge: adds tier1_* keys).

Alpaca US equities only. No cron, no promotion logic, no heartbeat.
Phase 2.

Usage:
  python scripts/run_alpaca_board_review_tier1.py [--base-dir PATH] [--date YYYY-MM-DD] [--since-hours 48] [--force] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
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


def _load_rolling_windows(base: Path, target_date: str) -> dict[str, Any]:
    """Call board.eod.rolling_windows.build_rolling_windows for 1, 3, 5 day."""
    if str(base) not in sys.path:
        sys.path.insert(0, str(base))
    try:
        from board.eod.rolling_windows import build_rolling_windows
        return build_rolling_windows(base, target_date, window_sizes=[1, 3, 5])
    except Exception:
        return {
            "date": target_date,
            "win_rate_by_window": {},
            "pnl_by_window": {},
            "exit_reason_counts_by_window": {},
            "blocked_trade_counts_by_window": {},
            "signal_decay_exit_rate_by_window": {},
            "windows": {},
        }


def _load_5d_rolling_state(base: Path) -> dict[str, Any] | None:
    """Last line of reports/state/rolling_pnl_5d.jsonl or latest ROLLING_PNL_5D_UPDATE_*.json."""
    jsonl_path = base / "reports" / "state" / "rolling_pnl_5d.jsonl"
    if jsonl_path.exists():
        lines = [ln.strip() for ln in jsonl_path.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()]
        if lines:
            try:
                return json.loads(lines[-1])
            except Exception:
                pass
    audit = base / "reports" / "audit"
    if audit.exists():
        candidates = list(audit.glob("ROLLING_PNL_5D_UPDATE_*.json"))
        if candidates:
            latest = max(candidates, key=lambda p: p.stat().st_mtime)
            return _load_json(latest)
    return None


def _trade_visibility_since_hours(base: Path, since_hours: float) -> dict[str, Any]:
    """Count executed and telemetry-backed in last since_hours from attribution/exit_attribution."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)
    cutoff_ts = cutoff.timestamp()
    executed = 0
    telemetry_backed = 0
    total_exit = 0

    def parse_ts(v: Any) -> float | None:
        if v is None:
            return None
        try:
            if isinstance(v, (int, float)):
                return float(v)
            s = str(v).replace("Z", "+00:00")[:26]
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.timestamp()
        except Exception:
            return None

    exit_path = base / "logs" / "exit_attribution.jsonl"
    if exit_path.exists():
        for line in exit_path.read_text(encoding="utf-8", errors="replace").splitlines()[-3000:]:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                ts = parse_ts(rec.get("timestamp") or rec.get("exit_ts") or rec.get("ts"))
                if ts is None or ts < cutoff_ts:
                    continue
                total_exit += 1
                embed = rec.get("direction_intel_embed")
                if isinstance(embed, dict) and embed.get("intel_snapshot_entry"):
                    telemetry_backed += 1
            except Exception:
                continue

    attr_path = base / "logs" / "attribution.jsonl"
    if attr_path.exists():
        for line in attr_path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                if rec.get("type") != "attribution" or str(rec.get("trade_id", "")).startswith("open_"):
                    continue
                ts = parse_ts(rec.get("ts") or rec.get("timestamp"))
                if ts is None or ts < cutoff_ts:
                    continue
                executed += 1
            except Exception:
                continue

    return {
        "since_hours": since_hours,
        "cutoff_utc": cutoff.isoformat(),
        "executed_in_window": executed,
        "exit_attribution_total": total_exit,
        "telemetry_backed": telemetry_backed,
    }


def _load_fast_lane(base: Path) -> dict[str, Any] | None:
    """Load fast-lane ledger; file may be list (cycles) or dict."""
    raw = _load_json(base / "state" / "fast_lane_experiment" / "fast_lane_ledger.json")
    if raw is None:
        return None
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, list):
        cycles = raw
        return {
            "cycles": cycles,
            "total_trades": sum(c.get("trade_count", 0) for c in cycles if isinstance(c, dict)),
            "cumulative_pnl": sum(c.get("pnl_usd", 0) for c in cycles if isinstance(c, dict)),
        }
    return None


def _daily_pack_present(base: Path, date_str: str) -> bool:
    pack_dir = base / "reports" / "stockbot" / date_str
    if not pack_dir.is_dir():
        return False
    return (pack_dir / "STOCK_EOD_SUMMARY.json").exists() or (pack_dir / "STOCK_EOD_SUMMARY.md").exists()


def load_tier1_inputs(base: Path, date_str: str, since_hours: float) -> dict[str, Any]:
    """Load all Tier 1 inputs."""
    rolling = _load_rolling_windows(base, date_str)
    rolling_5d_state = _load_5d_rolling_state(base)
    visibility = _trade_visibility_since_hours(base, since_hours)
    fast_lane = _load_fast_lane(base)
    daily_pack = _daily_pack_present(base, date_str)
    return {
        "rolling_windows": rolling,
        "rolling_pnl_5d": rolling_5d_state,
        "trade_visibility": visibility,
        "fast_lane": fast_lane,
        "daily_pack_present": daily_pack,
    }


def build_tier1_payload(sources: dict[str, Any], generated_ts: str, base_dir: str) -> dict[str, Any]:
    """Build TIER1_REVIEW.json payload."""
    rw = sources.get("rolling_windows") or {}
    r5 = sources.get("rolling_pnl_5d")
    vis = sources.get("trade_visibility") or {}
    fl = sources.get("fast_lane")
    daily = sources.get("daily_pack_present")

    inputs_present = {
        "rolling_1_3_5": bool(rw.get("pnl_by_window")),
        "rolling_pnl_5d": r5 is not None,
        "trade_visibility": True,
        "fast_lane": fl is not None,
        "daily_pack": daily,
    }

    cover = {
        "title": "Alpaca Tier 1 Board Review",
        "generated_ts": generated_ts,
        "base_dir": base_dir,
        "inputs_present": inputs_present,
    }

    tier1_summary = {
        "pnl_by_window": rw.get("pnl_by_window"),
        "win_rate_by_window": rw.get("win_rate_by_window"),
        "rolling_5d_last_point": r5,
        "trade_visibility": vis,
        "fast_lane_total_trades": fl.get("total_trades") if fl else None,
        "fast_lane_cumulative_pnl": fl.get("cumulative_pnl") if fl else None,
        "fast_lane_cycles_count": len(fl.get("cycles") or []) if fl else 0,
        "daily_pack_present": daily,
    }

    short_horizon = {
        "exit_reason_counts_by_window": rw.get("exit_reason_counts_by_window"),
        "blocked_trade_counts_by_window": rw.get("blocked_trade_counts_by_window"),
        "signal_decay_exit_rate_by_window": rw.get("signal_decay_exit_rate_by_window"),
    }

    appendices_paths = [
        "logs/attribution.jsonl",
        "logs/exit_attribution.jsonl",
        "reports/state/rolling_pnl_5d.jsonl",
        "state/fast_lane_experiment/fast_lane_ledger.json",
    ]

    return {
        "cover": cover,
        "tier1_summary": tier1_summary,
        "short_horizon_metrics": short_horizon,
        "appendices_paths": appendices_paths,
    }


def payload_to_md(payload: dict[str, Any]) -> str:
    """Render TIER1_REVIEW.md from payload."""
    lines: list[str] = []
    cover = payload.get("cover") or {}
    lines.append("# Alpaca Tier 1 Board Review")
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

    t1 = payload.get("tier1_summary") or {}
    lines.append("## 2. Tier 1 summary")
    lines.append("")
    lines.append(f"- **PnL by window:** {t1.get('pnl_by_window')}")
    lines.append(f"- **Win rate by window:** {t1.get('win_rate_by_window')}")
    lines.append(f"- **5d rolling last point:** {t1.get('rolling_5d_last_point')}")
    vis = t1.get("trade_visibility") or {}
    lines.append(f"- **Trade visibility (since_hours):** executed={vis.get('executed_in_window')}, exit_total={vis.get('exit_attribution_total')}, telemetry_backed={vis.get('telemetry_backed')}")
    lines.append(f"- **Fast-lane total_trades:** {t1.get('fast_lane_total_trades')}, cumulative_pnl: {t1.get('fast_lane_cumulative_pnl')}, cycles: {t1.get('fast_lane_cycles_count')}")
    lines.append(f"- **Daily pack present:** {t1.get('daily_pack_present')}")
    lines.append("")
    lines.append("---")
    lines.append("")

    sh = payload.get("short_horizon_metrics") or {}
    lines.append("## 3. Short-horizon metrics")
    lines.append("")
    lines.append("Exit reason counts (by window):")
    for k, v in (sh.get("exit_reason_counts_by_window") or {}).items():
        lines.append(f"- **{k}:** {v}")
    lines.append("")
    lines.append("Blocked trade counts (by window):")
    for k, v in (sh.get("blocked_trade_counts_by_window") or {}).items():
        lines.append(f"- **{k}:** {v}")
    lines.append("")
    lines.append("Signal decay exit rate (by window):")
    for k, v in (sh.get("signal_decay_exit_rate_by_window") or {}).items():
        lines.append(f"- **{k}:** {v}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 4. Appendices (paths)")
    lines.append("")
    for p in payload.get("appendices_paths") or []:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("*End of Alpaca Tier 1 Board Review.*")
    return "\n".join(lines)


def _read_state(base: Path) -> dict[str, Any]:
    p = base / "state" / "alpaca_board_review_state.json"
    if not p.exists():
        return {}
    return _load_json(p) or {}


def _write_state(base: Path, tier1_run_ts: str, tier1_packet_dir: str) -> None:
    state = _read_state(base)
    state["tier1_last_run_ts"] = tier1_run_ts
    state["tier1_last_packet_dir"] = tier1_packet_dir
    state_path = base / "state" / "alpaca_board_review_state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Alpaca Tier 1 Board Review — generate Tier 1 packet (MD + JSON)")
    ap.add_argument("--base-dir", default="", help="Repo root (default: script repo parent)")
    ap.add_argument("--date", default="", help="YYYY-MM-DD for rolling windows (default: today UTC)")
    ap.add_argument("--since-hours", type=float, default=48, help="Hours for trade visibility window (default 48)")
    ap.add_argument("--force", action="store_true", help="Allow run")
    ap.add_argument("--dry-run", action="store_true", help="Build payload only; do not write")
    ap.add_argument("--telegram", action="store_true", help="Send one-line summary to Telegram (best-effort; failures logged)")
    args = ap.parse_args()

    base = Path(args.base_dir).resolve() if args.base_dir else DEFAULT_BASE
    if not base.is_dir():
        print(f"Base dir not found: {base}", file=sys.stderr)
        return 1

    date_str = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    generated_ts = datetime.now(timezone.utc).isoformat()

    sources = load_tier1_inputs(base, date_str, args.since_hours)
    payload = build_tier1_payload(sources, generated_ts, str(base))

    if args.dry_run:
        print("DRY RUN — no files written")
        print(f"  Inputs present: {payload['cover'].get('inputs_present')}")
        print(f"  Payload keys: {list(payload.keys())}")
        return 0

    reports_dir = base / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    ts_dir = f"ALPACA_TIER1_REVIEW_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}"
    packet_dir = reports_dir / ts_dir
    packet_dir.mkdir(parents=True, exist_ok=True)
    md_path = packet_dir / "TIER1_REVIEW.md"
    json_path = packet_dir / "TIER1_REVIEW.json"

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

    print(f"Tier 1 packet written: {packet_dir}")
    print(f"  {md_path.name}")
    print(f"  {json_path.name}")
    if args.telegram:
        try:
            if str(base) not in sys.path:
                sys.path.insert(0, str(base))
            from scripts.alpaca_telegram import send_governance_telegram
            send_governance_telegram(f"Alpaca Tier1 review: {packet_dir}", script_name="tier1")
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
