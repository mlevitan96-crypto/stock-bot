#!/usr/bin/env python3
# To run this automatically every day after market close (example 21:00 UTC):
#   crontab -e
#   0 21 * * 1-5 /usr/bin/python3 /root/stock-bot/scripts/run_alpaca_daily_governance.py >> /root/alpaca_daily_governance.log 2>&1
#
# This is NOT installed automatically. You must opt-in.

"""
Alpaca Daily Governance — daily summary and Telegram ping (analysis-only).

Read-only on risk: no order logic, no sizing, no config writes.
Computes: PnL for the day, trade count, scenario vs baseline, whether there is
a change candidate to review. Sends a Telegram message every run (contract:
MUST send even if PnL negative or no candidate). States clearly:
  "NO CHANGE CANDIDATE TODAY" or "CHANGE CANDIDATE PRESENT — REVIEW REQUIRED".

Uses: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DECISION_SPINE = "reports/QUANTIFIED_DECISION_SPINE_ALPACA_EXPERIMENT_1_2026-03-12.md"
SCENARIO_SUMMARY_GLOB = "reports/scenario_lab/SCENARIO_SUMMARY_*.md"
BASELINE_BATCH = REPO / "reports" / "experiments" / "alpaca_baseline_batch_results.json"


def _logs_dir() -> Path:
    try:
        from config.registry import Directories
        return (REPO / Directories.LOGS).resolve()
    except ImportError:
        return REPO / "logs"


def _iter_jsonl(path: Path, day: str):
    if not path.exists():
        return
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = (rec.get("timestamp") or rec.get("ts") or rec.get("exit_timestamp") or "")[:10]
            if ts != day:
                continue
            yield rec


def _pnl_and_count_today(day: str) -> tuple[float, int]:
    logs = _logs_dir()
    pnl_sum = 0.0
    seen: set[tuple[str, str]] = set()
    for path in (logs / "exit_attribution.jsonl", logs / "attribution.jsonl"):
        for rec in _iter_jsonl(path, day):
            if path.name == "attribution.jsonl" and str(rec.get("trade_id", "")).startswith("open_"):
                continue
            sym = str(rec.get("symbol", "")).upper()
            ts = rec.get("timestamp") or rec.get("ts") or rec.get("exit_timestamp") or ""
            key = (sym, (ts or "")[:16])
            if key not in seen:
                seen.add(key)
                pnl = rec.get("pnl") or rec.get("pnl_usd")
                if pnl is not None:
                    pnl_sum += float(pnl)
    return round(pnl_sum, 2), len(seen)


def _has_scenario_better_than_baseline() -> bool:
    """True if any scenario lab output suggests better expectancy/drawdown than current baseline."""
    if not BASELINE_BATCH.exists():
        return False
    try:
        data = json.loads(BASELINE_BATCH.read_text(encoding="utf-8"))
        baseline_exp = None
        for r in data.get("results") or []:
            if r.get("metric") == "expectancy" and r.get("expectancy") is not None:
                baseline_exp = float(r["expectancy"])
                break
    except Exception:
        return False
    scenario_dir = REPO / "reports" / "scenario_lab"
    if not scenario_dir.exists():
        return False
    for p in scenario_dir.glob("scenario_*.json"):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            exp = d.get("expectancy") if isinstance(d, dict) else None
            if exp is not None and baseline_exp is not None and float(exp) > baseline_exp:
                return True
        except Exception:
            continue
    return False


def _send_telegram(text: str) -> bool:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        print("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID", file=sys.stderr)
        return False
    try:
        import requests
    except ImportError:
        print("pip install requests required for Telegram send", file=sys.stderr)
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    r = requests.post(url, json={"chat_id": chat, "text": text}, timeout=30)
    if not r.ok:
        print(r.text, file=sys.stderr)
        return False
    return True


def main() -> int:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    pnl_today, trade_count_today = _pnl_and_count_today(today)
    candidate = _has_scenario_better_than_baseline()

    summary_lines = [
        "ALPACA DAILY GOVERNANCE SUMMARY",
        "-------------------------------",
        f"Date: {today}",
        f"PnL (today): {pnl_today:.2f} USD",
        f"Trade count (today): {trade_count_today}",
        "Change candidate: YES — REVIEW REQUIRED" if candidate else "Change candidate: NO",
        f"Decision Spine: {DECISION_SPINE}",
    ]
    summary = "\n".join(summary_lines)
    print(summary)

    # Telegram: MUST send; state NO CHANGE or CHANGE CANDIDATE clearly
    candidate_label = "CHANGE CANDIDATE PRESENT — REVIEW REQUIRED" if candidate else "NO CHANGE CANDIDATE TODAY"
    msg = (
        "Alpaca Daily Governance Summary\n"
        f"Date: {today}\n"
        f"PnL (today): {pnl_today:.2f} USD\n"
        f"Trade count (today): {trade_count_today}\n"
        f"{candidate_label}\n"
        f"Report: {DECISION_SPINE}"
    )
    if not _send_telegram(msg):
        return 2
    print("Telegram sent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
