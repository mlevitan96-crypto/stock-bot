#!/usr/bin/env python3
"""
Offline verification for V5.0 Passive Hunter limit peg + 2026 decimal rules.
Run from repo root: python scripts/verify_v5_execution.py
"""

from __future__ import annotations

import os
import sys

# Import main only after cwd is repo root (paths + optional .env)
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)
os.chdir(_REPO_ROOT)

from main import normalize_equity_limit_price, v5_compute_limit_price  # noqa: E402


def main() -> None:
    # Institutional name: bid 150.05, ask 150.15 -> mid 150.10, buy peg min(mid, bid+0.01)=150.06
    px, abort = v5_compute_limit_price(150.05, 150.15, "buy", spread_guard_bps=20.0)
    assert abort is None, abort
    assert abs(px - 150.06) < 1e-9, f"expected buy 150.06, got {px}"

    # Penny stock: 0.5011 x 0.5022 is ~21.9 bps wide — exceeds 20 bps guard; relax guard to test decimals only.
    px2, abort2 = v5_compute_limit_price(0.5011, 0.5022, "buy", spread_guard_bps=100.0)
    assert abort2 is None, abort2
    assert px2 < 1.0
    assert abs(px2 - round(px2, 4)) < 1e-12, f"sub-dollar price must land on 4dp tick, got {px2}"
    assert px2 == normalize_equity_limit_price(
        min((0.5011 + 0.5022) / 2.0, 0.5011 + 0.01)
    )

    msg = "✅ V5 EXECUTION VERIFIED"
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        print(msg)
    except UnicodeEncodeError:
        print("[OK] V5 EXECUTION VERIFIED")


if __name__ == "__main__":
    main()
