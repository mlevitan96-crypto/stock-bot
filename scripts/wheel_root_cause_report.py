#!/usr/bin/env python3
"""
Wheel Strategy Root-Cause Report (A/B/C/D).
Run on droplet (or locally with repo root):
  python3 scripts/wheel_root_cause_report.py [--days 5] [--repo /path/to/stock-bot]
Output: stdout + reports/WHEEL_ROOT_CAUSE_REPORT_YYYY-MM-DD.md
Evidence-backed: system_events (wheel lifecycle), telemetry, attribution, wheel_state, cycles.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _tail_lines(path: Path, max_lines: int) -> list[str]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
        return lines[-max_lines:] if len(lines) > max_lines else lines
    except Exception:
        return []


def _count_by_reason(events: list[dict], event_type: str, reason_key: str = "reason") -> dict[str, int]:
    out: dict[str, int] = defaultdict(int)
    for e in events:
        if e.get("event_type") != event_type:
            continue
        r = e.get(reason_key) or "unknown"
        out[str(r)] += 1
    return dict(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="Wheel root-cause report (A/B/C/D)")
    ap.add_argument("--days", type=int, default=5, help="Lookback days for logs")
    ap.add_argument("--repo", type=str, default=str(ROOT), help="Repo root (logs, state, config)")
    args = ap.parse_args()
    base = Path(args.repo)
    logs_dir = base / "logs"
    state_dir = base / "state"
    reports_dir = base / "reports"
    config_dir = base / "config"

    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=args.days)).date().isoformat()
    report_lines: list[str] = []
    evidence: list[str] = []

    def out(s: str) -> None:
        report_lines.append(s)
        print(s)

    out("# Wheel Strategy Root-Cause Report")
    out(f"**Generated:** {datetime.now(timezone.utc).isoformat()}Z")
    out(f"**Repo:** {base}")
    out(f"**Lookback:** {args.days} days (since {cutoff_date})")
    out("")

    # --- 1. Config & dispatch (could cause A) ---
    out("## 1. Config and dispatch")
    wheel_enabled = False
    strategy_context_ok = False
    try:
        strat_path = config_dir / "strategies.yaml"
        if strat_path.exists():
            import yaml
            with strat_path.open() as f:
                cfg = yaml.safe_load(f) or {}
            wheel_cfg = (cfg.get("strategies") or {}).get("wheel") or {}
            wheel_enabled = wheel_cfg.get("enabled", False)
            out(f"- strategies.yaml: wheel.enabled = {wheel_enabled}")
        else:
            out("- strategies.yaml: MISSING (wheel defaults to disabled)")
    except Exception as e:
        out(f"- strategies.yaml: error {e}")
    try:
        from strategies.context import strategy_context
        strategy_context_ok = True
        out("- strategies.context.strategy_context: importable")
    except ImportError as e:
        out(f"- strategies.context: IMPORT FAILED — {e}")
    if not strategy_context_ok:
        out("- Note: main.py runs wheel when enabled even if strategy_context fails (fallback path).")
    if not wheel_enabled:
        out("")
        out("**OUTCOME A: Wheel NOT RUNNING** — wheel.enabled is false in config.")
        out("- **Fix:** Set strategies.wheel.enabled to true in config/strategies.yaml.")
        _write_report(reports_dir, report_lines)
        return 0
    out("")

    # --- 2. System events (wheel lifecycle) ---
    out("## 2. Wheel lifecycle events (logs/system_events.jsonl)")
    sys_events_path = logs_dir / "system_events.jsonl"
    wheel_events: list[dict] = []
    if sys_events_path.exists():
        for line in _tail_lines(sys_events_path, 50000):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                if rec.get("subsystem") == "wheel":
                    ts = (rec.get("timestamp") or "")[:10]
                    if ts >= cutoff_date:
                        wheel_events.append(rec)
            except json.JSONDecodeError:
                continue
    else:
        out("- system_events.jsonl: MISSING")
    run_started = sum(1 for e in wheel_events if e.get("event_type") == "wheel_run_started")
    order_submitted = sum(1 for e in wheel_events if e.get("event_type") == "wheel_order_submitted")
    order_filled = sum(1 for e in wheel_events if e.get("event_type") == "wheel_order_filled")
    order_failed = sum(1 for e in wheel_events if e.get("event_type") == "wheel_order_failed")
    skip_counts = _count_by_reason(wheel_events, "wheel_csp_skipped")
    run_failed = sum(1 for e in wheel_events if e.get("event_type") == "wheel_run_failed")

    out(f"- wheel_run_started: {run_started}")
    out(f"- wheel_order_submitted: {order_submitted}")
    out(f"- wheel_order_filled: {order_filled}")
    out(f"- wheel_order_failed: {order_failed}")
    out(f"- wheel_run_failed: {run_failed}")
    out(f"- wheel_csp_skipped (by reason): {dict(skip_counts) if skip_counts else 'none'}")

    # Representative log lines (3 per non-zero category)
    for event_type in ("wheel_run_started", "wheel_regime_audit", "wheel_csp_skipped", "wheel_order_submitted", "wheel_order_filled", "wheel_order_failed"):
        subset = [e for e in wheel_events if e.get("event_type") == event_type][-5:]
        for e in subset[:3]:
            evidence.append(f"[{event_type}] {json.dumps(e)}")
    out("")
    out("**Sample event lines (evidence):**")
    for ex in evidence[:15]:
        out(f"- `{ex[:200]}{'...' if len(ex) > 200 else ''}`")
    out("")

    if run_started == 0:
        out("**OUTCOME A: Wheel NOT RUNNING**")
        out("- **Evidence:** No wheel_run_started in system_events (wheel code path never reached).")
        out("- **Code path:** main.py run_all_strategies() calls run_wheel when wheel_enabled (with or without strategy_context). So either run_all_strategies() is not being called (e.g. market closed, worker not running) or an exception in run_wheel (check wheel_run_failed).")
        out("- **Verification:** Check that bot cycles run during market hours (worker_debug.log or run.jsonl), and that no wheel_run_failed appears (exception in run_wheel).")
        _write_report(reports_dir, report_lines)
        return 0

    if order_submitted == 0:
        out("**OUTCOME B: Wheel RUNNING but ALWAYS SKIPPING**")
        out("- **Evidence:** wheel_run_started > 0 but wheel_order_submitted == 0.")
        out("- **Skip reasons (ranked):**")
        for reason, count in sorted(skip_counts.items(), key=lambda x: -x[1]):
            out(f"  - {reason}: {count}")
        out("- **Code path:** strategies/wheel_strategy.py _run_csp_phase() — skips per ticker for: earnings_window, iv_rank, no_spot, no_contracts_in_range, capital_limit, per_position_limit, insufficient_buying_power, existing_order, max_positions_reached.")
        out("- **Fix:** Address top skip reason: e.g. no_contracts_in_range → relax DTE or check Alpaca options API; no_spot → quote API; capital/buying_power → account size.")
        _write_report(reports_dir, report_lines)
        return 0

    if order_filled == 0 and order_submitted > 0:
        out("**OUTCOME C: Wheel SUBMITTING but NOT FILLING**")
        out("- **Evidence:** wheel_order_submitted > 0, wheel_order_filled == 0.")
        out("- **Likely:** Orders are limit (e.g. 0.05) and not filling; or Alpaca paper options reject/expire. Check Alpaca dashboard for order status (filled/canceled/expired).")
        out("- **Fix (minimal):** Consider market order for CSP when limit is very low, or increase limit slightly within policy; add wheel_order_status telemetry (order_id → status) after submit.")
        _write_report(reports_dir, report_lines)
        return 0

    # --- 3. Telemetry & attribution (for D) ---
    out("## 3. Telemetry and attribution")
    telem_path = logs_dir / "telemetry.jsonl"
    wheel_telem: list[dict] = []
    if telem_path.exists():
        for line in _tail_lines(telem_path, 10000):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                if rec.get("strategy_id") == "wheel":
                    ts = (rec.get("timestamp") or rec.get("ts") or "")[:10]
                    if ts >= cutoff_date:
                        wheel_telem.append(rec)
            except json.JSONDecodeError:
                continue
    attr_wheel = 0
    attr_path = logs_dir / "attribution.jsonl"
    if attr_path.exists():
        for line in _tail_lines(attr_path, 15000):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                if rec.get("type") == "attribution" and (rec.get("strategy_id") or (rec.get("context") or {}).get("strategy_id")) == "wheel":
                    ts = (rec.get("ts") or rec.get("timestamp") or "")[:10]
                    if ts >= cutoff_date:
                        attr_wheel += 1
            except json.JSONDecodeError:
                continue
    out(f"- telemetry.jsonl strategy_id=wheel (since {cutoff_date}): {len(wheel_telem)}")
    out(f"- attribution.jsonl strategy_id=wheel (since {cutoff_date}): {attr_wheel}")
    if wheel_telem:
        out("- Sample telemetry (last 3):")
        for t in wheel_telem[-3:]:
            redacted = {k: v for k, v in t.items() if k not in ("secret", "token")}
            out(f"  - {json.dumps(redacted)[:300]}...")
    out("")

    # --- 4. Wheel state ---
    out("## 4. state/wheel_state.json")
    ws_path = state_dir / "wheel_state.json"
    if ws_path.exists():
        try:
            mtime = datetime.fromtimestamp(ws_path.stat().st_mtime, tz=timezone.utc)
            out(f"- mtime: {mtime.isoformat()}")
            ws = json.loads(ws_path.read_text(encoding="utf-8", errors="replace"))
            open_csps = ws.get("open_csps") or {}
            out(f"- open_csps keys: {list(open_csps.keys())}")
            out(f"- csp_history len: {len(ws.get('csp_history') or [])}")
        except Exception as e:
            out(f"- parse error: {e}")
    else:
        out("- MISSING")
    out("")

    # --- 5. Dashboard pipeline (D check) ---
    if order_filled > 0 or len(wheel_telem) > 0:
        # Could still be D if dashboard shows zero
        out("## 5. Dashboard pipeline check")
        out("- _load_stock_closed_trades() reads: attribution.jsonl (strategy_id), exit_attribution.jsonl, telemetry.jsonl (strategy_id=wheel).")
        out("- /api/stockbot/wheel_analytics filters: trades where strategy_id == 'wheel'; premium_sum = sum(premium).")
        out("- If telemetry has strategy_id=wheel rows but dashboard shows 0: check timestamp cutoff (max_days=90), or premium/key fields missing.")
        out("")
        if order_filled > 0:
            out("**OUTCOME: Wheel FILLING** — wheel_order_filled > 0. Dashboard should show non-zero premium if telemetry has premium set; verify /api/stockbot/wheel_analytics and Wheel Strategy tab.")
        else:
            out("**OUTCOME B/C with data** — Wheel running and submitting; telemetry has wheel rows. If dashboard still shows zeros, see section 5 (D) for pipeline check.")
    _write_report(reports_dir, report_lines)
    return 0


def _write_report(reports_dir: Path, lines: list[str]) -> None:
    reports_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).date().isoformat()
    path = reports_dir / f"WHEEL_ROOT_CAUSE_REPORT_{today}.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nReport written: {path}")


if __name__ == "__main__":
    sys.exit(main())
