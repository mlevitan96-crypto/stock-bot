"""
Post-epoch Telegram milestones (10 / 50 / 150 / 250 terminal exits).

Milestone 10 requires a strict data-integrity verdict before a GREEN Telegram.
"""
from __future__ import annotations

import json
import math
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

MILESTONE_LEVELS = (10, 50, 150, 250)


def _run_jsonl_path() -> Path:
    raw = os.environ.get("RUN_JSONL_PATH", "").strip()
    if raw:
        return Path(raw)
    return Path(__file__).resolve().parents[2] / "logs" / "run.jsonl"


def _parse_iso_ts_epoch(s: Any) -> Optional[float]:
    if not s or not isinstance(s, str):
        return None
    try:
        t = s.strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(t)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return float(dt.timestamp())
    except Exception:
        return None


def _finite_num(x: Any) -> bool:
    try:
        v = float(x)
        return math.isfinite(v)
    except (TypeError, ValueError):
        return False


def _snapshot_ok(snap: Any) -> Tuple[bool, List[str]]:
    """Chen gate: UW premium proxy + OFI + SIP/feed lineage."""
    reasons: List[str] = []
    if not isinstance(snap, dict):
        return False, ["missing_feature_snapshot"]
    uw_ok = False
    for k in ("net_premium", "total_premium", "uw_flow_strength", "flow_strength", "conviction"):
        if _finite_num(snap.get(k)):
            uw_ok = True
            break
    if not uw_ok:
        reasons.append("uw_flow_premium_proxy_missing_or_nonfinite")
    for k in ("ofi_l1_roll_60s_sum", "ofi_l1_roll_300s_sum"):
        if not _finite_num(snap.get(k)):
            reasons.append(f"ofi_missing_or_nonfinite:{k}")
    feed = None
    for k in ("sip_feed", "data_feed", "stream_feed", "preferred_feed", "alpaca_data_feed"):
        v = snap.get(k)
        if isinstance(v, str) and v.strip() and str(v).strip().lower() not in ("unknown", "none", ""):
            feed = str(v).strip()
            break
    if not feed:
        reasons.append("sip_feed_lineage_missing")
    return (len(reasons) == 0), reasons


def tail_exit_decision_made_rows(*, limit: int = 10) -> List[Dict[str, Any]]:
    p = _run_jsonl_path()
    if not p.is_file():
        return []
    try:
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return []
    out: List[Dict[str, Any]] = []
    for ln in reversed(lines):
        s = ln.strip()
        if not s:
            continue
        try:
            rec = json.loads(s)
        except Exception:
            continue
        if isinstance(rec, dict) and rec.get("event_type") == "exit_decision_made":
            out.append(rec)
            if len(out) >= limit:
                break
    out.reverse()
    return out


def strict_integrity_verdict_last_n(*, n: int = 10) -> Tuple[str, List[str]]:
    """
    Returns (\"GREEN\"|\"RED\", human-readable failure lines).
    """
    rows = tail_exit_decision_made_rows(limit=n)
    if len(rows) < n:
        return "RED", [f"expected_{n}_exit_decision_made_rows_got_{len(rows)}"]
    fails: List[str] = []
    for i, rec in enumerate(rows):
        tid = str(rec.get("trade_id") or rec.get("canonical_trade_id") or f"idx_{i}")
        snap = rec.get("feature_snapshot_at_exit") or rec.get("snapshot") or {}
        ok, rs = _snapshot_ok(snap)
        if not ok:
            fails.append(f"{tid}: " + ";".join(rs))
    return ("GREEN" if not fails else "RED", fails)


def _telegram(text: str, *, script_name: str) -> None:
    try:
        from scripts.alpaca_telegram import send_governance_telegram
    except Exception:
        return
    try:
        send_governance_telegram(text, script_name=script_name)
    except Exception:
        pass


def notify_milestone_async(*, milestone: int, post_epoch_count: int, epoch_start_ts: float) -> None:
    """Fire-and-forget thread entrypoint."""

    def _run() -> None:
        if milestone == 10:
            verdict, fails = strict_integrity_verdict_last_n(n=10)
            if verdict == "GREEN":
                body = (
                    f"ALPACA POST-EPOCH MILESTONE **10** (integrity **GREEN**)\n"
                    f"epoch_start_ts={epoch_start_ts:.3f}  post_epoch_exits={post_epoch_count}\n"
                    f"UW+OFI+SIP lineage checks passed on last 10 exit_decision_made rows."
                )
                _telegram(body, script_name="alpaca_post_epoch_milestone_10")
            else:
                body = (
                    f"ALPACA POST-EPOCH MILESTONE **10** (integrity **RED** — no GREEN ping)\n"
                    f"epoch_start_ts={epoch_start_ts:.3f}  post_epoch_exits={post_epoch_count}\n"
                    + "\n".join(fails[:24])
                )
                _telegram(body, script_name="alpaca_post_epoch_milestone_10")
        else:
            body = (
                f"ALPACA POST-EPOCH MILESTONE **{milestone}**\n"
                f"epoch_start_ts={epoch_start_ts:.3f}  post_epoch_exits={post_epoch_count}\n"
                f"Terminal exit_decision_made count reached {milestone}."
            )
            _telegram(body, script_name=f"alpaca_post_epoch_milestone_{milestone}")

    threading.Thread(target=_run, name=f"milestone-{milestone}", daemon=True).start()
