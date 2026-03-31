#!/usr/bin/env python3
"""
Auto-detect TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID for Alpaca governance (droplet).

Resolution order (first source where BOTH keys are non-empty wins):
1) systemd unit stock-bot.service: Environment= lines + EnvironmentFile= contents
2) /root/.alpaca_env
3) $TRADING_BOT_ROOT/.env
4) /etc/quant-dashboard.env
5) $TRADING_BOT_ROOT/venv/bin/activate
6) $TRADING_BOT_ROOT/venv/bin/postactivate

Never logs secret values. Call apply_detected_telegram_env() to load into os.environ.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_SYSTEMD_CANDIDATES = (
    "/etc/systemd/system/stock-bot.service",
    "/lib/systemd/system/stock-bot.service",
    "/etc/systemd/system/stock-bot.service.d/override.conf",
)


def _root() -> Path:
    r = os.environ.get("TRADING_BOT_ROOT", os.environ.get("DROPLET_TRADING_ROOT", "")).strip()
    return Path(r).resolve() if r else Path(__file__).resolve().parents[1]


def _strip_quotes(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return s[1:-1]
    return s


def _parse_env_file(path: Path) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not path.is_file():
        return out
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return out
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", line)
        if not m:
            continue
        k, v = m.group(1), _strip_quotes(m.group(2))
        out[k] = v
    return out


def _parse_shell_exports(path: Path, keys: Tuple[str, ...]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not path.is_file():
        return out
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return out
    for key in keys:
        pat = re.compile(
            rf"^\s*export\s+{re.escape(key)}=(.+)$",
            re.MULTILINE,
        )
        m = pat.search(raw)
        if m:
            out[key] = _strip_quotes(m.group(1).strip())
    return out


def _parse_systemd_unit(path: Path) -> Tuple[Dict[str, str], List[str]]:
    """Inline Environment= assignments and EnvironmentFile paths."""
    env: Dict[str, str] = {}
    env_files: List[str] = []
    if not path.is_file():
        return env, env_files
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return env, env_files
    for line in lines:
        s = line.strip()
        if s.startswith("EnvironmentFile="):
            val = s.split("=", 1)[1].strip()
            if val.startswith("-"):
                val = val[1:].strip()
            env_files.append(val)
        elif s.startswith("Environment="):
            val = s.split("=", 1)[1].strip()
            val = _strip_quotes(val)
            for part in re.split(r"\s+", val):
                if "=" in part:
                    k, v = part.split("=", 1)
                    env[k.strip()] = _strip_quotes(v.strip())
    return env, env_files


def _telegram_pair(d: Dict[str, str]) -> Optional[Dict[str, str]]:
    t = (d.get("TELEGRAM_BOT_TOKEN") or "").strip()
    c = (d.get("TELEGRAM_CHAT_ID") or "").strip()
    if t and c:
        return {"TELEGRAM_BOT_TOKEN": t, "TELEGRAM_CHAT_ID": c}
    return None


def collect_telegram_from_systemd() -> Optional[Tuple[Dict[str, str], str]]:
    for unit in _SYSTEMD_CANDIDATES:
        p = Path(unit)
        if not p.is_file():
            continue
        merged: Dict[str, str] = {}
        desc_parts: List[str] = [str(p)]
        inline, files = _parse_systemd_unit(p)
        merged.update(inline)
        for ef in files:
            fp = Path(ef.replace("%i", "").strip())
            merged.update(_parse_env_file(fp))
            desc_parts.append(str(fp))
        pair = _telegram_pair(merged)
        if pair:
            return pair, "systemd:" + "+".join(desc_parts)
    return None


def collect_telegram_from_fallback_paths(root: Path) -> Optional[Tuple[Dict[str, str], str]]:
    candidates: List[Tuple[Path, str]] = [
        (Path("/root/.alpaca_env"), "/root/.alpaca_env"),
        (root / ".env", str(root / ".env")),
        (Path("/etc/quant-dashboard.env"), "/etc/quant-dashboard.env"),
        (root / "venv" / "bin" / "activate", str(root / "venv/bin/activate")),
        (root / "venv" / "bin" / "postactivate", str(root / "venv/bin/postactivate")),
    ]
    keys = ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID")
    for path, label in candidates:
        if "activate" in path.name:
            d = _parse_shell_exports(path, keys)
        else:
            d = _parse_env_file(path)
        chk = _telegram_pair(d)
        if chk:
            return chk, label
    return None


def detect_telegram_credentials(root: Optional[Path] = None) -> Tuple[Optional[str], Optional[str], str]:
    """
    Returns (token, chat_id, source_label). Values None if not found.
    """
    root = root or _root()
    hit = collect_telegram_from_systemd()
    if hit:
        d, label = hit
        return d["TELEGRAM_BOT_TOKEN"], d["TELEGRAM_CHAT_ID"], label
    hit2 = collect_telegram_from_fallback_paths(root)
    if hit2:
        d, label = hit2
        return d["TELEGRAM_BOT_TOKEN"], d["TELEGRAM_CHAT_ID"], label
    return None, None, ""


def apply_detected_telegram_env(root: Optional[Path] = None) -> Tuple[bool, str]:
    """Load TELEGRAM_* into os.environ from the first valid canonical source."""
    token, chat, label = detect_telegram_credentials(root)
    if not token or not chat:
        return False, ""
    os.environ["TELEGRAM_BOT_TOKEN"] = token
    os.environ["TELEGRAM_CHAT_ID"] = chat
    return True, label


def main() -> int:
    """CLI: print source label only (no secrets), exit 0 if ok."""
    root = _root()
    ok, label = apply_detected_telegram_env(root)
    if ok:
        print(label)
        return 0
    print(
        "USER INPUT NEEDED (copy/paste):\n"
        "- Path to the env file or activation script that defines "
        "TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID\n"
        "(Do NOT send token values.)",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
