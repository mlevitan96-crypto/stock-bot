#!/usr/bin/env python3
"""
Snapshot→Outcome Attribution Report. NO-APPLY.
Joins decision-time snapshots to outcomes; quantifies signal separability and marginal value.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

COMPONENTS = [
    "flow", "dark_pool", "insider", "iv_skew", "smile", "whale", "event", "motif_bonus",
    "toxicity_penalty", "regime", "congress", "shorts_squeeze", "institutional", "market_tide",
    "calendar", "greeks_gamma", "ftd_pressure", "iv_rank", "oi_change", "etf_flow",
    "squeeze_score", "freshness_factor",
]


def _load_jsonl(path: Path) -> list:
    out = []
    if not path.exists():
        return out
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def _outcome_bucket(pnl: float | None) -> str:
    if pnl is None:
        return "unknown"
    try:
        p = float(pnl)
    except (TypeError, ValueError):
        return "unknown"
    if p > 0:
        return "WIN"
    if p < 0:
        return "LOSS"
    return "FLAT"


def _parse_ts(ts: str) -> int | None:
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--symbols", default="")
    ap.add_argument("--snapshots-path", default="logs/signal_snapshots.jsonl")
    ap.add_argument("--base-dir", default=None)
    args = ap.parse_args()

    base = Path(args.base_dir) if args.base_dir else REPO
    target_date = args.date
    symbols_set = {s.strip().upper() for s in args.symbols.split(",") if s.strip()}
    snap_path = base / args.snapshots_path

    logs_dir = base / "logs"
    state_dir = base / "state"
    reports_dir = base / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    snapshots = _load_jsonl(snap_path)
    master_log = _load_jsonl(logs_dir / "master_trade_log.jsonl")
    exit_attr = _load_jsonl(logs_dir / "exit_attribution.jsonl")
    blocked = _load_jsonl(state_dir / "blocked_trades.jsonl")

    # Filter by date
    def in_date(ts: str) -> bool:
        return str(ts or "")[:10] == target_date if ts else False

    snapshots = [s for s in snapshots if in_date(s.get("timestamp_utc", ""))]
    master_log = [m for m in master_log if in_date(m.get("entry_ts") or m.get("timestamp", ""))]
    exit_attr = [e for e in exit_attr if in_date(e.get("timestamp") or e.get("entry_timestamp", ""))]

    if symbols_set:
        snapshots = [s for s in snapshots if str(s.get("symbol", "")).upper() in symbols_set]
        master_log = [m for m in master_log if str(m.get("symbol", "")).upper() in symbols_set]
        exit_attr = [e for e in exit_attr if str(e.get("symbol", "")).upper() in symbols_set]

    from telemetry.snapshot_join_keys import (
        extract_join_key_from_snapshot,
        extract_join_key_from_master_trade,
    )

    # Join quality
    mtl_by_key = {}
    for m in master_log:
        jk, _ = extract_join_key_from_master_trade(m)
        mtl_by_key[jk] = m
    mtl_by_sym_ts = {}
    for m in master_log:
        sym = str(m.get("symbol", "")).upper()
        ts = m.get("entry_ts") or m.get("timestamp", "")
        mtl_by_sym_ts[(sym, str(ts)[:19])] = m

    matched_entries = 0
    matched_exits = 0
    unmatched_snapshots = 0
    unmatched_reasons = defaultdict(int)

    entry_snapshots = [s for s in snapshots if s.get("lifecycle_event") == "ENTRY_DECISION"]
    exit_snapshots = [s for s in snapshots if s.get("lifecycle_event") == "EXIT_DECISION"]

    for s in entry_snapshots:
        jk, fields = extract_join_key_from_snapshot(s)
        if jk in mtl_by_key:
            matched_entries += 1
        else:
            unmatched_snapshots += 1
            tid = s.get("trade_id")
            if not tid or not str(tid).startswith("live:"):
                unmatched_reasons["missing_trade_id"] += 1
            else:
                unmatched_reasons["ts_drift_or_no_mtl"] += 1

    for s in exit_snapshots:
        sym = str(s.get("symbol", "")).upper()
        ts = s.get("timestamp_utc", "")[:19]
        if (sym, ts) in mtl_by_sym_ts:
            matched_exits += 1
        else:
            unmatched_snapshots += 1
            unmatched_reasons["exit_no_matching_mtl"] += 1

    # Outcome buckets (from master_trade_log + exit_attr)
    outcome_counts = defaultdict(int)
    for m in master_log:
        if m.get("exit_ts"):
            pnl = m.get("realized_pnl_usd")
            outcome_counts[_outcome_bucket(pnl)] += 1
    for e in exit_attr:
        outcome_counts[_outcome_bucket(e.get("pnl"))] += 1
    outcome_counts["blocked"] = len([b for b in blocked if in_date(b.get("ts", b.get("timestamp", "")))])

    # Signal separability (per component)
    comp_win_present = defaultdict(int)
    comp_loss_present = defaultdict(int)
    comp_win_absent = defaultdict(int)
    comp_loss_absent = defaultdict(int)
    comp_contribs_win = defaultdict(list)
    comp_contribs_loss = defaultdict(list)

    for s in snapshots:
        comps = s.get("components") or {}
        outcome = None
        for m in master_log:
            if str(m.get("symbol", "")).upper() == str(s.get("symbol", "")).upper():
                ts_m = (m.get("entry_ts") or m.get("timestamp", ""))[:19]
                ts_s = (s.get("timestamp_utc", ""))[:19]
                if ts_m == ts_s or abs((_parse_ts(ts_m) or 0) - (_parse_ts(ts_s) or 0)) < 300:
                    outcome = _outcome_bucket(m.get("realized_pnl_usd"))
                    break
        if outcome is None:
            continue
        for c in COMPONENTS:
            v = comps.get(c)
            if isinstance(v, dict):
                present = v.get("present", False)
                contrib = v.get("contrib")
                try:
                    cv = float(contrib) if contrib is not None else None
                except (TypeError, ValueError):
                    cv = None
                if outcome == "WIN":
                    if present:
                        comp_win_present[c] += 1
                        if cv is not None:
                            comp_contribs_win[c].append(cv)
                    else:
                        comp_win_absent[c] += 1
                elif outcome == "LOSS":
                    if present:
                        comp_loss_present[c] += 1
                        if cv is not None:
                            comp_contribs_loss[c].append(cv)
                    else:
                        comp_loss_absent[c] += 1

    # Marginal value (top vs bottom quantile)
    def _quantile_delta(win_list: list, loss_list: list) -> tuple[str, str]:
        w = win_list or []
        l = loss_list or []
        if len(w) < 5 and len(l) < 5:
            return "insufficient_data", "low"
        w_sorted = sorted(w)
        l_sorted = sorted(l)
        w_top = w_sorted[-len(w_sorted) // 4:] if w_sorted else []
        w_bot = w_sorted[: max(1, len(w_sorted) // 4)] if w_sorted else []
        l_top = l_sorted[-len(l_sorted) // 4:] if l_sorted else []
        l_bot = l_sorted[: max(1, len(l_sorted) // 4)] if l_sorted else []
        win_rate_top = len(w_top) / max(1, len(w_top) + len(l_top)) if (w_top or l_top) else 0.5
        win_rate_bot = len(w_bot) / max(1, len(w_bot) + len(l_bot)) if (w_bot or l_bot) else 0.5
        delta = win_rate_top - win_rate_bot
        if delta > 0.1:
            return "informative", "medium" if len(w) + len(l) >= 20 else "low"
        if delta < -0.1:
            return "misleading", "medium" if len(w) + len(l) >= 20 else "low"
        return "neutral", "low"

    comp_marginal = {}
    for c in COMPONENTS:
        label, conf = _quantile_delta(comp_contribs_win.get(c, []), comp_contribs_loss.get(c, []))
        comp_marginal[c] = {"label": label, "confidence": conf}

    # Shadow comparisons (if shadow snapshots exist)
    shadow_path = base / "logs" / f"signal_snapshots_shadow_{target_date}.jsonl"
    shadow_section = []
    if shadow_path.exists():
        shadow_recs = _load_jsonl(shadow_path)
        shadow_by_profile = defaultdict(list)
        for r in shadow_recs:
            prof = r.get("shadow_profile", "baseline")
            shadow_by_profile[prof].append(r.get("composite_score_v2"))
        for prof, scores in shadow_by_profile.items():
            if scores:
                avg = sum(s for s in scores if s is not None) / len([s for s in scores if s is not None])
                shadow_section.append(f"- **{prof}**: avg composite={avg:.2f}, n={len(scores)}")
    else:
        shadow_section.append("- No shadow snapshots for this date.")

    # Build report
    lines = [
        f"# Snapshot→Outcome Attribution — {target_date}",
        "",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
        "**STATUS: NO-APPLY — Observability only.**",
        "",
        "## 1. Join quality",
        "",
        f"- Snapshot count: {len(snapshots)}",
        f"- Matched entries: {matched_entries}",
        f"- Matched exits: {matched_exits}",
        f"- Unmatched snapshots: {unmatched_snapshots}",
        f"- Top unmatched reasons: {dict(unmatched_reasons)}",
        "",
        "## 2. Outcome buckets",
        "",
        f"- WIN: {outcome_counts['WIN']}",
        f"- LOSS: {outcome_counts['LOSS']}",
        f"- FLAT: {outcome_counts['FLAT']}",
        f"- Blocked: {outcome_counts['blocked']}",
        "",
        "## 3. Signal separability (present rate: wins vs losses)",
        "",
        "| Component | Win present | Loss present | Win absent | Loss absent |",
        "|-----------|-------------|--------------|------------|-------------|",
    ]
    for c in COMPONENTS[:15]:
        wp = comp_win_present.get(c, 0)
        lp = comp_loss_present.get(c, 0)
        wa = comp_win_absent.get(c, 0)
        la = comp_loss_absent.get(c, 0)
        lines.append(f"| {c} | {wp} | {lp} | {wa} | {la} |")
    lines.extend([
        "",
        "## 4. Marginal value (top vs bottom quantile)",
        "",
        "| Component | Label | Confidence |",
        "|-----------|-------|------------|",
    ])
    for c in COMPONENTS[:15]:
        m = comp_marginal.get(c, {})
        lines.append(f"| {c} | {m.get('label', 'unknown')} | {m.get('confidence', '')} |")
    lines.extend([
        "",
        "## 5. Shadow comparisons",
        "",
    ] + shadow_section + [
        "",
        "---",
        "",
        "*Generated by scripts/generate_snapshot_outcome_attribution_report.py. NO-APPLY.*",
        "",
    ])

    out_path = reports_dir / f"SNAPSHOT_OUTCOME_ATTRIBUTION_{target_date}.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
