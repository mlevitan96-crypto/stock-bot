"""
Data Armor: safe JSON loading for Alpaca / equities state files.

Catches JSONDecodeError, empty files, FileNotFoundError, and IO errors; falls back to
a deep copy of the caller-provided default and emits WARN to logs/system_events.jsonl.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Optional, Union

PathLike = Union[str, Path]


def safe_requests_json(response: Any, *, url_hint: str = "", default: Optional[dict] = None) -> dict:
    """
    Parse ``requests.Response.json()`` without raising; return a dict default on failure.
    """
    d = dict(default) if default is not None else {"data": []}
    try:
        out = response.json()
        return out if isinstance(out, dict) else copy.deepcopy(d)
    except Exception as e:
        _warn(url_hint or "http_response", "response_json_error", str(e))
        return copy.deepcopy(d)


def _warn(path: PathLike, reason: str, detail: str = "") -> None:
    try:
        from utils.system_events import log_system_event

        log_system_event(
            subsystem="data_armor",
            event_type="safe_json_load_fallback",
            severity="WARN",
            details={
                "path": str(path),
                "reason": reason,
                "detail": (detail or "")[:2000],
            },
        )
    except Exception:
        pass


def safe_json_loads(raw: str, default: Any, *, path_hint: str = "") -> Any:
    """
    Parse JSON from a string; on failure return deepcopy(default) and warn.
    """
    p = path_hint or "<string>"
    if raw is None or not str(raw).strip():
        _warn(p, "empty_body", "")
        return copy.deepcopy(default)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        _warn(p, "json_decode_error", str(e))
        return copy.deepcopy(default)
    except Exception as e:
        _warn(p, "parse_exception", str(e))
        return copy.deepcopy(default)


def safe_json_load(path: PathLike, default: Any, *, context: str = "") -> Any:
    """
    Load JSON from path. Returns deepcopy(default) on missing file, empty file,
    JSONDecodeError, or read errors. ``context`` is included in the system event details.
    """
    p = Path(path)
    hint = str(p) + (f"::{context}" if context else "")
    if not p.exists():
        _warn(hint, "file_not_found", "")
        return copy.deepcopy(default)
    try:
        raw = p.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        _warn(hint, "read_error", str(e))
        return copy.deepcopy(default)
    except Exception as e:
        _warn(hint, "read_exception", str(e))
        return copy.deepcopy(default)
    if not raw.strip():
        _warn(hint, "empty_file", "")
        return copy.deepcopy(default)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        _warn(hint, "json_decode_error", str(e))
        return copy.deepcopy(default)
    except Exception as e:
        _warn(hint, "parse_exception", str(e))
        return copy.deepcopy(default)
