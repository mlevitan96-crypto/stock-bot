#!/usr/bin/env python3
"""
Exit regimes: Fire Sale (immediate exit on catastrophic decay) and Let-It-Breathe (relax decay for strong entries).
All exit decisions must log which regime fired, why, and thresholds used.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "config" / "exit_regimes.json"
log = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "fire_sale": {
        "signal_delta_threshold": -0.25,
        "price_delta_pct_threshold": -3.0,
        "catastrophic_decay_delta": -1.0,
        "enabled": True,
    },
    "let_it_breathe": {
        "entry_signal_strength_threshold": 2.5,
        "pnl_delta_15m_min": 0.0,
        "pnl_delta_15m_threshold": 0.0,
        "relax_decay_multiplier": 1.5,
        "enabled": True,
    },
}


def load_config() -> dict[str, Any]:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def get_exit_regime(
    *,
    signal_delta: float | None = None,
    price_delta_pct: float | None = None,
    entry_signal_strength: float | None = None,
    pnl_delta_15m: float | None = None,
    catastrophic_decay: bool = False,
) -> tuple[str, str, dict[str, Any]]:
    """
    Returns (regime_name, reason, context).
    regime_name: "fire_sale" | "let_it_breathe" | "normal"
    """
    cfg = load_config()
    fire = cfg.get("fire_sale") or {}
    breathe = cfg.get("let_it_breathe") or {}
    context: dict[str, Any] = {"thresholds_used": {}}

    if fire.get("enabled", True):
        sig_thr = fire.get("signal_delta_threshold", -0.25)
        price_thr = fire.get("price_delta_pct_threshold", -3.0)
        cat_decay = fire.get("catastrophic_decay_delta", -1.0)
        context["thresholds_used"]["fire_sale_signal_delta"] = sig_thr
        context["thresholds_used"]["fire_sale_price_delta_pct"] = price_thr
        context["thresholds_used"]["fire_sale_catastrophic_decay_delta"] = cat_decay
        if catastrophic_decay:
            return "fire_sale", f"exit_causality indicates catastrophic decay (threshold {cat_decay})", context
        if signal_delta is not None and signal_delta < sig_thr:
            return "fire_sale", f"signal_delta {signal_delta} < {sig_thr}", context
        if price_delta_pct is not None and price_delta_pct < price_thr:
            return "fire_sale", f"price_delta_pct {price_delta_pct}% < {price_thr}%", context

    if breathe.get("enabled", True):
        entry_thr = breathe.get("entry_signal_strength_threshold", 2.5)
        pnl_15m_min = breathe.get("pnl_delta_15m_min") or breathe.get("pnl_delta_15m_threshold", 0.0)
        relax_mult = breathe.get("relax_decay_multiplier", 1.5)
        context["thresholds_used"]["let_it_breathe_entry_threshold"] = entry_thr
        context["thresholds_used"]["let_it_breathe_pnl_delta_15m_threshold"] = pnl_15m_min
        context["thresholds_used"]["let_it_breathe_relax_decay_multiplier"] = relax_mult
        if (
            entry_signal_strength is not None
            and entry_signal_strength >= entry_thr
            and pnl_delta_15m is not None
            and pnl_delta_15m > pnl_15m_min
            and not catastrophic_decay
        ):
            return "let_it_breathe", f"entry_signal_strength>={entry_thr} and pnl_delta_15m>{pnl_15m_min}", context

    return "normal", "", context


def log_exit_regime_decision(
    symbol: str,
    regime: str,
    reason: str,
    context: dict[str, Any],
    log_dir: Path | None = None,
) -> None:
    """Append to logs/exit_regime_decisions.jsonl for audit."""
    log_dir = log_dir or (REPO_ROOT / "logs")
    path = log_dir / "exit_regime_decisions.jsonl"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        rec = {"symbol": symbol, "regime": regime, "reason": reason, "context": context}
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, default=str) + "\n")
    except Exception as e:
        log.warning("Could not log exit regime decision: %s", e)
