#!/usr/bin/env python3
"""
Lab-only: write synthetic logs under synthetic_lab_root/ for strict completeness proof.
Does not touch main.py, config, or live trading. Not imported by the engine.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

EVIDENCE = Path(__file__).resolve().parent
ROOT = EVIDENCE / "synthetic_lab_root"
REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

from src.telemetry.alpaca_trade_key import build_trade_key  # noqa: E402


def _bundle(
    symbol: str,
    side: str,
    entry_iso: str,
    exit_iso: str,
    pnl: float,
    ep: float,
    ip: float,
    qty: float,
    score: float,
) -> dict:
    tk = build_trade_key(symbol, side, entry_iso)
    trade_id = f"open_{symbol}_{entry_iso}"
    pos_side = "long" if side == "LONG" else "short"
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
        {"type": "order", "symbol": symbol, "canonical_trade_id": tk, "action": "buy" if side == "LONG" else "sell", "qty": qty},
        {"type": "order", "symbol": symbol, "canonical_trade_id": tk, "action": "close_position", "qty": qty},
    ]
    run_recs = [
        {
            "event_type": "trade_intent",
            "symbol": symbol,
            "decision_outcome": "entered",
            "canonical_trade_id": tk,
            "decision_event_id": f"de_{symbol}_lab",
        },
        {
            "event_type": "exit_intent",
            "symbol": symbol,
            "canonical_trade_id": tk,
            "timestamp": exit_iso,
        },
    ]
    ex = {
        "trade_id": trade_id,
        "symbol": symbol,
        "side": pos_side,
        "timestamp": exit_iso,
        "entry_timestamp": entry_iso,
        "exit_reason": "synthetic_lab_close",
        "pnl": pnl,
        "exit_price": ep,
        "entry_price": ip,
        "qty": qty,
        "snapshot": {"pnl": pnl},
    }
    sig_ctx = [
        {
            "timestamp": entry_iso,
            "symbol": symbol,
            "mode": "enter",
            "decision": "entered",
            "decision_reason": "synthetic_lab",
            "final_score": score,
            "threshold": 2.5,
            "signals": {"position_side": pos_side, "direction": "bullish" if side == "LONG" else "bearish"},
            "canonical_trade_id": tk,
        },
        {
            "timestamp": exit_iso,
            "symbol": symbol,
            "mode": "exit",
            "decision": "exit",
            "decision_reason": "synthetic_lab",
            "pnl_usd": pnl,
            "final_score": score,
            "signals": {"position_side": pos_side},
            "canonical_trade_id": tk,
        },
    ]
    return {
        "unified_lines": unified,
        "orders_lines": orders,
        "run_lines": run_recs,
        "exit_line": ex,
        "signal_lines": sig_ctx,
    }


def main() -> int:
    logs = ROOT / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    # Monday 2026-03-30 RTH (EDT): 9:45 ET -> 13:45Z, exit 14:30 ET -> 18:30Z (long); short similar window
    b_long = _bundle(
        "LABL",
        "LONG",
        "2026-03-30T13:45:00+00:00",
        "2026-03-30T18:30:00+00:00",
        12.34,
        102.0,
        100.0,
        5.0,
        3.1,
    )
    b_short = _bundle(
        "LABS",
        "SHORT",
        "2026-03-30T14:00:00+00:00",
        "2026-03-30T18:45:00+00:00",
        -4.2,
        50.5,
        51.0,
        10.0,
        2.8,
    )
    unified_all = b_long["unified_lines"] + b_short["unified_lines"]
    orders_all = b_long["orders_lines"] + b_short["orders_lines"]
    run_all = b_long["run_lines"] + b_short["run_lines"]
    exits_all = [b_long["exit_line"], b_short["exit_line"]]
    sig_all = b_long["signal_lines"] + b_short["signal_lines"]

    (logs / "alpaca_unified_events.jsonl").write_text(
        "\n".join(json.dumps(x) for x in unified_all) + "\n", encoding="utf-8"
    )
    (logs / "orders.jsonl").write_text("\n".join(json.dumps(x) for x in orders_all) + "\n", encoding="utf-8")
    (logs / "run.jsonl").write_text("\n".join(json.dumps(x) for x in run_all) + "\n", encoding="utf-8")
    (logs / "exit_attribution.jsonl").write_text("\n".join(json.dumps(x) for x in exits_all) + "\n", encoding="utf-8")
    (logs / "signal_context.jsonl").write_text("\n".join(json.dumps(x) for x in sig_all) + "\n", encoding="utf-8")
    # Minimal main.py — must NOT match structural anti-pattern in strict gate
    (ROOT / "main.py").write_text("# synthetic lab root — not production main\n", encoding="utf-8")
    print(json.dumps({"root": str(ROOT), "trades": 2}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
