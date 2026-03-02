#!/usr/bin/env python3
"""
Multi-model board diagnostic: Prosecutor, Defender, SRE, Board Verdict.
Run on droplet (or locally with droplet data) to find why real trades are not happening.
Writes reports/audit/REAL_TRADES_BOARD_VERDICT.md and prints summary.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

OUT_MD = REPO / "reports" / "audit" / "REAL_TRADES_BOARD_VERDICT.md"


def _read(path: Path, default: str = "") -> str:
    try:
        if path.exists():
            return path.read_text(encoding="utf-8", errors="replace").strip()
    except Exception:
        pass
    return default


def _read_json(path: Path, default=None):
    if default is None:
        default = {}
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        pass
    return default


def _last_n_lines(path: Path, n: int) -> list[str]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").strip().splitlines()
    return [l for l in lines if l.strip()][-n:]


def gather_evidence() -> dict:
    """Gather run, cache, gates, env for board review."""
    evidence = {
        "run_last_10": [],
        "clusters_0_count": 0,
        "orders_0_count": 0,
        "composite_enabled": None,
        "cache_exists": False,
        "cache_symbol_count": 0,
        "gate_last_20": [],
        "submit_entry_last_5": [],
        "freeze_active": False,
        "kill_switch_active": False,
        "armed": False,
        "inject_test": os.environ.get("INJECT_SIGNAL_TEST", ""),
        "uw_missing_input_mode": os.environ.get("UW_MISSING_INPUT_MODE", "reject"),
        "min_exec_score": os.environ.get("MIN_EXEC_SCORE", ""),
        "uw_root_cause_latest_exists": False,
        "score_snapshot_last_5": [],
    }
    # run.jsonl
    run_path = REPO / "logs" / "run.jsonl"
    for line in _last_n_lines(run_path, 10):
        try:
            r = json.loads(line)
            evidence["run_last_10"].append(r)
            if r.get("clusters") == 0:
                evidence["clusters_0_count"] += 1
            if r.get("orders") == 0:
                evidence["orders_0_count"] += 1
            if evidence["composite_enabled"] is None and r.get("metrics", {}).get("composite_enabled") is not None:
                evidence["composite_enabled"] = r["metrics"].get("composite_enabled")
        except Exception:
            pass
    # cache
    cache_path = REPO / "data" / "uw_flow_cache.json"
    evidence["cache_exists"] = cache_path.exists()
    if cache_path.exists():
        try:
            cache = _read_json(cache_path)
            evidence["cache_symbol_count"] = len([k for k in cache if not k.startswith("_")])
        except Exception:
            pass
    # gate.jsonl
    gate_path = REPO / "logs" / "gate.jsonl"
    for line in _last_n_lines(gate_path, 20):
        try:
            evidence["gate_last_20"].append(json.loads(line))
        except Exception:
            evidence["gate_last_20"].append({"raw": line[:120]})
    # submit_entry.jsonl
    sub_path = REPO / "logs" / "submit_entry.jsonl"
    for line in _last_n_lines(sub_path, 5):
        try:
            evidence["submit_entry_last_5"].append(json.loads(line))
        except Exception:
            pass
    # freeze / kill
    freeze_data = _read_json(REPO / "state" / "governor_freezes.json")
    evidence["freeze_active"] = bool(freeze_data and any(
        freeze_data.get(k) for k in freeze_data if isinstance(freeze_data.get(k), bool)
    ))
    kill_data = _read_json(REPO / "state" / "kill_switch.json")
    evidence["kill_switch_active"] = bool(kill_data and kill_data.get("enabled"))
    base_url = os.environ.get("ALPACA_BASE_URL", "")
    evidence["armed"] = "paper-api.alpaca.markets" in base_url and "live" not in base_url.lower()
    # board/eod/out latest uw_root_cause
    out_dir = REPO / "board" / "eod" / "out"
    if out_dir.exists():
        for d in sorted(out_dir.iterdir(), reverse=True):
            if d.is_dir() and len(d.name) == 10 and d.name[4] == "-":
                if (d / "uw_root_cause.json").exists():
                    evidence["uw_root_cause_latest_exists"] = True
                    break
    # score_snapshot
    snap_path = REPO / "logs" / "score_snapshot.jsonl"
    for line in _last_n_lines(snap_path, 5):
        try:
            evidence["score_snapshot_last_5"].append(json.loads(line))
        except Exception:
            pass
    return evidence


def prosecutor_view(ev: dict) -> list[str]:
    lines = [
        "# Prosecutor (Adversarial)",
        "",
        "## Claim",
    ]
    if ev["clusters_0_count"] == len(ev["run_last_10"]) and ev["run_last_10"]:
        lines.append("**Zero clusters every cycle** — the composite gate (`should_enter_v2`) is the choke. No symbol reaches the entry threshold (score >= 2.7, freshness >= 0.25, toxicity <= 0.90). Scores are too low because:")
        lines.append("- UW cache may have weak or stale data; freshness decay was fixed (180min half-life) but weights or conviction may still suppress scores.")
        lines.append("- Adaptive weights (`state/signal_weights.json`) may have reduced key components.")
        lines.append("- No symbol in cache currently has composite score >= 2.7.")
    elif ev["run_last_10"] and any(r.get("clusters", 0) > 0 for r in ev["run_last_10"]):
        orders = [r.get("orders", 0) for r in ev["run_last_10"] if r.get("clusters", 0) > 0]
        if all(o == 0 for o in orders):
            lines.append("**Clusters > 0 but orders = 0** — execution path is blocked after composite. First gate to block: check gate.jsonl (uw_deferred, expectancy_gate, score_below_min, etc.).")
            for g in ev["gate_last_20"][:5]:
                ev_name = g.get("event", g.get("gate_type", ""))
                lines.append(f"- Gate: `{ev_name}` symbol={g.get('symbol', '')} {g.get('defer_reason', g.get('message', ''))[:60]}")
        else:
            lines.append("Some cycles had orders > 0; recent run shows clusters and orders. Check if INJECT_SIGNAL_TEST=1 (only injected SPY would trade).")
    else:
        lines.append("Insufficient run.jsonl data or composite disabled. Enable composite (cache with symbols) and run at least one cycle.")
    lines.append("")
    lines.append("## Verdict")
    lines.append("**Adversarial:** Real trades are blocked either at composite (0 clusters) or at a post-composite gate (UW defer, expectancy score floor). Fix: raise scores or relax UW/expectancy for paper.")
    return lines


def defender_view(ev: dict) -> list[str]:
    lines = [
        "# Defender (Alternate / Fixes)",
        "",
        "## What is already fixed",
        "- **Freshness:** FRESHNESS_HALF_LIFE_MINUTES = 180 (was 15) so scores decay slower.",
        "- **Conviction default:** Missing conviction now 0.5 in composite core so flow component contributes.",
        "- **Execution path:** Inject test proved that with a passing cluster, orders are placed (SPY filled).",
        "",
        "## What still blocks real trades",
    ]
    if ev["uw_missing_input_mode"] != "passthrough":
        lines.append("- **UW root-cause data:** `apply_uw_to_score` loads `board/eod/out/<date>/uw_root_cause.json`. When missing or no candidate for symbol, the code defers or penalizes → score drops or candidate skipped. On paper, set **UW_MISSING_INPUT_MODE=passthrough** so score is preserved when no board data.")
    if (ev["inject_test"] or "").strip() == "1":
        lines.append("- **INJECT_SIGNAL_TEST=1:** Only synthetic SPY cluster is added when clusters=0. Set **INJECT_SIGNAL_TEST=0** (or unset) so only real composite signals produce orders.")
    if not ev["cache_exists"] or ev["cache_symbol_count"] == 0:
        lines.append("- **UW cache empty or missing:** Composite loop has no symbols. Ensure UW daemon/ingestion populates `data/uw_flow_cache.json`.")
    lines.append("")
    lines.append("## Verdict")
    lines.append("**Defender:** Apply passthrough for paper; turn off inject test; confirm cache is populated. Then re-run one cycle and check clusters/orders.")
    return lines


def sre_view(ev: dict) -> list[str]:
    lines = [
        "# SRE (Checklist)",
        "",
        "| Check | Status |",
        "|-------|--------|",
    ]
    lines.append(f"| Freeze (governor_freezes.json) | {'BLOCK' if ev['freeze_active'] else 'PASS'} |")
    lines.append(f"| Kill switch | {'BLOCK' if ev['kill_switch_active'] else 'PASS'} |")
    lines.append(f"| Armed (paper URL) | {'PASS' if ev['armed'] else 'BLOCK'} |")
    lines.append(f"| UW cache exists | {'PASS' if ev['cache_exists'] else 'BLOCK'} |")
    lines.append(f"| Cache symbol count | {ev['cache_symbol_count']} |")
    lines.append(f"| INJECT_SIGNAL_TEST | {ev['inject_test'] or '(unset)'} |")
    lines.append(f"| UW_MISSING_INPUT_MODE | {ev['uw_missing_input_mode']} |")
    lines.append(f"| MIN_EXEC_SCORE (env) | {ev['min_exec_score'] or '(default 2.5)'} |")
    lines.append(f"| UW root_cause latest (board/eod/out) | {'exists' if ev['uw_root_cause_latest_exists'] else 'missing'} |")
    lines.append("")
    return lines


def board_verdict(ev: dict) -> list[str]:
    lines = [
        "# Board Verdict",
        "",
        "## Immediate actions (to get real trades)",
        "",
        "1. **Set on droplet (e.g. in .env or systemd Environment):**",
        "   - `UW_MISSING_INPUT_MODE=passthrough`  (preserve score when no UW root-cause data)",
        "   - `INJECT_SIGNAL_TEST=0`  or remove it (so only real signals trade)",
        "2. **Restart the bot:** `systemctl restart stock-bot` (or equivalent).",
        "3. **After one cycle, verify:**",
        "   - `tail -1 logs/run.jsonl` → clusters and orders; if clusters > 0 and orders > 0, real trade path is working.",
        "   - If clusters still 0, run scoring audit: distribution of composite scores per symbol. Optionally set **ENTRY_THRESHOLD_BASE=2.5** (env) to allow more symbols through the composite gate (default 2.7).",
        "",
        "## References",
        "- Trade logic trace: reports/audit/TRADE_LOGIC_SIGNAL_TO_EXECUTION_TRACE.md",
        "- All gates: reports/audit/ALL_GATES_CHECKLIST.md",
        "- Dashboard P&L / symbol universe: reports/audit/DASHBOARD_PNL_AND_SYMBOL_UNIVERSE.md",
        "",
    ]
    return lines


def main() -> int:
    ev = gather_evidence()
    sections = [
        "# Real Trades Board Diagnostic (Multi-Model)",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "---",
        "",
    ]
    sections.extend(prosecutor_view(ev))
    sections.append("")
    sections.extend(defender_view(ev))
    sections.append("")
    sections.extend(sre_view(ev))
    sections.extend(board_verdict(ev))
    out_path = OUT_MD
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(sections), encoding="utf-8")
    print("Wrote", out_path)
    print("\n--- Summary ---")
    print(f"Run cycles (last 10): clusters=0 in {ev['clusters_0_count']}, orders=0 in {ev['orders_0_count']}")
    print(f"Cache: exists={ev['cache_exists']}, symbols={ev['cache_symbol_count']}")
    print(f"INJECT_SIGNAL_TEST={ev['inject_test']!r}  UW_MISSING_INPUT_MODE={ev['uw_missing_input_mode']!r}")
    print("\nBoard verdict and actions: see", OUT_MD)
    return 0


if __name__ == "__main__":
    sys.exit(main())
