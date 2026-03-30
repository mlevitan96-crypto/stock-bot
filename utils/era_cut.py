"""
Alpaca era cut: exclude pre-cut positions and log rows from learning, decay certification, and governance gaps.

Reads config/era_cut.json (repo root). If missing or unparsable, all helpers are no-ops (backward compatible).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

_REPO_ROOT = Path(__file__).resolve().parent.parent
_ERA_PATH = _REPO_ROOT / "config" / "era_cut.json"


def _repo_root() -> Path:
    return _REPO_ROOT


def load_era_cut_config() -> Optional[Dict[str, Any]]:
    if not _ERA_PATH.is_file():
        return None
    try:
        data = json.loads(_ERA_PATH.read_text(encoding="utf-8", errors="replace"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def get_alpaca_era_cut_dt_utc() -> Optional[datetime]:
    cfg = load_era_cut_config()
    if not cfg:
        return None
    alp = cfg.get("alpaca")
    if not isinstance(alp, dict):
        return None
    raw = alp.get("era_cut_ts")
    if not raw:
        return None
    return parse_iso_to_utc_aware(raw)


def parse_iso_to_utc_aware(raw: Any) -> Optional[datetime]:
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt
    except Exception:
        return None


def entry_ts_is_before_era_cut(entry_ts_raw: Any) -> bool:
    cut = get_alpaca_era_cut_dt_utc()
    if cut is None:
        return False
    et = parse_iso_to_utc_aware(entry_ts_raw)
    if et is None:
        return False
    return et < cut


def feature_vector_excluded_from_learning(feature_vector: Optional[Dict[str, Any]]) -> bool:
    if not isinstance(feature_vector, dict):
        return False
    return entry_ts_is_before_era_cut(
        feature_vector.get("entry_ts") or feature_vector.get("entry_timestamp")
    )


def learning_excluded_for_attribution_record(rec: Dict[str, Any]) -> bool:
    cut = get_alpaca_era_cut_dt_utc()
    if cut is None:
        return False
    ctx = rec.get("context") if isinstance(rec.get("context"), dict) else {}
    raw = (
        ctx.get("entry_ts")
        or rec.get("entry_ts")
        or ctx.get("entry_timestamp")
        or rec.get("entry_timestamp")
    )
    et = parse_iso_to_utc_aware(raw)
    if et is None:
        return False
    return et < cut


def learning_excluded_for_exit_record(rec: Dict[str, Any]) -> bool:
    cut = get_alpaca_era_cut_dt_utc()
    if cut is None:
        return False
    ctx = rec.get("context") if isinstance(rec.get("context"), dict) else {}
    raw = (
        rec.get("entry_timestamp")
        or rec.get("entry_ts")
        or ctx.get("entry_ts")
        or ctx.get("entry_timestamp")
    )
    et = parse_iso_to_utc_aware(raw)
    if et is None:
        return False
    return et < cut
