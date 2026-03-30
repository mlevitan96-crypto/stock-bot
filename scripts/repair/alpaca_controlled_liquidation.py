#!/usr/bin/env python3
"""
Controlled full liquidation of all Alpaca positions (equity bot repair).

Usage (repo root):
  python3 scripts/repair/alpaca_controlled_liquidation.py --dry-run
  python3 scripts/repair/alpaca_controlled_liquidation.py --execute

Writes evidence markdown path via --evidence-md (optional) or prints JSON summary.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

REPO = Path(__file__).resolve().parent.parent.parent
os.chdir(REPO)
sys.path.insert(0, str(REPO))

from dotenv import load_dotenv  # type: ignore

load_dotenv(REPO / ".env")


def _et_date() -> str:
    import subprocess

    try:
        r = subprocess.run(
            ["bash", "-lc", "TZ=America/New_York date +%Y-%m-%d"],
            cwd=str(REPO),
            capture_output=True,
            text=True,
            timeout=15,
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except Exception:
        pass
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--evidence-md", type=str, default="", help="Path to write ALPACA_FULL_LIQUIDATION_*.md")
    args = ap.parse_args()
    if not args.dry_run and not args.execute:
        print("Specify --dry-run or --execute", file=sys.stderr)
        return 2

    import alpaca_trade_api as tradeapi  # type: ignore

    from config.registry import StateFiles, atomic_write_json
    from main import Config

    api = tradeapi.REST(Config.ALPACA_KEY, Config.ALPACA_SECRET, Config.ALPACA_BASE_URL)
    positions = api.list_positions() or []

    rows: List[Dict[str, Any]] = []
    for p in positions:
        sym = getattr(p, "symbol", "")
        qty = getattr(p, "qty", 0)
        cur = getattr(p, "current_price", 0)
        entry = getattr(p, "avg_entry_price", 0)
        upl = getattr(p, "unrealized_pl", 0)
        rows.append(
            {
                "symbol": sym,
                "qty": qty,
                "current_price": float(cur) if cur else None,
                "avg_entry_price": float(entry) if entry else None,
                "unrealized_pl": float(upl) if upl else None,
            }
        )

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    lines: List[str] = []
    lines.append("# ALPACA CONTROLLED FULL LIQUIDATION\n\n")
    lines.append(f"- UTC `{ts}`\n")
    lines.append(f"- Mode: **`{'EXECUTE' if args.execute else 'DRY_RUN'}`**\n\n")
    lines.append(f"- Positions before: **{len(rows)}**\n\n")
    lines.append("## Intended closes\n\n")
    lines.append("```json\n" + json.dumps(rows, indent=2) + "\n```\n\n")

    results: List[Dict[str, Any]] = []
    if args.execute:
        try:
            api.cancel_all_orders()
            lines.append("## Pre-close\n\nCalled `cancel_all_orders()` (best effort).\n\n")
        except Exception as e:
            lines.append(f"## Pre-close\n\n`cancel_all_orders` skipped/failed: `{str(e)[:200]}`\n\n")

        for p in positions:
            sym = getattr(p, "symbol", "")
            if not sym:
                continue
            try:
                try:
                    api.close_position(sym, cancel_orders=True)
                except TypeError:
                    # Older alpaca_trade_api builds omit cancel_orders
                    api.close_position(sym)
                results.append({"symbol": sym, "ok": True, "error": None})
            except Exception as e:
                results.append({"symbol": sym, "ok": False, "error": str(e)[:500]})
            time.sleep(0.35)
        lines.append("## close_position results\n\n```json\n")
        lines.append(json.dumps(results, indent=2))
        lines.append("\n```\n\n")

        # Poll until flat (fills can lag, especially off-hours)
        max_poll = 40
        poll_interval = 3.0
        remaining: List[Any] = []
        for i in range(max_poll):
            remaining = api.list_positions() or []
            if not remaining:
                break
            time.sleep(poll_interval)
        lines.append(f"## Positions after (verify, up to {max_poll}×{poll_interval:.0f}s)\n\n")
        lines.append(f"**{len(remaining)}** open (poll rounds: {i + 1})\n\n")
        lines.append("```json\n" + json.dumps([getattr(x, "symbol", "") for x in remaining], indent=2) + "\n```\n")

        meta_path = REPO / StateFiles.POSITION_METADATA
        backup = meta_path.with_suffix(f".pre_liquidation.{ts}.json")
        if not remaining:
            if meta_path.exists():
                try:
                    backup.write_text(meta_path.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
                except Exception:
                    pass
            atomic_write_json(meta_path, {})
            lines.append(
                "\n## position_metadata.json\n\nReset to `{}`; backup at `" + backup.name + "`\n"
            )
        else:
            lines.append(
                "\n## position_metadata.json\n\n**Not cleared** — positions still open after poll. "
                "Fix close errors and re-run.\n"
            )
    else:
        lines.append("## DRY RUN — no orders sent\n")

    md = "".join(lines)
    out_path = args.evidence_md
    if not out_path:
        ev = REPO / "reports" / "daily" / _et_date() / "evidence"
        ev.mkdir(parents=True, exist_ok=True)
        out_path = str(ev / f"ALPACA_FULL_LIQUIDATION_{ts}.md")
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(md, encoding="utf-8")
    remaining_n = 0
    if args.execute:
        try:
            remaining_n = len(api.list_positions() or [])
        except Exception:
            remaining_n = -1
    print(
        json.dumps(
            {
                "evidence_md": out_path,
                "positions_before": len(rows),
                "executed": bool(args.execute),
                "positions_after": remaining_n if args.execute else None,
                "flat": bool(args.execute and remaining_n == 0),
            },
            indent=2,
        )
    )
    if args.execute and remaining_n != 0:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
