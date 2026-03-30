#!/usr/bin/env python3
"""Phase 1 snapshot for Alpaca full repair — writes ALPACA_FULL_REPAIR_SNAPSHOT_<TS>.md"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
os.chdir(REPO)
sys.path.insert(0, str(REPO))

from dotenv import load_dotenv  # type: ignore

load_dotenv(REPO / ".env")


def _et_date() -> str:
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


def tail(path: Path, n: int) -> str:
    if not path.exists():
        return f"(missing) {path}\n"
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    chunk = lines[-n:] if len(lines) > n else lines
    return "\n".join(chunk) + ("\n" if chunk else "")


def main() -> int:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    et = _et_date()
    ev = REPO / "reports" / "daily" / et / "evidence"
    ev.mkdir(parents=True, exist_ok=True)
    out = ev / f"ALPACA_FULL_REPAIR_SNAPSHOT_{ts}.md"

    import alpaca_trade_api as tradeapi  # type: ignore

    from main import Config

    api = tradeapi.REST(Config.ALPACA_KEY, Config.ALPACA_SECRET, Config.ALPACA_BASE_URL)
    pos = api.list_positions() or []
    acct = api.get_account()
    pos_rows = [
        {
            "symbol": getattr(p, "symbol", ""),
            "qty": getattr(p, "qty", ""),
            "avg_entry": getattr(p, "avg_entry_price", ""),
            "current": getattr(p, "current_price", ""),
            "unrealized_pl": getattr(p, "unrealized_pl", ""),
        }
        for p in pos
    ]

    parts: list[str] = []
    parts.append(f"# ALPACA FULL REPAIR SNAPSHOT\n\n- UTC `{ts}` ET `{et}`\n\n")
    parts.append("## Alpaca account\n\n```json\n")
    parts.append(
        json.dumps(
            {"equity": float(getattr(acct, "equity", 0)), "cash": float(getattr(acct, "cash", 0) or 0)},
            indent=2,
        )
    )
    parts.append("\n```\n\n## Positions\n\n```json\n" + json.dumps(pos_rows, indent=2) + "\n```\n")

    logd = REPO / "logs"
    for label, rel, n in [
        ("run.jsonl", "run.jsonl", 500),
        ("exit.jsonl", "exit.jsonl", 500),
        ("scoring_flow.jsonl", "scoring_flow.jsonl", 500),
        ("uw_attribution.jsonl", "uw_attribution.jsonl", 500),
        ("freeze.jsonl", "freeze.jsonl", 500),
    ]:
        parts.append(f"\n## Last {n} — {label}\n\n```\n")
        parts.append(tail(logd / rel, n))
        parts.append("\n```\n")

    for title, rel in [
        ("position_metadata.json", "state/position_metadata.json"),
        ("peak_equity.json", "state/peak_equity.json"),
        ("signal_strength_cache.json", "state/signal_strength_cache.json"),
        ("governor_freezes.json", "state/governor_freezes.json"),
    ]:
        p = REPO / rel
        parts.append(f"\n## {title}\n\n")
        if p.exists():
            raw = p.read_text(encoding="utf-8", errors="replace")
            if len(raw) > 60000:
                parts.append(f"(truncated)\n\n```json\n{raw[:60000]}\n```\n")
            else:
                parts.append(f"```json\n{raw}\n```\n")
        else:
            parts.append("(missing)\n")

    out.write_text("".join(parts), encoding="utf-8")
    print(json.dumps({"wrote": str(out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
