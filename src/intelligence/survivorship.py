"""
Survivorship scoring: penalize chronic losers, boost consistent winners, penalize high decay-exit symbols.
Used by live_entry_adjustments and EOD build_survivorship_adjustments.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Penalty for chronic losers (win_rate < 0.25)
CHRONIC_LOSER_PENALTY = -0.15
# Boost for consistent winners (win_rate > 0.55)
CONSISTENT_WINNER_BOOST = 0.10
# Penalty when >70% of exits are decay-triggered
DECAY_EXIT_RATE_THRESHOLD = 0.70
DECAY_EXIT_PENALTY = -0.10


def _repo_root(base: Path | None) -> Path:
    if base is not None:
        return base
    return Path(__file__).resolve().parents[2]


def _load_signal_survivorship_latest(base: Path) -> dict[str, Any]:
    """Load most recent state/signal_survivorship_<date>.json."""
    state_dir = base / "state"
    if not state_dir.exists():
        return {}
    best: dict[str, Any] = {}
    best_date = ""
    for p in state_dir.iterdir():
        if p.is_file() and p.name.startswith("signal_survivorship_") and p.suffix == ".json":
            try:
                date_part = p.stem.replace("signal_survivorship_", "")
                if len(date_part) == 10 and date_part[4] == "-":
                    if date_part > best_date:
                        best = json.loads(p.read_text(encoding="utf-8"))
                        best_date = date_part
            except Exception:
                continue
    return best.get("signals") or {}


def survivorship_score_delta(symbol: str, base: Path | None = None) -> float:
    """
    Return score delta from survivorship: chronic losers (win_rate < 0.25) -0.15,
    consistent winners (win_rate > 0.55) +0.10, decay-based (>70% decay exits) -0.10.
    """
    root = _repo_root(base)
    signals = _load_signal_survivorship_latest(root)
    d = signals.get(symbol) if isinstance(signals.get(symbol), dict) else None
    if not d:
        return 0.0
    wr = d.get("win_rate")
    try:
        wr = float(wr) if wr is not None else None
    except (TypeError, ValueError):
        wr = None
    trade_count = d.get("trade_count") or 0
    decay_count = d.get("decay_trigger_count") or 0
    decay_rate = (decay_count / trade_count) if trade_count else 0.0
    delta = 0.0
    if wr is not None and wr < 0.25:
        delta += CHRONIC_LOSER_PENALTY
    if wr is not None and wr > 0.55:
        delta += CONSISTENT_WINNER_BOOST
    if decay_rate > DECAY_EXIT_RATE_THRESHOLD:
        delta += DECAY_EXIT_PENALTY
    return round(delta, 4)


def get_decay_exit_rate(symbol: str, base: Path | None = None) -> float | None:
    """Return fraction of exits that were decay-triggered for symbol; None if no data."""
    root = _repo_root(base)
    signals = _load_signal_survivorship_latest(root)
    d = signals.get(symbol) if isinstance(signals.get(symbol), dict) else None
    if not d:
        return None
    tc = d.get("trade_count") or 0
    dc = d.get("decay_trigger_count") or 0
    return round((dc / tc), 4) if tc else None


def get_survivorship_score(symbol: str, base: Path | None = None) -> float | None:
    """
    Return survivorship score in [0, 1] for gating (e.g. wheel requires >= 0).
    Derived from win_rate and decay rate; None if no data.
    """
    root = _repo_root(base)
    signals = _load_signal_survivorship_latest(root)
    d = signals.get(symbol) if isinstance(signals.get(symbol), dict) else None
    if not d:
        return None
    wr = d.get("win_rate")
    try:
        wr = float(wr) if wr is not None else None
    except (TypeError, ValueError):
        wr = None
    trade_count = d.get("trade_count") or 0
    decay_count = d.get("decay_trigger_count") or 0
    decay_rate = (decay_count / trade_count) if trade_count else 0.0
    score = 0.5  # neutral
    if wr is not None:
        if wr < 0.25:
            score -= 0.25
        elif wr > 0.55:
            score += 0.2
    if decay_rate > DECAY_EXIT_RATE_THRESHOLD:
        score -= 0.2
    return round(max(0.0, min(1.0, score)), 4)
