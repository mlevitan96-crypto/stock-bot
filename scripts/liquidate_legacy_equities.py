#!/usr/bin/env python3
"""
Flatten all **US equity** positions on the Alpaca account linked by ``.env`` (paper or live).

- Uses ``close_position`` (same pattern as ``scripts/repair/alpaca_controlled_liquidation.py``).
- **Governance:** Refuses ``--execute`` while ``stock-bot.service`` is **active** unless you pass
  ``--allow-while-bot-running`` (avoids racing the live trading loop).
- **Confirmation:** Type ``CONFIRM`` at the prompt, or set ``LIQUIDATE_CONFIRM=CONFIRM`` for non-interactive runs.

Repo root:
  PYTHONPATH=. python3 scripts/liquidate_legacy_equities.py --dry-run
  PYTHONPATH=. python3 scripts/liquidate_legacy_equities.py --execute
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO = Path(__file__).resolve().parents[1]
os.chdir(REPO)
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

for path in (REPO / ".env", Path.home() / ".alpaca_env"):
    if not path.is_file():
        continue
    try:
        from dotenv import load_dotenv  # type: ignore

        load_dotenv(path, override=False)
    except Exception:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v


def _stock_bot_active() -> Optional[bool]:
    """True if systemd says stock-bot is active; None if check skipped/unavailable."""
    try:
        r = subprocess.run(
            ["systemctl", "is-active", "stock-bot.service"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return r.returncode == 0 and (r.stdout or "").strip() == "active"
    except Exception:
        return None


def _is_us_equity_position(p: Any) -> bool:
    """Exclude options / crypto; keep common stock roots."""
    sym = (getattr(p, "symbol", None) or (p.get("symbol") if isinstance(p, dict) else "") or "").strip()
    if not sym or "/" in sym:
        return False
    ac = getattr(p, "asset_class", None) or (p.get("asset_class") if isinstance(p, dict) else None)
    if ac:
        return str(ac).lower() in ("us_equity", "equity")
    # OCC-style option symbol (underlying + 6 date + C/P + strike)
    if len(sym) >= 15 and re.search(r"\d{6}[CP]\d{3,8}$", sym.upper().replace(".", "")):
        return False
    return True


def _confirm() -> bool:
    env = (os.environ.get("LIQUIDATE_CONFIRM") or "").strip()
    if env == "CONFIRM":
        print("LIQUIDATE_CONFIRM=CONFIRM detected.")
        return True
    if not sys.stdin.isatty():
        print("Non-interactive stdin: set LIQUIDATE_CONFIRM=CONFIRM or pipe CONFIRM on first line.", file=sys.stderr)
        return False
    typed = input('Type CONFIRM to liquidate all equities: ')
    return typed.strip() == "CONFIRM"


def main() -> int:
    ap = argparse.ArgumentParser(description="Close all US equity positions (Alpaca).")
    ap.add_argument("--dry-run", action="store_true", help="List positions only.")
    ap.add_argument("--execute", action="store_true", help="Cancel orders and close equity positions.")
    ap.add_argument(
        "--allow-while-bot-running",
        action="store_true",
        help="Skip systemd active check (dangerous if main loop trades the same account).",
    )
    args = ap.parse_args()
    if not args.dry_run and not args.execute:
        print("Specify --dry-run or --execute", file=sys.stderr)
        return 2

    import alpaca_trade_api as tradeapi  # type: ignore

    from main import Config

    api = tradeapi.REST(Config.ALPACA_KEY, Config.ALPACA_SECRET, Config.ALPACA_BASE_URL, api_version="v2")
    raw = api.list_positions() or []
    targets = [p for p in raw if _is_us_equity_position(p)]
    print("POSITIONS_TOTAL", len(raw))
    print("EQUITY_CLOSE_TARGETS", len(targets))
    rows = []
    for p in targets:
        sym = getattr(p, "symbol", "")
        qty = getattr(p, "qty", 0)
        side = getattr(p, "side", "")
        rows.append({"symbol": sym, "qty": str(qty), "side": side})
    print("TARGETS_JSON", json.dumps(rows, indent=2))

    if args.dry_run:
        print("Dry run: no orders sent.")
        return 0

    if not args.allow_while_bot_running:
        active = _stock_bot_active()
        if active is True:
            print(
                "ERROR: stock-bot.service is active. Stop it first: sudo systemctl stop stock-bot.service\n"
                "Or re-run with --allow-while-bot-running if you accept the race risk.",
                file=sys.stderr,
            )
            return 3
        if active is None:
            print("WARN: Could not determine stock-bot.service state; proceeding.")

    if not _confirm():
        print("Aborted (confirmation not received).", file=sys.stderr)
        return 4

    try:
        api.cancel_all_orders()
        print("cancel_all_orders: ok")
    except Exception as e:
        print("cancel_all_orders:", str(e)[:300])

    results: List[Dict[str, Any]] = []
    for p in targets:
        sym = getattr(p, "symbol", "")
        if not sym:
            continue
        try:
            try:
                api.close_position(sym, cancel_orders=True)
            except TypeError:
                api.close_position(sym)
            results.append({"symbol": sym, "ok": True, "error": None})
            print("CLOSED", sym)
        except Exception as e:
            results.append({"symbol": sym, "ok": False, "error": str(e)[:500]})
            print("CLOSE_FAIL", sym, str(e)[:200])
        time.sleep(0.35)

    time.sleep(2.0)
    remaining = [p for p in (api.list_positions() or []) if _is_us_equity_position(p)]
    print("REMAINING_EQUITY_COUNT", len(remaining))
    if remaining:
        for p in remaining:
            print("REMAINING", getattr(p, "symbol", ""), getattr(p, "qty", ""))
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    out_dir = REPO / "reports" / "daily" / datetime.now(timezone.utc).strftime("%Y-%m-%d") / "evidence"
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        ev = out_dir / f"LIQUIDATE_LEGACY_EQUITIES_{ts}.json"
        ev.write_text(
            json.dumps(
                {"utc": ts, "results": results, "remaining": [getattr(x, "symbol", "") for x in remaining]},
                indent=2,
            ),
            encoding="utf-8",
        )
        print("EVIDENCE_JSON", str(ev))
    except Exception as e:
        print("EVIDENCE_WRITE_SKIPPED", str(e)[:200])

    return 0 if not remaining else 5


if __name__ == "__main__":
    raise SystemExit(main())
