"""10-trade harvester checkpoint guard: state/alpaca_10trade_harvester_sent.json"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def checkpoint_10_state_path(root: Path) -> Path:
    return root / "state" / "alpaca_10trade_harvester_sent.json"


def load_checkpoint_10_state(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        o = json.loads(path.read_text(encoding="utf-8"))
        return o if isinstance(o, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_checkpoint_10_state(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)
