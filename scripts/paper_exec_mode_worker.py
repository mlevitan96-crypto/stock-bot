#!/usr/bin/env python3
"""
Paper-only worker: process state/paper_exec_pending.jsonl (PASSIVE_THEN_CROSS TTL + cross).

smoke_only synthetic rows need no Alpaca (processed first). Real rows require strict paper gateway.

Usage:
  PYTHONPATH=. python3 scripts/paper_exec_mode_worker.py --root /root/stock-bot --once
  PYTHONPATH=. python3 scripts/paper_exec_mode_worker.py --root /root/stock-bot --loop --sleep-sec 15
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Set, Tuple

REPO = Path(__file__).resolve().parents[2]


def _parse_ts_iso(s: str) -> Optional[datetime]:
    if not s:
        return None
    try:
        x = str(s).strip()
        if x.endswith("Z"):
            x = x[:-1] + "+00:00"
        return datetime.fromisoformat(x.replace(" ", "T")[:32]).astimezone(timezone.utc)
    except Exception:
        return None


def bar_touch_would_fill(
    api: Any,
    symbol: str,
    side: str,
    limit_px: float,
    window_start: datetime,
    window_end: datetime,
) -> Tuple[bool, Optional[str]]:
    try:
        raw = api.get_bars(symbol, "1Min", limit=120)
        df = getattr(raw, "df", None)
        if df is None or len(df) == 0:
            return False, None
        is_buy = str(side).lower() == "buy"
        for idx, row in df.iterrows():
            ts = idx.to_pydatetime() if hasattr(idx, "to_pydatetime") else idx
            if getattr(ts, "tzinfo", None) is None:
                ts = ts.replace(tzinfo=timezone.utc)
            else:
                ts = ts.astimezone(timezone.utc)
            if ts < window_start or ts > window_end:
                continue
            lo, hi = float(row["low"]), float(row["high"])
            if is_buy and lo <= float(limit_px) + 1e-9:
                return True, ts.isoformat()
            if not is_buy and hi >= float(limit_px) - 1e-9:
                return True, ts.isoformat()
        return False, None
    except Exception:
        return False, None


def _process_smoke_only(row: Dict[str, Any], done_keys: Set[str]) -> bool:
    pk = str(row.get("pretrade_key") or "")
    if not pk or pk in done_keys:
        return False
    if not (row.get("smoke_only") and row.get("synthetic")):
        return False
    from src.paper.paper_exec_mode_runtime import append_paper_exec_decision, append_paper_exec_done

    ts0 = row.get("ts") or datetime.now(timezone.utc).isoformat()
    append_paper_exec_decision(
        {
            "ts": ts0,
            "symbol": row.get("symbol"),
            "side": row.get("side"),
            "mode": "PASSIVE_THEN_CROSS",
            "ab_arm": "B",
            "ttl": row.get("ttl_minutes"),
            "decision_price_ref": row.get("decision_price_ref") or "synthetic_smoke",
            "fill_model": "synthetic_smoke",
            "fill_ts": datetime.now(timezone.utc).isoformat(),
            "fill_price": float(row.get("limit_px") or 0) or None,
            "cross_event": False,
            "pretrade_key": pk,
            "worker": "paper_exec_mode_worker",
        }
    )
    append_paper_exec_done({"pretrade_key": pk, "ts": datetime.now(timezone.utc).isoformat(), "outcome": "smoke"})
    done_keys.add(pk)
    return True


def _process_broker_row(
    row: Dict[str, Any],
    executor: Any,
    done_keys: Set[str],
    *,
    now: float,
) -> bool:
    pk = str(row.get("pretrade_key") or "")
    if not pk or pk in done_keys:
        return False

    oid = row.get("order_id")
    if not oid:
        return False

    sym = str(row.get("symbol") or "").upper()
    side = str(row.get("side") or "buy")
    limit_px = float(row.get("limit_px") or 0)
    ttl = int(row.get("ttl_minutes") or 3)
    cob = str(row.get("client_order_id_base") or "pexec")[:48]
    enq = _parse_ts_iso(str(row.get("enqueued_ts") or row.get("ts") or ""))
    if enq is None:
        enq = datetime.now(timezone.utc)
    deadline = float(row.get("deadline_epoch") or (enq.timestamp() + ttl * 60))

    from src.paper.paper_exec_mode_runtime import append_paper_exec_decision, append_paper_exec_done

    win_end = datetime.fromtimestamp(deadline, tz=timezone.utc)
    bar_fill, bar_ts = bar_touch_would_fill(executor.api, sym, side, limit_px, enq, win_end)

    filled, fq, fp = executor.check_order_filled(str(oid), max_wait_sec=2.0)
    if filled and fq > 0 and fp and float(fp) > 0:
        append_paper_exec_decision(
            {
                "ts": row.get("ts"),
                "symbol": sym,
                "side": side,
                "mode": "PASSIVE_THEN_CROSS",
                "ab_arm": "B",
                "ttl": ttl,
                "decision_price_ref": row.get("decision_price_ref"),
                "decision_close": limit_px,
                "fill_model": "P2_passive",
                "fill_ts": datetime.now(timezone.utc).isoformat(),
                "fill_price": float(fp),
                "cross_event": False,
                "pretrade_key": pk,
                "bar_sim_would_fill": bar_fill,
                "bar_sim_touch_ts": bar_ts,
                "worker": "paper_exec_mode_worker",
            }
        )
        append_paper_exec_done({"pretrade_key": pk, "ts": datetime.now(timezone.utc).isoformat(), "outcome": "passive_filled"})
        done_keys.add(pk)
        return True

    if now < deadline:
        return False

    try:
        executor.api.cancel_order(str(oid))
    except Exception:
        pass

    q_submit = max(1, int(round(float(row.get("qty") or 1))))
    mkt_cid = f"{cob}-pexec-mkt-w{int(now)}"
    o2 = executor._submit_order_guarded(
        symbol=sym,
        qty=q_submit,
        side=side,
        order_type="market",
        time_in_force="day",
        client_order_id=mkt_cid[:48],
        caller="paper_exec_mode_worker:cross_market",
        extended_hours=False,
    )
    oid2 = getattr(o2, "id", None) if o2 is not None else None
    fill_ts = datetime.now(timezone.utc).isoformat()
    fill_price = None
    cross_ok = False
    if oid2:
        f2, fq2, fp2 = executor.check_order_filled(str(oid2), max_wait_sec=20.0)
        if f2 and fq2 > 0 and fp2 and float(fp2) > 0:
            fill_price = float(fp2)
            cross_ok = True

    append_paper_exec_decision(
        {
            "ts": row.get("ts"),
            "symbol": sym,
            "side": side,
            "mode": "PASSIVE_THEN_CROSS",
            "ab_arm": "B",
            "ttl": ttl,
            "decision_price_ref": row.get("decision_price_ref"),
            "decision_close": limit_px,
            "fill_model": "P2_cross_market",
            "fill_ts": fill_ts,
            "fill_price": fill_price,
            "cross_event": True,
            "pretrade_key": pk,
            "bar_sim_would_fill": bar_fill,
            "bar_sim_touch_ts": bar_ts,
            "cross_submit_ok": cross_ok,
            "worker": "paper_exec_mode_worker",
        }
    )
    append_paper_exec_done({"pretrade_key": pk, "ts": datetime.now(timezone.utc).isoformat(), "outcome": "cross_or_timeout"})
    done_keys.add(pk)
    return True


def run_batch(root: Path) -> int:
    os.chdir(root)
    sys.path.insert(0, str(root))
    if (root / ".env").is_file():
        try:
            from dotenv import load_dotenv

            load_dotenv(root / ".env")
        except Exception:
            pass

    from main import AlpacaExecutor, Config
    from src.paper.paper_exec_mode_runtime import load_done_pretrade_keys, load_pending_rows, strict_paper_gateway

    done_keys = load_done_pretrade_keys()
    pending = load_pending_rows()
    now = time.time()
    n_smoke = 0
    for row in pending:
        if _process_smoke_only(row, done_keys):
            n_smoke += 1

    rest = [r for r in pending if not (r.get("smoke_only") and r.get("synthetic"))]
    if not rest:
        print(json.dumps({"processed_smoke": n_smoke, "broker_skipped": True}))
        return 0

    if not strict_paper_gateway(Config):
        print("paper_exec_mode_worker: strict paper gateway FAILED for broker rows — exit 2", file=sys.stderr)
        return 2

    ex = AlpacaExecutor(defer_reconcile=True)
    n_broker = 0
    for row in rest:
        if _process_broker_row(row, ex, done_keys, now=now):
            n_broker += 1
    print(json.dumps({"processed_smoke": n_smoke, "processed_broker": n_broker, "pending_scanned": len(pending)}))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=REPO)
    ap.add_argument("--once", action="store_true", help="Single pass (default if --loop not set)")
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--sleep-sec", type=float, default=15.0)
    args = ap.parse_args()
    root = args.root.resolve()

    if args.loop:
        while True:
            rc = run_batch(root)
            if rc != 0:
                return rc
            time.sleep(max(3.0, float(args.sleep_sec)))
    return run_batch(root)


if __name__ == "__main__":
    raise SystemExit(main())
