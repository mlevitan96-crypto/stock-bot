#!/usr/bin/env python3
"""
One-time operational reset:
- Flatten all Alpaca positions (market close)
- Reset internal position state files

This is NOT a strategy change. It uses existing bot primitives (AlpacaExecutor + log_event).
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_dotenv_if_present(env_path: Path) -> None:
    """Minimal .env loader (no external deps)."""
    try:
        if not env_path.exists():
            return
        for raw in env_path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip("'").strip('"')
            if k and k not in os.environ:
                os.environ[k] = v
    except Exception:
        # Best-effort: env is often already supplied via systemd_start.sh
        return


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fmt_money(x: Any) -> str:
    try:
        return f"{float(x):,.2f}"
    except Exception:
        return str(x)


@dataclass(frozen=True)
class PositionRow:
    symbol: str
    qty: int
    side: str
    market_value: float
    unrealized_pl: float


def _pos_to_row(p: Any) -> PositionRow:
    symbol = str(getattr(p, "symbol", "") or "")
    qty_raw = getattr(p, "qty", 0)
    qty = int(float(qty_raw)) if qty_raw is not None else 0
    side = "long" if qty > 0 else "short"
    mv = float(getattr(p, "market_value", 0.0) or 0.0)
    upl = float(getattr(p, "unrealized_pl", 0.0) or 0.0)
    return PositionRow(symbol=symbol, qty=abs(qty), side=side, market_value=mv, unrealized_pl=upl)


def _print_positions_table(rows: List[PositionRow]) -> None:
    print("")
    print("symbol | qty | side | market_value | unrealized_pl")
    print("------ | --- | ---- | ------------ | -------------")
    for r in rows:
        print(
            f"{r.symbol} | {r.qty} | {r.side} | {_fmt_money(r.market_value)} | {_fmt_money(r.unrealized_pl)}"
        )
    print("")


def _atomic_write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def _reset_state_files(*, state_files: List[Path], log_event) -> int:
    cleared = 0
    for p in state_files:
        try:
            # Use empty dict as the safest "no state" representation.
            _atomic_write_json(p, {})
            cleared += 1
        except Exception as e:
            try:
                log_event("state_reset", "position_state_clear_failed", path=str(p), error=str(e))
            except Exception:
                pass
    try:
        log_event("state_reset", "position_state_cleared", files=[str(p) for p in state_files], cleared=cleared)
    except Exception:
        pass
    return cleared


def _count_internal_positions(path: Path) -> int:
    try:
        if not path.exists():
            return 0
        data = json.loads(path.read_text(encoding="utf-8") or "{}")
        if isinstance(data, dict) and isinstance(data.get("positions"), list):
            return int(len(data["positions"]))
        if isinstance(data, dict):
            # position_metadata.json is a dict keyed by symbol
            return int(len(data))
    except Exception:
        return 0
    return 0


def flatten_and_reset(*, timeout_sec: int = 60) -> int:
    os.chdir(REPO_ROOT)
    _load_dotenv_if_present(REPO_ROOT / ".env")

    # Import bot primitives after cwd/env is set.
    import main as bot_main  # noqa: PLC0415
    from config.registry import StateFiles  # noqa: PLC0415

    log_event = bot_main.log_event
    AlpacaExecutor = bot_main.AlpacaExecutor

    log_event("state_reset", "forced_flatten_start", ts=_now_iso(), timeout_sec=timeout_sec)

    executor = AlpacaExecutor(defer_reconcile=True)
    try:
        positions = executor.api.list_positions() or []
    except Exception as e:
        log_event("state_reset", "forced_flatten_list_positions_failed", error=str(e))
        positions = []

    rows = [_pos_to_row(p) for p in positions if getattr(p, "symbol", None)]
    rows.sort(key=lambda r: r.symbol)
    print(f"[{_now_iso()}] Open positions: {len(rows)}")
    _print_positions_table(rows)

    # Best-effort cancel all open orders first (reduces reserved-qty failures).
    try:
        executor.api.cancel_all_orders()
        log_event("exit", "forced_flatten_cancel_all_orders")
    except Exception as e:
        log_event("exit", "forced_flatten_cancel_all_orders_failed", error=str(e))

    # Submit closes.
    for r in rows:
        qty_signed = r.qty if r.side == "long" else -r.qty
        for attempt in range(1, 4):
            try:
                try:
                    close_order = executor.api.close_position(r.symbol, cancel_orders=True)
                except TypeError:
                    close_order = executor.api.close_position(r.symbol)
                oid = getattr(close_order, "id", None)
                log_event(
                    "exit",
                    "forced_flatten",
                    symbol=r.symbol,
                    qty=qty_signed,
                    attempt=attempt,
                    order_id=str(oid) if oid else None,
                )
                break
            except Exception as e:
                log_event(
                    "exit",
                    "forced_flatten",
                    symbol=r.symbol,
                    qty=qty_signed,
                    attempt=attempt,
                    error=str(e),
                )
                if attempt < 3:
                    time.sleep(float(2**attempt))

    # Poll until flat or timeout.
    start = time.time()
    last_poll_log = 0.0
    remaining = []
    while (time.time() - start) < float(timeout_sec):
        try:
            remaining = executor.api.list_positions() or []
        except Exception as e:
            log_event("exit", "forced_flatten_poll_failed", error=str(e))
            remaining = []

        if not remaining:
            break

        now = time.time()
        if (now - last_poll_log) >= 5.0:
            last_poll_log = now
            try:
                syms = [str(getattr(p, "symbol", "")) for p in remaining]
            except Exception:
                syms = []
            log_event("exit", "forced_flatten_poll", remaining=len(remaining), symbols=syms[:50])
        time.sleep(2.0)

    success = not remaining
    log_event(
        "exit",
        "forced_flatten_complete",
        success=bool(success),
        remaining=int(len(remaining or [])),
        timeout_sec=timeout_sec,
    )

    # Reset internal state files (minimal set tied to position tracking).
    # NOTE: open_positions.json is not used in this repo, but we clear it if present.
    state_files: List[Path] = [
        Path(StateFiles.POSITION_METADATA),
        Path(StateFiles.INTERNAL_POSITIONS),
        Path(StateFiles.DISPLACEMENT_COOLDOWNS),
        REPO_ROOT / "state" / "open_positions.json",
    ]
    _reset_state_files(state_files=state_files, log_event=log_event)

    # Verification: Alpaca positions should be empty.
    try:
        final_positions = executor.api.list_positions() or []
    except Exception:
        final_positions = []

    alpaca_positions_count = int(len(final_positions))
    internal_positions_count = _count_internal_positions(Path(StateFiles.POSITION_METADATA))

    print("=== FLATTEN + STATE RESET CONFIRMATION ===")
    print(f"timestamp_utc: {_now_iso()}")
    print(f"alpaca_positions_count: {alpaca_positions_count}")
    print(f"internal_positions_count: {internal_positions_count}")
    print(f"success: {success and alpaca_positions_count == 0 and internal_positions_count == 0}")

    log_event(
        "state_reset",
        "forced_flatten_verification",
        timestamp=_now_iso(),
        alpaca_positions_count=alpaca_positions_count,
        internal_positions_count=internal_positions_count,
    )

    return 0 if (alpaca_positions_count == 0 and internal_positions_count == 0) else 2


def main() -> int:
    try:
        timeout_sec = int(os.getenv("FORCED_FLATTEN_TIMEOUT_SEC", "60"))
    except Exception:
        timeout_sec = 60
    return int(flatten_and_reset(timeout_sec=timeout_sec))


if __name__ == "__main__":
    raise SystemExit(main())

