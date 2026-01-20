#!/usr/bin/env python3
"""
Droplet sync utilities (base64 fetch + local logging)
====================================================

Contract:
- No secrets printed.
- PowerShell-safe: avoid heredocs; keep remote python snippets single-line.
"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict


@dataclass(frozen=True)
class SyncResult:
    success: bool
    stdout: str
    stderr: str


def _now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def append_sync_log(path: Path, rec: Dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": _now_iso(), **rec}) + "\n")
    except Exception:
        return


def decode_b64(b64_text: str) -> bytes:
    return base64.b64decode((b64_text or "").encode("ascii"))


def droplet_b64_read_file(client, remote_path: str, *, timeout: int = 60) -> SyncResult:
    """
    Read entire remote file and return base64 text in stdout.
    Uses droplet venv python to avoid reliance on `python`/`python3` in PATH.
    """
    cmd = (
        "./venv/bin/python -c "
        "\"import base64,sys; "
        f"p='{remote_path}'; "
        "sys.stdout.write(base64.b64encode(open(p,'rb').read()).decode('ascii'))\""
    )
    r = client.execute_command(cmd, timeout=timeout)
    return SyncResult(bool(r.get('success')), (r.get('stdout') or ''), (r.get('stderr') or ''))


def droplet_b64_tail_file(client, remote_path: str, *, lines: int = 500, timeout: int = 60) -> SyncResult:
    """
    Read last N lines of a remote file (text) and return base64 of UTF-8 bytes.
    Implemented purely in python on droplet to avoid shell quoting differences.
    """
    n = int(lines)
    cmd = (
        "./venv/bin/python -c "
        "\"import base64,pathlib; "
        f"p=pathlib.Path('{remote_path}'); "
        f"n={n}; "
        "b=(p.read_bytes() if p.exists() else b''); "
        "lines=b.splitlines()[-n:]; "
        "out=(b'\\n'.join(lines) + (b'\\n' if lines else b'')); "
        "print(base64.b64encode(out).decode('ascii'))\""
    )
    # IMPORTANT: `client.execute_command` runs inside `cd project_dir` already.
    r = client.execute_command(cmd, timeout=timeout)
    return SyncResult(bool(r.get('success')), (r.get('stdout') or ''), (r.get('stderr') or ''))

