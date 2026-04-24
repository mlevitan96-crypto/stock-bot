#!/usr/bin/env python3
"""
Write a minimal strict-complete log tree for one NYSE session date (synthetic DEMO cohort).

Used to prove market-session PnL pipeline in CI/workspace without droplet SSH.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _trade_bundle(symbol: str, entry_iso: str, exit_iso: str, pnl: float, ep: float, ip: float, qty: float) -> dict:
    sys.path.insert(0, str(REPO))
    from src.telemetry.alpaca_trade_key import build_trade_key

    tk = build_trade_key(symbol, "LONG", entry_iso)
    trade_id = f"open_{symbol}_{entry_iso}"
    unified = [
        {
            "event_type": "alpaca_entry_attribution",
            "trade_key": tk,
            "canonical_trade_id": tk,
            "symbol": symbol,
        },
        {
            "event_type": "alpaca_exit_attribution",
            "trade_id": trade_id,
            "terminal_close": True,
            "trade_key": tk,
            "canonical_trade_id": tk,
            "symbol": symbol,
        },
    ]
    orders = [
        {"type": "order", "symbol": symbol, "canonical_trade_id": tk, "action": "buy", "qty": qty},
        {"type": "order", "symbol": symbol, "canonical_trade_id": tk, "action": "close_position", "qty": qty},
    ]
    run_recs = [
        {
            "event_type": "trade_intent",
            "symbol": symbol,
            "decision_outcome": "entered",
            "canonical_trade_id": tk,
        },
        {"event_type": "exit_intent", "symbol": symbol, "canonical_trade_id": tk},
    ]
    ex = {
        "trade_id": trade_id,
        "symbol": symbol,
        "side": "long",
        "timestamp": exit_iso,
        "entry_timestamp": entry_iso,
        "exit_reason": "demo_session_fixture",
        "pnl": pnl,
        "exit_price": ep,
        "entry_price": ip,
        "qty": qty,
    }
    return {
        "unified_lines": unified,
        "orders_lines": orders,
        "run_lines": run_recs,
        "exit_line": ex,
        "trade_id": trade_id,
        "trade_key": tk,
    }


def write_fixture(root: Path) -> list[str]:
    root = root.resolve()
    logs = root / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    bundles = [
        _trade_bundle("MKT1", "2026-03-26T14:00:00+00:00", "2026-03-26T17:00:00+00:00", 10.0, 101.0, 100.0, 10.0),
        _trade_bundle("MKT2", "2026-03-26T15:30:00+00:00", "2026-03-26T17:45:00+00:00", -2.5, 99.5, 100.0, 5.0),
    ]
    unified_all = []
    orders_all = []
    run_all = []
    exits_all = []
    tids = []
    for b in bundles:
        unified_all.extend(b["unified_lines"])
        orders_all.extend(b["orders_lines"])
        run_all.extend(b["run_lines"])
        exits_all.append(b["exit_line"])
        tids.append(b["trade_id"])
    (logs / "alpaca_unified_events.jsonl").write_text(
        "\n".join(json.dumps(x) for x in unified_all) + "\n", encoding="utf-8"
    )
    (logs / "orders.jsonl").write_text("\n".join(json.dumps(x) for x in orders_all) + "\n", encoding="utf-8")
    (logs / "run.jsonl").write_text("\n".join(json.dumps(x) for x in run_all) + "\n", encoding="utf-8")
    (logs / "exit_attribution.jsonl").write_text("\n".join(json.dumps(x) for x in exits_all) + "\n", encoding="utf-8")
    (root / "main.py").write_text("# production-shaped main\n", encoding="utf-8")
    return tids


def main() -> int:
    ap_root = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "artifacts" / "alpaca_pnl_session_et_20260326"
    tids = write_fixture(ap_root)
    print(json.dumps({"root": str(ap_root), "trade_ids": tids}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
