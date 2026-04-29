#!/usr/bin/env python3
"""
SRE: droplet .env — strip trailing whitespace (sed), strip outer quotes on values (Python),
WebSocket smoke test, restart uw-flow-daemon + Telegram on SUCCESS.

Requires droplet_config.json (or set **DROPLET_HOST** / SSH env overrides). Does not print raw API keys.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from droplet_client import DropletClient  # noqa: E402

# Runs on Linux droplet after cd to project root
REMOTE_DEQUOTE = r'''from pathlib import Path
p = Path(".env")
raw = p.read_text(encoding="utf-8", errors="replace")
lines_in = raw.splitlines()
deq = 0
out = []
for s in lines_in:
    s2 = s.rstrip(" \t")
    if s2 and not s2.lstrip().startswith("#") and "=" in s2:
        k, v = s2.split("=", 1)
        if len(v) >= 2 and v[0] in "\"'" and v[0] == v[-1]:
            v = v[1:-1]
            deq += 1
        s2 = k + "=" + v
    out.append(s2)
text = "\n".join(out)
if raw.endswith("\n"):
    text += "\n"
p.write_text(text, encoding="utf-8")
print("lines_outer_dequoted:", deq)
'''


def _mask_uw_api_key_line(line: str) -> str:
    s = line.strip()
    if not s.startswith("UW_API_KEY="):
        return "(not a UW_API_KEY= line)"
    v = s.split("=", 1)[1].strip()
    if len(v) <= 8:
        return f"UW_API_KEY=<len={len(v)}>"
    return f"UW_API_KEY={v[:4]}...{v[-4:]} (len={len(v)}, no quotes in preview)"


def main() -> int:
    cfg = ROOT / "droplet_config.json"
    if not cfg.is_file():
        print("Missing droplet_config.json", file=sys.stderr)
        return 2
    c = DropletClient(str(cfg))

    r0 = c.execute_command("test -f .env && pwd || echo MISSING", timeout=15)
    out0 = (r0.get("stdout") or "").strip()
    if "MISSING" in out0 or not out0 or r0.get("exit_code") != 0:
        print("No .env or pwd failed:", r0, file=sys.stderr)
        return 3
    proj = out0.splitlines()[-1].strip()

    r_trail = c.execute_command(
        r"grep -nE '[[:blank:]]$' .env 2>/dev/null | wc -l",
        timeout=15,
    )
    trail_count = int((r_trail.get("stdout") or "0").strip() or "0")

    r_cp = c.execute_command("cp -a .env .env.presani.bak 2>/dev/null || cp .env .env.presani.bak", timeout=15)
    if r_cp.get("exit_code") != 0:
        print("backup failed", r_cp, file=sys.stderr)
        return 4

    r_sed = c.execute_command(r"sed -i 's/[[:space:]]*$//' .env", timeout=15)
    if r_sed.get("exit_code") != 0:
        print("sed failed", r_sed, file=sys.stderr)
        return 5

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tf:
        tf.write(REMOTE_DEQUOTE)
        local_py = tf.name
    try:
        remote_py = f"{proj.rstrip('/')}/.sanitize_env_once.py"
        c.put_file(local_py, remote_py)
    finally:
        Path(local_py).unlink(missing_ok=True)

    r_py = c.execute_command(f"python3 {remote_py} && rm -f {remote_py}", timeout=30)
    py_stdout = (r_py.get("stdout") or "").strip()
    if r_py.get("exit_code") != 0:
        print("dequote script failed", r_py, file=sys.stderr)
        return 6

    r_ws = c.execute_command(
        "bash -lc \"if grep -qE '^UW_FLOW_WS_ENABLED=' .env 2>/dev/null; then "
        "sed -i 's/^UW_FLOW_WS_ENABLED=.*/UW_FLOW_WS_ENABLED=1/' .env; "
        "else printf '\\nUW_FLOW_WS_ENABLED=1\\n' >> .env; fi; "
        "grep -E '^UW_FLOW_WS_ENABLED=' .env | head -1\"",
        timeout=15,
    )
    print("--- UW_FLOW_WS_ENABLED ---")
    print((r_ws.get("stdout") or "").strip())

    r_line = c.execute_command(r'grep -nE "^UW_API_KEY=" .env | head -1', timeout=15)
    raw_line = (r_line.get("stdout") or "").strip()
    uw_masked = _mask_uw_api_key_line(raw_line.split(":", 1)[-1] if ":" in raw_line else raw_line)

    r_smoke = c.execute_command(
        "set -a && [ -f .env ] && . ./.env; set +a && ./venv/bin/python scripts/debug/ws_smoke_test.py",
        timeout=120,
    )
    smoke_out = (r_smoke.get("stdout") or "").strip()
    ec = int(r_smoke.get("exit_code") or 1)

    print("--- SRE: sanitize ---")
    print(f"lines_with_trailing_space_before_sed: {trail_count}")
    print(py_stdout)
    print("--- SMOKE ---")
    print(smoke_out)
    print(f"exit_code={ec}")

    if "SUCCESS: JOIN OK" in smoke_out and ec == 0:
        tg = c.execute_command(
            r"""set -a && [ -f .env ] && . ./.env; set +a && printf '%s\n' '✅ PREDATOR DATA SPINE ONLINE: WebSocket Handshake Successful.' | ./venv/bin/python scripts/notify/send_telegram_message.py""",
            timeout=45,
        )
        print("--- Telegram ---")
        print("exit:", tg.get("exit_code"))
        se = (tg.get("stderr") or "").strip()
        if se:
            print("stderr:", se[:300])

    print("--- MASKED UW_API_KEY= line (format check) ---")
    print(uw_masked)

    r_dep = c.execute_command(
        "git fetch -q origin && git pull -q origin main && "
        "sudo systemctl restart uw-flow-daemon.service && sleep 2 && systemctl is-active uw-flow-daemon.service",
        timeout=180,
    )
    print("--- DEPLOY (pull + uw-flow-daemon restart) ---")
    print((r_dep.get("stdout") or "").strip())
    if (r_dep.get("stderr") or "").strip():
        print("stderr:", (r_dep.get("stderr") or "").strip()[:500], file=sys.stderr)

    r_j = c.execute_command("journalctl -u uw-flow-daemon -n 35 --no-pager", timeout=20)
    print("--- journalctl uw-flow-daemon (last 35) ---")
    print((r_j.get("stdout") or "").strip())

    if "SUCCESS: JOIN OK" in smoke_out and ec == 0:
        return 0
    return ec if ec != 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
