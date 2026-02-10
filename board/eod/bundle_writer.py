#!/usr/bin/env python3
"""
Write the canonical daily EOD output bundle (<=9 files) to board/eod/out/<date>/.
Reuses existing state and logs; no raw reprocessing.
"""

from __future__ import annotations

import gzip
import json
import logging
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent

log = logging.getLogger(__name__)


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


def _day_utc(ts: Any) -> str:
    s = str(ts or "")[:10]
    return s if len(s) == 10 and s[4] == "-" else ""


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
) -> Path:
    """
    Write the 9-file bundle to board/eod/out/<date_str>/.
    Returns the output directory path.
    """
    base = repo_root or REPO_ROOT
    out_dir = base / "board" / "eod" / "out" / date_str
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) eod_board.json — structured answers + challenges
    (out_dir / "eod_board.json").write_text(
        json.dumps(eod_board, indent=2, default=str), encoding="utf-8"
    )
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
        md_lines.append(str(challenge))
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

    # 4) derived_deltas.json — missed money + trends
    derived = {
        "date": date_str,
        "rolling_windows": {
            k: rolling_windows.get(k) for k in [
                "win_rate_by_window", "pnl_by_window", "exit_reason_counts_by_window",
                "blocked_trade_counts_by_window", "signal_decay_exit_rate_by_window",
            ]
        },
        "missed_money": missed_money,
    }
    (out_dir / "derived_deltas.json").write_text(
        json.dumps(derived, indent=2, default=str), encoding="utf-8"
    )
    log.info("Wrote %s", out_dir / "derived_deltas.json")

    # 5–8) Raw logs gzipped (window: last 7 days to keep size bounded)
    from datetime import datetime, timedelta, timezone
    try:
        t = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        window_days = [(t - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    except Exception:
        window_days = [date_str]

    def write_gz(name: str, path: Path, ts_keys: tuple = ("ts", "timestamp", "exit_ts")):
        records = list(_iter_jsonl(path))
        filtered = [r for r in records if any(_day_utc(r.get(k)) in window_days for k in ts_keys)]
        if not filtered and records:
            filtered = records[-500:]  # fallback: last 500 lines
        out_path = out_dir / name
        with gzip.open(out_path, "wt", encoding="utf-8") as f:
            for r in filtered:
                f.write(json.dumps(r, default=str) + "\n")
        log.info("Wrote %s", out_path)

    write_gz("raw_exit_attribution.jsonl.gz", base / "logs" / "exit_attribution.jsonl", ("ts", "timestamp", "exit_ts"))
    write_gz("raw_blocked_trades.jsonl.gz", base / "state" / "blocked_trades.jsonl")
    write_gz("raw_attribution.jsonl.gz", base / "logs" / "attribution.jsonl")

    # Signal events: system_events.jsonl filtered to signal-related
    sig_path = base / "logs" / "system_events.jsonl"
    signal_types = {"signal_strength_evaluated", "signal_trend_evaluated", "signal_strength_skipped", "signal_correlation_snapshot"}
    sig_records = [r for r in _iter_jsonl(sig_path) if r.get("event_type") in signal_types and _day_utc(r.get("timestamp")) in window_days]
    if not sig_records and sig_path.exists():
        sig_records = list(_iter_jsonl(sig_path))[-500:]
    out_sig = out_dir / "raw_signal_events.jsonl.gz"
    with gzip.open(out_sig, "wt", encoding="utf-8") as f:
        for r in sig_records:
            f.write(json.dumps(r, default=str) + "\n")
    log.info("Wrote %s", out_sig)

    # 9) weekly_review.md — generated from daily outputs (see generate_weekly_review)
    weekly_path = out_dir / "weekly_review.md"
    try:
        _write_weekly_review(out_dir, base, date_str, weekly_path)
    except Exception as e:
        weekly_path.write_text(f"# Weekly Review — {date_str}\n\n_Generation skipped: {e}_\n", encoding="utf-8")
    log.info("Wrote %s", weekly_path)

    return out_dir


def _write_weekly_review(out_dir: Path, base: Path, date_str: str, weekly_path: Path) -> None:
    """Aggregate from board/eod/out/* for the week ending date_str; no raw log reprocessing."""
    from datetime import datetime, timedelta, timezone
    try:
        end = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        start = end - timedelta(days=6)
        days = [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    except Exception:
        days = [date_str]
    eod_out = base / "board" / "eod" / "out"
    lines = [f"# Weekly Review — week ending {date_str}", ""]
    for d in days:
        day_dir = eod_out / d
        derived_path = day_dir / "derived_deltas.json"
        board_path = day_dir / "eod_board.json"
        if derived_path.exists():
            try:
                data = json.loads(derived_path.read_text(encoding="utf-8"))
                pnl = (data.get("rolling_windows") or {}).get("pnl_by_window") or {}
                lines.append(f"## {d}")
                lines.append(f"- PnL by window: {pnl}")
                lines.append("")
            except Exception:
                lines.append(f"## {d}")
                lines.append("- (derived_deltas unreadable)")
                lines.append("")
        if board_path.exists():
            try:
                board = json.loads(board_path.read_text(encoding="utf-8"))
                verdict = board.get("verdict", "?")
                lines.append(f"- Verdict: {verdict}")
                lines.append("")
            except Exception:
                pass
    lines.append("## Recurring failures / changes that worked / did not work")
    lines.append("(Synthesize from daily eod_board.json executive_answers and customer_advocate_challenges.)")
    weekly_path.write_text("\n".join(lines), encoding="utf-8")
