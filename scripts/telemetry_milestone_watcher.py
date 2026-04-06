#!/usr/bin/env python3
"""
Telemetry milestone watcher: refresh Gemini CSVs, count trades since reset date,
optionally verify SPI column integrity at the 10-trade gate, Telegram alerts, deduped state.

Scaling / OOS Telegram thresholds (trade rows in entries_and_exits since cutoff): see
MILESTONE_ALERT_THRESHOLDS = [10, 50, 100, 150, 250]. Ten triggers SPI pass/warn only;
50/100/150/250 use OOS_MILESTONE_STEPS messages (deduped per state key).

Env:
  TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID — required to send (else logs only).
  TELEMETRY_MILESTONE_SINCE_DATE — optional YYYY-MM-DD; trade/SPI filter starts that day 00:00 UTC.
      If unset, uses start of **today UTC**.
  TELEGRAM_MILESTONE_RESPECT_QUIET_HOURS=1 — if set, use send_governance_telegram (subject to ET window + INTEGRITY_ONLY).

State: data/.milestone_state.json (gitignored via data/ or add pattern if needed)

Cron (hourly, droplet):
  17 * * * * cd /root/stock-bot && /usr/bin/python3 scripts/telemetry_milestone_watcher.py >> /var/log/telemetry_milestone.log 2>&1
"""
from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parent.parent
os.chdir(REPO)
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

try:
    from dotenv import load_dotenv

    load_dotenv(REPO / ".env")
except Exception:
    pass

GEMINI_DIR = REPO / "reports" / "Gemini"
ENTRIES_CSV = GEMINI_DIR / "entries_and_exits.csv"
SPI_CSV = GEMINI_DIR / "signal_intelligence_spi.csv"
STATE_PATH = REPO / "data" / ".milestone_state.json"
EXTRACT_SCRIPT = REPO / "scripts" / "extract_gemini_telemetry.py"

SPI_CORE_COLS = [
    "component_options_flow",
    "component_dark_pool",
    "component_greeks_gamma",
    "component_ftd_pressure",
    "component_iv_skew",
    "component_oi_change",
    "component_toxicity_penalty",
]

MILESTONE_10_OK = "10_trade_checkpoint_passed"
MILESTONE_10_WARN = "10_trade_data_integrity_warning"
MILESTONE_100_ML = "100_trade_ml_ready"

# Canonical trade-count pings (entries_and_exits since cutoff). 10 = SPI integrity only (below).
MILESTONE_ALERT_THRESHOLDS = [10, 50, 100, 150, 250]

# Out-of-sample / scaling Telegram milestones (deduped in state by second column).
OOS_MILESTONE_STEPS: List[Tuple[int, str, str]] = [
    (
        50,
        "equities_oos_50_trades",
        "🟦 [Equities OOS] 50 trades reached — mid-sample scaling checkpoint.",
    ),
    (
        100,
        MILESTONE_100_ML,
        "🔵 100 Trades Completed: Ready for ML Feature Importance Analysis.",
    ),
    (
        150,
        "equities_oos_150_trades",
        "🟪 [Equities OOS] 150 trades reached — deep OOS checkpoint before the 250 definitive review.",
    ),
    (
        250,
        "equities_oos_250_trades",
        "🎯 [Equities OOS] 250 Trades Reached! The Microstructure Edge is ready for its definitive Out-of-Sample Review.",
    ),
]


def _load_state() -> Dict[str, Any]:
    if not STATE_PATH.is_file():
        return {"milestones_sent": {}, "meta": {}}
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {"milestones_sent": {}, "meta": {}}
        data.setdefault("milestones_sent", {})
        data.setdefault("meta", {})
        if not isinstance(data["milestones_sent"], dict):
            data["milestones_sent"] = {}
        return data
    except Exception:
        return {"milestones_sent": {}, "meta": {}}


def _save_state(data: Dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(STATE_PATH)


def _since_datetime_utc() -> datetime:
    raw = (os.environ.get("TELEMETRY_MILESTONE_SINCE_DATE") or "").strip()
    if raw:
        try:
            y, m, d = (int(x) for x in raw.split("-", 2))
            return datetime(y, m, d, tzinfo=timezone.utc)
        except Exception:
            print(f"WARN: invalid TELEMETRY_MILESTONE_SINCE_DATE={raw!r}, using today UTC", file=sys.stderr)
    st = _load_state()
    meta = st.get("meta") or {}
    if isinstance(meta, dict) and meta.get("trade_count_since_date"):
        try:
            y, m, d = (int(x) for x in str(meta["trade_count_since_date"]).split("-", 2))
            return datetime(y, m, d, tzinfo=timezone.utc)
        except Exception:
            pass
    today = datetime.now(timezone.utc).date()
    return datetime(today.year, today.month, today.day, tzinfo=timezone.utc)


def _parse_ts(s: str) -> Optional[datetime]:
    if not s or not str(s).strip():
        return None
    try:
        return datetime.fromisoformat(str(s).strip().replace("Z", "+00:00"))
    except ValueError:
        return None


def run_extract() -> Tuple[int, str]:
    """Run Gemini telemetry extract; return (exit_code, tail of stderr+stdout)."""
    cmd = [sys.executable, str(EXTRACT_SCRIPT)]
    try:
        p = subprocess.run(
            cmd,
            cwd=str(REPO),
            capture_output=True,
            text=True,
            timeout=600,
        )
        out = (p.stdout or "") + ("\n" + p.stderr if p.stderr else "")
        return p.returncode, out[-4000:]
    except Exception as e:
        return 1, str(e)


def count_entries_since(cutoff: datetime) -> int:
    if not ENTRIES_CSV.is_file():
        return 0
    n = 0
    with ENTRIES_CSV.open("r", encoding="utf-8", errors="replace", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            ts = _parse_ts(row.get("timestamp_utc") or "")
            if ts is None:
                continue
            if ts >= cutoff:
                n += 1
    return n


def _verify_spi_core_columns_fixed(cutoff: datetime, recent_cap: int) -> Tuple[bool, str]:
    tuples: List[Tuple[datetime, Dict[str, str]]] = []
    with SPI_CSV.open("r", encoding="utf-8", errors="replace", newline="") as f:
        r = csv.DictReader(f)
        headers = r.fieldnames or []
        missing_hdr = [c for c in SPI_CORE_COLS if c not in headers]
        if missing_hdr:
            return False, f"SPI missing columns: {missing_hdr}"
        for row in r:
            ts = _parse_ts(row.get("timestamp_utc") or "")
            if ts is None or ts < cutoff:
                continue
            tuples.append(
                (
                    ts,
                    {c: (row.get(c) or "").strip() for c in SPI_CORE_COLS},
                )
            )
    if not tuples:
        return False, "no SPI rows on or after cutoff"
    tuples.sort(key=lambda x: x[0])
    recent = tuples[-recent_cap:]

    def is_numeric_cell(val: str) -> bool:
        if val == "":
            return False
        if val.lower() in ("null", "none", "nan"):
            return False
        try:
            float(val)
            return True
        except ValueError:
            return False

    bad: List[str] = []
    for ts, cells in recent:
        for col in SPI_CORE_COLS:
            v = cells.get(col, "")
            if not is_numeric_cell(v):
                bad.append(f"{ts.isoformat()} {col}={v!r}")
                if len(bad) >= 8:
                    break
        if len(bad) >= 8:
            break
    if bad:
        return False, "blank/non-numeric: " + "; ".join(bad[:6])
    return True, f"checked {len(recent)} recent SPI rows (>= cutoff), all 7 core columns numeric"


def send_telegram(text: str) -> bool:
    if (os.environ.get("TELEGRAM_MILESTONE_RESPECT_QUIET_HOURS") or "").strip().lower() in (
        "1",
        "true",
        "yes",
    ):
        try:
            from scripts.alpaca_telegram import send_governance_telegram

            return bool(send_governance_telegram(text, script_name="telemetry_milestone_watcher"))
        except Exception:
            pass

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        print("Telegram skipped: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set", file=sys.stderr)
        return False
    try:
        import requests

        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat, "text": text},
            timeout=30,
        )
        return bool(r.ok)
    except Exception:
        try:
            import urllib.parse
            import urllib.request

            data = urllib.parse.urlencode({"chat_id": chat, "text": text}).encode()
            req = urllib.request.Request(
                f"https://api.telegram.org/bot{token}/sendMessage",
                data=data,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                return 200 <= resp.status < 300
        except Exception as e:
            print(f"Telegram send failed: {e}", file=sys.stderr)
            return False


def main() -> int:
    cutoff = _since_datetime_utc()
    print(f"telemetry_milestone_watcher: cutoff UTC {cutoff.isoformat()}", flush=True)

    ex_code, ex_tail = run_extract()
    print(f"extract_gemini_telemetry.py exit={ex_code}", flush=True)
    if ex_code != 0:
        print(ex_tail, file=sys.stderr)

    trade_count = count_entries_since(cutoff)
    print(f"entries_and_exits rows since cutoff: {trade_count}", flush=True)

    state = _load_state()
    sent: Dict[str, Any] = state["milestones_sent"]

    def already(k: str) -> bool:
        return bool(sent.get(k))

    def mark(k: str) -> None:
        sent[k] = {"sent_at": datetime.now(timezone.utc).isoformat(), "trade_count": trade_count}

    # --- OOS / scaling milestones (50, 100, 150, 250) — see MILESTONE_ALERT_THRESHOLDS ---
    for threshold, key, msg in OOS_MILESTONE_STEPS:
        if trade_count >= threshold and not already(key):
            if send_telegram(msg):
                mark(key)
                print(f"Sent {threshold}-trade OOS/scaling Telegram ({key})", flush=True)
            else:
                print(f"{threshold}-trade Telegram not sent (credentials or HTTP)", flush=True)

    # --- 10-trade SPI gate ---
    if trade_count >= 10:
        ok, detail = _verify_spi_core_columns_fixed(cutoff, recent_cap=200)
        print(f"SPI integrity: ok={ok} — {detail}", flush=True)
        if ok and not already(MILESTONE_10_OK):
            msg = "🟢 10-Trade Checkpoint Passed: Telemetry is 100% intact."
            if send_telegram(msg):
                mark(MILESTONE_10_OK)
                print("Sent 10-trade OK Telegram", flush=True)
        elif not ok and not already(MILESTONE_10_WARN):
            msg = "🔴 Data Integrity Warning: Blank columns detected in SPI CSV!"
            if send_telegram(msg):
                mark(MILESTONE_10_WARN)
                print("Sent 10-trade WARN Telegram", flush=True)

    state["meta"]["last_run_utc"] = datetime.now(timezone.utc).isoformat()
    state["meta"]["last_trade_count_since_cutoff"] = trade_count
    state["meta"]["cutoff_utc"] = cutoff.isoformat()
    _save_state(state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
