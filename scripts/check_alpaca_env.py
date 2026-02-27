#!/usr/bin/env python3
"""
Phase 0: Verify Alpaca env vars (ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL).
Load .env if present. If any required var is missing, print which and exit 1.
Write reports/bars/alpaca_env_check.md.
Run from repo root. On droplet: source .env then run this (or run with python that loads .env).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

REPORT_DIR = REPO / "reports" / "bars"
REPORT_PATH = REPORT_DIR / "alpaca_env_check.md"

REQUIRED = [
    "ALPACA_API_KEY",
    "ALPACA_SECRET_KEY",
    "ALPACA_BASE_URL",
]


def load_dotenv() -> None:
    env_path = REPO / ".env"
    if not env_path.exists():
        return
    try:
        from dotenv import load_dotenv as _load
        _load(env_path, override=True)
    except Exception:
        for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v


def main() -> int:
    load_dotenv()
    missing = [k for k in REQUIRED if not (os.getenv(k) or "").strip()]
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    if missing:
        lines = [
            "# Alpaca env check",
            "",
            "**Status:** FAIL",
            "",
            "Missing or empty: " + ", ".join(missing),
            "",
            "Set in .env or environment and re-run.",
        ]
        REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
        print("Alpaca env check: FAIL")
        print("Missing:", ", ".join(missing))
        return 1
    lines = [
        "# Alpaca env check",
        "",
        "**Status:** PASS",
        "",
        "| Variable | Set |",
        "|----------|-----|",
    ]
    for k in REQUIRED:
        val = os.getenv(k) or ""
        display = "yes (hidden)" if val else "no"
        lines.append(f"| {k} | {display} |")
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print("Alpaca env check: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
