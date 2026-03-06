"""
Canonical readiness counter for directional intelligence replay.

Review baseline: last READINESS_SAMPLE_SIZE exits (default 100). We do not use
all-time totals (e.g. 2000) for readiness or replay decisions; we evaluate
the last 100 exits so that telemetry % reflects recent capture, not history.

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

# Baseline for readiness/replay: last N exits. Do not use all-time totals (e.g. 2000).
READINESS_SAMPLE_SIZE = 100

# Default base_dir: repo root (when run from repo, cwd is repo)
def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def count_direction_intel_backed_trades(
    base_dir: Path | None = None,
    sample_size: int | None = None,
) -> Tuple[int, int, float]:
    """
    Count trades that have full direction telemetry in the LAST sample_size exits.

    Uses logs/exit_attribution.jsonl: takes only the last sample_size (default 100)
    lines; total_trades = len(recent), telemetry_trades = count with intel_snapshot_entry.
    This makes readiness and replay decisions based on the last 100 exits, not all-time.

    Returns:
        (total_trades, telemetry_trades, pct_telemetry)
    """
    base = (base_dir or _repo_root()).resolve()
    exit_path = base / "logs" / "exit_attribution.jsonl"
    n = sample_size if sample_size is not None else READINESS_SAMPLE_SIZE

    if not exit_path.exists():
        return 0, 0, 0.0

    try:
        lines = [
            ln.strip()
            for ln in exit_path.read_text(encoding="utf-8", errors="replace").splitlines()
            if ln.strip()
        ]
    except Exception:
        return 0, 0, 0.0

    recent = lines[-n:] if len(lines) > n else lines
    total_trades = len(recent)
    telemetry_trades = 0

    for line in recent:
        try:
            rec = json.loads(line)
            if not isinstance(rec, dict):
                continue
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
    total_trades: int | None = None,
    *,
    min_window: int = 100,
    min_pct: float = 90.0,
) -> bool:
    """
    Returns True when we have a full review window and enough telemetry coverage:
    - total_trades >= min_window (default 100: we have 100 exits in the baseline)
    - pct_telemetry >= min_pct (default 90: at least 90% of those have telemetry)
    If total_trades not provided, requires telemetry_trades >= min_window and pct >= min_pct (legacy).
    """
    if total_trades is not None:
        return total_trades >= min_window and pct_telemetry >= min_pct
    return telemetry_trades >= min_window and pct_telemetry >= min_pct


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
    current_ready = is_direction_ready(telemetry, pct, total_trades=total)

    prev = load_direction_readiness_state(base)
    # Once ready flips TRUE, it must not flip back
    already_ready = prev.get("ready") is True
    ready = already_ready or current_ready
    ready_ts = prev.get("ready_ts")
    if current_ready and not already_ready:
        ready_ts = datetime.now(timezone.utc).isoformat()

    # All-time exit count (so dashboard can show growing total)
    all_time_exits = 0
    try:
        exit_path = base / "logs" / "exit_attribution.jsonl"
        if exit_path.exists():
            all_time_exits = sum(1 for ln in exit_path.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip())
    except Exception:
        pass

    updated_ts = datetime.now(timezone.utc).isoformat()
    state = {
        "total_trades": total,
        "telemetry_trades": telemetry,
        "pct_telemetry": round(pct, 2),
        "ready": ready,
        "ready_ts": ready_ts,
        "updated_ts": updated_ts,
        "all_time_exits": all_time_exits,
    }
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return state
