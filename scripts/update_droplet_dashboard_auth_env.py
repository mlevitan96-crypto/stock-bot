#!/usr/bin/env python3
"""
Update droplet /root/stock-bot/.env with DASHBOARD_USER / DASHBOARD_PASS.

Contract:
- Do NOT overwrite other secrets in .env.
- Do NOT print secrets to stdout/stderr.
- Fail closed if local .env is missing required keys.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys


def _read_local_dashboard_creds(env_path: Path) -> tuple[str, str]:
    if not env_path.exists():
        raise SystemExit(f"Local {env_path} not found")
    raw = env_path.read_text(encoding="utf-8", errors="replace").splitlines()
    data: dict[str, str] = {}
    for line in raw:
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        k = k.strip()
        if k in ("DASHBOARD_USER", "DASHBOARD_PASS"):
            data[k] = v.strip()
    user = data.get("DASHBOARD_USER", "").strip()
    pw = data.get("DASHBOARD_PASS", "").strip()
    if not user or not pw:
        raise SystemExit("Local .env missing DASHBOARD_USER and/or DASHBOARD_PASS")
    return user, pw


def _upsert_kv(lines: list[str], key: str, value: str) -> list[str]:
    pat = re.compile(r"^" + re.escape(key) + r"=")
    updated = False
    out: list[str] = []
    for ln in lines:
        if pat.match(ln):
            out.append(f"{key}={value}")
            updated = True
        else:
            out.append(ln)
    if not updated:
        out.append(f"{key}={value}")
    return out


def main() -> int:
    # Ensure repo root is importable when running from scripts/
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    # Read local creds (do not print)
    user, pw = _read_local_dashboard_creds(Path(".env"))

    from droplet_client import DropletClient  # local import (requires paramiko)

    client = DropletClient()
    ssh = None
    sftp = None
    try:
        ssh = client._connect()
        sftp = ssh.open_sftp()

        remote_env = "/root/stock-bot/.env"
        tmp_env = "/root/stock-bot/.env.tmp"

        # Read current remote .env
        with sftp.open(remote_env, "r") as f:
            raw = f.read().decode("utf-8", errors="replace")

        original_mode = sftp.stat(remote_env).st_mode

        lines = raw.splitlines()
        lines = _upsert_kv(lines, "DASHBOARD_USER", user)
        lines = _upsert_kv(lines, "DASHBOARD_PASS", pw)

        new_payload = "\n".join(lines).rstrip("\n") + "\n"

        # Write to temp, then move into place via SSH (more reliable than SFTP rename on some servers).
        with sftp.open(tmp_env, "w") as f:
            f.write(new_payload)
        try:
            sftp.chmod(tmp_env, original_mode)
        except Exception:
            # Best-effort; systemd loads via EnvironmentFile regardless.
            pass
        # Move into place (overwrite).
        stdin, stdout, stderr = ssh.exec_command(f"bash -lc 'mv -f {tmp_env} {remote_env}'", timeout=30)
        rc = stdout.channel.recv_exit_status()
        if rc != 0:
            err_txt = (stderr.read() or b"").decode("utf-8", errors="replace")
            raise SystemExit(f"Failed to move updated .env into place (rc={rc}): {err_txt[:200]}")

        # Sanity check: verify keys exist (do not print values)
        with sftp.open(remote_env, "r") as f:
            final_txt = f.read().decode("utf-8", errors="replace")
        if "DASHBOARD_USER=" not in final_txt or "DASHBOARD_PASS=" not in final_txt:
            raise SystemExit("Remote .env update failed (keys not present after write)")

        print("[OK] Droplet .env updated with DASHBOARD_USER/DASHBOARD_PASS (values not shown).")
        return 0
    finally:
        try:
            if sftp is not None:
                sftp.close()
        except Exception:
            pass
        try:
            client.close()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())

