#!/usr/bin/env python3
"""
One-shot: on the droplet, discover TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID from /root and systemd,
write canonical KEY=VALUE lines (no export, no quotes) to /root/stock-bot/.env and /root/.alpaca_env,
daemon-reload, restart alpaca-telegram-integrity.timer.

Stdout is non-secret (source paths only). Requires DropletClient config (droplet_config.json or env).
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

REMOTE_PY = r'''#!/usr/bin/env python3
import glob
import re
import subprocess
from pathlib import Path

KEYS = ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID")


def gather_paths() -> list[str]:
    files: set[str] = set()
    for base in ("/root", "/etc/systemd/system"):
        for needle in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"):
            try:
                p = subprocess.run(
                    ["grep", "-rsl", needle, base],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                for line in p.stdout.splitlines():
                    line = line.strip()
                    if line and "/proc/" not in line and "/sys/" not in line:
                        files.add(line)
            except (subprocess.TimeoutExpired, OSError):
                pass
    for name in ("alpaca_secrets.txt",):
        for parent in (Path("/root"), Path("/root/stock-bot")):
            p = parent / name
            if p.is_file():
                files.add(str(p))
    for pattern in ("/root/**/*.bak", "/root/stock-bot/**/*.bak"):
        try:
            for g in glob.glob(pattern, recursive=True):
                try:
                    if Path(g).is_file() and Path(g).stat().st_size < 2_000_000:
                        files.add(g)
                except OSError:
                    pass
        except OSError:
            pass
    return sorted(files)


def parse_kv_line(raw: str) -> tuple[str | None, str | None]:
    line = raw.strip()
    if not line or line.startswith("#"):
        return None, None
    if line.startswith("export "):
        line = line[7:].strip()
    m = re.match(r"^(TELEGRAM_BOT_TOKEN|TELEGRAM_CHAT_ID)=(.*)$", line)
    if not m:
        return None, None
    key, val = m.group(1), m.group(2).strip()
    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
        val = val[1:-1].strip()
    if not val:
        return None, None
    return key, val


def scan_file(path: str) -> dict[str, str]:
    out: dict[str, str] = {}
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return out
    for line in text.splitlines():
        k, v = parse_kv_line(line)
        if k and v:
            out[k] = v
    if len(out) < 2:
        for key in KEYS:
            if key in out:
                continue
            m = re.search(
                rf"(?:^|[\s\"']){re.escape(key)}=([^\s#\"']+|\"[^\"]+\"|'[^']+')",
                text,
            )
            if not m:
                continue
            val = m.group(1).strip()
            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
            elif val.startswith("'") and val.endswith("'"):
                val = val[1:-1]
            if val:
                out[key] = val
    return out


def merge_env_file(path: Path, token: str, chat: str) -> None:
    lines: list[str] = []
    if path.is_file():
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    filtered: list[str] = []
    for ln in lines:
        st = ln.strip()
        if st.startswith("#"):
            filtered.append(ln)
            continue
        s2 = st[7:].strip() if st.startswith("export ") else st
        if re.match(r"^(TELEGRAM_BOT_TOKEN|TELEGRAM_CHAT_ID)=", s2):
            continue
        filtered.append(ln)
    while filtered and not filtered[-1].strip():
        filtered.pop()
    filtered.append(f"TELEGRAM_BOT_TOKEN={token}")
    filtered.append(f"TELEGRAM_CHAT_ID={chat}")
    filtered.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(filtered), encoding="utf-8")


def main() -> int:
    token = chat = None
    token_src = chat_src = None
    for f in gather_paths():
        d = scan_file(f)
        if "TELEGRAM_BOT_TOKEN" in d and not token:
            token, token_src = d["TELEGRAM_BOT_TOKEN"], f
        if "TELEGRAM_CHAT_ID" in d and not chat:
            chat, chat_src = d["TELEGRAM_CHAT_ID"], f
        if token and chat:
            break
    if not token or not chat:
        print("FAIL could not resolve TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from search paths")
        return 1
    for p in (Path("/root/stock-bot/.env"), Path("/root/.alpaca_env")):
        merge_env_file(p, token, chat)
    print(f"OK wrote {KEYS[0]} and {KEYS[1]} to /root/stock-bot/.env and /root/.alpaca_env")
    print(f"OK token_first_seen={token_src} chat_first_seen={chat_src}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def main() -> int:
    sys.path.insert(0, str(REPO))
    from droplet_client import DropletClient

    c = DropletClient()
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tf:
            tf.write(REMOTE_PY)
            local_py = Path(tf.name)
        try:
            c.put_file(local_py, "/tmp/sre_wire_telegram_env.py")
        finally:
            local_py.unlink(missing_ok=True)

        r = c.execute_command(
            "chmod +x /tmp/sre_wire_telegram_env.py && python3 /tmp/sre_wire_telegram_env.py",
            timeout=180,
        )
        print(r["stdout"], end="")
        if r["stderr"]:
            print(r["stderr"], file=sys.stderr, end="")
        if r["exit_code"] != 0:
            return r["exit_code"]

        c.put_file(REPO / "scripts" / "alpaca_telegram.py", "/root/stock-bot/scripts/alpaca_telegram.py")

        r2 = c.execute_command(
            "systemctl daemon-reload && systemctl restart alpaca-telegram-integrity.timer "
            "&& systemctl is-active alpaca-telegram-integrity.timer",
            timeout=60,
        )
        print(r2["stdout"], end="")
        if r2["stderr"]:
            print(r2["stderr"], file=sys.stderr, end="")
        if r2["exit_code"] != 0:
            return r2["exit_code"]

        hb = (
            "cd /root/stock-bot && "
            "TELEGRAM_GOVERNANCE_RESPECT_MARKET_HOURS=0 TELEGRAM_GOVERNANCE_INTEGRITY_ONLY=0 "
            "PYTHONPATH=. /root/stock-bot/venv/bin/python3 scripts/alpaca_telegram.py "
            "--message 'SRE HEARTBEAT: Alpaca Monitoring is ONLINE. Z-Count: 392.' "
            "--script-name sre_heartbeat"
        )
        r3 = c.execute_command(hb, timeout=90)
        print(r3["stdout"], end="")
        if r3["stderr"]:
            print(r3["stderr"], file=sys.stderr, end="")
        return 0 if r3["exit_code"] == 0 else r3["exit_code"]
    finally:
        c.close()


if __name__ == "__main__":
    raise SystemExit(main())
