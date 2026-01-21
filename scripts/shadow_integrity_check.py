#!/usr/bin/env python3
"""
Shadow trading integrity + gap analysis orchestrator (repo-native)

Run from project root:
    python scripts/shadow_integrity_check.py

Notes (repo defaults):
- UW health sentinel: state/uw_daemon_health_state.json
- Shadow trade decisions: logs/shadow_trades.jsonl
- Legacy shadow stream: logs/shadow.jsonl (optional, separate engine)

This script is intentionally verbose in its prints so you can read it like a forensic report.
It is safe-by-default (read-only).

Optional:
- Use --droplet to run systemd/journal checks on the droplet via DropletClient.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


# -----------------------------
# DEFAULTS — REPO-CORRECT
# -----------------------------

DEFAULT_UW_HEALTH_PATH = "state/uw_daemon_health_state.json"
DEFAULT_SHADOW_TRADES_PATH = "logs/shadow_trades.jsonl"
DEFAULT_SHADOW_STREAM_PATH = "logs/shadow.jsonl"
DEFAULT_TIME_WINDOW_HOURS = 48
DEFAULT_JOURNAL_UNIT = "uw-flow-daemon.service"


# -----------------------------
# UTILITIES
# -----------------------------


def parse_iso(ts: str) -> datetime:
    """
    Accepts:
    - 2026-01-21T16:20:36.495667+00:00
    - 2026-01-21T16:20:36+00:00
    - 2026-01-21T16:20:36Z
    - 2026-01-21T16:20:36 (assumed UTC)
    """
    s = (ts or "").strip()
    if not s:
        raise ValueError("empty timestamp")
    # Normalize Z
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    # Try fromisoformat first (covers offsets)
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        pass
    # Fallback formats (no timezone)
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.strptime(s[:19], fmt).replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            continue
    raise ValueError(f"Unrecognized timestamp format: {ts}")


def safe_load_json(path: str) -> Optional[Dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        print(f"[WARN] File not found: {path}")
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except Exception as e:
        print(f"[ERROR] Failed to load JSON from {path}: {e}")
        return None


def iter_jsonl(path: str) -> Iterable[Dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                yield obj
        except Exception:
            continue


def run_cmd(cmd: List[str]) -> Tuple[int, str, str]:
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out, err = proc.communicate()
        return proc.returncode, out, err
    except Exception as e:
        return 1, "", f"Exception running {' '.join(cmd)}: {e}"


def print_section(title: str):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80 + "\n")


def _has_local_systemctl() -> bool:
    return os.name == "posix" and shutil.which("systemctl") is not None


@dataclass(frozen=True)
class JournalStormWindow:
    start: datetime
    end: datetime


# -----------------------------
# 1. DAEMON + SYSTEMD STATUS
# -----------------------------


def check_daemon_and_systemd(*, unit: str, droplet: bool) -> None:
    print_section("1. UW daemon + systemd status")
    if droplet:
        try:
            from droplet_client import DropletClient
        except Exception as e:
            print(f"[ERROR] DropletClient import failed: {e}")
            return
        with DropletClient() as c:
            so, se, rc = c._execute(f"systemctl status {unit} --no-pager --plain", timeout=30)
            print(f"[INFO] droplet systemctl status rc={rc}")
            if se.strip():
                print(f"[WARN] stderr:\n{se.strip()[:1000]}")
            print("\n".join((so or "").splitlines()[:50]))
            so, se, rc = c._execute("pgrep -af uw_flow_daemon.py || true", timeout=20)
            print("\n[INFO] droplet uw_flow_daemon processes:")
            print((so or "").strip() or "(none)")
        return

    if not _has_local_systemctl():
        print("[INFO] Local systemd checks skipped (not a Linux systemctl environment).")
        return

    code, out, err = run_cmd(["systemctl", "status", unit, "--no-pager", "--plain"])
    if code != 0:
        print(f"[ERROR] systemctl status failed: {err.strip()}")
    else:
        print("[INFO] systemctl status output (truncated):")
        print("\n".join(out.splitlines()[:50]))

    code, out, err = run_cmd(["ps", "aux"])
    if code != 0:
        print(f"[ERROR] ps aux failed: {err.strip()}")
    else:
        lines = [l for l in out.splitlines() if "uw_flow_daemon" in l and "grep" not in l]
        print("\n[INFO] Matching uw_flow_daemon processes:")
        if not lines:
            print("  (none found)")
        else:
            for l in lines:
                print("  " + l)


# -----------------------------
# 2. HEALTH SENTINEL
# -----------------------------


def check_health_sentinel(health_path: str) -> Optional[Dict[str, Any]]:
    print_section("2. UW health sentinel state")

    health = safe_load_json(health_path)
    if not health:
        print("[WARN] No health sentinel loaded.")
        return None

    print("[INFO] Raw health sentinel JSON:")
    print(json.dumps(health, indent=2, sort_keys=True))

    status = health.get("status")
    pid_ok = health.get("pid_ok")
    lock_ok = health.get("lock_ok")
    poll_fresh = health.get("poll_fresh")
    det = health.get("details") if isinstance(health.get("details"), dict) else {}
    endpoint_error_counts = det.get("endpoint_error_counts") or det.get("endpoint_errors") or {}

    print("\n[SUMMARY]")
    print(f"  status: {status}")
    print(f"  pid_ok: {pid_ok}")
    print(f"  lock_ok: {lock_ok}")
    print(f"  poll_fresh: {poll_fresh}")
    print(f"  endpoint_error_counts: {endpoint_error_counts}")
    return health


# -----------------------------
# 3. JOURNAL — RESTART STORM WINDOW
# -----------------------------


def parse_journal_for_restart_storm(*, unit: str, droplet: bool) -> Optional[JournalStormWindow]:
    print_section("3. Journal analysis for restart storm window")

    out = ""
    if droplet:
        try:
            from droplet_client import DropletClient
        except Exception as e:
            print(f"[ERROR] DropletClient import failed: {e}")
            return None
        with DropletClient() as c:
            so, se, rc = c._execute(f"journalctl -u {unit} --no-pager --output=short-iso -n 2000", timeout=60)
            if rc != 0:
                print(f"[ERROR] droplet journalctl failed: {se.strip()[:1000]}")
                return None
            out = so or ""
    else:
        if not _has_local_systemctl():
            print("[INFO] Local journal analysis skipped (not a Linux systemctl environment).")
            return None
        code, out, err = run_cmd(["journalctl", "-u", unit, "--no-pager", "--output=short-iso"])
        if code != 0:
            print(f"[ERROR] journalctl failed: {err.strip()}")
            return None

    lines = out.splitlines()
    storm_start: Optional[datetime] = None
    storm_end: Optional[datetime] = None
    match = "Another instance is already running. Exiting."

    for line in lines:
        parts = line.split()
        if not parts:
            continue
        raw_ts = parts[0]
        # short-iso can include TZ offset; keep first 19 chars as naive (UTC-ish) then assume UTC
        raw_ts = raw_ts[:19]
        try:
            ts = parse_iso(raw_ts)
        except Exception:
            continue
        if match in line:
            if storm_start is None:
                storm_start = ts
            storm_end = ts

    if storm_start and storm_end:
        print("[INFO] Detected restart storm window from journal (lock contention loop):")
        print(f"  start: {storm_start.isoformat()}")
        print(f"  end:   {storm_end.isoformat()}")
        return JournalStormWindow(start=storm_start, end=storm_end)

    print("[INFO] No explicit restart storm pattern detected in journal.")
    return None


# -----------------------------
# 4. LOAD SHADOW TRADES
# -----------------------------


def load_shadow_trades(path: str, *, event_type: Optional[str]) -> List[Dict[str, Any]]:
    print_section("4. Loading shadow trades")
    p = Path(path)
    if not p.exists():
        print(f"[WARN] Shadow trades file not found: {path}")
        return []

    trades: List[Dict[str, Any]] = []
    bad = 0
    for obj in iter_jsonl(path):
        if event_type and str(obj.get("event_type", "")) != event_type:
            continue
        trades.append(obj)
    if not trades:
        # Estimate parse failures (optional)
        try:
            for ln in p.read_text(encoding="utf-8", errors="replace").splitlines():
                if not ln.strip():
                    continue
                try:
                    json.loads(ln)
                except Exception:
                    bad += 1
        except Exception:
            pass
    print(f"[INFO] Loaded {len(trades)} shadow trade records from {path}" + (f" (filtered event_type={event_type})" if event_type else ""))
    if bad:
        print(f"[WARN] Approx parse failures: {bad}")
    return trades


# -----------------------------
# 5. FILTER + GAP ANALYSIS
# -----------------------------


def filter_trades_by_time(trades: List[Dict[str, Any]], since: datetime) -> List[Dict[str, Any]]:
    filtered = []
    for t in trades:
        ts_raw = t.get("timestamp") or t.get("ts") or t.get("time")
        if not ts_raw:
            continue
        try:
            ts = parse_iso(str(ts_raw))
        except Exception:
            continue
        if ts >= since:
            t["_dt"] = ts  # type: ignore[assignment]
            filtered.append(t)
    return filtered


def analyze_trade_gaps(trades: List[Dict[str, Any]], *, gap_threshold_minutes: int = 60) -> None:
    print_section("5. Shadow trade continuity + gap analysis")

    if not trades:
        print("[WARN] No trades in selected window.")
        return

    trades_sorted = sorted(trades, key=lambda x: x["_dt"])  # type: ignore[index]
    first = trades_sorted[0]["_dt"]
    last = trades_sorted[-1]["_dt"]
    print(f"[INFO] Trades in window: {len(trades_sorted)}")
    print(f"  first trade: {first.isoformat()}")
    print(f"  last trade:  {last.isoformat()}")

    gaps: List[Tuple[datetime, datetime, float]] = []
    prev = trades_sorted[0]["_dt"]
    for t in trades_sorted[1:]:
        cur = t["_dt"]
        delta_min = (cur - prev).total_seconds() / 60.0
        if delta_min > float(gap_threshold_minutes):
            gaps.append((prev, cur, delta_min))
        prev = cur

    if not gaps:
        print(f"[INFO] No large gaps (> {gap_threshold_minutes} minutes) detected between shadow trades.")
    else:
        print("[WARN] Detected large gaps between shadow trades:")
        for a, b, dm in gaps:
            print(f"  gap from {a.isoformat()} to {b.isoformat()} ({dm:.1f} minutes)")


# -----------------------------
# 6. PnL ANALYSIS (SKELETON)
# -----------------------------


def compute_shadow_pnl(trades: List[Dict[str, Any]]) -> None:
    print_section("6. Shadow PnL (best-effort)")
    pnl = 0.0
    wins = 0
    losses = 0
    num_trades = 0

    for t in trades:
        side = t.get("side") or t.get("direction")
        entry = t.get("entry_price")
        exit_ = t.get("exit_price")
        qty = t.get("qty") or t.get("size") or 1.0

        if side is None or entry is None or exit_ is None:
            continue
        try:
            entry_f = float(entry)
            exit_f = float(exit_)
            qty_f = float(qty)
        except Exception:
            continue

        s = str(side).lower()
        if s in ("long", "buy", "bullish"):
            trade_pnl = (exit_f - entry_f) * qty_f
        elif s in ("short", "sell", "bearish"):
            trade_pnl = (entry_f - exit_f) * qty_f
        else:
            continue

        pnl += trade_pnl
        num_trades += 1
        if trade_pnl > 0:
            wins += 1
        elif trade_pnl < 0:
            losses += 1

    if num_trades == 0:
        print("[WARN] No trades with usable entry/exit/qty fields in this window (expected for shadow_trades.jsonl).")
        return

    win_rate = wins / num_trades if num_trades > 0 else 0.0
    print(f"[INFO] Trades with PnL: {num_trades}")
    print(f"  Total PnL: {pnl:.2f}")
    print(f"  Wins: {wins}, Losses: {losses}, Win rate: {win_rate:.2%}")


# -----------------------------
# 7. TRUSTED WINDOW LOGIC
# -----------------------------


def determine_trusted_window(
    *,
    known_fix_time_iso: Optional[str],
    storm_window: Optional[JournalStormWindow],
) -> Optional[datetime]:
    """
    Decide from what time onward we consider shadow data "trusted".
    Priority:
      1. known_fix_time_iso if provided
      2. storm_window end + small buffer
      3. None (no special trusted window)
    """
    if known_fix_time_iso:
        try:
            fix_dt = parse_iso(known_fix_time_iso)
            print(f"[INFO] Using known fix time as trusted window start: {fix_dt.isoformat()}")
            return fix_dt
        except Exception as e:
            print(f"[WARN] Failed to parse known fix time: {e}")

    if storm_window:
        trusted_start = storm_window.end + timedelta(minutes=5)
        print(f"[INFO] Using storm_end+5min as trusted window start: {trusted_start.isoformat()}")
        return trusted_start

    print("[INFO] No explicit trusted window; using generic time window only.")
    return None


# -----------------------------
# MAIN
# -----------------------------


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--health-path", default=DEFAULT_UW_HEALTH_PATH)
    ap.add_argument("--shadow-trades-path", default=DEFAULT_SHADOW_TRADES_PATH)
    ap.add_argument("--hours", type=int, default=DEFAULT_TIME_WINDOW_HOURS)
    ap.add_argument("--event-type", default="shadow_trade_candidate", help="Filter shadow trades by event_type (empty to disable filter)")
    ap.add_argument("--unit", default=DEFAULT_JOURNAL_UNIT)
    ap.add_argument("--known-fix-time-iso", default="", help="Optional trusted start ISO timestamp (UTC recommended)")
    ap.add_argument("--gap-threshold-min", type=int, default=60)
    ap.add_argument("--droplet", action="store_true", help="Run systemd/journal checks on droplet via DropletClient")
    args = ap.parse_args()

    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=int(args.hours))

    print_section("Shadow trading integrity + gap analysis")
    print(f"[INFO] Now (UTC): {now.isoformat()}")
    print(f"[INFO] Analyzing last {int(args.hours)} hours (since {since.isoformat()})")
    print(f"[INFO] shadow_trades_path: {args.shadow_trades_path}")
    print(f"[INFO] uw_health_path: {args.health_path}")
    print(f"[INFO] droplet_checks: {bool(args.droplet)}")

    # 1) Daemon + systemd
    check_daemon_and_systemd(unit=str(args.unit), droplet=bool(args.droplet))

    # 2) Health sentinel
    _ = check_health_sentinel(str(args.health_path))

    # 3) Journal — restart storm window
    storm_window = parse_journal_for_restart_storm(unit=str(args.unit), droplet=bool(args.droplet))

    # 4) Load shadow trades
    event_type = str(args.event_type).strip()
    event_filter = event_type if event_type else None
    all_trades = load_shadow_trades(str(args.shadow_trades_path), event_type=event_filter)
    if not all_trades:
        print("[FATAL] No shadow trades loaded; exiting early.")
        return 2

    # 5) Filter by time window
    trades_recent = filter_trades_by_time(all_trades, since)
    print(f"\n[INFO] Trades in last {int(args.hours)} hours: {len(trades_recent)}")

    # 6) Trusted window
    trusted_start = determine_trusted_window(
        known_fix_time_iso=(str(args.known_fix_time_iso).strip() or None),
        storm_window=storm_window,
    )
    if trusted_start:
        trades_trusted = [t for t in trades_recent if t["_dt"] >= trusted_start]  # type: ignore[index]
        print(f"[INFO] Trades in trusted window (>= {trusted_start.isoformat()}): {len(trades_trusted)}")
    else:
        trades_trusted = trades_recent

    # 7) Gap analysis
    analyze_trade_gaps(trades_recent, gap_threshold_minutes=int(args.gap_threshold_min))

    # 8) PnL (best-effort)
    compute_shadow_pnl(trades_trusted)

    print_section("DONE")
    print("[INFO] Review the sections above for:")
    print("  - Daemon stability (local or droplet)")
    print("  - Restart storm window (if any)")
    print("  - Shadow trade gaps")
    print("  - Shadow PnL (if your shadow trade logs include prices)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

