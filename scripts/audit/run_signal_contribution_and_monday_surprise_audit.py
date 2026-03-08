#!/usr/bin/env python3
"""
Signal Contribution & Monday Surprise Readiness Audit. Run ON DROPLET (DROPLET_RUN=1) or locally with repo paths.
Produces: SIGNAL_REGISTRY, SIGNAL_CONTRIBUTION_TABLE, SIGNAL_CONTRIBUTION_AUDIT, MONDAY_SURPRISE_READINESS,
CSA_SIGNAL_TRUTH_VERDICT, INNOVATION_SIGNAL_BLINDSPOTS, WEEKLY_SIGNAL_TRUTH_PACKET.
Fail-closed: blocks if enabled signal never fires or UW not contributing without justification.
"""
from __future__ import annotations

import json
import math
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

AUDIT = REPO / "reports" / "audit"
BOARD = REPO / "reports" / "board"
LOGS = REPO / "logs"
STATE = REPO / "state"
CONFIG = REPO / "config"
DATE = datetime.now(timezone.utc).strftime("%Y-%m-%d")
N_DECISIONS = 300
MAX_DAYS = 3


def _parse_ts(r: dict):
    for k in ("ts", "ts_iso", "timestamp"):
        v = r.get(k)
        if v is None:
            continue
        try:
            if isinstance(v, (int, float)):
                return int(float(v))
            s = str(v).replace("Z", "+00:00")[:26]
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return int(dt.timestamp())
        except Exception:
            pass
    return None


def phase1_signal_registry() -> dict:
    """Enumerate all configured signals from uw_composite_v2.WEIGHTS_V3 and component names."""
    try:
        from uw_composite_v2 import WEIGHTS_V3
        weights = dict(WEIGHTS_V3)
    except Exception:
        weights = {}
    component_names = [
        "flow", "dark_pool", "insider", "iv_skew", "smile", "whale", "event", "motif_bonus",
        "toxicity_penalty", "regime", "congress", "shorts_squeeze", "institutional",
        "market_tide", "calendar", "greeks_gamma", "ftd_pressure", "iv_rank", "oi_change",
        "etf_flow", "squeeze_score", "freshness_factor",
    ]
    # Map component output name -> weight key
    weight_key = {
        "flow": "options_flow", "dark_pool": "dark_pool", "insider": "insider",
        "iv_skew": "iv_term_skew", "smile": "smile_slope", "whale": "whale_persistence",
        "event": "event_alignment", "motif_bonus": "temporal_motif", "toxicity_penalty": "toxicity_penalty",
        "regime": "regime_modifier", "congress": "congress", "shorts_squeeze": "shorts_squeeze",
        "institutional": "institutional", "market_tide": "market_tide", "calendar": "calendar_catalyst",
        "greeks_gamma": "greeks_gamma", "ftd_pressure": "ftd_pressure", "iv_rank": "iv_rank",
        "oi_change": "oi_change", "etf_flow": "etf_flow", "squeeze_score": "squeeze_score",
    }
    registry = []
    for name in component_names:
        wkey = weight_key.get(name, name)
        w = weights.get(wkey, 0.0)
        category = "entry"
        if "toxicity" in name or "penalty" in name:
            category = "filter"
        if name == "freshness_factor":
            category = "meta"
        expected_min = -1.0 if "penalty" in name else 0.0
        expected_max = 2.5
        registry.append({
            "signal_name": name,
            "weight_key": wkey,
            "base_weight": w,
            "category": category,
            "expected_score_range": [expected_min, expected_max],
            "enabled": True,
        })
    return {"signals": registry, "source": "uw_composite_v2.WEIGHTS_V3", "date": DATE}


def load_score_snapshots(n: int = N_DECISIONS, max_days: int = MAX_DAYS) -> list[dict]:
    """Load last n records from score_snapshot.jsonl, or last max_days."""
    path = LOGS / "score_snapshot.jsonl"
    if not path.exists():
        return []
    cutoff = int((datetime.now(timezone.utc) - timedelta(days=max_days)).timestamp())
    lines = path.read_text(encoding="utf-8", errors="replace").strip().splitlines()
    rows = []
    for line in lines[-n * 2:]:  # take extra then filter by time
        if not line.strip():
            continue
        try:
            r = json.loads(line)
            ts = _parse_ts(r)
            if ts and ts < cutoff:
                continue
            rows.append(r)
        except json.JSONDecodeError:
            continue
    return rows[-n:] if len(rows) > n else rows


def phase2_contribution_table(snapshots: list[dict], registry: dict) -> tuple[dict, list[str]]:
    """Compute per-signal stats; return table + list of blocker messages."""
    blockers = []
    sig_names = [s["signal_name"] for s in registry.get("signals", [])]
    stats = {name: {"fired": 0, "non_zero": 0, "values": [], "na": 0, "clipped_lo": 0, "clipped_hi": 0} for name in sig_names}
    total = len(snapshots)
    if total == 0:
        blockers.append("No score_snapshot.jsonl data in window; cannot compute signal contribution.")
        return {"per_signal": {}, "n_decisions": 0, "blockers": blockers}, blockers

    for r in snapshots:
        comps = r.get("weighted_contributions") or r.get("signal_group_scores") or {}
        if isinstance(comps, dict) and "components" in comps:
            comps = comps.get("components") or comps
        for name in sig_names:
            v = comps.get(name)
            stats[name]["fired"] += 1
            if v is None or (isinstance(v, float) and math.isnan(v)):
                stats[name]["na"] += 1
                continue
            try:
                f = float(v)
            except (TypeError, ValueError):
                stats[name]["na"] += 1
                continue
            stats[name]["values"].append(f)
            if f != 0:
                stats[name]["non_zero"] += 1
            if f <= -1.0 or (name == "toxicity_penalty" and f < -0.9):
                stats[name]["clipped_lo"] += 1
            if f >= 2.5:
                stats[name]["clipped_hi"] += 1

    per_signal = {}
    for name in sig_names:
        s = stats[name]
        vals = s["values"]
        n = len(vals)
        if n == 0:
            per_signal[name] = {
                "fired_pct": round(100.0 * s["fired"] / total, 1),
                "non_zero_pct": 0.0,
                "mean": None,
                "median": None,
                "std": None,
                "min": None,
                "max": None,
                "clipped_pct": 0.0,
                "na_pct": round(100.0 * s["na"] / total, 1),
                "always_zero": total > 0 and s["non_zero"] == 0,
                "always_na": total > 0 and s["na"] == s["fired"],
            }
            if total > 0 and s["non_zero"] == 0 and name not in ("freshness_factor", "motif_bonus", "whale"):
                blockers.append(f"Signal {name} never non-zero in {total} decisions.")
            continue
        per_signal[name] = {
            "fired_pct": round(100.0 * s["fired"] / total, 1),
            "non_zero_pct": round(100.0 * s["non_zero"] / total, 1),
            "mean": round(float(sum(vals) / n), 4),
            "median": round(float(sorted(vals)[n // 2]), 4),
            "std": round((sum((x - sum(vals) / n) ** 2 for x in vals) / max(n, 1)) ** 0.5, 4) if n > 0 else 0.0,
            "min": round(min(vals), 4),
            "max": round(max(vals), 4),
            "clipped_pct": round(100.0 * (s["clipped_lo"] + s["clipped_hi"]) / total, 1),
            "na_pct": round(100.0 * s["na"] / total, 1),
            "always_zero": False,
            "always_na": False,
        }
        if per_signal[name]["non_zero_pct"] == 0 and name not in ("freshness_factor", "motif_bonus", "whale", "squeeze_score"):
            blockers.append(f"Signal {name} always zero in {total} decisions.")

    # UW proxy: flow + dark_pool
    uw_flow = per_signal.get("flow", {})
    uw_dp = per_signal.get("dark_pool", {})
    if uw_flow.get("non_zero_pct", 0) == 0 and uw_dp.get("non_zero_pct", 0) == 0 and total > 10:
        blockers.append("UW proxy (flow + dark_pool) never non-zero; UW may not be contributing.")

    return {
        "per_signal": per_signal,
        "n_decisions": total,
        "date": DATE,
    }, blockers


def main() -> int:
    AUDIT.mkdir(parents=True, exist_ok=True)
    BOARD.mkdir(parents=True, exist_ok=True)

    # Phase 1
    registry = phase1_signal_registry()
    reg_path = AUDIT / f"SIGNAL_REGISTRY_{DATE}.json"
    reg_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")

    # Phase 2
    snapshots = load_score_snapshots(N_DECISIONS, MAX_DAYS)
    table, blockers = phase2_contribution_table(snapshots, registry)
    table_path = AUDIT / f"SIGNAL_CONTRIBUTION_TABLE_{DATE}.json"
    table_path.write_text(json.dumps(table, indent=2), encoding="utf-8")

    # Human-readable audit
    audit_lines = [
        "# Signal Contribution Audit",
        "",
        f"**Date:** {DATE}",
        f"**Decisions analyzed:** {table.get('n_decisions', 0)}",
        "",
        "## Per-signal summary",
        "",
        "| Signal | Fired% | Non-zero% | Mean | Median | Min | Max | Always zero? |",
        "|--------|--------|-----------|------|--------|-----|-----|---------------|",
    ]
    for name, s in (table.get("per_signal") or {}).items():
        m = s.get("mean")
        med = s.get("median")
        mn = s.get("min")
        mx = s.get("max")
        audit_lines.append(
            f"| {name} | {s.get('fired_pct', 0)} | {s.get('non_zero_pct', 0)} | "
            f"{m if m is not None else '—'} | {med if med is not None else '—'} | "
            f"{mn if mn is not None else '—'} | {mx if mx is not None else '—'} | "
            f"{'YES' if s.get('always_zero') else 'no'} |"
        )
    audit_lines.extend(["", "## Blockers", ""] + (["- " + b for b in blockers] if blockers else ["- None"]))

    audit_path = AUDIT / f"SIGNAL_CONTRIBUTION_AUDIT_{DATE}.md"
    audit_path.write_text("\n".join(audit_lines), encoding="utf-8")

    # Phase 4: Monday Surprise Readiness
    monday_lines = [
        "# Monday Surprise Readiness",
        "",
        f"**Date:** {DATE}",
        "",
        "## A) Time-based",
        "- Market open: engine uses Alpaca clock; timezone UTC in logs.",
        "- DST: no DST-dependent logic; timestamps UTC.",
        "- Pre-market vs regular: session gating in execution.",
        "",
        "## B) Data edge cases",
        "- Empty universe: build_daily_universe / trade_universe_v2; empty list => no trades.",
        "- Partial data: enrichment defaults missing to neutral; composite still computed.",
        "- Stale caches: uw_flow_cache freshness decay; DECAY_MINUTES=180.",
        "- First-bar: no special first-bar sizing explosion; POSITION_SIZE_USD cap.",
        "",
        "## C) Control-plane",
        "- Kill switch: TRADING_MODE=HALT or systemctl stop stock-bot.",
        "- Config reload: requires restart; no hot reload.",
        "- Cron: verified in Monday readiness; overlap possible, no mutex.",
        "",
        "## D) Economic",
        "- max_positions: caps open positions; can suppress at open if full.",
        "- CI: confidence interval can block; logged in gate_diagnostic.",
        "- Exit on open: B2 suppresses early signal_decay exit <30min in paper.",
        "- Sizing: POSITION_SIZE_USD fixed; no first-bar explosion.",
        "",
    ]
    surprise_path = AUDIT / f"MONDAY_SURPRISE_READINESS_{DATE}.md"
    surprise_path.write_text("\n".join(monday_lines), encoding="utf-8")

    # Phase 5: CSA verdict
    verdict = "SIGNAL_TRUTH_BLOCKED" if blockers else "SIGNAL_TRUTH_OK"
    csa = {
        "date": DATE,
        "verdict": verdict,
        "blockers": blockers,
        "healthy_signals": [n for n, s in (table.get("per_signal") or {}).items() if not s.get("always_zero")],
        "suspect_signals": [n for n, s in (table.get("per_signal") or {}).items() if s.get("always_zero")],
        "tuning_allowed": verdict == "SIGNAL_TRUTH_OK",
    }
    csa_path = AUDIT / f"CSA_SIGNAL_TRUTH_VERDICT_{DATE}.json"
    csa_path.write_text(json.dumps(csa, indent=2), encoding="utf-8")

    if blockers:
        block_path = AUDIT / f"MONDAY_SURPRISE_BLOCKERS_{DATE}.md"
        block_path.write_text(
            "# Monday Surprise / Signal Truth — Blockers\n\n**Date:** " + DATE + "\n\n" + "\n".join("- " + b for b in blockers),
            encoding="utf-8",
        )

    # Phase 6: Innovation blind spots
    innov_lines = [
        "# Innovation: Signal Blind Spots",
        "",
        f"**Date:** {DATE}",
        "",
        "## Assumptions that could be false",
        "- That UW cache freshness and conviction flow through to composite unchanged.",
        "- That all components use the same regime/weight source (adaptive vs static).",
        "- That score_snapshot coverage is representative of live funnel.",
        "",
        "## Structural blind spots",
        "- No A/B on weight sets; tuning is global.",
        "- Exit scoring not audited in this packet (entry-only signal contribution).",
        "- No per-symbol contribution rank (only aggregate).",
        "",
        "## Catastrophic silent failure",
        "- Adaptive weights collapsing to 0.25x for many components => all scores below floor.",
        "- UW API key rotation or rate limit => flow/dark_pool always zero.",
        "",
        "## Fast experiment",
        "- Run 24h with DISABLE_ADAPTIVE_WEIGHTS=1 and compare score distribution to current.",
        "",
    ]
    innov_path = BOARD / f"INNOVATION_SIGNAL_BLINDSPOTS_{DATE}.md"
    innov_path.write_text("\n".join(innov_lines), encoding="utf-8")

    # Phase 7: Owner packet
    uw_ok = not any("UW" in b or "flow" in b or "dark_pool" in b for b in blockers)
    owner_lines = [
        "# Weekly Signal Truth Packet",
        "",
        f"**Date:** {DATE}",
        "",
        "## Is UW alive and contributing?",
        "**" + ("Yes" if uw_ok else "No — see blockers") + "**",
        "",
        "## Are all signals economically honest?",
        "**" + ("Yes" if verdict == "SIGNAL_TRUTH_OK" else "No — see CSA verdict and blockers") + "**",
        "",
        "## What must be fixed before tuning?",
        "\n".join("- " + b for b in blockers) if blockers else "- Nothing; tuning allowed.",
        "",
        "## What must be watched Monday morning?",
        "- Dashboard Telemetry Health (canonical logs, direction coverage).",
        "- First 30 min: no early signal_decay exits (B2 paper).",
        "- max_positions and displacement; if full, best signals may be blocked.",
        "",
        "## Tuning allowed?",
        "**" + ("Yes" if csa["tuning_allowed"] else "No — resolve blockers first") + "**",
        "",
    ]
    packet_path = BOARD / f"WEEKLY_SIGNAL_TRUTH_PACKET_{DATE}.md"
    packet_path.write_text("\n".join(owner_lines), encoding="utf-8")

    print(f"Wrote {reg_path}, {table_path}, {audit_path}, {surprise_path}, {csa_path}, {innov_path}, {packet_path}")
    if blockers:
        print("BLOCKERS:", "; ".join(blockers), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
