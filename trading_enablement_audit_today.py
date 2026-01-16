#!/usr/bin/env python3
"""
Read-only: End-to-end "no trades" audit for TODAY (UTC day) on the droplet.

Outputs JSON summary suitable for:
- last ~20 cycles timeline table
- pipeline stage activity (scoring/gates/orders/exits)
- top blockers (gate reasons) and risk/freeze signals

This script does NOT modify production state.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from droplet_client import DropletClient


def _safe_json_lines(text: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for ln in (text or "").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            obj = json.loads(ln)
            if isinstance(obj, dict):
                out.append(obj)
        except Exception:
            continue
    return out


def _iso_or_none(ts: Any) -> Optional[str]:
    if ts is None:
        return None
    return str(ts)


def _utc_day_of(ts: Any) -> Optional[str]:
    if ts is None:
        return None
    s = str(ts)
    try:
        s2 = s.replace("Z", "+00:00")
        if "T" not in s2 and " " in s2:
            s2 = s2.replace(" ", "T", 1)
        dt = datetime.fromisoformat(s2)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).date().isoformat()
    except Exception:
        return s[:10] if len(s) >= 10 else None


def _parse_dt(ts: Any) -> Optional[datetime]:
    if ts is None:
        return None
    s = str(ts).replace("Z", "+00:00")
    if "T" not in s and " " in s:
        s = s.replace(" ", "T", 1)
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _remote(c: DropletClient, cmd: str, timeout: int = 60) -> str:
    r = c.execute_command(cmd, timeout=timeout)
    return (r.get("stdout") or r.get("stderr") or "").strip()


def _tail(c: DropletClient, rel_path: str, n: int) -> str:
    return _remote(c, f"cd /root/stock-bot && test -f {rel_path} && tail -n {n} {rel_path} || true", timeout=60)


def _systemd_active_enter_utc(c: DropletClient) -> Optional[str]:
    # Example: "ActiveEnterTimestamp=Fri 2026-01-16 16:08:39 UTC"
    out = _remote(c, "systemctl show stock-bot -p ActiveEnterTimestamp --no-pager || true", timeout=20)
    if "ActiveEnterTimestamp=" not in out:
        return None
    val = out.split("ActiveEnterTimestamp=", 1)[-1].strip()
    return val or None


def _parse_systemd_utc(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    # Example: "Fri 2026-01-16 16:36:25 UTC"
    try:
        dt = datetime.strptime(s, "%a %Y-%m-%d %H:%M:%S %Z")
        return dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _window(events: List[Dict[str, Any]], center: datetime, sec: int = 70) -> List[Dict[str, Any]]:
    lo = center.timestamp() - sec
    hi = center.timestamp() + sec
    out = []
    for e in events:
        dt = _parse_dt(e.get("ts"))
        if not dt:
            continue
        t = dt.timestamp()
        if lo <= t <= hi:
            out.append(e)
    return out


def main() -> int:
    with DropletClient() as c:
        utc_day = _remote(c, "date -u +%F", timeout=10)
        now_utc = _remote(c, 'date -u +"%Y-%m-%dT%H:%M:%SZ"', timeout=10)
        head = _remote(c, "cd /root/stock-bot && git rev-parse --short HEAD", timeout=10)
        active_enter = _systemd_active_enter_utc(c)
        active_dt = _parse_systemd_utc(active_enter)

        # Pull tails. Keep moderate sizes; we only need today+recent.
        raw_run = _tail(c, "logs/run.jsonl", 2500)
        raw_run_once = _tail(c, "logs/run_once.jsonl", 1200)
        raw_scoring_flow = _tail(c, "logs/scoring_flow.jsonl", 2500)
        raw_gate = _tail(c, "logs/gate.jsonl", 4000)
        raw_orders = _tail(c, "logs/orders.jsonl", 2500)
        raw_exit = _tail(c, "logs/exit.jsonl", 2500)
        raw_market_data = _tail(c, "logs/market_data.jsonl", 2500)
        raw_sre = _tail(c, "logs/sre_health.jsonl", 1200)
        raw_worker = _tail(c, "logs/worker.jsonl", 1200)
        raw_worker_err = _tail(c, "logs/worker_error.jsonl", 600)

        # Also capture short raw tails (for debugging exactly what's being written now).
        tail_run_once_raw = _tail(c, "logs/run_once.jsonl", 30)
        tail_scoring_flow_raw = _tail(c, "logs/scoring_flow.jsonl", 30)
        tail_gate_raw = _tail(c, "logs/gate.jsonl", 30)
        tail_orders_raw = _tail(c, "logs/orders.jsonl", 30)
        tail_run_raw = _tail(c, "logs/run.jsonl", 30)

        run = [e for e in _safe_json_lines(raw_run) if _utc_day_of(e.get("ts")) == utc_day]
        run_once = [e for e in _safe_json_lines(raw_run_once) if _utc_day_of(e.get("ts")) == utc_day]
        scoring_flow = [e for e in _safe_json_lines(raw_scoring_flow) if _utc_day_of(e.get("ts")) == utc_day]
        gate = [e for e in _safe_json_lines(raw_gate) if _utc_day_of(e.get("ts")) == utc_day]
        orders = [e for e in _safe_json_lines(raw_orders) if _utc_day_of(e.get("ts")) == utc_day]
        exits = [e for e in _safe_json_lines(raw_exit) if _utc_day_of(e.get("ts")) == utc_day]
        market_data = [e for e in _safe_json_lines(raw_market_data) if _utc_day_of(e.get("ts")) == utc_day]
        sre = [e for e in _safe_json_lines(raw_sre) if _utc_day_of(e.get("ts")) == utc_day]
        worker = [e for e in _safe_json_lines(raw_worker) if _utc_day_of(e.get("ts")) == utc_day]
        worker_err = [e for e in _safe_json_lines(raw_worker_err) if _utc_day_of(e.get("ts")) == utc_day]

        def _post(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            if not active_dt:
                return events
            out = []
            for e in events:
                dt = _parse_dt(e.get("ts"))
                if dt and dt >= active_dt:
                    out.append(e)
            return out

        run_post = _post(run)
        run_once_post = _post(run_once)
        scoring_flow_post = _post(scoring_flow)
        gate_post = _post(gate)
        orders_post = _post(orders)
        exits_post = _post(exits)
        market_data_post = _post(market_data)
        sre_post = _post(sre)
        worker_post = _post(worker)
        worker_err_post = _post(worker_err)

        # last ~20 cycles from run.jsonl "complete" records
        cycles = [e for e in run_post if e.get("msg") in ("complete", "cycle_complete")]
        cycles = cycles[-20:]

        timeline = []
        for cy in cycles:
            ts = cy.get("ts")
            dt = _parse_dt(ts)
            if not dt:
                continue
            w_scoring = _window(scoring_flow_post, dt)
            w_gate = _window(gate_post, dt)
            w_orders = _window(orders_post, dt)
            w_exit = _window(exits_post, dt)

            scoring_ran = any(e.get("msg") in ("cluster_creation", "composite_scoring_start") for e in w_scoring) or bool(w_scoring)
            decisions_ran = bool(w_gate) or (cy.get("clusters") not in (None, 0))
            orders_attempted = len([o for o in w_orders if (o.get("action") or o.get("msg"))])
            exits_ran = bool(w_exit)

            timeline.append(
                {
                    "cycle_time": _iso_or_none(ts),
                    "market_open": cy.get("market_open"),
                    "clusters": cy.get("clusters"),
                    "orders": cy.get("orders"),
                    "scoring_ran": bool(scoring_ran),
                    "decisions_ran": bool(decisions_ran),
                    "orders_attempted": int(orders_attempted),
                    "exits_ran": bool(exits_ran),
                    "metrics": cy.get("metrics") if isinstance(cy.get("metrics"), dict) else None,
                }
            )

        # Aggregate blockers for today
        gate_msgs = [str(e.get("msg")) for e in gate_post if e.get("msg")]
        top_gate = Counter(gate_msgs).most_common(30)

        run_once_msgs = [str(e.get("msg")) for e in run_once_post if e.get("msg")]
        top_run_once = Counter(run_once_msgs).most_common(30)

        run_halts = [e for e in run_post if e.get("msg") in ("halted_freeze",)]

        # Spot common "no entries" states
        capacity_blocks = [e for e in gate_post if e.get("msg") in ("max_positions_reached", "max_new_positions_per_cycle_reached")]
        score_blocks = [e for e in gate_post if e.get("msg") in ("score_below_min", "expectancy_blocked")]
        cooldown_blocks = [e for e in gate_post if e.get("msg") in ("symbol_on_cooldown",)]

        # Stale bars signals
        stale_bars = [e for e in market_data_post if e.get("msg") == "stale_bars_detected"]

        # Scoring distribution (post-restart)
        comp_events = [e for e in scoring_flow_post if e.get("msg") == "composite_calculated"]
        comp_scores: List[float] = []
        for e in comp_events:
            s = e.get("score")
            if isinstance(s, (int, float)):
                comp_scores.append(float(s))
        rounded = [round(x, 3) for x in comp_scores]
        score_dist = {
            "n": len(comp_scores),
            "unique_rounded_3dp": len(set(rounded)),
            "min": min(comp_scores) if comp_scores else None,
            "max": max(comp_scores) if comp_scores else None,
            "top_repeated_rounded_3dp": Counter(rounded).most_common(10),
        }

        report = {
            "droplet": {
                "now_utc": now_utc,
                "utc_day": utc_day,
                "git_head": head,
                "service_active_enter": active_enter,
                "service_active_enter_utc_iso": active_dt.isoformat() if active_dt else None,
            },
            "counts_today": {
                "run": len(run_post),
                "run_once": len(run_once_post),
                "scoring_flow": len(scoring_flow_post),
                "gate": len(gate_post),
                "orders": len(orders_post),
                "exit": len(exits_post),
                "market_data": len(market_data_post),
                "sre_health": len(sre_post),
                "worker": len(worker_post),
                "worker_error": len(worker_err_post),
            },
            "score_distribution_post_restart": score_dist,
            "timeline_last20": timeline,
            "top_gate_msgs": top_gate,
            "top_run_once_msgs": top_run_once,
            "run_halts_freeze": [{"ts": e.get("ts"), "alerts": e.get("alerts")} for e in run_halts[-10:]],
            "blockers_counts": {
                "capacity_blocks": len(capacity_blocks),
                "score_blocks": len(score_blocks),
                "cooldown_blocks": len(cooldown_blocks),
                "stale_bars_detected": len(stale_bars),
            },
            "examples": {
                "capacity_block_last5": capacity_blocks[-5:],
                "score_block_last5": score_blocks[-5:],
                "cooldown_block_last5": cooldown_blocks[-5:],
                "stale_bars_last5": stale_bars[-5:],
            },
            "raw_tails_last30": {
                "run.jsonl": tail_run_raw,
                "run_once.jsonl": tail_run_once_raw,
                "scoring_flow.jsonl": tail_scoring_flow_raw,
                "gate.jsonl": tail_gate_raw,
                "orders.jsonl": tail_orders_raw,
            },
        }

        print(json.dumps(report, indent=2, sort_keys=True, default=str))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

