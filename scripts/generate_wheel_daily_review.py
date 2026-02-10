#!/usr/bin/env python3
"""
Generate the daily wheel strategy review artifact for Board consumption.

Reads logs/system_events.jsonl and state/wheel_state.json; outputs
reports/wheel_daily_review_<YYYY-MM-DD>.md with execution summary,
performance proxy, top decisions per fill, skip analysis, and
deterministic board actions.

Usage:
  python scripts/generate_wheel_daily_review.py [--date YYYY-MM-DD] [--days 1]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_EVENTS = REPO_ROOT / "logs" / "system_events.jsonl"
WHEEL_STATE_PATH = REPO_ROOT / "state" / "wheel_state.json"
REPORTS_DIR = REPO_ROOT / "reports"
# Must match strategies/wheel_strategy.WHEEL_EVENT_SCHEMA_VERSION
EXPECTED_WHEEL_EVENT_SCHEMA_VERSION = 1


def _wheel_action_id(title: str, owner: str, reference_section: str) -> str:
    raw = f"{title}|{owner}|{reference_section}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _check_board_action_closure(date_str: str) -> str:
    """Return PASS if no prior actions or all prior actions have closure in today's wheel_actions file; else FAIL."""
    try:
        target_dt = datetime.fromisoformat(date_str + "T00:00:00+00:00")
    except Exception:
        return "PASS"
    prior_date = (target_dt - timedelta(days=1)).strftime("%Y-%m-%d")
    prior_path = REPORTS_DIR / f"wheel_actions_{prior_date}.json"
    today_path = REPORTS_DIR / f"wheel_actions_{date_str}.json"
    if not prior_path.exists():
        return "PASS"
    prior_data = _load_json(prior_path, {})
    prior_actions = prior_data.get("actions") or []
    for a in prior_actions:
        if not a.get("action_id"):
            a["action_id"] = _wheel_action_id(a.get("title", ""), a.get("owner", ""), a.get("reference_section", ""))
    if not prior_actions:
        return "PASS"
    if not today_path.exists():
        return "FAIL"
    today_data = _load_json(today_path, {})
    today_actions = {}
    for wa in (today_data.get("actions") or []):
        key = wa.get("action_id") or _wheel_action_id(wa.get("title", ""), wa.get("owner", ""), wa.get("reference_section", ""))
        today_actions[key] = wa
    for a in prior_actions:
        aid = a.get("action_id")
        entry = today_actions.get(aid) or next((t for t in (today_data.get("actions") or []) if (t.get("action_id") or _wheel_action_id(t.get("title", ""), t.get("owner", ""), t.get("reference_section", ""))) == aid), None)
        if not entry:
            return "FAIL"
        status = (entry.get("status") or "").lower()
        if status not in ("done", "blocked", "deferred"):
            return "FAIL"
    return "PASS"


def _load_jsonl(path: Path) -> list[dict]:
    out: list[dict] = []
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


def _load_json(path: Path, default: dict | None = None) -> dict:
    if not path.exists():
        return default or {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (json.JSONDecodeError, OSError):
        return default or {}


def _parse_ts(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        if "Z" in ts or ts.endswith("+00:00"):
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return datetime.fromisoformat(ts)
    except Exception:
        return None


def _day_utc(dt: datetime) -> str:
    return dt.date().isoformat() if dt.tzinfo else (dt.replace(tzinfo=timezone.utc).date().isoformat())


def generate(
    *,
    date_str: str | None = None,
    lookback_hours: float = 24,
) -> tuple[str, bool, dict, dict]:
    """Generate markdown content for wheel daily review. Returns (markdown, verdict_ok, counters, badge)."""
    today = datetime.now(timezone.utc).date()
    target_date = date_str or today.isoformat()
    try:
        target_dt = datetime.fromisoformat(target_date + "T00:00:00+00:00")
    except Exception:
        target_dt = datetime.now(timezone.utc)
    window_start = target_dt - timedelta(hours=lookback_hours)
    window_end = target_dt + timedelta(hours=24)

    events = _load_jsonl(SYSTEM_EVENTS)
    wheel_events = [e for e in events if e.get("subsystem") == "wheel" and e.get("strategy_id") == "wheel"]
    in_window = []
    for e in wheel_events:
        ts = _parse_ts(e.get("timestamp"))
        if ts and window_start <= ts <= window_end:
            in_window.append(e)

    wheel_state = _load_json(WHEEL_STATE_PATH, {})

    # Schema version warning (do not crash; only warn)
    missing_schema = [e for e in in_window if e.get("event_schema_version") is None or e.get("event_schema_version") != EXPECTED_WHEEL_EVENT_SCHEMA_VERSION]
    schema_warn = len(missing_schema)

    # Governance completeness: cycle_ids from wheel_run_started
    cycle_ids = {e.get("cycle_id") for e in in_window if e.get("event_type") == "wheel_run_started" and e.get("cycle_id")}
    decision_context_cycles = {e.get("cycle_id") for e in in_window if e.get("event_type") == "wheel_decision_context" and e.get("cycle_id")}
    submitted_cycles = {e.get("cycle_id") for e in in_window if e.get("event_type") == "wheel_order_submitted" and e.get("cycle_id")}
    filled_cycles = {e.get("cycle_id") for e in in_window if e.get("event_type") == "wheel_order_filled" and e.get("cycle_id")}
    contract_selected_cycles = {e.get("cycle_id") for e in in_window if e.get("event_type") == "wheel_contract_selected" and e.get("cycle_id")}
    candidate_evaluated_cycles = {e.get("cycle_id") for e in in_window if e.get("event_type") == "wheel_candidate_evaluated" and e.get("cycle_id")}
    state_changed_cycles = {e.get("cycle_id") for e in in_window if e.get("event_type") == "wheel_position_state_changed" and e.get("cycle_id")}

    cycles_missing_decision_context = cycle_ids - decision_context_cycles
    cycles_with_submit_but_missing_contract = submitted_cycles - contract_selected_cycles
    cycles_with_submit_but_missing_candidate = submitted_cycles - candidate_evaluated_cycles
    cycles_with_fill_but_missing_submit = filled_cycles - submitted_cycles
    cycles_with_fill_but_missing_state_change = filled_cycles - state_changed_cycles

    regressions: list[dict] = []
    if cycles_missing_decision_context:
        regressions.append({"rule": "cycle must have wheel_decision_context", "cycle_ids": list(cycles_missing_decision_context)})
    if cycles_with_submit_but_missing_contract:
        regressions.append({"rule": "cycle with wheel_order_submitted must have wheel_contract_selected", "cycle_ids": list(cycles_with_submit_but_missing_contract)})
    if cycles_with_submit_but_missing_candidate:
        regressions.append({"rule": "cycle with wheel_order_submitted must have at least one wheel_candidate_evaluated", "cycle_ids": list(cycles_with_submit_but_missing_candidate)})
    if cycles_with_fill_but_missing_submit:
        regressions.append({"rule": "cycle with wheel_order_filled must have wheel_order_submitted", "cycle_ids": list(cycles_with_fill_but_missing_submit)})
    if cycles_with_fill_but_missing_state_change:
        regressions.append({"rule": "cycle with wheel_order_filled must have wheel_position_state_changed", "cycle_ids": list(cycles_with_fill_but_missing_state_change)})

    full_chain_cycles = cycle_ids & decision_context_cycles
    for cid in submitted_cycles:
        if cid not in contract_selected_cycles or cid not in candidate_evaluated_cycles:
            full_chain_cycles.discard(cid)
    for cid in filled_cycles:
        if cid not in submitted_cycles or cid not in state_changed_cycles:
            full_chain_cycles.discard(cid)
    cycles_with_full_chain = len(full_chain_cycles)
    verdict_ok = len(regressions) == 0
    cycles_total = len(cycle_ids)
    event_chain_coverage_pct = (cycles_with_full_chain / cycles_total * 100.0) if cycles_total else 100.0
    idempotency_hits = sum(1 for e in in_window if e.get("event_type") == "wheel_order_idempotency_hit")
    board_action_closure = _check_board_action_closure(target_date)

    skipped = [e for e in in_window if e.get("event_type") == "wheel_csp_skipped"]
    capital_blocked = sum(1 for e in in_window if e.get("event_type") == "wheel_capital_blocked")
    position_limit_blocked = sum(1 for e in in_window if e.get("event_type") == "wheel_position_limit_blocked")
    skip_counts: dict[str, int] = defaultdict(int)
    for e in skipped:
        reason = e.get("reason") or "unknown"
        skip_counts[reason] += 1
    if capital_blocked:
        skip_counts["allocation_exceeded"] = skip_counts.get("allocation_exceeded", 0) + capital_blocked
    if position_limit_blocked:
        skip_counts["per_position_limit_exceeded"] = skip_counts.get("per_position_limit_exceeded", 0) + position_limit_blocked
    fills = [e for e in in_window if e.get("event_type") == "wheel_order_filled"]
    if fills:
        dominant_blocker = "none"
    else:
        excluding_none = [(r, c) for r, c in skip_counts.items() if r and r != "none"]
        dominant_blocker = max(excluding_none, key=lambda x: x[1])[0] if excluding_none else "none"

    overall_status = "FAIL" if (
        not verdict_ok
        or (cycles_total > 0 and event_chain_coverage_pct < 100.0)
        or board_action_closure == "FAIL"
    ) else "PASS"

    generated_at = datetime.now(timezone.utc).isoformat()
    badge = {
        "overall_status": overall_status,
        "event_chain_coverage_pct": round(event_chain_coverage_pct, 1),
        "cycles_with_full_chain": cycles_with_full_chain,
        "cycles_total": cycles_total,
        "idempotency_hits": idempotency_hits,
        "board_action_closure": board_action_closure,
        "dominant_blocker": dominant_blocker,
        "generated_at": generated_at,
    }
    counters = {
        "cycles_with_full_chain": cycles_with_full_chain,
        "cycles_missing_decision_context": len(cycles_missing_decision_context),
        "cycles_missing_contract_selected": len(cycles_with_submit_but_missing_contract),
        "cycles_missing_state_change_after_fill": len(cycles_with_fill_but_missing_state_change),
    }

    # --- 3.1 Execution summary ---
    cycles_run = sum(1 for e in in_window if e.get("event_type") == "wheel_run_started")
    orders_submitted = sum(1 for e in in_window if e.get("event_type") == "wheel_order_submitted")
    open_csps = wheel_state.get("open_csps") or {}
    open_count = sum(len(v) if isinstance(v, list) else 1 for v in open_csps.values())

    badge_section = [
        "## Wheel governance badge",
        "",
        f"- **Status:** {badge['overall_status']}",
        f"- **Event chain coverage:** {badge['event_chain_coverage_pct']}%",
        f"- **Cycles with full chain:** {badge['cycles_with_full_chain']} / {badge['cycles_total']}",
        f"- **Idempotency hits:** {badge['idempotency_hits']}",
        f"- **Board action closure:** {badge['board_action_closure']}",
        f"- **Dominant blocker:** {badge['dominant_blocker']}",
        f"- **Generated at:** {badge['generated_at']}",
        "",
        "---",
        "",
    ]
    lines = badge_section + [
        f"# Wheel Daily Review — {target_date}",
        "",
        f"**Verdict:** {'PASS' if verdict_ok else 'FAIL'}",
        "",
        "## 3.1 Execution summary",
        "",
        f"- **Cycles run:** {cycles_run}",
        f"- **Orders submitted:** {orders_submitted}",
        f"- **Fills:** {len(fills)}",
        f"- **Open CSP positions (count):** {open_count}",
        f"- **Cycles with full chain:** {counters['cycles_with_full_chain']}",
        f"- **Cycles missing decision_context:** {counters['cycles_missing_decision_context']}",
        f"- **Cycles missing contract_selected (given submit):** {counters['cycles_missing_contract_selected']}",
        f"- **Cycles missing state_change after fill:** {counters['cycles_missing_state_change_after_fill']}",
        "",
    ]
    if schema_warn:
        lines.extend([
            "### WARN: Schema version",
            "",
            f"- {schema_warn} wheel event(s) in window have missing or unexpected event_schema_version (expected {EXPECTED_WHEEL_EVENT_SCHEMA_VERSION}).",
            "",
        ])
    if regressions:
        lines.extend([
            "## Governance regressions",
            "",
            "Mandatory expectations failed. Review event chain per cycle_id.",
            "",
        ])
        for r in regressions:
            lines.append(f"- **{r['rule']}**")
            lines.append(f"  cycle_ids: {r['cycle_ids'][:10]}{' ...' if len(r['cycle_ids']) > 10 else ''}")
            lines.append("")
        lines.append("")

    # --- 3.2 Performance proxy ---
    total_premium = sum(float(e.get("premium") or e.get("credit_realized_est") or 0) for e in fills)
    wheel_budget_any = next((e.get("wheel_budget") for e in in_window if e.get("wheel_budget") is not None), None)
    wheel_budget = float(wheel_budget_any) if wheel_budget_any is not None else None
    premium_per_budget = (total_premium / wheel_budget) if wheel_budget and wheel_budget > 0 else None
    days_span = max(1, lookback_hours / 24)
    premium_per_day = total_premium / days_span if days_span else 0

    lines.extend([
        "## 3.2 Performance proxy (paper-safe)",
        "",
        f"- **Total premium collected (fills):** ${total_premium:.2f}",
        f"- **Premium per day (window):** ${premium_per_day:.2f}",
    ])
    if wheel_budget is not None:
        lines.append(f"- **Wheel budget (from events):** ${wheel_budget:.2f}")
        if premium_per_budget is not None:
            lines.append(f"- **Premium / wheel budget:** {premium_per_budget:.4f}")
    lines.append("")

    # --- 3.3 Top decisions (per fill) ---
    lines.append("## 3.3 Top decisions (per fill)")
    lines.append("")
    if not fills:
        lines.append("_No fills in window._")
        lines.append("")
    else:
        for i, fill in enumerate(fills, 1):
            cycle_id = fill.get("cycle_id")
            symbol = fill.get("symbol")
            order_id = fill.get("order_id")
            premium = fill.get("premium") or fill.get("credit_realized_est")
            # Try to attach decision context from same cycle
            ctx = next((e for e in in_window if e.get("event_type") == "wheel_decision_context" and e.get("cycle_id") == cycle_id), None)
            cand = next((e for e in in_window if e.get("event_type") == "wheel_candidate_evaluated" and e.get("symbol") == symbol and e.get("cycle_id") == cycle_id and e.get("next_step") == "fetch_chain"), None)
            contract = next((e for e in in_window if e.get("event_type") == "wheel_contract_selected" and e.get("symbol") == symbol and e.get("cycle_id") == cycle_id), None)
            lines.append(f"### Fill {i}: {symbol}")
            lines.append(f"- **Cycle ID:** {cycle_id or 'N/A'}")
            lines.append(f"- **Order ID:** {order_id or 'N/A'}")
            lines.append(f"- **Credit realized (est):** ${premium:.2f}" if premium else "- **Credit:** N/A")
            if cand:
                lines.append(f"- **UW score / rank:** {cand.get('uw_score')} / {cand.get('rank')}")
                lines.append(f"- **Spot source:** {cand.get('spot_source')}")
                lines.append(f"- **Budget checks:** capital={cand.get('capital_check_decision')}, position_limit={cand.get('position_limit_decision')}")
            if contract:
                lines.append(f"- **Contract:** strike={contract.get('strike')}, expiry={contract.get('expiry')}, dte={contract.get('dte')}")
            lines.append("")
    lines.append("")

    # --- 3.4 Skip analysis ---
    symbol_skip_count: dict[str, int] = defaultdict(int)
    symbol_skip_reasons: dict[str, set[str]] = defaultdict(set)
    for e in skipped:
        sym = e.get("symbol") or "unknown"
        reason = e.get("reason") or "unknown"
        symbol_skip_count[sym] += 1
        symbol_skip_reasons[sym].add(reason)

    lines.append("## 3.4 Skip analysis")
    lines.append("")
    lines.append("### Counts by skip reason")
    lines.append("")
    for reason, count in sorted(skip_counts.items(), key=lambda x: -x[1]):
        lines.append(f"- **{reason}:** {count}")
    lines.append("")
    lines.append("### Top 10 symbols most skipped (and why)")
    lines.append("")
    top_symbols = sorted(symbol_skip_count.items(), key=lambda x: -x[1])[:10]
    for sym, count in top_symbols:
        reasons = sorted(symbol_skip_reasons.get(sym, set()))
        lines.append(f"- **{sym}:** {count} — {', '.join(reasons)}")
    lines.append("")
    lines.append("")

    # --- 3.4a Signal trend (open positions, analytics only) ---
    signal_cache_path = REPO_ROOT / "state" / "signal_strength_cache.json"
    signal_cache_data = _load_json(signal_cache_path, {})
    if isinstance(signal_cache_data, dict) and signal_cache_data:
        trend_counts: dict[str, int] = defaultdict(int)
        rows: list[tuple[str, str, float, float | None, float | None, str, str]] = []
        for sym, ent in signal_cache_data.items():
            if not isinstance(ent, dict) or "signal_strength" not in ent:
                continue
            try:
                current = float(ent["signal_strength"])
            except (TypeError, ValueError):
                continue
            side = (ent.get("position_side") or "LONG").upper()
            if side not in ("LONG", "SHORT"):
                side = "LONG"
            prev = ent.get("prev_signal_strength")
            prev_f = float(prev) if prev is not None else None
            delta = ent.get("signal_delta")
            delta_f = float(delta) if delta is not None else None
            trend = (ent.get("signal_trend") or "unknown").lower()
            evaluated_at = ent.get("evaluated_at") or ""
            trend_counts[trend] += 1
            rows.append((sym, side, current, prev_f, delta_f, trend, evaluated_at))
        lines.append("## 3.4a Signal trend (open positions)")
        lines.append("")
        lines.append("| symbol | side | current | prev | delta | trend | evaluated_at |")
        lines.append("|--------|------|---------|------|-------|-------|--------------|")
        for sym, side, current, prev_f, delta_f, trend, evaluated_at in sorted(rows, key=lambda r: (r[5], -(r[4] or 0))):
            prev_s = f"{prev_f:.2f}" if prev_f is not None else "—"
            delta_s = f"{delta_f:+.2f}" if delta_f is not None else "—"
            lines.append(f"| {sym} | {side} | {current:.2f} | {prev_s} | {delta_s} | {trend} | {evaluated_at[:19] if evaluated_at else '—'} |")
        lines.append("")
        lines.append("**Summary:** " + ", ".join(f"{k}: {v}" for k, v in sorted(trend_counts.items())))
        if rows:
            with_delta = [(r[0], r[4]) for r in rows if r[4] is not None]
            if with_delta:
                most_weakening = min(with_delta, key=lambda x: x[1])
                most_strengthening = max(with_delta, key=lambda x: x[1])
                lines.append(f"- **Most weakening:** {most_weakening[0]} (delta {most_weakening[1]:+.2f})")
                lines.append(f"- **Most strengthening:** {most_strengthening[0]} (delta {most_strengthening[1]:+.2f})")
        lines.append("")
    else:
        lines.append("## 3.4a Signal trend (open positions)")
        lines.append("")
        lines.append("_No signal_strength_cache data (run engine so open_position_refresh runs)._")
        lines.append("")

    # --- 3.4b Correlation concentration ---
    corr_cache_path = REPO_ROOT / "state" / "signal_correlation_cache.json"
    corr_data = _load_json(corr_cache_path, {})
    if isinstance(corr_data, dict) and corr_data.get("pairs"):
        pairs = corr_data.get("pairs") or []
        top_syms = corr_data.get("top_symbols") or {}
        lines.append("## 3.4b Correlation concentration")
        lines.append("")
        lines.append(f"- **as_of:** {corr_data.get('as_of', '—')} | **window_minutes:** {corr_data.get('window_minutes', '—')}")
        if pairs:
            best = max(pairs, key=lambda p: abs(p.get("corr") or 0))
            lines.append(f"- **Max |corr| pair:** {best.get('a', '')}–{best.get('b', '')} (corr={best.get('corr', 0):.2f}, n={best.get('n', 0)})")
        lines.append("")
        lines.append("**Top pairs:**")
        for p in pairs[:10]:
            lines.append(f"- {p.get('a', '')}–{p.get('b', '')}: corr={p.get('corr', 0):.2f}, n={p.get('n', 0)}")
        conc = [(s, (top_syms.get(s) or {}).get("max_corr")) for s in top_syms if isinstance(top_syms.get(s), dict)]
        conc = [(s, c) for s, c in conc if c is not None]
        if conc:
            conc.sort(key=lambda x: abs(x[1]) if x[1] is not None else 0, reverse=True)
            lines.append("")
            lines.append("**Symbols by highest max_corr (concentration risk proxy):**")
            for sym, mc in conc[:5]:
                lines.append(f"- **{sym}:** max_corr={mc:.2f}")
        lines.append("")
    else:
        lines.append("## 3.4b Correlation concentration")
        lines.append("")
        lines.append("_WARN: Correlation cache missing or empty. Run: `python3 scripts/compute_signal_correlation_snapshot.py --minutes 60 --topk 20`_")
        lines.append("")

    # --- 3.5 Board actions (deterministic rules) ---
    lines.append("## 3.5 Board actions (recommended)")
    lines.append("")
    actions: list[str] = []
    if skip_counts.get("per_position_limit_exceeded", 0) > 10:
        actions.append("- **Per-position limit blocks high:** Consider increasing `per_position_fraction_of_wheel_budget` or narrowing universe so smaller notionals are chosen (config change).")
    if skip_counts.get("allocation_exceeded", 0) > 5 or skip_counts.get("capital_limit", 0) > 5:
        actions.append("- **Capital/allocation blocks:** Wheel budget may be tight; review 25% allocation or reduce concurrent positions (config / MEMORY_BANK).")
    if skip_counts.get("no_contracts_in_range", 0) > 20:
        actions.append("- **No contracts in range dominates:** Widen DTE or delta bands in `strategies.wheel.csp` (target_dte_min/max, delta_min/max).")
    if skip_counts.get("no_spot", 0) > 50:
        actions.append("- **No spot / quotes empty:** Spot source distribution suggests data feed issue; verify Alpaca quote/bar and normalize_alpaca_quote (Cursor / SRE).")
    if symbol_skip_count and len(top_symbols) >= 1 and top_symbols[0][1] > 5:
        sym, cnt = top_symbols[0]
        actions.append(f"- **Concentration of skips in {sym}:** Consider diversifying via max symbol frequency or universe constraints (config).")
    if cycles_run > 0 and orders_submitted == 0 and len(fills) == 0:
        dominant = max(skip_counts.items(), key=lambda x: x[1]) if skip_counts else ("none", 0)
        actions.append(f"- **Wheel running but zero submissions:** Dominant blocker is **{dominant[0]}** ({dominant[1]}). Address with the matching action above (Cursor / config).")
    if fills and wheel_budget and total_premium > 0:
        actions.append("- **Fills present:** Review top decisions (3.3) for UW alignment and risk concentration; promote or tune rules as in MEMORY_BANK (Mark / Cursor).")
    if not actions:
        actions.append("- **No strong signal:** Review skip distribution and open positions; run `python3 scripts/run_wheel_check_on_droplet.py` for live diagnostics.")
    for i, a in enumerate(actions[:7], 1):
        lines.append(f"{i}. {a}")
    lines.append("")

    # --- Board Watchlists (derived from signal trends & correlation) ---
    watchlists_path = REPORTS_DIR / f"wheel_watchlists_{target_date}.json"
    if watchlists_path.exists():
        try:
            watchlists_data = _load_json(watchlists_path, {})
            weakening_count = len(watchlists_data.get("weakening_signals") or [])
            corr_count = len(watchlists_data.get("correlation_concentration") or [])
            lines.append("## Board Watchlists (Derived from Signal Trends & Correlation)")
            lines.append("")
            lines.append(f"- **Weakening signal watchlist:** {weakening_count} symbol(s)")
            lines.append(f"- **Correlation concentration watchlist:** {corr_count} symbol(s)")
            lines.append(f"- Artifact: `reports/wheel_watchlists_{target_date}.json`")
            lines.append("")
        except Exception:
            lines.append("## Board Watchlists (Derived from Signal Trends & Correlation)")
            lines.append("")
            lines.append(f"- Artifact: `reports/wheel_watchlists_{target_date}.json` (present; parse skipped)")
            lines.append("")
    else:
        lines.append("## Board Watchlists (Derived from Signal Trends & Correlation)")
        lines.append("")
        lines.append("_No watchlist artifact for this date. Run Board EOD to generate `reports/wheel_watchlists_<date>.json`._")
        lines.append("")

    lines.append("---")
    lines.append(f"*Generated by scripts/generate_wheel_daily_review.py for {target_date} (lookback {lookback_hours}h).*")
    return "\n".join(lines), verdict_ok, counters, badge


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate wheel daily review markdown")
    parser.add_argument("--date", type=str, help="Date YYYY-MM-DD (default: today UTC)")
    parser.add_argument("--days", type=float, default=1, help="Lookback window in days (default 1)")
    parser.add_argument("--no-fail", action="store_true", help="Do not exit non-zero on governance regressions")
    parser.add_argument("--no-correlation-snapshot", action="store_true", help="Do not run correlation snapshot before review")
    args = parser.parse_args()
    if not args.no_correlation_snapshot:
        try:
            import subprocess
            subprocess.run(
                [sys.executable, str(REPO_ROOT / "scripts" / "compute_signal_correlation_snapshot.py"), "--minutes", "60", "--topk", "20", "--no-emit"],
                cwd=str(REPO_ROOT),
                timeout=120,
                capture_output=True,
            )
        except Exception:
            pass
    lookback_hours = args.days * 24
    md, verdict_ok, counters, badge = generate(date_str=args.date, lookback_hours=lookback_hours)
    date_str = args.date or datetime.now(timezone.utc).date().isoformat()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORTS_DIR / f"wheel_daily_review_{date_str}.md"
    out_path.write_text(md, encoding="utf-8")
    print(f"Wrote {out_path}")
    badge_path = REPORTS_DIR / f"wheel_governance_badge_{date_str}.json"
    badge_path.write_text(json.dumps(badge, indent=2, default=str), encoding="utf-8")
    print(f"Wrote {badge_path}")
    if not verdict_ok and not args.no_fail:
        print("Governance regressions detected; exiting with code 1.", file=sys.stderr)
        sys.exit(1)
    if badge.get("overall_status") == "FAIL" and not args.no_fail:
        print("Wheel governance badge FAIL; exiting with code 1.", file=sys.stderr)
        sys.exit(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
