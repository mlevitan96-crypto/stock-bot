#!/usr/bin/env python3
"""
Wednesday handoff: Mon–Wed ET performance summary, decile analysis (subprocess), Cursor prompt
for Gemini, and Telegram delivery (split if >4096).

Cron (use CRON_TZ so 20:15 is America/New_York):
  CRON_TZ=America/New_York
  15 20 * * 3 root /root/stock-bot/venv/bin/python3 /root/stock-bot/scripts/analysis/alpaca_weekly_handoff.py >> /var/log/alpaca_handoff.log 2>&1
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None  # type: ignore[misc, assignment]


def _infer_repo_root() -> Path:
    env = os.environ.get("ALPACA_ROOT") or os.environ.get("STOCKBOT_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    p = Path(__file__).resolve()
    if p.parent.name == "analysis" and p.parent.parent.name == "scripts":
        return p.parent.parent.parent
    return Path.cwd()


def _load_dotenv(repo: Path) -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    for env_path in (repo / ".env", Path("/root/.alpaca_env")):
        try:
            load_dotenv(env_path)
        except OSError:
            pass


def _mon_wed_window_et(now_et: datetime) -> Tuple[datetime, datetime]:
    """Monday 00:00 ET through Wednesday 23:59:59 ET of the same ISO week as `now_et`."""
    d = now_et.date()
    monday = d - timedelta(days=d.weekday())
    wednesday = monday + timedelta(days=2)
    tz = now_et.tzinfo or ZoneInfo("America/New_York")
    start = datetime.combine(monday, time(0, 0, 0), tzinfo=tz)
    end = datetime.combine(wednesday, time(23, 59, 59), tzinfo=tz)
    return start, end


def _parse_ts_to_et(s: Any, et: Any) -> Optional[datetime]:
    if s is None or (isinstance(s, str) and not str(s).strip()):
        return None
    raw = str(s).strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(et)


def _load_telegram_sender(repo: Path):
    """Import scripts/alpaca_telegram.py without requiring `scripts` to be a package."""
    path = repo / "scripts" / "alpaca_telegram.py"
    spec = importlib.util.spec_from_file_location("alpaca_telegram_handoff", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.send_governance_telegram


def _filter_week_rows(
    cohort_path: Path,
    start_et: datetime,
    end_et: datetime,
    et: Any,
) -> Tuple[List[Dict[str, str]], List[str]]:
    """Return rows whose exit_ts (else entry_ts) falls in [start_et, end_et]."""
    if not cohort_path.is_file():
        return [], []
    rows: List[Dict[str, str]] = []
    fieldnames: List[str] = []
    with cohort_path.open("r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        for r in reader:
            if not r:
                continue
            ts = _parse_ts_to_et(r.get("exit_ts") or r.get("exit_timestamp"), et) or _parse_ts_to_et(
                r.get("entry_ts") or r.get("entry_timestamp"), et
            )
            if ts is None:
                continue
            if start_et <= ts <= end_et:
                rows.append(r)
    return rows, fieldnames


def _write_temp_cohort(rows: List[Dict[str, str]], fieldnames: List[str]) -> Path:
    fd, name = tempfile.mkstemp(prefix="alpaca_week_", suffix=".csv", text=True)
    os.close(fd)
    p = Path(name)
    with p.open("w", encoding="utf-8", newline="") as f:
        if not fieldnames:
            return p
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return p


def _week_pnl_stats(rows: List[Dict[str, str]]) -> Tuple[int, float, float, int]:
    """count, total_pnl, win_rate_pct, wins"""
    total = 0.0
    wins = 0
    n = 0
    for r in rows:
        try:
            p = float(r.get("realized_pnl_usd") or "")
        except (TypeError, ValueError):
            continue
        if not (p == p):
            continue
        n += 1
        total += p
        if p > 0:
            wins += 1
    wr = (100.0 * wins / n) if n else 0.0
    return n, total, wr, wins


def _extract_decile_table_block(decile_md: str) -> str:
    m = re.search(r"(## Decile table[\s\S]*?)(?=\n## |\Z)", decile_md)
    if m:
        return m.group(1).strip()
    return decile_md.strip()


def _parse_decile_total_pnl_from_table(decile_md: str) -> Optional[float]:
    """Sum the `Total PnL ($)` column from decile data rows (sanity vs cohort slice)."""
    lines = decile_md.splitlines()
    header_idx = None
    for i, ln in enumerate(lines):
        if "Total PnL" in ln and ln.strip().startswith("|"):
            header_idx = i
            break
    if header_idx is None:
        return None
    headers = [c.strip() for c in lines[header_idx].strip("|").split("|")]
    try:
        col = headers.index("Total PnL ($)")
    except ValueError:
        return None
    s = 0.0
    n = 0
    for ln in lines[header_idx + 2 :]:
        ln = ln.strip()
        if not ln.startswith("|"):
            break
        parts = [c.strip() for c in ln.strip("|").split("|")]
        if len(parts) <= col:
            continue
        try:
            s += float(parts[col])
            n += 1
        except ValueError:
            continue
    return s if n else None


def _split_message(text: str, limit: int = 3800) -> List[str]:
    if len(text) <= limit:
        return [text]
    chunks: List[str] = []
    i = 0
    while i < len(text):
        chunks.append(text[i : i + limit])
        i += limit
    return chunks


def main() -> int:
    ap = argparse.ArgumentParser(description="Wednesday weekly handoff: deciles + Telegram + Cursor prompt.")
    ap.add_argument("--root", type=Path, default=None, help="Repo root (default: infer / env).")
    ap.add_argument(
        "--cohort",
        type=Path,
        default=None,
        help="Flattened cohort CSV (default: <root>/reports/Gemini/alpaca_ml_cohort_flat.csv).",
    )
    ap.add_argument("--dry-run", action="store_true", help="Print payload only; do not call Telegram.")
    args = ap.parse_args()

    root = (args.root or _infer_repo_root()).resolve()
    _load_dotenv(root)
    cohort = (args.cohort or (root / "reports" / "Gemini" / "alpaca_ml_cohort_flat.csv")).resolve()

    if ZoneInfo is None:
        print("error: zoneinfo not available", file=sys.stderr)
        return 1
    et = ZoneInfo("America/New_York")
    now_et = datetime.now(et)
    w_start, w_end = _mon_wed_window_et(now_et)

    week_rows, fieldnames = _filter_week_rows(cohort, w_start, w_end, et)
    w_n, w_total, w_wr, w_wins = _week_pnl_stats(week_rows)

    min_decile_rows = int(os.environ.get("ALPACA_HANDOFF_MIN_DECILE_ROWS", "10"))
    if len(week_rows) >= min_decile_rows and fieldnames:
        decile_csv = _write_temp_cohort(week_rows, fieldnames)
        decile_label = "Mon-Wed ET slice (same window as headline stats)"
    else:
        decile_csv = cohort
        decile_label = (
            f"Full cohort file (Mon-Wed rows={len(week_rows)} < {min_decile_rows}; "
            "deciles need enough trades - compare headline to decile cohort carefully)"
        )

    decile_py = root / "scripts" / "analysis" / "alpaca_decile_pnl_analysis.py"
    proc = subprocess.run(
        [
            sys.executable,
            str(decile_py),
            "--root",
            str(root),
            "--csv",
            str(decile_csv),
        ],
        capture_output=True,
        text=True,
        timeout=180,
        cwd=str(root),
    )
    decile_out = (proc.stdout or "").strip()
    if proc.returncode != 0:
        decile_out += f"\n\n(decile exit {proc.returncode})\n{(proc.stderr or '').strip()}".rstrip()

    if decile_csv != cohort and decile_csv.is_file():
        try:
            decile_csv.unlink()
        except OSError:
            pass

    table_block = _extract_decile_table_block(decile_out)
    decile_table_sum = _parse_decile_total_pnl_from_table(decile_out)

    cursor_prompt = (
        "Here is the Alpaca performance data from Monday to Wednesday.\n\n"
        f"{table_block}\n\n"
        "Analyze this for alpha decay and suggest 3 specific mathematical refinements to the scoring engine."
    )

    lines = [
        "# Alpaca Wednesday handoff",
        "",
        f"- **Window (ET):** {w_start.isoformat()} -> {w_end.isoformat()}",
        f"- **Cohort file:** `{cohort}`",
        f"- **Decile input:** {decile_label}",
        "",
        "## Mon-Wed headline (exit/entry timestamp in window)",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Trade count | {w_n} |",
        f"| Wins | {w_wins} |",
        f"| Win rate | {w_wr:.2f}% |",
        f"| Total PnL ($) | {w_total:.4f} |",
        "",
    ]
    if decile_table_sum is not None and w_n > 0:
        lines.append(f"- **Decile table Total PnL sum (sanity):** ${decile_table_sum:.4f}")
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(decile_out)
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Cursor Prompt for Gemini")
    lines.append("")
    lines.append(cursor_prompt)

    payload = "\n".join(lines)

    if args.dry_run or os.environ.get("ALPACA_HANDOFF_DRY_RUN") == "1":
        print(payload)
        return 0

    try:
        send = _load_telegram_sender(root)
    except Exception as e:
        print(f"Telegram helper load failed: {e}", file=sys.stderr)
        print(payload)
        return 1

    chunks = _split_message(payload)
    ok_any = False
    for part_i, chunk in enumerate(chunks, start=1):
        header = f"[Alpaca handoff {part_i}/{len(chunks)}]\n\n" if len(chunks) > 1 else ""
        ok = send(header + chunk, script_name="alpaca_weekly_handoff")
        ok_any = ok_any or ok
    return 0 if ok_any else 1


if __name__ == "__main__":
    raise SystemExit(main())
