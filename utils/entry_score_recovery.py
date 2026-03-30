"""
Recover entry_score for positions that were added by reconciliation (e.g. pending fill later detected).
Used so the dashboard and exit logic see a real entry score instead of 0.0.

- persist_pending_fill_score(symbol, score): call when order is submitted but not yet filled.
- recover_entry_score_for_symbol(symbol, pop_pending=True): call when adding/updating position
  metadata for a symbol; returns score from pending_fill_scores or last open_ record in attribution.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


def _state_dir() -> Path:
    try:
        from config.registry import Directories
        return Directories.STATE
    except Exception:
        return Path("state")


def _pending_fill_path() -> Path:
    try:
        from config.registry import StateFiles
        return getattr(StateFiles, "PENDING_FILL_SCORES", _state_dir() / "pending_fill_scores.json")
    except Exception:
        return _state_dir() / "pending_fill_scores.json"


def _attribution_path() -> Path:
    try:
        from config.registry import LogFiles
        return LogFiles.ATTRIBUTION
    except Exception:
        return Path("logs/attribution.jsonl")


def _scoring_flow_path() -> Path:
    return Path("logs/scoring_flow.jsonl")


def persist_pending_fill_score(symbol: str, score: float) -> None:
    """Persist entry score for a symbol whose order was submitted but not yet filled.
    Reconciliation or health check can later apply this when the position appears in Alpaca."""
    if not symbol or score <= 0:
        return
    path = _pending_fill_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        from config.registry import atomic_write_json
        data = {}
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
            except Exception:
                data = {}
        if not isinstance(data, dict):
            data = {}
        from datetime import datetime, timezone
        data[str(symbol).upper()] = {"score": float(score), "ts": datetime.now(timezone.utc).isoformat()}
        atomic_write_json(path, data)
    except Exception:
        pass


def recover_entry_score_for_symbol(symbol: str, pop_pending: bool = True) -> Optional[float]:
    """Return entry_score for a symbol from pending_fill_scores (then remove if pop_pending)
    or from the most recent open_ record in attribution.jsonl. Returns None if nothing found."""
    sym = str(symbol).upper()
    path = _pending_fill_path()
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
            if isinstance(data, dict) and sym in data:
                entry = data[sym]
                if isinstance(entry, dict):
                    score = entry.get("score")
                else:
                    score = entry
                try:
                    score = float(score)
                except (TypeError, ValueError):
                    score = None
                if score is not None and score > 0:
                    if pop_pending:
                        from config.registry import atomic_write_json
                        data = {k: v for k, v in data.items() if k != sym}
                        atomic_write_json(path, data)
                    return score
        except Exception:
            pass
    attr_path = _attribution_path()
    if attr_path.exists():
        last_score = None
        try:
            with open(attr_path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                        if rec.get("type") != "attribution":
                            continue
                        if rec.get("symbol", "").upper() != sym:
                            continue
                        tid = str(rec.get("trade_id", ""))
                        if not tid.startswith("open_"):
                            continue
                        ctx = rec.get("context") if isinstance(rec.get("context"), dict) else {}
                        s = ctx.get("entry_score")
                        if s is not None:
                            try:
                                last_score = float(s)
                            except (TypeError, ValueError):
                                pass
                    except Exception:
                        continue
        except Exception:
            pass
        if last_score is not None and last_score > 0:
            return last_score
    # Last composite_calculated in scoring_flow.jsonl (authoritative recent composite)
    sf = _scoring_flow_path()
    if sf.exists():
        last_sf = None
        try:
            with open(sf, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                        if rec.get("msg") != "composite_calculated":
                            continue
                        if str(rec.get("symbol", "")).upper() != sym:
                            continue
                        s = rec.get("score")
                        if s is not None:
                            try:
                                last_sf = float(s)
                            except (TypeError, ValueError):
                                pass
                    except json.JSONDecodeError:
                        continue
        except OSError:
            pass
        if last_sf is not None and last_sf > 0:
            return last_sf
    return None
