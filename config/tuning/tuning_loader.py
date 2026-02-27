"""
Phase 6 — Load governed tuning overlay (config-only, versioned, reversible).

Reads config/tuning/active.json or GOVERNED_TUNING_CONFIG path and returns
merged overlays for COMPOSITE_WEIGHTS_V2, WEIGHTS_V3, EXIT_WEIGHTS, ENTRY_THRESHOLDS.
If no overlay exists, returns empty dicts so code uses built-in defaults.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

# Default: repo root relative to this file
_CONFIG_TUNING_DIR = Path(__file__).resolve().parent
ACTIVE_PATH = _CONFIG_TUNING_DIR / "active.json"


def load_tuning_overlay(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load a single tuning overlay file. Returns {} if file missing or invalid."""
    p = path or os.environ.get("GOVERNED_TUNING_CONFIG") or ACTIVE_PATH
    if p is None:
        return {}
    if isinstance(p, str):
        p = Path(p)
    if not p.exists():
        return {}
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def get_merged_entry_v2_params(builtin: Dict[str, Any]) -> Dict[str, Any]:
    """Merge tuning overlay 'entry' over builtin COMPOSITE_WEIGHTS_V2. Does not mutate builtin."""
    overlay = load_tuning_overlay()
    entry = overlay.get("entry")
    if not entry or not isinstance(entry, dict):
        return dict(builtin)
    out = dict(builtin)
    for k, v in entry.items():
        if v is not None:
            if isinstance(v, dict) and isinstance(out.get(k), dict):
                out[k] = {**out[k], **v}
            else:
                out[k] = v
    return out


def get_merged_exit_weights(builtin: Dict[str, float]) -> Dict[str, float]:
    """Merge tuning overlay 'exit_weights' over builtin EXIT_WEIGHTS. Does not mutate builtin."""
    overlay = load_tuning_overlay()
    exit_w = overlay.get("exit_weights")
    if not exit_w or not isinstance(exit_w, dict):
        return dict(builtin)
    out = dict(builtin)
    for k, v in exit_w.items():
        if isinstance(v, (int, float)):
            out[k] = float(v)
    return out


def get_tuning_version() -> str:
    """Return version string from active overlay, or 'builtin'."""
    overlay = load_tuning_overlay()
    return str(overlay.get("version", "builtin"))
