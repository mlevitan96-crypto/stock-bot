#!/usr/bin/env python3
"""
Alpaca Shadow ML milestone watcher — counts ``ml_expected_eod_return`` in live JSONL and
fires Telegram at N=10, 100, 250 (deduped via state file).

Scans ``logs/run.jsonl`` by default (append-only byte offset). Optional env:
  ALPACA_SHADOW_ML_LOG — override path (single file).
  TELEGRAM_MILESTONE_RESPECT_QUIET_HOURS — same contract as telemetry_milestone_watcher.

State: data/.alpaca_shadow_ml_milestone_state.json
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO = Path(__file__).resolve().parents[2]
os.chdir(REPO)
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

try:
    from dotenv import load_dotenv

    load_dotenv(REPO / ".env")
except Exception:
    pass

STATE_PATH = REPO / "data" / ".alpaca_shadow_ml_milestone_state.json"
DEFAULT_LOG = REPO / "logs" / "run.jsonl"

MILESTONES: List[Tuple[int, str, str]] = [
    (
        10,
        "alpaca_shadow_ml_n10",
        "🧠 [Alpaca Shadow ML] N=10 ``ml_expected_eod_return`` telemetry rows observed.\n\n"
        "Downstream analytics stress path may be triggered; continue collecting toward 100/250.",
    ),
    (
        100,
        "alpaca_shadow_ml_n100",
        "🧠 [Alpaca Shadow ML] N=100 telemetry rows. Shadow brain signal volume healthy.",
    ),
    (
        250,
        "alpaca_shadow_ml_n250",
        "🧠 [Alpaca Shadow ML] N=250 telemetry rows. Checkpoint for shadow review / retrain cadence.",
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


def _send_telegram(text: str, script_name: str) -> bool:
    if (os.environ.get("TELEGRAM_MILESTONE_RESPECT_QUIET_HOURS") or "").strip().lower() in (
        "1",
        "true",
        "yes",
    ):
        try:
            from scripts.alpaca_telegram import send_governance_telegram

            return bool(send_governance_telegram(text, script_name=script_name))
        except Exception:
            pass
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        print("Telegram skipped: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set", file=sys.stderr)
        return False
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


def _finite_ml_val(obj: Any) -> bool:
    if obj is None:
        return False
    try:
        v = float(obj)
    except (TypeError, ValueError):
        return False
    import math

    return math.isfinite(v)


def _count_new_ml_rows(path: Path, state: Dict[str, Any]) -> int:
    """Append-only counter with rotation handling; updates meta offset + returns new hit count."""
    meta = state.setdefault("meta", {})
    key = str(path.resolve())
    off_key = f"offset:{key}"
    prev_off = int(meta.get(off_key, 0) or 0)
    if not path.is_file():
        return 0
    try:
        size = path.stat().st_size
    except OSError:
        return 0
    truncated = size < prev_off
    if truncated:
        # Log rotation / truncate: avoid double-count by resetting baseline.
        prev_off = 0
        meta["total_ml_rows"] = 0
    new_hits = 0
    try:
        with path.open("rb") as f:
            f.seek(prev_off)
            chunk = f.read()
        end_off = path.stat().st_size
        text = chunk.decode("utf-8", errors="replace")
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(o, dict):
                continue
            if "ml_expected_eod_return" not in o:
                continue
            if not _finite_ml_val(o.get("ml_expected_eod_return")):
                continue
            new_hits += 1
        meta[off_key] = end_off
        return new_hits
    except Exception:
        return 0


def main() -> int:
    log_path = Path(os.environ.get("ALPACA_SHADOW_ML_LOG") or str(DEFAULT_LOG)).resolve()
    state = _load_state()
    sent: Dict[str, bool] = {str(k): bool(v) for k, v in state.get("milestones_sent", {}).items()}

    new_rows = _count_new_ml_rows(log_path, state)
    total = int(state.get("meta", {}).get("total_ml_rows", 0) or 0) + int(new_rows)
    state["meta"]["total_ml_rows"] = total
    print(f"alpaca_shadow_ml_milestone_watcher: log={log_path} +{new_rows} new rows, total={total}", flush=True)

    for threshold, script_name, message in MILESTONES:
        key = str(threshold)
        if total < threshold or sent.get(key):
            continue
        body = f"{message}\n\n``total={total}`` log={log_path.name}"
        if _send_telegram(body, script_name=script_name):
            sent[key] = True
            print(f"Sent Telegram for {script_name}", flush=True)
        else:
            print(f"Telegram not sent for {script_name} (missing creds or transport failure)", flush=True)

    state["milestones_sent"] = sent
    _save_state(state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
