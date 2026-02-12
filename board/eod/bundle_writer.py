#!/usr/bin/env python3
"""
Write the canonical daily EOD output bundle (<=9 files) to board/eod/out/<date>/.
Reuses existing state and logs; no raw reprocessing.
Outputs: JSON/MD only. Legacy artifacts moved to legacy/. Missed money computed from logs when available.
"""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent

log = logging.getLogger(__name__)

PLACEHOLDER_PHRASES = frozenset({
    "(review daily eod_board", "(synthesize from", "(derive from",
    "placeholder text", "stub)", "to be filled", "coming soon)",
})


def sanitize_for_json(obj: Any) -> Any:
    """
    Make obj JSON-serializable: convert sets/tuples to list, datetime to ISO string,
    NaN/Infinity to null, ensure dict keys are strings.
    """
    if obj is None:
        return None
    if isinstance(obj, (str, int, bool)):
        return obj
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, (set, tuple)):
        return [sanitize_for_json(x) for x in obj]
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            sk = str(k) if not isinstance(k, str) else k
            try:
                out[sk] = sanitize_for_json(v)
            except (TypeError, ValueError, RecursionError):
                out[sk] = str(v)
        return out
    if isinstance(obj, (list,)):
        return [sanitize_for_json(x) for x in obj]
    # datetime, bytes, or other non-serializable
    try:
        import datetime
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
    except Exception:
        pass
    return str(obj)


def _iter_jsonl(path: Path):
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            if isinstance(rec, dict):
                yield rec
        except Exception:
            continue


UNKNOWN_COUNTDOWN_PATH = REPO_ROOT / "state" / "unknown_metrics_countdown.json"


def _update_unknown_metrics_countdown(missed_money: dict, date_str: str) -> dict:
    """
    Track consecutive days unknown per missed_money key. If same field unknown for 3+ days:
    countdown_breach=True, policy_must_disable_or_instrument=True.
    """
    state: dict = {}
    if UNKNOWN_COUNTDOWN_PATH.exists():
        try:
            state = json.loads(UNKNOWN_COUNTDOWN_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    prev = state.get("by_field", {})
    last_date = state.get("last_date", "")
    advanced = bool(last_date) and last_date < date_str
    by_field: dict = {}
    for key, val in (missed_money or {}).items():
        if not isinstance(val, dict):
            continue
        is_unknown = bool(val.get("unknown", False))
        prev_count = prev.get(key, {}).get("consecutive_days", 0)
        # Only increment when calendar advanced; same-day re-run keeps prev
        if is_unknown:
            count = (prev_count + 1) if advanced else (prev_count or 1)
        else:
            count = 0
        by_field[key] = {
            "consecutive_days": count,
            "unknown": is_unknown,
            "countdown_breach": count >= 3,
            "policy_must_disable_or_instrument": count >= 3,
        }
    out = {"last_date": date_str, "by_field": by_field}
    try:
        UNKNOWN_COUNTDOWN_PATH.parent.mkdir(parents=True, exist_ok=True)
        UNKNOWN_COUNTDOWN_PATH.write_text(json.dumps(out, indent=2), encoding="utf-8")
    except Exception:
        pass
    return out


def _day_utc(ts: Any) -> str:
    s = str(ts or "")[:10]
    return s if len(s) == 10 and s[4] == "-" else ""


def compute_missed_money(base: Path, date_str: str, window_days: int = 7) -> dict:
    """
    Compute missed_money from logs when available. Returns merged structure:
    blocked_trade_opportunity_cost, early_exit_opportunity_cost, correlation_concentration_cost.
    """
    from datetime import datetime, timedelta, timezone
    result: dict = {}
    try:
        t = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        start = t - timedelta(days=window_days - 1)
        days = [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(window_days)]
    except ValueError:
        days = [date_str]

    # blocked_trade_opportunity_cost: sum expected_value_usd from blocked_trades
    blocked_path = base / "state" / "blocked_trades.jsonl"
    ev_sum = 0.0
    ev_by_reason: dict[str, float] = {}
    if blocked_path.exists():
        for rec in _iter_jsonl(blocked_path):
            if _day_utc(rec.get("timestamp") or rec.get("ts")) not in days:
                continue
            ev = rec.get("expected_value_usd")
            try:
                ev = float(ev)
            except (TypeError, ValueError):
                ev = None
            if ev is not None and not math.isnan(ev):
                ev_sum += ev
                reason = str(rec.get("block_reason") or rec.get("reason") or "unknown")
                ev_by_reason[reason] = ev_by_reason.get(reason, 0) + ev
    if ev_sum > 0 or ev_by_reason:
        result["blocked_trade_opportunity_cost"] = {
            "unknown": False,
            "total_expected_value_usd": round(ev_sum, 2),
            "by_reason": {k: round(v, 2) for k, v in ev_by_reason.items()},
        }
    else:
        result["blocked_trade_opportunity_cost"] = {
            "unknown": True,
            "reason": "blocked_trades lack expected_value_usd",
            "missing_inputs": ["expected_value_usd in blocked_trades.jsonl"],
        }

    # early_exit_opportunity_cost: aggregate pnl_delta from exit_hold_longer for signal_decay
    exit_path = base / "logs" / "exit_hold_longer.jsonl"
    delta_15 = 0.0
    delta_60 = 0.0
    hold_longer_count = 0
    if exit_path.exists():
        for rec in _iter_jsonl(exit_path):
            if "signal_decay" not in str(rec.get("exit_reason", "")).lower():
                continue
            if _day_utc(rec.get("timestamp") or rec.get("ts")) not in days:
                continue
            hold_longer_count += 1
            for k in ("pnl_delta_15m", "pnl_delta_60m"):
                v = rec.get(k)
                try:
                    v = float(v)
                except (TypeError, ValueError):
                    v = None
                if v is not None and not math.isnan(v):
                    if k == "pnl_delta_15m":
                        delta_15 += v
                    else:
                        delta_60 += v
    if hold_longer_count > 0 and (delta_15 != 0 or delta_60 != 0):
        result["early_exit_opportunity_cost"] = {
            "unknown": False,
            "signal_decay_exits_with_marks": hold_longer_count,
            "pnl_delta_15m_total_usd": round(delta_15, 2),
            "pnl_delta_60m_total_usd": round(delta_60, 2),
        }
    else:
        result["early_exit_opportunity_cost"] = {
            "unknown": True,
            "reason": "exit_hold_longer lacks pnl_delta_15m/60m for signal_decay exits",
            "missing_inputs": ["exit_hold_longer.jsonl marks for signal_decay exits"],
        }

    # correlation_concentration_cost: risk score from signal_correlation_cache if pairs exist
    corr_path = base / "state" / "signal_correlation_cache.json"
    if corr_path.exists():
        try:
            data = json.loads(corr_path.read_text(encoding="utf-8"))
            pairs = data.get("pairs") or []
            if pairs:
                abs_corrs = [abs(float(p.get("corr", 0))) for p in pairs[:5] if isinstance(p, dict)]
                risk_score = round(sum(abs_corrs), 4) if abs_corrs else None
                result["correlation_concentration_cost"] = {
                    "unknown": False,
                    "correlation_cache_present": True,
                    "concentration_risk_score": risk_score,
                    "top_pairs_count": len(pairs[:5]),
                }
            else:
                result["correlation_concentration_cost"] = {
                    "unknown": False,
                    "correlation_cache_present": True,
                    "message": data.get("message", "insufficient pairs"),
                    "concentration_risk_score": None,
                }
        except Exception:
            result["correlation_concentration_cost"] = {
                "unknown": True,
                "reason": "signal_correlation_cache unreadable",
                "missing_inputs": [],
            }
    else:
        result["correlation_concentration_cost"] = {
            "unknown": True,
            "reason": "signal_correlation_cache missing",
            "missing_inputs": ["state/signal_correlation_cache.json"],
        }
    return result


def _filter_by_date(records: list[dict], date_str: str, ts_keys: tuple = ("ts", "timestamp", "exit_ts")):
    out = []
    for r in records:
        for k in ts_keys:
            if _day_utc(r.get(k)) == date_str:
                out.append(r)
                break
    return out


def write_daily_bundle(
    date_str: str,
    eod_board: dict,
    rolling_windows: dict,
    missed_money: dict,
    repo_root: Path | None = None,
    signal_survivorship: dict | None = None,
) -> Path:
    """
    Write the 9-file bundle to board/eod/out/<date_str>/.
    Returns the output directory path.
    """
    base = repo_root or REPO_ROOT
    out_dir = base / "board" / "eod" / "out" / date_str
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) eod_board.json — structured answers + challenges; MUST always write valid JSON
    try:
        sanitized = sanitize_for_json(eod_board)
        raw = json.dumps(sanitized, indent=2, default=str)
        (out_dir / "eod_board.json").write_text(raw, encoding="utf-8")
    except Exception as e:
        fallback: dict = {"error": "serialization_failed", "reason": str(e)}
        try:
            b = eod_board or {}
            partial = {}
            for k in ("verdict", "summary", "rollback_decision"):
                if k in b:
                    partial[k] = sanitize_for_json(b[k])
            fallback["partial"] = partial
        except Exception:
            pass
        (out_dir / "eod_board.json").write_text(json.dumps(fallback, indent=2), encoding="utf-8")
    log.info("Wrote %s", out_dir / "eod_board.json")

    # 2) eod_board.md — human-readable narrative (from eod_board summary + sections)
    md_lines = [
        f"# EOD Board — {date_str}",
        "",
        f"**Verdict:** {eod_board.get('verdict', '—')}",
        "",
        "## Summary",
        "",
        str(eod_board.get("summary") or "—"),
        "",
    ]
    rollback = eod_board.get("rollback_decision")
    if isinstance(rollback, dict):
        md_lines.append("## Canary rollback")
        md_lines.append("")
        md_lines.append(json.dumps(rollback, indent=2, default=str))
        md_lines.append("")
    for role, answers in (eod_board.get("executive_answers") or {}).items():
        md_lines.append(f"## {role}")
        md_lines.append("")
        if isinstance(answers, dict):
            for q, a in answers.items():
                md_lines.append(f"- **{q}**")
                md_lines.append(f"  {a}")
                md_lines.append("")
        else:
            md_lines.append(str(answers))
            md_lines.append("")
    for challenge in eod_board.get("customer_advocate_challenges") or []:
        md_lines.append("## Customer Advocate challenge")
        md_lines.append("")
        if isinstance(challenge, dict):
            md_lines.append("```json")
            md_lines.append(json.dumps(sanitize_for_json(challenge), indent=2, default=str))
            md_lines.append("```")
        elif isinstance(challenge, str):
            try:
                parsed = json.loads(challenge)
                md_lines.append("```json")
                md_lines.append(json.dumps(sanitize_for_json(parsed), indent=2, default=str))
                md_lines.append("```")
            except (json.JSONDecodeError, TypeError):
                md_lines.append("```json")
                md_lines.append(json.dumps({"raw": challenge}, indent=2))
                md_lines.append("```")
        else:
            md_lines.append("```json")
            md_lines.append(json.dumps({"raw": str(challenge)}, indent=2))
            md_lines.append("```")
        md_lines.append("")
    md_lines.append("## Unresolved disputes")
    md_lines.append("")
    for d in eod_board.get("unresolved_disputes") or []:
        md_lines.append(f"- {d}")
    md_lines.append("")
    (out_dir / "eod_board.md").write_text("\n".join(md_lines), encoding="utf-8")
    log.info("Wrote %s", out_dir / "eod_board.md")

    # 3) eod_review.md — consolidated truth (multi-day summary from rolling windows)
    review_lines = [
        f"# EOD Consolidated Review — {date_str}",
        "",
        "## Rolling windows (1/3/5/7 day)",
        "",
    ]
    for key in ["pnl_by_window", "win_rate_by_window", "signal_decay_exit_rate_by_window"]:
        val = rolling_windows.get(key) or {}
        review_lines.append(f"### {key}")
        review_lines.append(json.dumps(val, indent=2))
        review_lines.append("")
    review_lines.append("## Missed money (Board-quantified)")
    review_lines.append("")
    review_lines.append(json.dumps(missed_money, indent=2))
    review_lines.append("")
    (out_dir / "eod_review.md").write_text("\n".join(review_lines), encoding="utf-8")
    log.info("Wrote %s", out_dir / "eod_review.md")

    # Unknown metrics 3-day countdown
    unknown_countdown = _update_unknown_metrics_countdown(missed_money, date_str)

    # 4) derived_deltas.json — missed money + trends + signal survivorship + variant attribution
    derived = {
        "date": date_str,
        "rolling_windows": {
            k: rolling_windows.get(k) for k in [
                "win_rate_by_window", "pnl_by_window", "exit_reason_counts_by_window",
                "blocked_trade_counts_by_window", "signal_decay_exit_rate_by_window",
            ]
        },
        "missed_money": missed_money,
        "signal_survivorship": signal_survivorship or {},
        "unknown_metrics_countdown": unknown_countdown,
        "variant_attribution": {
            "baseline": {"pnl_usd": None, "win_rate": None, "exit_mix": {}},
            "live_canary": {"pnl_usd": None, "win_rate": None, "exit_mix": {}},
            "paper_aggressive": {"pnl_usd": None, "win_rate": None, "exit_mix": {}},
            "message": "Requires variant tagging on position entry and close.",
        },
    }
    (out_dir / "derived_deltas.json").write_text(
        json.dumps(derived, indent=2, default=str), encoding="utf-8"
    )
    log.info("Wrote %s", out_dir / "derived_deltas.json")

    # 5–8) Raw logs as JSON/CSV (no .gz — review artifacts must be clickable in GitHub)
    from datetime import datetime, timedelta, timezone
    import csv
    try:
        t = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        window_days = [(t - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    except Exception:
        window_days = [date_str]

    def write_jsonl_as_json(name: str, path: Path, ts_keys: tuple = ("ts", "timestamp", "exit_ts")) -> None:
        records = list(_iter_jsonl(path))
        filtered = [r for r in records if any(_day_utc(r.get(k)) in window_days for k in ts_keys)]
        if not filtered and records:
            filtered = records[-500:]
        (out_dir / name).write_text(json.dumps([sanitize_for_json(r) for r in filtered], indent=2, default=str), encoding="utf-8")
        log.info("Wrote %s", out_dir / name)

    def write_jsonl_as_csv(name: str, path: Path, ts_keys: tuple = ("ts", "timestamp")) -> None:
        records = list(_iter_jsonl(path))
        filtered = [r for r in records if any(_day_utc(r.get(k)) in window_days for k in ts_keys)]
        if not filtered and records:
            filtered = records[-500:]
        if not filtered:
            (out_dir / name).write_text("", encoding="utf-8")
            log.info("Wrote %s (empty)", out_dir / name)
            return
        all_keys = sorted({k for r in filtered for k in r.keys()})
        with (out_dir / name).open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=all_keys, extrasaction="ignore")
            w.writeheader()
            for r in filtered:
                w.writerow({k: str(v) if not isinstance(v, (int, float, bool, type(None))) else v for k, v in r.items()})
        log.info("Wrote %s", out_dir / name)

    write_jsonl_as_json("raw_exit_attribution.json", base / "logs" / "exit_attribution.jsonl", ("ts", "timestamp", "exit_ts"))
    write_jsonl_as_csv("raw_blocked_trades.csv", base / "state" / "blocked_trades.jsonl", ("ts", "timestamp"))
    write_jsonl_as_json("raw_attribution.json", base / "logs" / "attribution.jsonl")

    # Signal events: system_events.jsonl filtered to signal-related
    sig_path = base / "logs" / "system_events.jsonl"
    signal_types = {"signal_strength_evaluated", "signal_trend_evaluated", "signal_strength_skipped", "signal_correlation_snapshot"}
    sig_records = [r for r in _iter_jsonl(sig_path) if r.get("event_type") in signal_types and _day_utc(r.get("timestamp")) in window_days]
    if not sig_records and sig_path.exists():
        sig_records = list(_iter_jsonl(sig_path))[-500:]
    (out_dir / "raw_signal_events.json").write_text(
        json.dumps([sanitize_for_json(r) for r in sig_records], indent=2, default=str),
        encoding="utf-8",
    )
    log.info("Wrote %s", out_dir / "raw_signal_events.json")

    # 9) weekly_review.md — generated from daily outputs (see generate_weekly_review)
    weekly_path = out_dir / "weekly_review.md"
    try:
        _write_weekly_review(out_dir, base, date_str, weekly_path)
    except Exception as e:
        weekly_path.write_text(f"# Weekly Review — {date_str}\n\n_Generation skipped: {e}_\n", encoding="utf-8")
    log.info("Wrote %s", weekly_path)

    # Move legacy artifacts (.gz, .jsonl.gz, etc.) to legacy/; do not count toward bundle
    ALLOWED = {".json", ".md", ".txt", ".csv"}
    DISALLOWED_SUFFIXES = (".gz", ".jsonl.gz")
    legacy_dir = out_dir / "legacy"
    for p in list(out_dir.iterdir()):
        if p.is_dir() and p.name == "legacy":
            continue
        if p.is_file():
            suf = p.suffix
            if p.name.endswith(".jsonl.gz"):
                suf = ".jsonl.gz"
            if suf in DISALLOWED_SUFFIXES or suf not in ALLOWED:
                legacy_dir.mkdir(exist_ok=True)
                try:
                    p.rename(legacy_dir / p.name)
                    log.info("Moved %s to legacy/", p.name)
                except Exception as e:
                    log.warning("Could not move %s to legacy: %s", p.name, e)
    # Enforce JSON/MD only (fail pipeline if disallowed extensions remain)
    try:
        from board.eod.output_format_enforcer import validate_date_dir
        ok, errs = validate_date_dir(date_str)
        if not ok:
            for e in errs:
                log.error("%s", e)
            raise SystemExit(1)
    except SystemExit:
        raise
    except Exception:
        pass

    return out_dir


def _write_weekly_review(out_dir: Path, base: Path, date_str: str, weekly_path: Path) -> None:
    """Aggregate from board/eod/out/* for the week ending date_str; no placeholder text allowed."""
    from collections import Counter
    from datetime import datetime, timedelta, timezone
    try:
        end = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        start = end - timedelta(days=6)
        days = [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    except Exception:
        days = [date_str]
    eod_out = base / "board" / "eod" / "out"
    lines: list[str] = [f"# Weekly Review — week ending {date_str}", ""]
    failure_counts: Counter = Counter()
    blocker_counts: Counter = Counter()
    exit_reason_counts: Counter = Counter()
    advocate_notes: list[str] = []
    pnl_by_day: dict[str, float] = {}
    win_rate_by_day: dict[str, float] = {}
    exit_by_day: dict[str, dict[str, int]] = {}
    blocker_by_day: dict[str, dict[str, int]] = {}
    double_down_themes: list[str] = []
    kill_themes: list[str] = []
    rollback_triggered_days: list[str] = []
    for d in days:
        day_dir = eod_out / d
        derived_path = day_dir / "derived_deltas.json"
        board_path = day_dir / "eod_board.json"
        if derived_path.exists():
            try:
                data = json.loads(derived_path.read_text(encoding="utf-8"))
                rw = data.get("rolling_windows") or {}
                pnl = rw.get("pnl_by_window") or {}
                wr = rw.get("win_rate_by_window") or {}
                pnl_by_day[d] = pnl.get("1_day") if isinstance(pnl.get("1_day"), (int, float)) else 0.0
                win_rate_by_day[d] = wr.get("1_day") if isinstance(wr.get("1_day"), (int, float)) else 0.0
                for _w, counts in rw.get("exit_reason_counts_by_window") or {}.items():
                    if isinstance(counts, dict):
                        for reason, c in counts.items():
                            exit_reason_counts[reason] += int(c) if isinstance(c, (int, float)) else 0
                ex1 = (rw.get("exit_reason_counts_by_window") or {}).get("1_day") or {}
                exit_by_day[d] = dict(ex1) if isinstance(ex1, dict) else {}
                for _w, counts in rw.get("blocked_trade_counts_by_window") or {}.items():
                    if isinstance(counts, dict):
                        for block_reason, c in counts.items():
                            blocker_counts[block_reason] += int(c) if isinstance(c, (int, float)) else 0
                bl1 = (rw.get("blocked_trade_counts_by_window") or {}).get("1_day") or {}
                blocker_by_day[d] = dict(bl1) if isinstance(bl1, dict) else {}
            except Exception:
                pass
        if board_path.exists():
            try:
                board = json.loads(board_path.read_text(encoding="utf-8"))
                rollback = board.get("rollback_decision") or {}
                if isinstance(rollback, dict) and rollback.get("triggered"):
                    rollback_triggered_days.append(d)
                for ch in (board.get("customer_advocate_challenges") or []):
                    if isinstance(ch, dict) and ch.get("claim_summary"):
                        advocate_notes.append(str(ch.get("claim_summary", "")))
                    elif isinstance(ch, str):
                        advocate_notes.append(ch)
                for _k, v in (board.get("executive_summary") or {}).items():
                    if isinstance(v, str) and ("fail" in v.lower() or "improv" in v.lower()):
                        failure_counts[v[:200]] += 1
                exec_answers = board.get("executive_answers") or {}
                for role, ans in exec_answers.items():
                    if isinstance(ans, dict):
                        for _q, a in ans.items():
                            if isinstance(a, str):
                                al = a.lower()
                                if "fail" in al or "block" in al:
                                    failure_counts[a[:200]] += 1
                                if "improve" in al or "help" in al or "working" in al:
                                    double_down_themes.append(a[:150])
                                if "kill" in al or "disable" in al or "stop" in al or "hurt" in al:
                                    kill_themes.append(a[:150])
                mm = board.get("missed_money") or {}
                if isinstance(mm, dict):
                    for key, val in mm.items():
                        if isinstance(val, dict) and val.get("unknown"):
                            kill_themes.append(f"{key}: instrumentation needed")
            except Exception:
                pass
    lines.append("## PnL and win rate trend by day")
    lines.append("")
    lines.append("| Date | PnL 1d | Win rate 1d |")
    lines.append("|------|--------|-------------|")
    for d in days:
        p = pnl_by_day.get(d, 0)
        w = win_rate_by_day.get(d, 0)
        lines.append(f"| {d} | {p:.2f} | {w:.2%} |")
    lines.append("")
    lines.append("## Top exit reasons by day")
    for d in days:
        ex = exit_by_day.get(d) or {}
        top5 = sorted(ex.items(), key=lambda x: -int(x[1]))[:5]
        if top5:
            lines.append(f"- **{d}:** " + ", ".join(f"{r}({c})" for r, c in top5))
    lines.append("")
    lines.append("## Top blockers by day")
    for d in days:
        bl = blocker_by_day.get(d) or {}
        top5 = sorted(bl.items(), key=lambda x: -int(x[1]))[:5]
        if top5:
            lines.append(f"- **{d}:** " + ", ".join(f"{r}({c})" for r, c in top5))
    lines.append("")
    lines.append("## Recurring failures (top 5)")
    for s, _ in failure_counts.most_common(5):
        lines.append(f"- {s}")
    lines.append("")
    lines.append("## Recurring blockers (top 5)")
    for block_reason, c in blocker_counts.most_common(5):
        lines.append(f"- {block_reason}: {c}")
    lines.append("")
    lines.append("## Exit reason trends (week)")
    for reason, c in exit_reason_counts.most_common(10):
        lines.append(f"- {reason}: {c}")
    lines.append("")
    lines.append("## Customer Advocate recurring critiques (top 5 themes)")
    for note in advocate_notes[:5]:
        lines.append(f"- {note[:300]}")
    lines.append("")
    if rollback_triggered_days:
        lines.append("## Canary rollback triggered")
        lines.append(f"Rollback triggered on: {', '.join(rollback_triggered_days)}")
        lines.append("")
    lines.append("## What to double down on")
    for t in double_down_themes[:5]:
        lines.append(f"- {t}")
    if not double_down_themes:
        lines.append("- No explicit double-down themes in executive answers this week.")
    lines.append("")
    lines.append("## What to kill immediately")
    for t in kill_themes[:5]:
        lines.append(f"- {t}")
    if not kill_themes:
        lines.append("- No explicit kill/disable themes in executive answers this week.")
    lines.append("")
    lines.append("## Changes deployed and outcomes")
    lines.append("Review daily eod_board.json wheel_actions and recommendations for what was deployed.")
    content = "\n".join(lines)
    for phrase in PLACEHOLDER_PHRASES:
        if phrase in content.lower():
            raise ValueError(f"Weekly review must not contain placeholder text: {phrase!r}")
    weekly_path.write_text(content, encoding="utf-8")
