#!/usr/bin/env python3
"""
Telemetry milestone watcher: refresh Gemini CSVs, rebuild strict ML flat cohort, Telegram milestones.

**Milestone counter = strict ML-ready Z** (not gross executions): rows must pass
`ml.alpaca_cohort_train.load_and_filter` with `strict_scoreflow` — finite `realized_pnl_usd` and
all `mlf_scoreflow_components_*` plus `mlf_scoreflow_total_score`, with entry time on/after the
effective cutoff. Implemented via `strict_ml_ready_count_since_cutoff` after
`scripts/telemetry/alpaca_ml_flattener.py` writes `reports/Gemini/alpaca_ml_cohort_flat.csv`.

Telegram milestone thresholds (Z only): 10, 100, 250 (deduped per state key).

**Zero-tolerance tripwire:** last 3 deduped closes in `logs/exit_attribution.jsonl` must carry
finite PnL and `entry_uw.earnings_proximity` / `entry_uw.sentiment_score`; otherwise a high-priority
Telegram fires (see `telemetry/alpaca_zero_tolerance_tripwire.py`). Not keyed on `MIN_EXEC_SCORE`
or entry composite — a lower score floor does not cause false degradation alerts unless
recent exits lack PnL or `entry_uw` fields.

SPI CSV columns are logged as a diagnostic only (no Telegram SPI gate).

Default cutoff: telemetry `STRICT_EPOCH_START` (2026-04-24T23:59:59Z V2 Vanguard era). Optional
TELEMETRY_MILESTONE_SINCE_DATE=YYYY-MM-DD is interpreted as that day 00:00 UTC but never earlier
than `STRICT_EPOCH_START` (no stale state override — avoids ghost milestone alerts).

Env:
  TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID — required to send (else logs only).
  TELEMETRY_MILESTONE_SINCE_DATE — optional YYYY-MM-DD; floor is max(that day 00:00 UTC, STRICT_EPOCH).
  TELEGRAM_MILESTONE_RESPECT_QUIET_HOURS=1 — if set, use send_governance_telegram (subject to ET window + INTEGRITY_ONLY).
  EXIT_ATTRIBUTION_LOG_PATH — optional override for zero-tolerance tripwire (default logs/exit_attribution.jsonl).
  ZERO_TOLERANCE_ALERT_COOLDOWN_SEC — seconds between repeat Telegram for the same degradation detail (default 1800).

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
import time
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

try:
    from telemetry.alpaca_strict_completeness_gate import STRICT_EPOCH_START
except Exception:  # pragma: no cover
    STRICT_EPOCH_START = 1777075199.0  # keep in sync with telemetry/alpaca_strict_completeness_gate.py

GEMINI_DIR = REPO / "reports" / "Gemini"
ENTRIES_CSV = GEMINI_DIR / "entries_and_exits.csv"
FLAT_CSV = GEMINI_DIR / "alpaca_ml_cohort_flat.csv"
SPI_CSV = GEMINI_DIR / "signal_intelligence_spi.csv"
STATE_PATH = REPO / "data" / ".milestone_state.json"
EXTRACT_SCRIPT = REPO / "scripts" / "extract_gemini_telemetry.py"
FLATTENER_SCRIPT = REPO / "scripts" / "telemetry" / "alpaca_ml_flattener.py"

_SRC = REPO / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
from ml.alpaca_cohort_train import strict_ml_ready_count_since_cutoff  # noqa: E402

from telemetry.alpaca_zero_tolerance_tripwire import (  # noqa: E402
    DEGRADATION_TELEGRAM,
    default_exit_attribution_path,
    evaluate_last_n_exit_quality,
)

SPI_CORE_COLS = [
    "component_options_flow",
    "component_dark_pool",
    "component_greeks_gamma",
    "component_ftd_pressure",
    "component_iv_skew",
    "component_oi_change",
    "component_toxicity_penalty",
]

def _strict_epoch_datetime_utc() -> datetime:
    """Single source of truth with strict-gate / canonical trade count (Harvester era)."""
    return datetime.fromtimestamp(float(STRICT_EPOCH_START), tz=timezone.utc)

# Strict ML-ready Z milestones only (deduped in state by key). Order enforced: lower before higher.
STRICT_ML_Z_MILESTONES: List[Tuple[int, str, str]] = [
    (
        10,
        "strict_ml_z_10",
        "🎯 [Alpaca ML Cohort] 10 strict ML-ready trades (Z). Vanguard / Shadow era checkpoint.",
    ),
    (
        100,
        "strict_ml_z_100",
        "🎯 [Alpaca ML Cohort] 100 strict ML-ready trades (Z). ML data collection on track.",
    ),
    (
        250,
        "strict_ml_z_250",
        "📊 [Alpaca ML Cohort] 250 strict ML-ready trades (Z). Checkpoint for ML retrain readiness.",
    ),
]

_STRICT_Z_SENT_KEYS = tuple(k for _, k, _ in STRICT_ML_Z_MILESTONES)


def _maybe_reset_strict_z_milestones_on_harvester_floor_change(
    state: Dict[str, Any], cutoff: datetime
) -> None:
    """If the effective cutoff changed, drop strict-Z Telegram sent flags (stale vs new floor)."""
    meta = state.setdefault("meta", {})
    cur = cutoff.isoformat()
    prev = meta.get("harvester_count_floor_utc")
    sent = state.setdefault("milestones_sent", {})
    if prev is not None and prev != cur:
        for k in _STRICT_Z_SENT_KEYS:
            sent.pop(k, None)
        print(
            f"telemetry_milestone_watcher: cleared strict-Z milestone flags (floor {prev!r} -> {cur!r})",
            flush=True,
        )
    meta["harvester_count_floor_utc"] = cur


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
    """
    Never use persisted milestone state to choose the cutoff (that caused pre-epoch rows to count).
    Env date is optional; effective cutoff is always >= STRICT_EPOCH_START.
    """
    floor = _strict_epoch_datetime_utc()
    raw = (os.environ.get("TELEMETRY_MILESTONE_SINCE_DATE") or "").strip()
    if not raw:
        return floor
    try:
        y, m, d = (int(x) for x in raw.split("-", 2))
        env_start = datetime(y, m, d, tzinfo=timezone.utc)
    except Exception:
        print(
            f"WARN: invalid TELEMETRY_MILESTONE_SINCE_DATE={raw!r}, using STRICT_EPOCH_START",
            file=sys.stderr,
        )
        return floor
    return env_start if env_start >= floor else floor


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


def run_ml_flattener() -> Tuple[int, str]:
    """Rebuild alpaca_ml_cohort_flat.csv; return (exit_code, tail)."""
    cmd = [sys.executable, str(FLATTENER_SCRIPT), "--root", str(REPO)]
    try:
        p = subprocess.run(
            cmd,
            cwd=str(REPO),
            capture_output=True,
            text=True,
            timeout=900,
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


def _zero_tolerance_should_send(state: Dict[str, Any], detail: str) -> bool:
    """Resend on new failure detail immediately; repeat identical detail only after cooldown."""
    raw = (os.environ.get("ZERO_TOLERANCE_ALERT_COOLDOWN_SEC") or "1800").strip() or "1800"
    try:
        cooldown = float(raw)
    except ValueError:
        cooldown = 1800.0
    zt = state.setdefault("zero_tolerance", {})
    now = time.time()
    prev_t = zt.get("last_alert_epoch")
    prev_d = zt.get("last_detail")
    if prev_t is None:
        return True
    if detail != prev_d:
        return True
    return (now - float(prev_t)) >= cooldown


def _zero_tolerance_mark_sent(state: Dict[str, Any], detail: str) -> None:
    zt = state.setdefault("zero_tolerance", {})
    zt["last_alert_epoch"] = time.time()
    zt["last_detail"] = detail


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

    flat_code, flat_tail = run_ml_flattener()
    print(f"alpaca_ml_flattener.py exit={flat_code}", flush=True)
    if flat_code != 0:
        print(flat_tail, file=sys.stderr)

    gross_entries = count_entries_since(cutoff)
    print(f"entries_and_exits rows since cutoff (diagnostic gross): {gross_entries}", flush=True)

    z_count = 0
    z_meta: Dict[str, Any] = {}
    if FLAT_CSV.is_file():
        try:
            z_count, z_meta = strict_ml_ready_count_since_cutoff(
                FLAT_CSV,
                cutoff,
                feature_mode="strict_scoreflow",
                # Telegram Z = trades with real snapshot or scoreflow join, not neutral padding only.
                skip_neutral_no_join=True,
            )
        except SystemExit as e:
            print(f"strict_ml_ready_count_since_cutoff failed: {e}", file=sys.stderr, flush=True)
        except Exception as e:
            print(f"strict_ml_ready_count_since_cutoff error: {e}", file=sys.stderr, flush=True)
    else:
        print(f"WARN: flat cohort missing at {FLAT_CSV} — Z=0", flush=True)

    print(
        f"strict ML-ready Z since cutoff: {z_count} "
        f"(all-time strict in CSV: {z_meta.get('strict_ml_ready_all_time_in_csv', '?')})",
        flush=True,
    )

    state = _load_state()
    _maybe_reset_strict_z_milestones_on_harvester_floor_change(state, cutoff)
    sent: Dict[str, Any] = state["milestones_sent"]

    def already(k: str) -> bool:
        return bool(sent.get(k))

    def mark(k: str) -> None:
        sent[k] = {
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "strict_ml_z": z_count,
            "gross_entries_since_cutoff": gross_entries,
        }

    # --- Strict Z milestones (50 … 250); lower keys must send before higher ---
    for threshold, key, msg in STRICT_ML_Z_MILESTONES:
        if z_count < threshold or already(key):
            continue
        blocked = False
        for t2, k2, _ in STRICT_ML_Z_MILESTONES:
            if t2 < threshold and not already(k2):
                blocked = True
                break
        if blocked:
            print(
                f"telemetry_milestone_watcher: skip Z>={threshold} Telegram until lower strict milestones sent "
                f"(z_count={z_count})",
                flush=True,
            )
            continue
        if send_telegram(msg):
            mark(key)
            print(f"Sent strict-Z {threshold} Telegram ({key})", flush=True)
        else:
            print(f"strict-Z {threshold} Telegram not sent (credentials or HTTP)", flush=True)

    # --- SPI diagnostic only (no Telegram) ---
    if z_count >= 10 and SPI_CSV.is_file():
        spi_ok, spi_detail = _verify_spi_core_columns_fixed(cutoff, recent_cap=200)
        print(f"SPI integrity (diagnostic only): ok={spi_ok} — {spi_detail}", flush=True)

    # --- Zero-tolerance: last 3 exits must have PnL + UW earnings/sentiment ---
    exit_path = default_exit_attribution_path(REPO)
    zt_ok, zt_detail = evaluate_last_n_exit_quality(exit_path, n=3)
    print(f"zero_tolerance_last_3: ok={zt_ok} detail={zt_detail}", flush=True)
    if not zt_ok and _zero_tolerance_should_send(state, zt_detail):
        if send_telegram(DEGRADATION_TELEGRAM):
            _zero_tolerance_mark_sent(state, zt_detail)
            print("Sent zero-tolerance degradation Telegram", flush=True)
        else:
            print("zero-tolerance Telegram not sent (credentials or HTTP)", flush=True)

    state["meta"]["last_run_utc"] = datetime.now(timezone.utc).isoformat()
    state["meta"]["last_strict_ml_z_since_cutoff"] = z_count
    state["meta"]["last_gross_entries_since_cutoff"] = gross_entries
    state["meta"]["last_z_meta"] = {
        k: z_meta.get(k)
        for k in (
            "dropped_missing_pnl",
            "dropped_neutral_no_join",
            "dropped_feature_nan",
            "gross_rows",
            "kept",
        )
        if k in z_meta
    }
    state["meta"]["cutoff_utc"] = cutoff.isoformat()
    _save_state(state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
