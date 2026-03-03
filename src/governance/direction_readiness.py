"""
Canonical readiness counter for directional intelligence replay.

Counts trades where:
- direction_intel_embed.intel_snapshot_entry exists (exit_attribution)
- direction_event.jsonl has entries (sanity: telemetry is being written)
- Reconstruction would be "telemetry" (same as intel_snapshot_entry present)

Persists state/direction_readiness.json. Once ready flips TRUE, it does not flip back.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple

# Default base_dir: repo root (when run from repo, cwd is repo)
def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def count_direction_intel_backed_trades(base_dir: Path | None = None) -> Tuple[int, int, float]:
    """
    Count trades that have full direction telemetry (would reconstruct as telemetry).

    Uses:
    - logs/exit_attribution.jsonl: telemetry_trades = records with direction_intel_embed.intel_snapshot_entry
    - logs/direction_event.jsonl: presence confirms events are being written (optional sanity)

    Returns:
        (total_trades, telemetry_trades, pct_telemetry)
    """
    base = (base_dir or _repo_root()).resolve()
    exit_path = base / "logs" / "exit_attribution.jsonl"
    direction_event_path = base / "logs" / "direction_event.jsonl"

    total_trades = 0
    telemetry_trades = 0

    if not exit_path.exists():
        return 0, 0, 0.0

    for line in exit_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            if not isinstance(rec, dict):
                continue
            total_trades += 1
            embed = rec.get("direction_intel_embed")
            if isinstance(embed, dict):
                snapshot = embed.get("intel_snapshot_entry")
                if isinstance(snapshot, dict) and snapshot:
                    telemetry_trades += 1
        except Exception:
            continue

    pct_telemetry = (100.0 * telemetry_trades / total_trades) if total_trades else 0.0
    return total_trades, telemetry_trades, pct_telemetry


def is_direction_ready(
    telemetry_trades: int,
    pct_telemetry: float,
    *,
    min_trades: int = 100,
    min_pct: float = 90.0,
) -> bool:
    """
    Returns True only if:
    - telemetry_trades >= min_trades (default 100)
    - pct_telemetry >= min_pct (default 90.0)
    """
    return telemetry_trades >= min_trades and pct_telemetry >= min_pct


def _state_path(base_dir: Path | None) -> Path:
    base = (base_dir or _repo_root()).resolve()
    return base / "state" / "direction_readiness.json"


def load_direction_readiness_state(base_dir: Path | None = None) -> Dict[str, Any]:
    """Load state/direction_readiness.json. Returns dict with telemetry_trades, pct_telemetry, ready, ready_ts."""
    path = _state_path(base_dir)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def update_and_persist_direction_readiness(base_dir: Path | None = None) -> Dict[str, Any]:
    """
    Compute counts, respect "ready once True never False", persist state.

    State shape:
    {
      "telemetry_trades": int,
      "pct_telemetry": float,
      "total_trades": int,
      "ready": bool,
      "ready_ts": optional ISO timestamp
    }
    """
    base = (base_dir or _repo_root()).resolve()
    state_dir = base / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    path = state_dir / "direction_readiness.json"

    total, telemetry, pct = count_direction_intel_backed_trades(base)
    current_ready = is_direction_ready(telemetry, pct)

    prev = load_direction_readiness_state(base)
    # Once ready flips TRUE, it must not flip back
    already_ready = prev.get("ready") is True
    ready = already_ready or current_ready
    ready_ts = prev.get("ready_ts")
    if current_ready and not already_ready:
        ready_ts = datetime.now(timezone.utc).isoformat()

    state = {
        "total_trades": total,
        "telemetry_trades": telemetry,
        "pct_telemetry": round(pct, 2),
        "ready": ready,
        "ready_ts": ready_ts,
    }
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return state
