"""
State IO helpers (self-healing).

Goal: state file corruption must never crash the trading loop.
This module provides defensive JSON readers that:
- catch JSON decode / IO errors
- optionally back up corrupted files to *.corrupted.<ts>.json
- optionally rewrite a minimal default file ({} / [] / etc.)
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Callable, Optional, Union


LoggerFn = Callable[[str, str], None]


def read_json_self_heal(
    path: Union[str, Path],
    default: Any,
    *,
    heal: bool = True,
    mkdir: bool = True,
    on_event: Optional[Callable[[str, dict], None]] = None,
) -> Any:
    """
    Read JSON from `path` safely.

    - If file missing: returns `default`
    - If JSON is corrupt: backs it up and rewrites `default` (when heal=True), then returns `default`

    `on_event` if provided is called as: on_event(event_name, payload_dict).
    """
    p = Path(path)

    if not p.exists():
        return default

    try:
        raw = p.read_text(encoding="utf-8")
        return json.loads(raw)
    except Exception as e:
        if on_event:
            try:
                on_event("state_read_failed", {"path": str(p), "error": str(e), "error_type": type(e).__name__})
            except Exception:
                pass

        if not heal:
            return default

        try:
            ts = int(time.time())
            backup = p.with_suffix(p.suffix + f".corrupted.{ts}.json")
            try:
                p.rename(backup)
            except Exception:
                # If rename fails (permissions/locks), still attempt rewrite below.
                backup = None

            if mkdir:
                p.parent.mkdir(parents=True, exist_ok=True)

            try:
                p.write_text(json.dumps(default, indent=2), encoding="utf-8")
            except Exception:
                pass

            if on_event:
                try:
                    on_event(
                        "state_self_healed",
                        {"path": str(p), "backup": str(backup) if backup else None, "default_type": type(default).__name__},
                    )
                except Exception:
                    pass
        except Exception:
            # Never raise from self-healing.
            pass

        return default

