#!/usr/bin/env python3
"""
Stock Quant Officer EOD runner.

- Ensures board/eod/ and board/eod/out/
- Loads canonical 8-file EOD bundle from repo root (logs/, state/)
- Loads Stock Quant Officer contract (board/stock_quant_officer_contract.md)
- Builds prompt (contract + bundle summary), calls Clawdbot agent, parses JSON
- Writes board/eod/out/stock_quant_officer_eod_<DATE>.json and .md

Run from repo root: python board/eod/run_stock_quant_officer_eod.py
Use --dry-run to skip Clawdbot and write stub JSON/memo (for testing without clawdbot).
Set CLAWDBOT_SESSION_ID for clawdbot agent --session-id.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Repo root: parent of board/ (script at board/eod/run_...py -> parents[2])
SCRIPT_DIR = Path(__file__).resolve().parent
BOARD_DIR = SCRIPT_DIR.parent
REPO_ROOT = BOARD_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
OUT_DIR = SCRIPT_DIR / "out"  # board/eod/out; daily bundle goes in OUT_DIR / <date>/
REPORTS_DIR = REPO_ROOT / "reports"
CONTRACT_PATH = BOARD_DIR / "stock_quant_officer_contract.md"

# Board watchlist thresholds (REVIEW ONLY — do not import in trading code).
SIGNAL_WEAKENING_THRESHOLD = -0.50
CORRELATION_CONCENTRATION_THRESHOLD = 0.80

STATE_DIR = REPO_ROOT / "state"
SIGNAL_STRENGTH_CACHE_PATH = STATE_DIR / "signal_strength_cache.json"
SIGNAL_CORRELATION_CACHE_PATH = STATE_DIR / "signal_correlation_cache.json"

CLAWDBOT_PATH = os.environ.get("CLAWDBOT_PATH") or (
    r"C:\Users\markl\AppData\Roaming\npm\clawdbot.cmd" if sys.platform == "win32" else "clawdbot"
)
# Windows CLI length limit; keep prompt under this to avoid "command line too long".
MAX_PROMPT_LEN = 6000

# Canonical EOD bundle paths (source of truth on droplet: logs/, state/ under repo root).
# Do not move or rename; trading engine writes these.
BUNDLE_FILES = [
    ("logs/attribution.jsonl", "attribution"),
    ("logs/exit_attribution.jsonl", "exit_attribution"),
    ("logs/master_trade_log.jsonl", "master_trade_log"),
    ("state/blocked_trades.jsonl", "blocked_trades"),
    ("state/daily_start_equity.json", "daily_start_equity"),
    ("state/peak_equity.json", "peak_equity"),
    ("state/signal_weights.json", "signal_weights"),
    ("state/daily_universe_v2.json", "daily_universe_v2"),
]

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)


def ensure_dirs() -> None:
    SCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)


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


def _load_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (json.JSONDecodeError, OSError):
        return None


def load_bundle() -> tuple[dict[str, dict | list | None], list[str]]:
    """Load 8-file bundle from repo root (canonical paths: logs/, state/). Returns (data, missing)."""
    data: dict[str, dict | list | None] = {}
    missing: list[str] = []
    for rel, name in BUNDLE_FILES:
        path = (REPO_ROOT / rel).resolve()
        if not path.exists():
            log.error("Bundle file missing: %s", path)
            missing.append(rel)
            data[name] = None
            continue
        try:
            size = path.stat().st_size
        except OSError:
            size = -1
        if size == 0:
            log.warning("Bundle file empty: %s", path)
            data[name] = [] if name in ("attribution", "exit_attribution", "master_trade_log", "blocked_trades") else None
            continue
        if name in ("attribution", "exit_attribution", "master_trade_log", "blocked_trades"):
            data[name] = _load_jsonl(path)
        else:
            data[name] = _load_json(path)
    return data, missing


def ensure_wheel_daily_review(date_str: str) -> None:
    """Generate reports/wheel_daily_review_<date>.md if not present (for Board)."""
    reports_dir = REPO_ROOT / "reports"
    path = reports_dir / f"wheel_daily_review_{date_str}.md"
    if path.exists():
        return
    try:
        import sys
        if str(REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(REPO_ROOT))
        from scripts.generate_wheel_daily_review import generate
        reports_dir.mkdir(parents=True, exist_ok=True)
        md, _ok, _, badge = generate(date_str=date_str, lookback_hours=24)
        path.write_text(md, encoding="utf-8")
        log.info("Generated %s", path)
        badge_path = reports_dir / f"wheel_governance_badge_{date_str}.json"
        badge_path.write_text(json.dumps(badge, indent=2, default=str), encoding="utf-8")
        log.info("Generated %s", badge_path)
    except Exception as e:
        log.warning("Could not generate wheel daily review: %s", e)


def load_rolling_windows(date_str: str) -> dict:
    """Load or compute 1/3/5/7 day rolling windows for Board. Persists to state/ to keep date folder at <=9 files."""
    state_path = STATE_DIR / f"eod_rolling_windows_{date_str}.json"
    if state_path.exists():
        try:
            data = json.loads(state_path.read_text(encoding="utf-8", errors="replace"))
            return {
                "win_rate_by_window": data.get("win_rate_by_window") or {},
                "pnl_by_window": data.get("pnl_by_window") or {},
                "exit_reason_counts_by_window": data.get("exit_reason_counts_by_window") or {},
                "blocked_trade_counts_by_window": data.get("blocked_trade_counts_by_window") or {},
                "signal_decay_exit_rate_by_window": data.get("signal_decay_exit_rate_by_window") or {},
                "multi_day_analysis": data.get("multi_day_analysis") or {},
            }
        except (json.JSONDecodeError, OSError):
            pass
    try:
        from board.eod.rolling_windows import build_rolling_windows
        rolling = build_rolling_windows(REPO_ROOT, date_str, [1, 3, 5, 7])
        payload = {
            "date": date_str,
            "win_rate_by_window": rolling.get("win_rate_by_window", {}),
            "pnl_by_window": rolling.get("pnl_by_window", {}),
            "exit_reason_counts_by_window": rolling.get("exit_reason_counts_by_window", {}),
            "blocked_trade_counts_by_window": rolling.get("blocked_trade_counts_by_window", {}),
            "signal_decay_exit_rate_by_window": rolling.get("signal_decay_exit_rate_by_window", {}),
        }
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        log.info("Computed and wrote rolling windows to %s", state_path)
        return {
            "win_rate_by_window": rolling.get("win_rate_by_window", {}),
            "pnl_by_window": rolling.get("pnl_by_window", {}),
            "exit_reason_counts_by_window": rolling.get("exit_reason_counts_by_window", {}),
            "blocked_trade_counts_by_window": rolling.get("blocked_trade_counts_by_window", {}),
            "signal_decay_exit_rate_by_window": rolling.get("signal_decay_exit_rate_by_window", {}),
            "multi_day_analysis": {},
        }
    except Exception as e:
        log.warning("Could not build rolling windows: %s", e)
        return {
            "win_rate_by_window": {},
            "pnl_by_window": {},
            "exit_reason_counts_by_window": {},
            "blocked_trade_counts_by_window": {},
            "signal_decay_exit_rate_by_window": {},
            "multi_day_analysis": {},
        }


def summarize_bundle(
    data: dict[str, dict | list | None],
    missing: list[str],
    date_str: str = "",
    wheel_governance_badge: dict | None = None,
) -> str:
    """Build text summary of EOD bundle for the prompt. If wheel_governance_badge is provided, it is included near the top."""
    lines: list[str] = []
    if wheel_governance_badge:
        lines.extend([
            "## Wheel governance badge",
            "",
            f"- **Status:** {wheel_governance_badge.get('overall_status', '?')}",
            f"- **Event chain coverage:** {wheel_governance_badge.get('event_chain_coverage_pct', '')}%",
            f"- **Cycles with full chain:** {wheel_governance_badge.get('cycles_with_full_chain', 0)} / {wheel_governance_badge.get('cycles_total', 0)}",
            f"- **Idempotency hits:** {wheel_governance_badge.get('idempotency_hits', 0)}",
            f"- **Board action closure:** {wheel_governance_badge.get('board_action_closure', '?')}",
            f"- **Dominant blocker:** {wheel_governance_badge.get('dominant_blocker', '?')}",
            f"- **Generated at:** {wheel_governance_badge.get('generated_at', '')}",
            "",
            "---",
            "",
        ])
    lines.extend(["## EOD bundle summary", ""])

    # Attribution + exit attribution
    attr = data.get("attribution") or []
    exit_attr = data.get("exit_attribution") or []
    if isinstance(attr, list) and attr:
        wins = sum(1 for r in attr if (r.get("pnl_usd") or 0) > 0)
        losses = sum(1 for r in attr if (r.get("pnl_usd") or 0) < 0)
        total_pnl = sum(float(r.get("pnl_usd") or 0) for r in attr)
        reasons: dict[str, int] = {}
        for r in attr:
            ctx = r.get("context") or {}
            ex = ctx.get("close_reason") or "unknown"
            reasons[ex] = reasons.get(ex, 0) + 1
        sample = attr[-5:] if len(attr) >= 5 else attr
        lines.append("### Attribution (logs/attribution.jsonl)")
        lines.append(f"- Trades: {len(attr)}, Wins: {wins}, Losses: {losses}, Total P&L USD: {total_pnl:.2f}")
        lines.append(f"- Exit reasons: {reasons}")
        lines.append("- Sample trades (last 5):")
        for t in sample:
            lines.append(f"  - {t.get('symbol')} pnl_usd={t.get('pnl_usd')} ts={t.get('ts', '')[:19]}")
        lines.append("")
    elif "logs/attribution.jsonl" not in missing:
        lines.append("### Attribution (logs/attribution.jsonl): empty or invalid.")
        lines.append("")
    else:
        lines.append("### Attribution: **MISSING**")
        lines.append("")

    if isinstance(exit_attr, list) and exit_attr:
        total_pnl_ex = sum(float(r.get("pnl") or 0) for r in exit_attr)
        reasons_ex: dict[str, int] = {}
        for r in exit_attr:
            ex = str(r.get("exit_reason") or "unknown")
            reasons_ex[ex] = reasons_ex.get(ex, 0) + 1
        sample_ex = exit_attr[-5:] if len(exit_attr) >= 5 else exit_attr
        lines.append("### Exit attribution (logs/exit_attribution.jsonl)")
        lines.append(f"- Exits: {len(exit_attr)}, Total P&L: {total_pnl_ex:.2f}")
        lines.append(f"- Exit reasons: {reasons_ex}")
        lines.append("- Sample (last 5):")
        for t in sample_ex:
            lines.append(f"  - {t.get('symbol')} pnl={t.get('pnl')} reason={t.get('exit_reason')}")
        lines.append("")
    elif "logs/exit_attribution.jsonl" not in missing:
        lines.append("### Exit attribution: empty or invalid.")
        lines.append("")
    else:
        lines.append("### Exit attribution: **MISSING**")
        lines.append("")

    # Master trade log
    mtl = data.get("master_trade_log") or []
    if isinstance(mtl, list) and mtl:
        entries = sum(1 for r in mtl if r.get("entry_ts") and not r.get("exit_ts"))
        exits = sum(1 for r in mtl if r.get("exit_ts"))
        lines.append("### Master trade log (logs/master_trade_log.jsonl)")
        lines.append(f"- Records: {len(mtl)}, entries-without-exit: {entries}, with-exit: {exits}")
        lines.append("")
    elif "logs/master_trade_log.jsonl" not in missing:
        lines.append("### Master trade log: empty or invalid.")
        lines.append("")
    else:
        lines.append("### Master trade log: **MISSING**")
        lines.append("")

    # Blocked trades
    bt = data.get("blocked_trades") or []
    if isinstance(bt, list) and bt:
        by_reason: dict[str, int] = {}
        for r in bt:
            reason = str(r.get("reason") or "unknown")
            by_reason[reason] = by_reason.get(reason, 0) + 1
        sample_bt = bt[-5:] if len(bt) >= 5 else bt
        lines.append("### Blocked trades (state/blocked_trades.jsonl)")
        lines.append(f"- Count: {len(bt)}")
        lines.append(f"- By reason: {by_reason}")
        lines.append("- Sample (last 5):")
        for t in sample_bt:
            lines.append(f"  - {t.get('symbol')} reason={t.get('reason')} score={t.get('score')}")
        lines.append("")
    elif "state/blocked_trades.jsonl" not in missing:
        lines.append("### Blocked trades: empty or invalid.")
        lines.append("")
    else:
        lines.append("### Blocked trades: **MISSING**")
        lines.append("")

    # Equity
    dse = data.get("daily_start_equity")
    pe = data.get("peak_equity")
    lines.append("### Daily start equity (state/daily_start_equity.json)")
    if isinstance(dse, dict):
        lines.append(f"- equity: {dse.get('equity')}, date: {dse.get('date')}, updated: {dse.get('updated')}")
    elif "state/daily_start_equity.json" in missing:
        lines.append("- **MISSING**")
    else:
        lines.append("- empty or invalid")
    lines.append("")
    lines.append("### Peak equity (state/peak_equity.json)")
    if isinstance(pe, dict):
        lines.append(f"- peak_equity: {pe.get('peak_equity')}, peak_timestamp: {pe.get('peak_timestamp')}")
    elif "state/peak_equity.json" in missing:
        lines.append("- **MISSING**")
    else:
        lines.append("- empty or invalid")
    lines.append("")

    # Signal weights
    sw = data.get("signal_weights")
    lines.append("### Signal weights (state/signal_weights.json)")
    if isinstance(sw, dict):
        keys = list(sw.keys())[:20]
        lines.append(f"- Top-level keys (up to 20): {keys}")
    elif "state/signal_weights.json" in missing:
        lines.append("- **MISSING**")
    else:
        lines.append("- empty or invalid")
    lines.append("")

    # Daily universe v2
    uv = data.get("daily_universe_v2")
    lines.append("### Daily universe v2 (state/daily_universe_v2.json)")
    if isinstance(uv, dict):
        syms = uv.get("symbols")
        if isinstance(syms, list):
            lines.append(f"- Symbol count: {len(syms)}, sample: {syms[:15]}")
        else:
            lines.append(f"- Keys: {list(uv.keys())[:15]}")
    elif "state/daily_universe_v2.json" in missing:
        lines.append("- **MISSING**")
    else:
        lines.append("- empty or invalid")
    lines.append("")

    if missing:
        lines.append("### Missing files")
        lines.append(", ".join(missing))
        lines.append("")

    # Wheel strategy daily review (reports/wheel_daily_review_<date>.md)
    if date_str:
        wheel_review_path = REPO_ROOT / "reports" / f"wheel_daily_review_{date_str}.md"
        if wheel_review_path.exists():
            lines.append("## Wheel strategy daily review")
            lines.append("")
            lines.append("(See reports/wheel_daily_review_<date>.md. Excerpt below.)")
            lines.append("")
            try:
                lines.append(wheel_review_path.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                lines.append("_Could not read file._")
        else:
            lines.append("## Wheel strategy daily review")
            lines.append("")
            lines.append("_Report not generated for this date. Run: python3 scripts/generate_wheel_daily_review.py --date " + date_str + "_")
        lines.append("")

    return "\n".join(lines)


def load_contract() -> str:
    if not CONTRACT_PATH.exists():
        log.warning("Contract missing: %s", CONTRACT_PATH)
        return ""
    return CONTRACT_PATH.read_text(encoding="utf-8", errors="replace")


def wheel_action_id(title: str, owner: str, reference_section: str) -> str:
    """Stable action_id: hash(title + owner + reference_section)."""
    raw = f"{title}|{owner}|{reference_section}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def load_prior_wheel_actions(date_str: str) -> list[dict]:
    """Load the most recent prior wheel_actions_<date>.json (yesterday or latest before today)."""
    try:
        today = datetime.fromisoformat(date_str + "T00:00:00+00:00")
    except Exception:
        return []
    prior_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    path = REPORTS_DIR / f"wheel_actions_{prior_date}.json"
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
            actions = data.get("actions") or []
            for a in actions:
                if not a.get("action_id"):
                    a["action_id"] = wheel_action_id(a.get("title", ""), a.get("owner", ""), a.get("reference_section", ""))
            return actions
        except (json.JSONDecodeError, OSError):
            pass
    # Fallback: any wheel_actions_*.json with date < today
    candidates = sorted(REPORTS_DIR.glob("wheel_actions_*.json"), reverse=True)
    for p in candidates:
        try:
            d = p.stem.replace("wheel_actions_", "")
            if d < date_str:
                data = json.loads(p.read_text(encoding="utf-8", errors="replace"))
                actions = data.get("actions") or []
                for a in actions:
                    if not a.get("action_id"):
                        a["action_id"] = wheel_action_id(a.get("title", ""), a.get("owner", ""), a.get("reference_section", ""))
                return actions
        except Exception:
            continue
    return []


def load_signal_strength_cache() -> dict:
    """Load state/signal_strength_cache.json. Returns {} if missing or invalid."""
    data = _load_json(SIGNAL_STRENGTH_CACHE_PATH)
    return data if isinstance(data, dict) else {}


def load_signal_correlation_cache() -> dict:
    """Load state/signal_correlation_cache.json. Returns {} if missing or invalid."""
    data = _load_json(SIGNAL_CORRELATION_CACHE_PATH)
    return data if isinstance(data, dict) else {}


def build_weakening_watchlist(signal_cache: dict) -> list[dict]:
    """Build Weakening Signal Watchlist: open positions with trend==weakening and delta <= threshold.
    REVIEW ONLY; not used by trading code.
    """
    out: list[dict] = []
    for sym, ent in signal_cache.items():
        if not isinstance(ent, dict) or "signal_strength" not in ent:
            continue
        trend = (ent.get("signal_trend") or "").lower()
        if trend != "weakening":
            continue
        delta_raw = ent.get("signal_delta")
        if delta_raw is None:
            continue
        try:
            delta = float(delta_raw)
        except (TypeError, ValueError):
            continue
        if delta > SIGNAL_WEAKENING_THRESHOLD:
            continue
        try:
            current = float(ent["signal_strength"])
        except (TypeError, ValueError):
            current = 0.0
        prev_raw = ent.get("prev_signal_strength")
        prev_signal = float(prev_raw) if prev_raw is not None else None
        side = (ent.get("position_side") or "LONG").upper()
        if side not in ("LONG", "SHORT"):
            side = "LONG"
        out.append({
            "symbol": sym,
            "side": side,
            "current_signal": round(current, 4),
            "prev_signal": round(prev_signal, 4) if prev_signal is not None else None,
            "signal_delta": round(delta, 4),
            "evaluated_at": ent.get("evaluated_at") or "",
        })
    return out


def build_correlation_watchlist(corr_cache: dict) -> list[dict]:
    """Build Correlation Concentration Watchlist: symbols with max_corr >= threshold.
    REVIEW ONLY; not used by trading code.
    """
    out: list[dict] = []
    top_symbols = corr_cache.get("top_symbols") or {}
    if not isinstance(top_symbols, dict):
        return out
    for sym, info in top_symbols.items():
        if not isinstance(info, dict):
            continue
        max_corr_raw = info.get("max_corr")
        if max_corr_raw is None:
            continue
        try:
            max_corr = float(max_corr_raw)
        except (TypeError, ValueError):
            continue
        if max_corr < CORRELATION_CONCENTRATION_THRESHOLD:
            continue
        avg_raw = info.get("avg_corr_topk")
        try:
            avg_corr_topk = round(float(avg_raw), 4) if avg_raw is not None else None
        except (TypeError, ValueError):
            avg_corr_topk = None
        out.append({
            "symbol": sym,
            "max_corr": round(max_corr, 4),
            "most_correlated_with": info.get("most_correlated_with"),
            "avg_corr_topk": avg_corr_topk,
        })
    return out


def validate_survivorship_correlation_review(
    obj: dict, signal_survivorship: dict | None, corr_cache: dict | None
) -> tuple[bool, list[str]]:
    """Board must review signal survivorship and correlation when data exists. Return (ok, errors)."""
    errors: list[str] = []
    refs = str(obj.get("summary") or "") + json.dumps(obj.get("executive_answers") or {})
    if signal_survivorship and (signal_survivorship.get("signals") or {}):
        if "survivorship" not in refs.lower() and "signal_survivorship" not in refs.lower():
            errors.append("Board must reference signal survivorship when signals exist")
    if corr_cache and (corr_cache.get("pairs") or corr_cache.get("top_symbols")):
        if "correlation" not in refs.lower() and "correl" not in refs.lower():
            errors.append("Board must reference correlation when cache has data")
    return (len(errors) == 0), errors


def validate_adversarial_output(obj: dict, rolling_windows: dict) -> tuple[bool, list[str]]:
    """Board must reference rolling windows, include executive answers, customer advocate challenges, concrete change, and missed_money. Return (ok, errors)."""
    errors: list[str] = []
    # Rolling windows referenced (in summary or executive_answers)
    summary = str(obj.get("summary") or "")
    exec_answers = obj.get("executive_answers") or {}
    if not isinstance(exec_answers, dict):
        exec_answers = {}
    refs = summary + json.dumps(exec_answers)
    if rolling_windows and (rolling_windows.get("pnl_by_window") or rolling_windows.get("win_rate_by_window")):
        if "1_day" not in refs and "3_day" not in refs and "5_day" not in refs and "7_day" not in refs and "pnl_by_window" not in refs:
            errors.append("Board output must reference rolling windows (1/3/5/7 day or pnl_by_window)")
    # Executive answers present
    for role in ("CEO", "CTO_SRE", "Head_of_Trading", "Risk_CRO"):
        if not exec_answers.get(role):
            errors.append(f"executive_answers missing role: {role}")
    # Customer Advocate challenged
    challenges = obj.get("customer_advocate_challenges") or []
    if not challenges and exec_answers:
        errors.append("customer_advocate_challenges must be non-empty when executive_answers present")
    # Concrete change
    recs = obj.get("recommendations") or []
    actions = obj.get("wheel_actions") or []
    if not recs and not actions:
        errors.append("At least one concrete change required (recommendations or wheel_actions)")
    # Missed money
    missed = obj.get("missed_money") or {}
    if not isinstance(missed, dict):
        missed = {}
    for key in ("blocked_trade_opportunity_cost", "early_exit_opportunity_cost", "correlation_concentration_cost"):
        val = missed.get(key)
        if val is None and key not in missed:
            errors.append(f"missed_money missing: {key}")
        elif isinstance(val, dict) and val.get("unknown") and not val.get("reason"):
            errors.append(f"missed_money.{key} if unknown must include reason")
    return (len(errors) == 0), errors


def validate_watchlist_responses(
    obj: dict,
    weakening_list: list[dict],
    correlation_list: list[dict],
) -> tuple[bool, list[str]]:
    """If watchlists are non-empty, Board must provide wheel_watchlists with rationales. Return (ok, errors)."""
    errors: list[str] = []
    wheel_watchlists = obj.get("wheel_watchlists") or {}
    if not isinstance(wheel_watchlists, dict):
        wheel_watchlists = {}

    weakening_out = wheel_watchlists.get("weakening_signals") or []
    if not isinstance(weakening_out, list):
        weakening_out = []
    if weakening_list:
        required_symbols = {e["symbol"] for e in weakening_list}
        by_symbol = {e.get("symbol"): e for e in weakening_out if e.get("symbol")}
        for sym in required_symbols:
            entry = by_symbol.get(sym)
            if not entry:
                errors.append(f"weakening_signals: missing Board response for symbol {sym}")
            elif not (entry.get("board_rationale") or str(entry.get("board_rationale")).strip()):
                errors.append(f"weakening_signals: empty board_rationale for {sym}")
            elif entry.get("exit_review_condition") is None and "exit_review_condition" not in entry:
                errors.append(f"weakening_signals: missing exit_review_condition for {sym}")

    corr_out = wheel_watchlists.get("correlation_concentration") or []
    if not isinstance(corr_out, list):
        corr_out = []
    if correlation_list:
        required_symbols = {e["symbol"] for e in correlation_list}
        by_symbol = {e.get("symbol"): e for e in corr_out if e.get("symbol")}
        for sym in required_symbols:
            entry = by_symbol.get(sym)
            if not entry:
                errors.append(f"correlation_concentration: missing Board response for symbol {sym}")
            elif not (entry.get("board_rationale") or str(entry.get("board_rationale")).strip()):
                errors.append(f"correlation_concentration: empty board_rationale for {sym}")
            elif entry.get("mitigation_considered") is None and "mitigation_considered" not in entry:
                errors.append(f"correlation_concentration: missing mitigation_considered for {sym}")

    return (len(errors) == 0), errors


def build_closure_table(prior_actions: list[dict]) -> str:
    """Build REQUIRED closure table for prompt."""
    if not prior_actions:
        return ""
    lines = ["## Prior wheel actions (REQUIRED closure)", ""]
    for a in prior_actions:
        aid = a.get("action_id", wheel_action_id(a.get("title", ""), a.get("owner", ""), a.get("reference_section", "")))
        lines.append(f"- action_id: {aid} | title: {a.get('title', '')} | prior_status: {a.get('status', 'proposed')} | notes: {a.get('notes', '')}")
    lines.append("")
    lines.append("For EVERY prior action_id above, your wheel_actions output MUST include an entry with that action_id, status in {\"done\", \"blocked\", \"deferred\"}, and a short note. New actions may have status=\"proposed\".")
    lines.append("")
    return "\n".join(lines)


def validate_closure(obj: dict, prior_actions: list[dict]) -> tuple[bool, list[str]]:
    """Check that every prior action has closure in obj['wheel_actions']. Return (ok, list of missing action_ids)."""
    if not prior_actions:
        return True, []
    wheel_actions = obj.get("wheel_actions") or []
    missing: list[str] = []
    for a in prior_actions:
        aid = a.get("action_id") or wheel_action_id(a.get("title", ""), a.get("owner", ""), a.get("reference_section", ""))
        entry = next((w for w in wheel_actions if (w.get("action_id") or wheel_action_id(w.get("title", ""), w.get("owner", ""), w.get("reference_section", ""))) == aid), None)
        if not entry:
            missing.append(aid)
            continue
        status = (entry.get("status") or "").lower()
        if status not in ("done", "blocked", "deferred"):
            missing.append(aid)
    return (len(missing) == 0), missing


def write_wheel_actions(date_str: str, obj: dict, prior_actions: list[dict]) -> None:
    """Persist reports/wheel_actions_<date>.json from board output and prior closures."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    wheel_actions = obj.get("wheel_actions") or []
    # Resolve action_id for each
    out_actions: list[dict] = []
    for wa in wheel_actions:
        aid = wa.get("action_id") or wheel_action_id(wa.get("title", ""), wa.get("owner", ""), wa.get("reference_section", ""))
        out_actions.append({
            "action_id": aid,
            "title": wa.get("title", ""),
            "owner": wa.get("owner", ""),
            "reference_section": wa.get("reference_section", ""),
            "rationale": wa.get("body", wa.get("rationale", "")),
            "status": (wa.get("status") or "proposed").lower(),
            "notes": wa.get("note", wa.get("notes", "")),
        })
    payload = {"date": date_str, "actions": out_actions}
    path = REPORTS_DIR / f"wheel_actions_{date_str}.json"
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    log.info("Wrote %s", path)


def write_wheel_watchlists(
    date_str: str,
    weakening_input: list[dict],
    correlation_input: list[dict],
    obj: dict,
) -> None:
    """Persist reports/wheel_watchlists_<date>.json (input watchlists + thresholds + board responses)."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    watchlists = obj.get("wheel_watchlists") or {}
    if not isinstance(watchlists, dict):
        watchlists = {}
    weakening_out = {e.get("symbol"): e for e in (watchlists.get("weakening_signals") or []) if e.get("symbol")}
    correlation_out = {e.get("symbol"): e for e in (watchlists.get("correlation_concentration") or []) if e.get("symbol")}

    weakening_merged: list[dict] = []
    for e in weakening_input:
        rec = dict(e)
        br = weakening_out.get(e["symbol"]) or {}
        rec["board_rationale"] = br.get("board_rationale")
        rec["exit_review_condition"] = br.get("exit_review_condition")
        weakening_merged.append(rec)

    correlation_merged: list[dict] = []
    for e in correlation_input:
        rec = dict(e)
        br = correlation_out.get(e["symbol"]) or {}
        rec["board_rationale"] = br.get("board_rationale")
        rec["mitigation_considered"] = br.get("mitigation_considered")
        correlation_merged.append(rec)

    payload = {
        "date": date_str,
        "thresholds": {
            "signal_weakening": SIGNAL_WEAKENING_THRESHOLD,
            "correlation_concentration": CORRELATION_CONCENTRATION_THRESHOLD,
        },
        "weakening_signals": weakening_merged,
        "correlation_concentration": correlation_merged,
    }
    path = REPORTS_DIR / f"wheel_watchlists_{date_str}.json"
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    log.info("Wrote %s", path)


def _rolling_windows_prompt_block(rolling_windows: dict) -> str:
    """Inject rolling 1/3/5/7 day data and executive + Customer Advocate + missed money requirements."""
    pnl = rolling_windows.get("pnl_by_window") or {}
    win_rate = rolling_windows.get("win_rate_by_window") or {}
    exit_reasons = rolling_windows.get("exit_reason_counts_by_window") or {}
    blocked = rolling_windows.get("blocked_trade_counts_by_window") or {}
    decay_rate = rolling_windows.get("signal_decay_exit_rate_by_window") or {}
    def _sample(d: dict, per_key: int = 5) -> dict:
        out = {}
        for k, v in list(d.items())[:2]:
            out[k] = dict(list(v.items())[:per_key]) if isinstance(v, dict) else v
        return out
    lines = [
        "## REQUIRED: Rolling windows (1/3/5/7 day) — cite this data in your answers",
        "",
        f"- **pnl_by_window:** " + json.dumps(pnl),
        f"- **win_rate_by_window:** " + json.dumps(win_rate),
        f"- **exit_reason_counts_by_window:** (sample) " + json.dumps(_sample(exit_reasons)),
        f"- **blocked_trade_counts_by_window:** (sample) " + json.dumps(_sample(blocked)),
        f"- **signal_decay_exit_rate_by_window:** " + json.dumps(decay_rate),
        "",
        "### REQUIRED: Executive role answers (cite raw or derived data for each)",
        "",
        "**CEO:** (1) Are we converging or oscillating across 1/3/5/7 days? (2) Which change improved metrics? Which failed? (3) What single decision goes live tomorrow?",
        "",
        "**CTO/SRE:** (1) Which systems blocked trades most over 7 days? (2) Are constraints suppressing edge? (3) What instrumentation is still missing?",
        "",
        "**Head of Trading:** (1) Which exit reasons cost the most money over 5/7 days? (2) Did holding longer improve outcomes? (3) Which signals deserve relaxed decay?",
        "",
        "**Risk/CRO:** (1) Are losses clustered by correlation? (2) Are we over-concentrated? (3) What risk is not being priced?",
        "",
        "### REQUIRED: Customer Advocate (MANDATORY ADVERSARIAL)",
        "For EACH executive answer above, the Customer Advocate MUST challenge with: (1) What data supports this? (2) What did this cost the customer? (3) Why hasn't this been fixed yet? (4) What happens if we do nothing?",
        "Output customer_advocate_challenges as a list of challenge objects (one per executive or per claim), each with role, claim_summary, data_support, cost_to_customer, why_not_fixed, if_we_do_nothing.",
        "",
        "### REQUIRED: Missed money (quantify or explicitly mark unknown)",
        "Board MUST output missed_money with:",
        "- blocked_trade_opportunity_cost: USD estimate for 1/3/5/7 day OR { \"unknown\": true, \"reason\": \"...\", \"missing_inputs\": [...], \"instrumentation_needed\": [...] }",
        "- early_exit_opportunity_cost: USD (signal_decay focus) OR unknown + reason + missing_inputs + instrumentation_needed",
        "- correlation_concentration_cost: USD or qualitative OR unknown + reason",
        "Failure to quantify or mark unknown with reason FAILS the run.",
        "",
    ]
    return "\n".join(lines)


def build_prompt(
    contract: str,
    bundle_summary: str,
    date_str: str,
    prior_wheel_actions: list[dict] | None = None,
    wheel_governance_badge_status: str = "?",
    weakening_watchlist: list[dict] | None = None,
    correlation_watchlist: list[dict] | None = None,
    rolling_windows: dict | None = None,
) -> str:
    prior = prior_wheel_actions or []
    closure_table = build_closure_table(prior)
    weakening = weakening_watchlist or []
    correlation = correlation_watchlist or []
    rolling = rolling_windows or {}

    wheel_instructions = f"""
Wheel strategy: Answer from the Wheel strategy daily review section when present.
Wheel governance badge status is {wheel_governance_badge_status}. If FAIL, address blockers before proposing new actions.
- What changed since yesterday in wheel performance?
- What is the dominant blocker and the highest-ROI fix?
- Are fills aligned with UW intelligence (top ranks)?
- What is the risk concentration (symbols/sector)?
- What rule should be promoted/changed today?

Signal trend and correlation (review only; do not gate trades): Use sections 3.4a (Signal trend) and 3.4b (Correlation concentration) when present.
You MUST answer: (1) Which open positions show weakening signals (largest negative deltas)? (2) Are exits aligned with signal weakening, or are we holding through decay? (3) Is the wheel concentrated in highly correlated exposures? What are the top correlated pairs? (4) What single analytics improvement would most improve tomorrow's review quality?
Include wheel_signal_trend_insights (list of short insights) and wheel_correlation_risks (list of short risk notes) in your JSON output. wheel_actions must reference trend/correlation sections (e.g. 3.4a, 3.4b) when relevant.
Include 3–5 wheel-specific action items with owners (Cursor / Mark / config change) and explicit references to wheel_daily_review sections when applicable.
"""
    if closure_table:
        wheel_instructions += "\n" + closure_table + "\n"

    # REQUIRED watchlist sections (governance only; omission FAILS the run).
    if weakening or correlation:
        wheel_instructions += "\n### REQUIRED: Weakening Signal Watchlist Review\n"
        if weakening:
            wheel_instructions += "The following open positions are on the Weakening Signal Watchlist (signal_trend=weakening, signal_delta <= " + str(SIGNAL_WEAKENING_THRESHOLD) + "):\n"
            for e in weakening:
                wheel_instructions += f"- **{e.get('symbol')}** side={e.get('side')} current_signal={e.get('current_signal')} prev_signal={e.get('prev_signal')} signal_delta={e.get('signal_delta')} evaluated_at={e.get('evaluated_at')}\n"
            wheel_instructions += "For EACH symbol above you MUST state: (1) Why the position is still held, OR (2) What condition would trigger exit review. Include these in wheel_watchlists.weakening_signals with symbol, board_rationale, exit_review_condition.\n\n"
        else:
            wheel_instructions += "No symbols on the weakening watchlist today.\n\n"

        wheel_instructions += "### REQUIRED: Correlation Concentration Review\n"
        if correlation:
            wheel_instructions += "The following symbols are on the Correlation Concentration Watchlist (max_corr >= " + str(CORRELATION_CONCENTRATION_THRESHOLD) + "):\n"
            for e in correlation:
                wheel_instructions += f"- **{e.get('symbol')}** max_corr={e.get('max_corr')} most_correlated_with={e.get('most_correlated_with')} avg_corr_topk={e.get('avg_corr_topk')}\n"
            wheel_instructions += "For EACH symbol above you MUST state: (1) Whether the concentration is acceptable, OR (2) What diversification or sizing review is warranted. Include these in wheel_watchlists.correlation_concentration with symbol, board_rationale, mitigation_considered.\n\n"
        else:
            wheel_instructions += "No symbols on the correlation concentration watchlist today.\n\n"

        wheel_instructions += "If any watchlist is non-empty, responses are mandatory. Omission FAILS the run.\n\n"

    rolling_block = _rolling_windows_prompt_block(rolling) if rolling else ""

    return f"""You are the Gemini Stock Quant Officer. Today's EOD date: {date_str}.
Ignore any prior context. Use ONLY the EOD bundle summary and rolling window data below.

{contract}
{rolling_block}
{wheel_instructions}
---

{bundle_summary}

---

Produce a single JSON object with keys: verdict, summary, pnl_metrics, regime_context, sector_context, recommendations, citations, falsification_criteria, wheel_actions, wheel_signal_trend_insights, wheel_correlation_risks, wheel_watchlists, executive_answers, customer_advocate_challenges, unresolved_disputes, missed_money. Emit only valid JSON, no markdown fences or surrounding text.

executive_answers: object with keys CEO, CTO_SRE, Head_of_Trading, Risk_CRO; each value is an object mapping question_short_name to answer (must cite pnl_by_window, exit_reason_counts_by_window, or other rolling data).
customer_advocate_challenges: list of {{ role, claim_summary, data_support, cost_to_customer, why_not_fixed, if_we_do_nothing }} — at least one per executive.
unresolved_disputes: list of strings (disagreements left open).
missed_money: {{ blocked_trade_opportunity_cost: number or {{ unknown, reason, missing_inputs?, instrumentation_needed? }}, early_exit_opportunity_cost: same, correlation_concentration_cost: same or qualitative }} — required; unknown must include reason.

wheel_actions: list of concrete actions; each title, body, owner, reference_section; prior action_ids need status (done|blocked|deferred), note. wheel_watchlists: required when watchlists non-empty. At least one concrete change must be proposed (recommendations or wheel_actions). Omission of rolling window citations, executive answers, customer advocate challenges, or missed_money FAILS the run."""


def _truncate_prompt_for_cli(prompt: str, max_len: int = MAX_PROMPT_LEN) -> str:
    """Truncate prompt to avoid Windows 'command line too long' when passing via --message."""
    if sys.platform != "win32":
        return prompt  # no truncation on Linux (droplet); full bundle summary required
    if len(prompt) <= max_len:
        return prompt
    suffix = "\n\n[EOD bundle summary truncated for Windows CLI length.]"
    return prompt[: max_len - len(suffix)] + suffix


def run_clawdbot_prompt(prompt: str, dry_run: bool = False) -> str:
    """Call Clawdbot agent with prompt, return stdout.
    TODO: Model/provider selection (Gemini). Use clawdbot --help to confirm subcommand.
    Uses `clawdbot agent --message` for one-off agent turn; `message send` targets channels.
    """
    if dry_run:
        log.info("Dry-run: skipping clawdbot call.")
        return json.dumps({
            "verdict": "CAUTION",
            "summary": "Dry-run; no model response.",
            "pnl_metrics": {},
            "regime_context": {"regime_label": "", "regime_confidence": None, "notes": "dry-run"},
            "sector_context": {"sectors_traded": [], "sector_pnl": None, "notes": "dry-run"},
            "recommendations": [],
            "citations": [],
            "falsification_criteria": [{"id": "fc-dry", "description": "Dry-run; replace with real run.", "observed": None, "data_source": "dry-run"}],
            "wheel_actions": [{"title": "Dry-run", "body": "Run with CLAWDBOT_SESSION_ID for real wheel review.", "owner": "Mark", "reference_section": "3.5"}],
            "wheel_signal_trend_insights": [],
            "wheel_correlation_risks": [],
            "wheel_watchlists": {"weakening_signals": [], "correlation_concentration": []},
            "executive_answers": {"CEO": {"converging": "Dry-run."}, "CTO_SRE": {"blockers": "Dry-run."}, "Head_of_Trading": {"exit_reasons": "Dry-run."}, "Risk_CRO": {"correlation": "Dry-run."}},
            "customer_advocate_challenges": [{"role": "CEO", "claim_summary": "Dry-run", "data_support": "N/A", "cost_to_customer": "N/A", "why_not_fixed": "N/A", "if_we_do_nothing": "N/A"}],
            "unresolved_disputes": [],
            "missed_money": {"blocked_trade_opportunity_cost": {"unknown": True, "reason": "dry-run"}, "early_exit_opportunity_cost": {"unknown": True, "reason": "dry-run"}, "correlation_concentration_cost": {"unknown": True, "reason": "dry-run"}},
        })
    prompt = _truncate_prompt_for_cli(prompt)
    session_id = os.environ.get("CLAWDBOT_SESSION_ID")
    if not session_id:
        log.error("CLAWDBOT_SESSION_ID is not set.")
        raise ValueError("CLAWDBOT_SESSION_ID required")
    cmd = [CLAWDBOT_PATH, "agent", "--session-id", session_id, "--message", prompt]
    try:
        r = subprocess.run(
            cmd,
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=300,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError:
        log.error("clawdbot not found. Install or add to PATH. Try: npx clawdbot or moltbot. Use --dry-run to skip.")
        raise
    if r.returncode != 0:
        log.warning("clawdbot exit %s stderr: %s", r.returncode, (r.stderr or "")[:500])
    return r.stdout or ""


def extract_json(raw: str) -> str | None:
    """Try to extract JSON from raw response (e.g. ```json ... ```)."""
    raw = raw.strip()
    # Try parse as-is
    try:
        json.loads(raw)
        return raw
    except json.JSONDecodeError:
        pass
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw)
    if m:
        cand = m.group(1).strip()
        try:
            json.loads(cand)
            return cand
        except json.JSONDecodeError:
            pass
    # Try first { ... } block
    start = raw.find("{")
    if start != -1:
        depth = 0
        for i in range(start, len(raw)):
            if raw[i] == "{":
                depth += 1
            elif raw[i] == "}":
                depth -= 1
                if depth == 0:
                    cand = raw[start : i + 1]
                    try:
                        json.loads(cand)
                        return cand
                    except json.JSONDecodeError:
                        break
    return None


def parse_response(raw: str) -> dict:
    """Parse agent response as JSON. On failure, raise and save raw."""
    extracted = extract_json(raw)
    if extracted is None:
        raise ValueError("Could not extract valid JSON from response")
    return json.loads(extracted)


def write_artifacts(
    obj: dict,
    date_str: str,
    weakening_watchlist: list[dict] | None = None,
    correlation_watchlist: list[dict] | None = None,
    output_dir: Path | None = None,
) -> None:
    date_out_dir = output_dir or (OUT_DIR / date_str)
    date_out_dir.mkdir(parents=True, exist_ok=True)
    json_path = date_out_dir / "eod_board.json"
    md_path = date_out_dir / "eod_board.md"
    json_path.write_text(json.dumps(obj, indent=2, default=str), encoding="utf-8")
    log.info("Wrote %s", json_path)

    weakening = weakening_watchlist or []
    correlation = correlation_watchlist or []

    md_lines = [
        f"# Stock Quant Officer EOD — {date_str}",
        "",
        f"**Verdict:** {obj.get('verdict', '—')}",
        "",
        "## Summary",
        "",
        str(obj.get("summary") or "—"),
        "",
        "## P&L metrics",
        "",
        "```json",
        json.dumps(obj.get("pnl_metrics") or {}, indent=2),
        "```",
        "",
        "## Regime context",
        "",
        "```json",
        json.dumps(obj.get("regime_context") or {}, indent=2),
        "```",
        "",
        "## Sector context",
        "",
        "```json",
        json.dumps(obj.get("sector_context") or {}, indent=2),
        "```",
        "",
        "## Recommendations",
        "",
    ]
    for rec in obj.get("recommendations") or []:
        md_lines.append(f"- **[{rec.get('priority', '')}]** {rec.get('title', '')}")
        md_lines.append(f"  {rec.get('body', '')}")
        md_lines.append("")
    md_lines.append("## Citations")
    md_lines.append("")
    for c in obj.get("citations") or []:
        md_lines.append(f"- `{c.get('source', '')}`: {c.get('quote', '')}")
    md_lines.append("")
    md_lines.append("## Falsification criteria")
    md_lines.append("")
    for fc in obj.get("falsification_criteria") or []:
        md_lines.append(f"- **{fc.get('id', '')}** ({fc.get('data_source', '')}): {fc.get('description', '')}")
    md_lines.append("")
    md_lines.append("## Wheel signal trend insights")
    md_lines.append("")
    for insight in obj.get("wheel_signal_trend_insights") or []:
        md_lines.append(f"- {insight}")
    md_lines.append("")
    md_lines.append("## Wheel correlation risks")
    md_lines.append("")
    for risk in obj.get("wheel_correlation_risks") or []:
        md_lines.append(f"- {risk}")
    md_lines.append("")
    if weakening or correlation:
        md_lines.append("## Wheel watchlists (required review)")
        md_lines.append("")
        watchlists = obj.get("wheel_watchlists") or {}
        for e in (watchlists.get("weakening_signals") or []):
            md_lines.append(f"- **{e.get('symbol')}** (weakening): {e.get('board_rationale', '')} | Exit review: {e.get('exit_review_condition', '')}")
        for e in (watchlists.get("correlation_concentration") or []):
            md_lines.append(f"- **{e.get('symbol')}** (correlation): {e.get('board_rationale', '')} | Mitigation: {e.get('mitigation_considered', '')}")
        md_lines.append("")
    md_lines.append("## Wheel actions")
    md_lines.append("")
    for wa in obj.get("wheel_actions") or []:
        md_lines.append(f"- **[{wa.get('owner', '')}]** {wa.get('title', '')}")
        md_lines.append(f"  {wa.get('body', '')} (ref: {wa.get('reference_section', '')})")
    # Executive answers and Customer Advocate
    for role, answers in (obj.get("executive_answers") or {}).items():
        md_lines.append(f"## Executive: {role}")
        md_lines.append("")
        if isinstance(answers, dict):
            for q, a in answers.items():
                md_lines.append(f"- **{q}:** {a}")
        else:
            md_lines.append(str(answers))
        md_lines.append("")
    for c in (obj.get("customer_advocate_challenges") or []):
        md_lines.append("## Customer Advocate challenge")
        md_lines.append("")
        md_lines.append(str(c))
        md_lines.append("")
    md_lines.append("## Missed money")
    md_lines.append("")
    md_lines.append(json.dumps(obj.get("missed_money") or {}, indent=2))
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    log.info("Wrote %s", md_path)


def main() -> int:
    ap = argparse.ArgumentParser(description="Stock Quant Officer EOD")
    ap.add_argument("--dry-run", action="store_true", help="Skip Clawdbot, write stub JSON")
    ap.add_argument("--date", default="", help="YYYY-MM-DD (default: today UTC)")
    args = ap.parse_args()
    dry_run = args.dry_run
    date_str = (args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")).strip()
    ensure_dirs()
    date_out_dir = OUT_DIR / date_str
    date_out_dir.mkdir(parents=True, exist_ok=True)

    ensure_wheel_daily_review(date_str)
    rolling_windows = load_rolling_windows(date_str)
    # Signal survivorship: per-symbol avg hold, win rate, P&L, decay-trigger frequency
    try:
        from board.eod.rolling_windows import build_signal_survivorship
        signal_survivorship = build_signal_survivorship(REPO_ROOT, date_str, window_days=7)
    except Exception as e:
        log.warning("Signal survivorship build failed: %s", e)
        signal_survivorship = {"date": date_str, "signals": {}, "message": str(e)}

    prior_wheel_actions = load_prior_wheel_actions(date_str)
    data, missing = load_bundle()
    if missing:
        log.warning("Missing bundle files: %s; continuing with partial analysis.", missing)

    wheel_governance_badge: dict | None = None
    badge_path = REPORTS_DIR / f"wheel_governance_badge_{date_str}.json"
    if badge_path.exists():
        try:
            wheel_governance_badge = json.loads(badge_path.read_text(encoding="utf-8", errors="replace"))
        except (json.JSONDecodeError, OSError):
            pass
    signal_cache = load_signal_strength_cache()
    corr_cache = load_signal_correlation_cache()
    weakening_watchlist = build_weakening_watchlist(signal_cache)
    correlation_watchlist = build_correlation_watchlist(corr_cache)

    contract = load_contract()
    bundle_summary = summarize_bundle(data, missing, date_str, wheel_governance_badge)
    badge_status = (wheel_governance_badge or {}).get("overall_status", "?")
    prompt = build_prompt(
        contract, bundle_summary, date_str, prior_wheel_actions, badge_status,
        weakening_watchlist=weakening_watchlist,
        correlation_watchlist=correlation_watchlist,
        rolling_windows=rolling_windows,
    )

    log.info("Calling Clawdbot agent (TODO: model/provider Gemini)...")
    try:
        raw = run_clawdbot_prompt(prompt, dry_run=dry_run)
    except (FileNotFoundError, ValueError):
        return 1

    try:
        obj = parse_response(raw)
    except (ValueError, json.JSONDecodeError) as e:
        log.error("Parse failed: %s", e)
        raw_path = OUT_DIR / f"stock_quant_officer_eod_raw_{date_str}.txt"
        raw_path.write_text(raw, encoding="utf-8")
        log.error("Saved raw response to %s", raw_path)
        return 1

    if not dry_run:
        closure_ok, missing_ids = validate_closure(obj, prior_wheel_actions)
        if not closure_ok:
            log.error("Wheel action closure required but missing for action_ids: %s", missing_ids)
            sys.exit(1)
        watchlist_ok, watchlist_errors = validate_watchlist_responses(obj, weakening_watchlist, correlation_watchlist)
        if not watchlist_ok:
            for err in watchlist_errors:
                log.error("%s", err)
            log.error("Board must address all watchlist symbols; omission FAILS the run.")
            sys.exit(1)
        adv_ok, adv_errors = validate_adversarial_output(obj, rolling_windows)
        if not adv_ok:
            for err in adv_errors:
                log.error("%s", err)
            log.error("Board must reference rolling windows, include executive answers, customer advocate challenges, and missed_money. Omission FAILS the run.")
            sys.exit(1)
        surv_corr_ok, surv_corr_errs = validate_survivorship_correlation_review(obj, signal_survivorship, corr_cache)
        if not surv_corr_ok:
            for err in surv_corr_errs:
                log.error("%s", err)
            log.error("Board must review signal survivorship and correlation when data exists. Omission FAILS the run.")
            sys.exit(1)
    write_artifacts(obj, date_str, weakening_watchlist, correlation_watchlist, output_dir=date_out_dir)
    write_wheel_actions(date_str, obj, prior_wheel_actions)
    write_wheel_watchlists(date_str, weakening_watchlist, correlation_watchlist, obj)
    # Auto-rollback: wire check_auto_rollback_and_disable into every EOD run
    try:
        from policy_variants import check_auto_rollback_and_disable, _is_canary_disabled
        rw = rolling_windows or {}
        pnl_1d = (rw.get("pnl_by_window") or {}).get("1_day")
        win_rate_1d = (rw.get("win_rate_by_window") or {}).get("1_day")
        triggered, reason = check_auto_rollback_and_disable(pnl_1d=pnl_1d, win_rate_1d=win_rate_1d)
        obj["rollback_decision"] = {
            "triggered": triggered,
            "reason": reason or "",
            "canary_disabled": _is_canary_disabled(),
            "pnl_1d": pnl_1d,
            "win_rate_1d": win_rate_1d,
        }
    except Exception as e:
        obj["rollback_decision"] = {"triggered": False, "reason": str(e), "canary_disabled": False}
    # Compute missed_money from logs when available; merge with board guesses
    try:
        from board.eod.bundle_writer import compute_missed_money
        computed = compute_missed_money(REPO_ROOT, date_str, window_days=7)
        board_missed = obj.get("missed_money") or {}
        merged_missed = {}
        for key in ("blocked_trade_opportunity_cost", "early_exit_opportunity_cost", "correlation_concentration_cost"):
            comp = computed.get(key) or {}
            board_val = board_missed.get(key) if isinstance(board_missed, dict) else None
            merged_missed[key] = comp if not comp.get("unknown", True) else (board_val if isinstance(board_val, dict) else comp)
        obj["missed_money"] = merged_missed
    except Exception as e:
        log.warning("compute_missed_money failed: %s", e)
    # Canonical 9-file bundle to board/eod/out/<date>/
    try:
        from board.eod.bundle_writer import write_daily_bundle
        write_daily_bundle(date_str, obj, rolling_windows, obj.get("missed_money") or {}, REPO_ROOT, signal_survivorship=signal_survivorship)
    except Exception as e:
        log.warning("Bundle writer failed (non-fatal): %s", e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
