#!/usr/bin/env python3
"""
One-shot SRE backfill: strict gate ghost trade repair.

Trade: open_TSLA_2026-04-15T15:50:19.641173+00:00
Authoritative join key (matches alpaca_exit_attribution + exit orders): TSLA|LONG|1776268116

Appends:
  - trade_intent(entered) to logs/run.jsonl
  - alpaca_entry_attribution to logs/alpaca_unified_events.jsonl

Run on droplet:
  cd /root/stock-bot && PYTHONPATH=/root/stock-bot python3 scripts/_tmp_tsla_intent_repair.py
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--root", default="/root/stock-bot", help="Repo root")
    args = p.parse_args()
    root = Path(args.root).resolve()
    run_path = root / "logs" / "run.jsonl"
    uni_path = root / "logs" / "alpaca_unified_events.jsonl"

    trade_id = "open_TSLA_2026-04-15T15:50:19.641173+00:00"
    ct = "TSLA|LONG|1776268116"
    sym = "TSLA"
    entry_ts = "2026-04-15T15:50:19.641173+00:00"
    now = datetime.now(timezone.utc).isoformat()

    trade_intent = {
        "ts": now,
        "event_type": "trade_intent",
        "symbol": sym,
        "side": "buy",
        "score": 3.9672,
        "decision_outcome": "entered",
        "blocked_reason": None,
        "canonical_trade_id": ct,
        "trade_key": ct,
        "trade_id": trade_id,
        "entry_intent_synthetic": True,
        "entry_intent_source": "sre_strict_backfill",
        "displacement_context": {"kind": "ghost_trade_repair", "reason": "strict_gate_TSLA_20260415"},
        "strategy_id": "equity",
    }

    entry_unified = {
        "event_type": "alpaca_entry_attribution",
        "schema_version": "1.2.0",
        "trade_id": trade_id,
        "trade_key": ct,
        "symbol": sym,
        "timestamp": entry_ts,
        "side": "LONG",
        "raw_signals": {"close_chain": 1.0},
        "weights": {"close_chain": 1.0},
        "contributions": {"close_chain": 1.0},
        "composite_score": 3.9672,
        "entry_dominant_component": "close_chain",
        "entry_dominant_component_value": 1.0,
        "entry_margin_to_threshold": None,
        "gates": {
            "lead_gate": {"pass": None, "reason": ""},
            "exhaustion_gate": {"pass": None, "reason": ""},
            "funding_veto": {"pass": None, "reason": ""},
            "whitelist": {"pass": None, "reason": ""},
            "regime_gate": {"pass": None, "reason": ""},
            "score_threshold": {"pass": None, "reason": ""},
            "cooldown": {"pass": None, "reason": ""},
            "position_exists": {"pass": None, "reason": ""},
        },
        "decision": "OPEN_LONG",
        "decision_reason": "SRE_strict_gate_backfill_20260415",
        "schema_role": "strict_chain_manual_backfill",
        "is_repair_row": True,
        "canonical_trade_id": ct,
        "fees_usd": 0.0,
    }

    run_path.parent.mkdir(parents=True, exist_ok=True)
    uni_path.parent.mkdir(parents=True, exist_ok=True)
    with run_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(trade_intent, separators=(",", ":")) + "\n")
    with uni_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry_unified, separators=(",", ":")) + "\n")
    print("appended_ok", ct, str(run_path), str(uni_path))


if __name__ == "__main__":
    main()
