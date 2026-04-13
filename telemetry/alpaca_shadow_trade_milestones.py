"""
Canonical trade-count milestones (600 / 750 / 1000) for Alpha-10 shadow march.

State: ``state/alpaca_shadow_trade_milestones.json`` — prevents double-fire across restarts.
Telegram style aligned with ``telemetry/alpaca_telegram_integrity`` templates (multi-line, emoji lead).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

STATE_REL = Path("state") / "alpaca_shadow_trade_milestones.json"

THRESHOLDS: List[Tuple[int, str, str]] = [
    (
        600,
        "alpaca_shadow_milestone_600",
        "🎯 MILESTONE: 600 Trades. Statistical significance improving.\n\n"
        "[ALPACA] Canonical trade_key count (post-era) has reached 600.\n"
        "Shadow ML collection continues — review cohort quality periodically.",
    ),
    (
        750,
        "alpaca_shadow_milestone_750",
        "🚀 MILESTONE: 750 Trades. N-count high. Review pending.\n\n"
        "[ALPACA] Canonical trade_key count (post-era) has reached 750.\n"
        "Prepare for Alpha 10 / brain promotion readiness review.",
    ),
    (
        1000,
        "alpaca_shadow_milestone_1000",
        "🏆 MILESTONE: 1000 Trades. DATASET COMPLETE. Ready for Final Alpha 10 Review & Brain Deployment.\n\n"
        "[ALPACA] Canonical trade_key count (post-era) has reached 1000.\n"
        "Execute final governance review and deployment checklist before promoting ML out of shadow.",
    ),
]


def _state_path(root: Path) -> Path:
    return (root / STATE_REL).resolve()


def _load_state(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {"fired": {}, "last_total": 0}
    try:
        o = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(o, dict):
            return {"fired": {}, "last_total": 0}
        fired = o.get("fired")
        if not isinstance(fired, dict):
            fired = {}
        last = o.get("last_total", 0)
        try:
            last_i = int(last)
        except (TypeError, ValueError):
            last_i = 0
        return {"fired": {str(k): bool(v) for k, v in fired.items()}, "last_total": last_i}
    except (OSError, json.JSONDecodeError):
        return {"fired": {}, "last_total": 0}


def _save_state(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    out = {
        "fired": dict(sorted(data.get("fired", {}).items(), key=lambda kv: int(kv[0]) if str(kv[0]).isdigit() else 0)),
        "last_total": int(data.get("last_total", 0)),
        "updated_note": "canonical_trade_milestones_shadow_v1",
    }
    tmp.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def maybe_notify_canonical_trade_milestones(root: Path) -> None:
    """
    After a new exit attribution row is persisted, recompute canonical count and send any new milestones.
    """
    try:
        from scripts.alpaca_telegram import send_governance_telegram
        from src.governance.canonical_trade_count import compute_canonical_trade_count
    except Exception:
        return

    sp = _state_path(root)
    st = _load_state(sp)
    fired: Dict[str, bool] = {str(k): bool(v) for k, v in st.get("fired", {}).items()}

    try:
        summary = compute_canonical_trade_count(root, floor_epoch=None)
        n = int(summary.get("total_trades_post_era") or 0)
    except Exception:
        return

    for threshold, script_name, message in THRESHOLDS:
        key = str(threshold)
        if n < threshold or fired.get(key):
            continue
        if send_governance_telegram(message, script_name=script_name):
            fired[key] = True

    try:
        _save_state(sp, {"fired": fired, "last_total": n})
    except Exception:
        pass
