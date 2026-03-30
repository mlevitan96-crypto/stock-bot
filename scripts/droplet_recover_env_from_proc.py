#!/usr/bin/env python3
"""
Rebuild /root/stock-bot/.env from a running dashboard / uw_flow process environ.

Use when .env was wiped but systemd-spawned children still hold ALPACA_* / UW_*.
Does not print secret values. Intended for droplet recovery only.

CSA/SRE: restores operational parity with MEMORY_BANK canon (EnvironmentFile=.env).
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ENV_PATH = REPO / ".env"


def _read_proc_environ(pid: int) -> dict[str, str]:
    raw = Path(f"/proc/{pid}/environ").read_bytes()
    out: dict[str, str] = {}
    for part in raw.split(b"\0"):
        if not part or b"=" not in part:
            continue
        k, _, v = part.partition(b"=")
        out[k.decode(errors="replace")] = v.decode(errors="replace")
    return out


def _first_pid(pattern: str) -> int | None:
    r = subprocess.run(
        ["pgrep", "-f", pattern],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0 or not r.stdout.strip():
        return None
    return int(r.stdout.strip().split()[0])


def main() -> int:
    dash_pid = _first_pid(r"dashboard\.py")
    uw_pid = _first_pid(r"uw_flow_daemon\.py")
    merged: dict[str, str] = {}
    # Prefer dashboard (full trading env), then uw_flow for gaps / Telegram
    for pid in (dash_pid, uw_pid):
        if pid is None:
            continue
        try:
            env = _read_proc_environ(pid)
        except OSError as e:
            print(f"recover_fail read pid={pid}: {e}", file=sys.stderr)
            continue
        for k, v in env.items():
            if not (v or "").strip():
                continue
            if k not in merged or not (merged.get(k) or "").strip():
                merged[k] = v.strip()

    keys = [
        "ALPACA_KEY",
        "ALPACA_SECRET",
        "UW_API_KEY",
        "ALPACA_BASE_URL",
        "ALPACA_SIGNAL_CONTEXT_EMIT",
        "UW_MISSING_INPUT_MODE",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
    ]
    lines: list[str] = []
    for k in keys:
        v = merged.get(k, "").strip()
        if v and "\n" not in v and "\r" not in v:
            lines.append(f"{k}={v}\n")

    if not any(x.startswith("ALPACA_KEY=") for x in lines):
        print("recover_fail missing ALPACA_KEY in target process environ", file=sys.stderr)
        return 1
    if not any(x.startswith("ALPACA_SECRET=") for x in lines):
        print("recover_fail missing ALPACA_SECRET", file=sys.stderr)
        return 1
    if not any(x.startswith("UW_API_KEY=") for x in lines):
        print("recover_fail missing UW_API_KEY", file=sys.stderr)
        return 1

    ENV_PATH.write_text("".join(lines), encoding="utf-8")
    os.chmod(ENV_PATH, 0o600)
    print(f"recover_ok entries={len(lines)} path={ENV_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
