#!/usr/bin/env python3
"""
Inspect .env for Alpaca key lines without printing secret values.

Reports: length, leading/trailing whitespace, surrounding quotes, non-printable bytes.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent


def _audit_value(name: str, raw_val: str) -> None:
    v = raw_val
    stripped = v.strip()
    non_print = sum(1 for c in v if ord(c) < 32 and c not in "\t\n\r")
    quoted = len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in "\"'"
    print(f"  {name}:")
    print(f"    length(raw)={len(v)} length(strip)={len(stripped)}")
    print(f"    raw_neq_strip={v != stripped}")
    print(f"    surrounded_by_quotes={quoted}")
    print(f"    non_printable_count={non_print}")
    if stripped:
        print(f"    first_char={stripped[0]!r} last_char={stripped[-1]!r}")
        print(f"    key_id_prefix={stripped[:8]}…" if len(stripped) >= 8 else f"    key_id_prefix={stripped!r}")


def _parse_env_file(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$", line)
        if not m:
            continue
        k, val = m.group(1), m.group(2)
        out[k] = val
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Alpaca .env hygiene (no full secrets printed)")
    ap.add_argument("--env-file", type=Path, default=REPO / ".env")
    args = ap.parse_args()

    data = _parse_env_file(args.env_file)
    names = (
        "ALPACA_KEY",
        "ALPACA_SECRET",
        "ALPACA_API_KEY",
        "ALPACA_API_SECRET",
        "APCA_API_KEY_ID",
        "APCA_API_SECRET_KEY",
    )
    print(f"--- file: {args.env_file} ---")
    found = False
    for n in names:
        if n in data:
            found = True
            _audit_value(n, data[n])
    if not found:
        print("  (no Alpaca key variables found in file)")
    print()
    try:
        from config.registry import get_alpaca_trading_credentials

        try:
            from dotenv import load_dotenv

            load_dotenv(args.env_file)
        except Exception:
            pass
        k, s, b = get_alpaca_trading_credentials()
        print("--- get_alpaca_trading_credentials() after load_dotenv ---")
        print(f"  resolved_base_url={b!r}")
        print(f"  key_len={len(k)} secret_len={len(s)}")
        if k:
            print(f"  key_id_prefix={k[:8]}…")
    except Exception as e:
        print(f"  (registry probe skipped: {e})")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(REPO))
    raise SystemExit(main())
