"""
Multi-universe versioning: LIVE, PAPER, SHADOW.

Loads config/versioning.yaml. Exposes get_version(mode), set_version(mode, version, commit), get_all_versions().
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yaml
except Exception:
    yaml = None

CONFIG_DIR = Path(__file__).resolve().parent
VERSIONING_PATH = CONFIG_DIR / "versioning.yaml"


def _parse_yaml_fallback(text: str) -> Dict[str, Any]:
    """Minimal YAML parse when PyYAML missing (nested key: value)."""
    out: Dict[str, Any] = {}
    current: Optional[Dict[str, Any]] = None
    current_key: Optional[str] = None
    for line in text.splitlines():
        s = line.split("#")[0].rstrip()
        if not s:
            continue
        if ":" in s:
            k, v = s.split(":", 1)
            k, v = k.strip(), v.strip().strip('"\'')
            if not s[0].isspace():
                current_key = k
                current = {}
                out[k] = current
                if v and v.lower() not in ("true", "false"):
                    current["version"] = v
                continue
            if current is not None and s.startswith("  "):
                if v.lower() == "true":
                    v = True
                elif v.lower() == "false":
                    v = False
                elif v == "null" or not v:
                    v = None
                elif v.isdigit():
                    v = int(v)
                else:
                    try:
                        v = float(v)
                    except ValueError:
                        pass
                current[k] = v
    return out


def _load_versioning() -> Dict[str, Any]:
    if not VERSIONING_PATH.exists():
        return {"live": {"version": "live_v1", "commit": None}, "paper": {"version": "paper_v2", "commit": None}, "shadow": {"version": "shadow_v3", "commit": None}}
    text = VERSIONING_PATH.read_text(encoding="utf-8")
    if yaml is not None:
        try:
            data = yaml.safe_load(text)
            return data if isinstance(data, dict) else _parse_yaml_fallback(text)
        except Exception:
            pass
    return _parse_yaml_fallback(text)


def _save_versioning(data: Dict[str, Any]) -> None:
    if yaml is not None:
        VERSIONING_PATH.write_text(yaml.dump(data, default_flow_style=False, allow_unicode=True), encoding="utf-8")
    else:
        out = []
        for mode, d in data.items():
            if isinstance(d, dict):
                out.append(f"{mode}:")
                for k, v in d.items():
                    out.append(f"  {k}: {v}")
        VERSIONING_PATH.write_text("\n".join(out), encoding="utf-8")


def get_version(mode: str) -> Dict[str, Any]:
    """Return {version, commit} for mode (live, paper, shadow)."""
    data = _load_versioning()
    mode = (mode or "").strip().lower()
    d = data.get(mode) if isinstance(data.get(mode), dict) else {}
    return {"version": d.get("version") or "", "commit": d.get("commit")}


def set_version(mode: str, version: str, commit: Optional[str] = None) -> None:
    """Set version and commit for mode; persist to versioning.yaml."""
    data = _load_versioning()
    mode = (mode or "").strip().lower()
    if mode not in data or not isinstance(data[mode], dict):
        data[mode] = {}
    data[mode]["version"] = version
    data[mode]["commit"] = commit
    _save_versioning(data)


def get_all_versions() -> Dict[str, Dict[str, Any]]:
    """Return {live: {version, commit}, paper: {...}, shadow: {...}}."""
    data = _load_versioning()
    out = {}
    for m in ("live", "paper", "shadow"):
        d = data.get(m) if isinstance(data.get(m), dict) else {}
        out[m] = {"version": d.get("version") or "", "commit": d.get("commit")}
    return out


def current_git_commit() -> Optional[str]:
    """Return current git HEAD commit (short)."""
    try:
        r = subprocess.run(
            [os.getenv("GIT_CMD", "git"), "rev-parse", "HEAD"],
            cwd=CONFIG_DIR.parent,
            capture_output=True,
            text=True,
            timeout=2,
        )
        if r.returncode == 0 and r.stdout:
            return r.stdout.strip()
    except Exception:
        pass
    return None
