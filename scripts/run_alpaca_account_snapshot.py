#!/usr/bin/env python3
"""
Alpaca account + PDT / wash-loss radar — read-only.

Pulls broker **account** state via ``alpaca_trade_api.REST.get_account()`` (no orders)
and scans ``logs/exit_attribution.jsonl`` for **loss exits** in the last **30** calendar days
to build a **wash_risk_watchlist** (re-entry within the IRS 30-day window can disallow a loss).

Does **not** modify ``main.py`` or the live router. Outputs:
  - ``state/alpaca_account_snapshot.json``
  - ``reports/audit/alpaca_compliance_health_<ts>.md``

Environment (same as bot):
  ALPACA_API_KEY / ALPACA_KEY, ALPACA_SECRET_KEY / ALPACA_SECRET / ALPACA_API_SECRET,
  ALPACA_BASE_URL (paper or live).

Usage (repo root):
  PYTHONPATH=. python3 scripts/run_alpaca_account_snapshot.py --root /root/stock-bot
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# Optional dotenv (same pattern as research_fetch_alpaca_bars)
for path, override in ((REPO / ".env", False), (Path.home() / ".alpaca_env", False)):
    if not path.is_file():
        continue
    try:
        from dotenv import load_dotenv

        load_dotenv(path, override=override)
    except Exception:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and (override or k not in os.environ):
                os.environ[k] = v


def _parse_ts(v: Any) -> Optional[datetime]:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        try:
            return datetime.fromtimestamp(float(v), tz=timezone.utc)
        except (OSError, ValueError, OverflowError):
            return None
    s = str(v).strip().replace("Z", "+00:00")
    if not s:
        return None
    try:
        d = datetime.fromisoformat(s)
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d.astimezone(timezone.utc)
    except Exception:
        return None


def _coerce_float(v: Any) -> Optional[float]:
    if v is None:
        return None
    try:
        x = float(v)
        if x != x:
            return None
        return x
    except (TypeError, ValueError):
        return None


def _exit_row_timestamp(row: Dict[str, Any]) -> Optional[datetime]:
    for k in ("exit_ts", "timestamp", "ts", "exit_timestamp"):
        if k in row and row[k]:
            dt = _parse_ts(row.get(k))
            if dt is not None:
                return dt
    return None


def _exit_row_pnl(row: Dict[str, Any]) -> Optional[float]:
    for k in ("realized_pnl_usd", "pnl", "realized_pnl"):
        if k in row:
            x = _coerce_float(row.get(k))
            if x is not None:
                return x
    return None


def _exit_row_symbol(row: Dict[str, Any]) -> str:
    s = row.get("symbol") or row.get("sym") or ""
    return str(s).upper().strip()


def _serialize_account(account: Any) -> Dict[str, Any]:
    """Best-effort dict from Alpaca Account entity (SDK version differences)."""
    keys = (
        "account_number",
        "status",
        "currency",
        "equity",
        "last_equity",
        "buying_power",
        "regt_buying_power",
        "daytrading_buying_power",
        "non_marginable_buying_power",
        "cash",
        "portfolio_value",
        "pattern_day_trader",
        "daytrade_count",
        "multiplier",
        "shorting_enabled",
        "trading_blocked",
        "account_blocked",
        "transfers_blocked",
        "trade_suspended_by_user",
        "long_market_value",
        "short_market_value",
        "initial_margin",
        "maintenance_margin",
        "last_maintenance_margin",
        "sma",
        "accrued_fees",
    )
    out: Dict[str, Any] = {}
    for k in keys:
        try:
            v = getattr(account, k, None)
        except Exception:
            v = None
        if v is not None:
            if isinstance(v, datetime):
                out[k] = v.astimezone(timezone.utc).isoformat()
            elif isinstance(v, (int, float, str, bool)):
                out[k] = v
            else:
                try:
                    out[k] = float(v)
                except (TypeError, ValueError):
                    out[k] = str(v)
    return out


def _build_alpaca_rest():
    key = os.getenv("ALPACA_API_KEY") or os.getenv("ALPACA_KEY") or os.getenv("APCA_API_KEY_ID", "")
    secret = (
        os.getenv("ALPACA_SECRET_KEY")
        or os.getenv("ALPACA_API_SECRET_KEY")
        or os.getenv("ALPACA_SECRET")
        or os.getenv("ALPACA_API_SECRET")
        or os.getenv("APCA_API_SECRET_KEY", "")
    )
    base = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets").strip()
    if not key or not secret:
        return None, "missing_alpaca_credentials"
    try:
        import alpaca_trade_api as tradeapi  # type: ignore

        return tradeapi.REST(key, secret, base, api_version="v2"), None
    except Exception as e:
        return None, f"import_or_rest_init_failed:{e}"


def _scan_loss_exits(
    exit_path: Path,
    *,
    since: datetime,
) -> Dict[str, Dict[str, Any]]:
    """
    Map symbol -> aggregate loss-exit info since ``since`` (UTC).
    Only rows with strictly negative realized PnL (wash-relevant loss).
    """
    agg: Dict[str, Dict[str, Any]] = {}
    if not exit_path.is_file():
        return agg
    with exit_path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(row, dict):
                continue
            ts = _exit_row_timestamp(row)
            if ts is None or ts < since:
                continue
            pnl = _exit_row_pnl(row)
            if pnl is None or pnl >= 0:
                continue
            sym = _exit_row_symbol(row)
            if not sym:
                continue
            prev = agg.get(sym)
            prev_ts = _parse_ts(prev["last_loss_exit_ts"]) if prev else None
            if prev is None or prev_ts is None or ts > prev_ts:
                prev_n = int(prev.get("loss_exit_count_in_window", 0)) if prev else 0
                agg[sym] = {
                    "symbol": sym,
                    "last_loss_exit_ts": ts.isoformat(),
                    "last_realized_pnl_usd": round(pnl, 6),
                    "loss_exit_count_in_window": prev_n + 1,
                    "note": "Loss exit in lookback window; re-entry within 30 days may trigger wash-sale treatment (consult tax advisor).",
                }
            else:
                prev["loss_exit_count_in_window"] = int(prev.get("loss_exit_count_in_window", 1)) + 1
    return agg


def _watchlist_from_agg(agg: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(agg.values(), key=lambda x: str(x.get("symbol") or ""))


def main() -> int:
    ap = argparse.ArgumentParser(description="Alpaca compliance snapshot (read-only).")
    ap.add_argument("--root", type=Path, default=REPO, help="Repo root.")
    ap.add_argument(
        "--exit-log",
        type=Path,
        default=None,
        help="Path to exit_attribution.jsonl (default: <root>/logs/exit_attribution.jsonl)",
    )
    ap.add_argument(
        "--lookback-days",
        type=int,
        default=30,
        help="Calendar days for loss-exit scan (default 30 = typical wash window).",
    )
    ap.add_argument(
        "--out-json",
        type=Path,
        default=None,
        help="Override output JSON path (default: <root>/state/alpaca_account_snapshot.json)",
    )
    args = ap.parse_args()
    root = args.root.resolve()
    exit_path = (args.exit_log or (root / "logs" / "exit_attribution.jsonl")).resolve()
    state_dir = root / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    out_json = (args.out_json or (state_dir / "alpaca_account_snapshot.json")).resolve()
    audit_dir = root / "reports" / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    ts_tag = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_md = audit_dir / f"alpaca_compliance_health_{ts_tag}.md"

    now = datetime.now(timezone.utc)
    since = now - timedelta(days=max(1, int(args.lookback_days)))
    loss_agg = _scan_loss_exits(exit_path, since=since)
    watchlist = _watchlist_from_agg(loss_agg)

    api, api_err = _build_alpaca_rest()
    account_dict: Optional[Dict[str, Any]] = None
    account_raw_error: Optional[str] = None
    if api is not None:
        try:
            acct = api.get_account()
            account_dict = _serialize_account(acct)
        except Exception as e:
            account_raw_error = f"{type(e).__name__}: {e}"
    else:
        account_raw_error = api_err

    payload: Dict[str, Any] = {
        "schema_version": "alpaca_account_snapshot_v1",
        "generated_ts_utc": now.isoformat(),
        "lookback_days": int(args.lookback_days),
        "lookback_since_utc": since.isoformat(),
        "exit_log": str(exit_path),
        "account": account_dict,
        "account_fetch_error": account_raw_error,
        "wash_risk_watchlist": watchlist,
        "wash_risk_watchlist_count": len(watchlist),
    }

    out_json.write_text(json.dumps(payload, indent=2, sort_keys=False), encoding="utf-8")

    pdt = (account_dict or {}).get("pattern_day_trader")
    dtc = (account_dict or {}).get("daytrade_count")
    bp = (account_dict or {}).get("buying_power")
    eq = (account_dict or {}).get("equity")
    mult = (account_dict or {}).get("multiplier")

    md_lines = [
        "# Alpaca compliance health",
        "",
        f"- **Generated (UTC):** `{ts_tag}`",
        f"- **JSON snapshot:** `{out_json}`",
        f"- **Exit log scanned:** `{exit_path}`",
        f"- **Loss lookback:** last **{args.lookback_days}** day(s) (UTC)",
        "",
        "## Broker account (read-only pull)",
        "",
    ]
    if account_dict:
        md_lines.extend(
            [
                f"| Field | Value |",
                f"|-------|-------|",
                f"| Equity | **{eq}** |",
                f"| Buying power | **{bp}** |",
                f"| Multiplier | **{mult}** |",
                f"| Pattern day trader | **{pdt}** |",
                f"| Day trade count | **{dtc}** |",
                "",
            ]
        )
    else:
        md_lines.extend(
            [
                "**Account fetch failed or credentials missing.**",
                "",
                f"```\n{account_raw_error}\n```",
                "",
            ]
        )

    md_lines.extend(
        [
            "## Wash-risk watchlist (loss exits in lookback)",
            "",
            f"**Count:** {len(watchlist)}",
            "",
            "Symbols with at least one **negative** `realized_pnl_usd` / `pnl` close in the window. "
            "Re-opening the same symbol while this advisory is active increases **wash-sale** risk; "
            "this file is **not** tax advice.",
            "",
        ]
    )
    if watchlist:
        md_lines.append("| Symbol | Last loss exit (UTC) | PnL USD | Loss exits in window |")
        md_lines.append("|--------|------------------------|---------|------------------------|")
        for w in watchlist:
            md_lines.append(
                f"| {w.get('symbol')} | {w.get('last_loss_exit_ts')} | {w.get('last_realized_pnl_usd')} | "
                f"{w.get('loss_exit_count_in_window', '')} |"
            )
        md_lines.append("")
    else:
        md_lines.append("_No qualifying loss exits in the lookback window._")
        md_lines.append("")

    out_md.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
