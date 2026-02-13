"""
Policy variants: baseline, live_canary, paper_aggressive.
LIVE = baseline + live_canary by canary_ratio (default 0.2).
PAPER = paper_aggressive (ratio 1.0).
Deterministic canary assignment: hash(symbol + day + strategy) % 100 < canary_ratio*100.
Persist assignment per position so it does not flip intraday.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CONFIG_PATH = Path("config") / "policy_variants.json"
STATE_DIR = Path("state")
CANARY_ASSIGNMENTS_PATH = STATE_DIR / "canary_assignments.json"
KILL_SWITCH_PATH = STATE_DIR / "kill_switch.json"
LIVE_CANARY_DISABLED_PATH = STATE_DIR / "live_canary_disabled.json"


def _load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def is_live() -> bool:
    """True if Alpaca is live (not paper)."""
    url = os.environ.get("APCA_API_BASE_URL") or os.environ.get("ALPACA_BASE_URL", "")
    if not url:
        try:
            from config.registry import APIConfig
            url = getattr(APIConfig, "ALPACA_BASE_URL", "") or ""
        except Exception:
            pass
    return "paper" not in url.lower()


def _canary_ratio() -> float:
    config = _load_config()
    if is_live():
        return float(config.get("live", {}).get("canary_ratio", 0.2))
    return float(config.get("paper", {}).get("canary_ratio", 1.0))


def _canary_assignment_key(symbol: str, strategy: str = "equity") -> str:
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"{symbol}|{day}|{strategy}"


def canary_assignment(symbol: str, strategy: str = "equity", persist: bool = True) -> bool:
    """
    Deterministic: hash(symbol + day + strategy) % 100 < canary_ratio*100.
    Persist so assignment does not flip intraday. Returns True if this (symbol, day, strategy) is in canary.
    """
    if not is_live():
        return True  # PAPER always gets aggressive
    ratio = _canary_ratio()
    if ratio <= 0:
        return False
    if ratio >= 1.0:
        return True
    key = _canary_assignment_key(symbol, strategy)
    # Check persisted first
    if persist and CANARY_ASSIGNMENTS_PATH.exists():
        try:
            data = json.loads(CANARY_ASSIGNMENTS_PATH.read_text(encoding="utf-8"))
            if key in data:
                return bool(data[key])
        except Exception:
            pass
    h = hash(key) % 100
    if h < 0:
        h += 100
    assigned = h < (ratio * 100)
    if persist:
        try:
            STATE_DIR.mkdir(parents=True, exist_ok=True)
            data = {}
            if CANARY_ASSIGNMENTS_PATH.exists():
                try:
                    data = json.loads(CANARY_ASSIGNMENTS_PATH.read_text(encoding="utf-8"))
                except Exception:
                    pass
            data[key] = assigned
            CANARY_ASSIGNMENTS_PATH.write_text(json.dumps(data), encoding="utf-8")
        except Exception:
            pass
    return assigned


def get_variant_id(symbol: str, strategy: str = "equity") -> str:
    """Return variant identifier for attribution: baseline, live_canary, or paper_aggressive."""
    if not is_live():
        return "paper_aggressive"
    if _is_canary_disabled():
        return "baseline"
    if canary_assignment(symbol, strategy, persist=True):
        return "live_canary"
    return "baseline"


def get_variant_params(symbol: str, strategy: str = "equity") -> dict:
    """Return effective signal_decay and blockers params for this (symbol, strategy) from the active variant."""
    config = _load_config()
    baseline = config.get("baseline", {})
    if is_live():
        if _is_canary_disabled():
            return {**baseline.get("signal_decay", {}), **baseline.get("blockers", {})}
        use_canary = canary_assignment(symbol, strategy, persist=True)
        if use_canary:
            canary = config.get("live_canary", {})
            return {
                **baseline.get("signal_decay", {}),
                **baseline.get("blockers", {}),
                **canary.get("signal_decay", {}),
                **canary.get("blockers", {}),
            }
        return {**baseline.get("signal_decay", {}), **baseline.get("blockers", {})}
    # PAPER: paper_aggressive
    agg = config.get("paper_aggressive", {})
    return {
        **baseline.get("signal_decay", {}),
        **baseline.get("blockers", {}),
        **agg.get("signal_decay", {}),
        **agg.get("blockers", {}),
    }


def _is_canary_disabled() -> bool:
    if not LIVE_CANARY_DISABLED_PATH.exists():
        return False
    try:
        data = json.loads(LIVE_CANARY_DISABLED_PATH.read_text(encoding="utf-8"))
        return bool(data.get("disabled", False))
    except Exception:
        return False


def kill_switch_active() -> bool:
    """If state/kill_switch.json exists and enabled=true, trading halts."""
    if not KILL_SWITCH_PATH.exists():
        return False
    try:
        data = json.loads(KILL_SWITCH_PATH.read_text(encoding="utf-8"))
        return bool(data.get("enabled", False))
    except Exception:
        return True  # fail closed if file present but unreadable


def write_live_canary_disabled(reason: str) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    LIVE_CANARY_DISABLED_PATH.write_text(
        json.dumps({
            "disabled": True,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }),
        encoding="utf-8",
    )


def get_live_safety_caps() -> dict:
    """LIVE only: return live_safety caps from config (max_daily_loss_usd, max_open_positions, etc.)."""
    if not is_live():
        return {}
    config = _load_config()
    return dict(config.get("live_safety") or {})


def check_live_safety_caps(
    *,
    daily_pnl_usd: float | None = None,
    open_positions_count: int | None = None,
    notional_exposure_usd: float | None = None,
    new_positions_this_cycle: int | None = None,
) -> tuple[bool, str]:
    """
    LIVE only: check current state against live_safety caps.
    Returns (allowed, reason). If not allowed, reason describes which cap was hit.
    """
    if not is_live():
        return True, ""
    caps = get_live_safety_caps()
    if not caps:
        return True, ""
    max_loss = caps.get("max_daily_loss_usd")
    if max_loss is not None and daily_pnl_usd is not None and float(daily_pnl_usd) <= -float(max_loss):
        return False, f"max_daily_loss_usd cap hit: pnl={daily_pnl_usd} <= -{max_loss}"
    max_pos = caps.get("max_open_positions")
    if max_pos is not None and open_positions_count is not None and int(open_positions_count) >= int(max_pos):
        return False, f"max_open_positions cap hit: {open_positions_count} >= {max_pos}"
    max_notional = caps.get("max_notional_exposure")
    if max_notional is not None and notional_exposure_usd is not None and float(notional_exposure_usd) >= float(max_notional):
        return False, f"max_notional_exposure cap hit: {notional_exposure_usd} >= {max_notional}"
    max_new = caps.get("max_new_positions_per_cycle")
    if max_new is not None and new_positions_this_cycle is not None and int(new_positions_this_cycle) >= int(max_new):
        return False, f"max_new_positions_per_cycle cap hit: {new_positions_this_cycle} >= {max_new}"
    return True, ""


def get_auto_rollback_config() -> dict:
    """Return auto_rollback config (pnl_threshold_usd, win_rate_threshold, cycles_lookback, etc.)."""
    config = _load_config()
    return dict(config.get("auto_rollback") or {})


def check_auto_rollback_and_disable(
    pnl_1d: float | None = None,
    win_rate_1d: float | None = None,
) -> tuple[bool, str]:
    """
    LIVE only: if 1d PnL or win rate breaches auto_rollback thresholds, disable canary and return (True, reason).
    Otherwise return (False, ""). Call from EOD or rolling window pipeline.
    """
    if not is_live() or _is_canary_disabled():
        return False, ""
    cfg = get_auto_rollback_config()
    if not cfg:
        return False, ""
    pnl_thresh = cfg.get("pnl_threshold_usd")
    wr_thresh = cfg.get("win_rate_threshold")
    reasons = []
    if pnl_thresh is not None and pnl_1d is not None and float(pnl_1d) <= float(pnl_thresh):
        reasons.append(f"1d PnL {pnl_1d} <= threshold {pnl_thresh}")
    if wr_thresh is not None and win_rate_1d is not None and float(win_rate_1d) < float(wr_thresh):
        reasons.append(f"1d win_rate {win_rate_1d} < threshold {wr_thresh}")
    if not reasons:
        return False, ""
    reason = "; ".join(reasons)
    write_live_canary_disabled(f"auto_rollback: {reason}")
    return True, reason
