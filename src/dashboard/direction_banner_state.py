"""
Dashboard banner state for directional intelligence replay.
Exposes get_direction_banner_state() for the dashboard to show a persistent banner.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def get_direction_banner_state(base_dir: Path | None = None) -> Dict[str, Any]:
    """
    Returns banner state: WAITING | RUNNING | RESULTS | BLOCKED.
    Banner updates live as counts increase and when replay completes.
    """
    base = (base_dir or _repo_root()).resolve()
    readiness_path = base / "state" / "direction_readiness.json"
    replay_status_path = base / "state" / "direction_replay_status.json"
    results_md = base / "reports" / "board" / "DIRECTION_REPLAY_30D_RESULTS.md"
    blocked_md = base / "reports" / "board" / "DIRECTION_REPLAY_BLOCKED_SYNTHETIC.md"

    telemetry_trades = 0
    ready = False
    try:
        if readiness_path.exists():
            data = json.loads(readiness_path.read_text(encoding="utf-8"))
            telemetry_trades = int(data.get("telemetry_trades") or 0)
            ready = data.get("ready") is True
    except Exception:
        pass

    replay_status: Dict[str, Any] = {}
    try:
        if replay_status_path.exists():
            replay_status = json.loads(replay_status_path.read_text(encoding="utf-8"))
    except Exception:
        pass

    status = (replay_status.get("status") or "").strip().upper()

    # A) WAITING
    if not ready:
        return {
            "state": "WAITING",
            "message": "Directional intelligence accumulating",
            "detail": f"Telemetry-backed trades: {telemetry_trades}/100",
            "severity": "info",
        }

    # B) RUNNING
    if status == "RUNNING":
        return {
            "state": "RUNNING",
            "message": "Directional replay running",
            "detail": "100 telemetry-backed trades reached",
            "severity": "warning",
        }

    # D) BLOCKED
    if status == "BLOCKED" or blocked_md.exists():
        return {
            "state": "BLOCKED",
            "message": "Directional replay blocked",
            "detail": "Insufficient telemetry coverage",
            "severity": "error",
            "link": "/reports/board/DIRECTION_REPLAY_BLOCKED_SYNTHETIC.md",
        }

    # C) RESULTS_AVAILABLE
    if status == "SUCCESS" or results_md.exists():
        return {
            "state": "RESULTS",
            "message": "Directional replay results available",
            "detail": "Click to review board report",
            "severity": "success",
            "link": "/reports/board/DIRECTION_REPLAY_30D_RESULTS.md",
        }

    # Ready but replay failed or not yet run
    if status == "FAILED":
        return {
            "state": "FAILED",
            "message": "Directional replay failed",
            "detail": replay_status.get("reason") or "See state/direction_replay_status.json",
            "severity": "error",
        }

    return {
        "state": "WAITING",
        "message": "Directional replay pending",
        "detail": "100 telemetry-backed trades reached; replay will run on next check",
        "severity": "info",
    }
}
