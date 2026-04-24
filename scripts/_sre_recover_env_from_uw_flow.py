#!/usr/bin/env python3
"""One-shot SRE: merge UW + dashboard auth from live uw_flow_daemon environ into .env (droplet)."""
from __future__ import annotations

import glob
import os
import sys
from pathlib import Path


def uw_flow_pid() -> int | None:
    for p in glob.glob("/proc/[0-9]*/cmdline"):
        try:
            c = Path(p).read_bytes()
            if b"uw_flow_daemon.py" in c:
                return int(p.split("/")[2])
        except (OSError, ValueError):
            continue
    return None


def main() -> int:
    pid = uw_flow_pid()
    if not pid:
        print("RECOVER_FAIL: no uw_flow_daemon pid")
        return 1
    raw = Path(f"/proc/{pid}/environ").read_bytes()
    env: dict[str, str] = {}
    for item in raw.split(b"\x00"):
        if not item or b"=" not in item:
            continue
        k, v = item.split(b"=", 1)
        env[k.decode(errors="replace")] = v.decode(errors="replace")

    want = ["UW_API_KEY", "DASHBOARD_USER", "DASHBOARD_PASS"]
    recovered = {k: env[k] for k in want if env.get(k, "").strip()}
    if len(recovered) < 3:
        missing = [k for k in want if k not in recovered or not recovered.get(k, "").strip()]
        print("RECOVER_FAIL: missing keys", missing)
        return 2

    path = Path("/root/stock-bot/.env")
    text = path.read_text() if path.exists() else ""
    lines = text.splitlines()
    have: set[str] = set()
    for line in lines:
        s = line.strip()
        if s and not s.startswith("#") and "=" in s:
            have.add(s.split("=", 1)[0].strip())

    to_add = [k for k in want if k not in have]
    if not to_add:
        print("MERGE_OK: already_present", ",".join(want))
        print("SOURCE_PID:", pid)
        return 0

    with open(path, "a", encoding="utf-8") as f:
        if text and not text.endswith("\n"):
            f.write("\n")
        f.write("\n# Recovered from live uw_flow_daemon process environ (SRE recovery)\n")
        for k in to_add:
            f.write(f"{k}={recovered[k]}\n")
    os.chmod(path, 0o600)
    print("APPENDED:", ",".join(to_add))
    print("SOURCE_PID:", pid)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
