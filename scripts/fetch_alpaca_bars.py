#!/usr/bin/env python3
"""
Phase 2: Fetch Alpaca historical daily bars via Data API v2 (REST).
Usage: --symbols SYM1,SYM2 --start YYYY-MM-DD --end YYYY-MM-DD --timeframe 1Day --out data/bars/alpaca_daily.parquet
Respects pagination and rate limits. Requires >=90% trading-day coverage per symbol; else writes
reports/bars/incomplete_symbols.md and exits 1.
"""
from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

REPORT_DIR = REPO / "reports" / "bars"
INCOMPLETE_PATH = REPORT_DIR / "incomplete_symbols.md"

# Load .env.research first (override=True), then .env (override=False) so research/shell env wins
_env_research = REPO / ".env.research"
_env_path = REPO / ".env"
for path, override in [(_env_research, True), (_env_path, False)]:
    if not path.exists():
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


def _data_base_url() -> str:
    base = os.getenv("ALPACA_BASE_URL", "")
    if "sandbox" in base.lower() or "paper" in base.lower():
        return os.getenv("ALPACA_DATA_URL", "https://data.sandbox.alpaca.markets")
    return os.getenv("ALPACA_DATA_URL", "https://data.alpaca.markets")


def _headers() -> dict:
    key = os.getenv("ALPACA_API_KEY") or os.getenv("ALPACA_KEY", "")
    secret = os.getenv("ALPACA_SECRET_KEY") or os.getenv("ALPACA_API_SECRET") or os.getenv("ALPACA_SECRET", "")
    return {
        "APCA-API-KEY-ID": key,
        "APCA-API-SECRET-KEY": secret,
    }


def _trading_days_in_range(start: str, end: str) -> int:
    d_start = datetime.strptime(start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    d_end = datetime.strptime(end, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    n = 0
    d = d_start
    while d <= d_end:
        if d.weekday() < 5:
            n += 1
        d += timedelta(days=1)
    return n


def fetch_bars(symbols: list[str], start: str, end: str, timeframe: str = "1Day") -> dict[str, list[dict]]:
    """Fetch all bars via Alpaca Data API v2 with pagination. Returns {symbol: [bars]}."""
    import urllib.request
    import urllib.parse

    base = _data_base_url().rstrip("/")
    result: dict[str, list[dict]] = {s: [] for s in symbols}
    page_token = None
    limit = 10000

    while True:
        params = {
            "symbols": ",".join(symbols),
            "timeframe": timeframe,
            "start": start,
            "end": end,
            "limit": limit,
            "sort": "asc",
        }
        if page_token:
            params["page_token"] = page_token
        url = base + "/v2/stocks/bars?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers=_headers(), method="GET")
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read().decode("utf-8")
        except Exception as e:
            print(f"Alpaca bars request failed: {e}", file=sys.stderr)
            break
        try:
            import json as _json
            j = _json.loads(data)
        except Exception as e:
            print(f"Alpaca bars response parse error: {e}", file=sys.stderr)
            break
        bars_map = j.get("bars") or {}
        for sym, arr in bars_map.items():
            if sym not in result:
                result[sym] = []
            for b in arr:
                result[sym].append({
                    "t": b.get("t"),
                    "o": float(b.get("o", 0)),
                    "h": float(b.get("h", 0)),
                    "l": float(b.get("l", 0)),
                    "c": float(b.get("c", 0)),
                    "v": int(b.get("v", 0)),
                })
        page_token = j.get("next_page_token")
        if not page_token:
            break
        time.sleep(0.2)
    return result


def _bars_to_rows(symbols: list[str], bars_by_sym: dict, required_days: int, min_days: int) -> tuple[list[dict], list[tuple]]:
    """Build rows and list of (sym, n_days, required, pct) for symbols below min_days."""
    incomplete = []
    rows = []
    for sym in symbols:
        bars = bars_by_sym.get(sym) or []
        dates = set()
        for b in bars:
            t = b.get("t")
            if t:
                if isinstance(t, str) and "T" in t:
                    dates.add(t.split("T")[0])
                else:
                    dates.add(str(t)[:10])
        n_days = len(dates)
        pct = (n_days / required_days * 100) if required_days else 0
        if n_days < min_days:
            incomplete.append((sym, n_days, required_days, round(pct, 1)))
        for b in bars:
            t = b.get("t") or ""
            date_str = t.split("T")[0] if isinstance(t, str) else str(t)[:10]
            rows.append({
                "symbol": sym,
                "date": date_str,
                "o": b["o"],
                "h": b["h"],
                "l": b["l"],
                "c": b["c"],
                "volume": b["v"],
            })
    return rows, incomplete


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", required=True, help="Comma-separated symbols")
    ap.add_argument("--start", required=True, help="Start date YYYY-MM-DD")
    ap.add_argument("--end", required=True, help="End date YYYY-MM-DD")
    ap.add_argument("--timeframe", default="1Day", help="Bar timeframe (default 1Day)")
    ap.add_argument("--out", default=None, help="Output parquet path (default data/bars/alpaca_daily.parquet)")
    ap.add_argument("--chunk-size", type=int, default=0, help="Fetch in batches of N (0 = all at once; 10-20 for OOM safety)")
    args = ap.parse_args()
    out_path = Path(args.out) if args.out else REPO / "data" / "bars" / "alpaca_daily.parquet"
    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    if not symbols:
        print("No symbols", file=sys.stderr)
        return 1
    required_days = _trading_days_in_range(args.start, args.end)
    min_coverage_pct = 90
    min_days = max(1, int(required_days * min_coverage_pct / 100))

    chunk_size = max(0, int(args.chunk_size))
    if chunk_size <= 0:
        # Original single-shot behavior
        bars_by_sym = fetch_bars(symbols, args.start, args.end, args.timeframe)
        rows, incomplete = _bars_to_rows(symbols, bars_by_sym, required_days, min_days)
        if incomplete:
            REPORT_DIR.mkdir(parents=True, exist_ok=True)
            lines = [
                "# Incomplete symbols (<90% coverage)",
                "",
                "| symbol | days | required | pct |",
                "|--------|------|----------|-----|",
            ]
            for sym, n, req, pct in incomplete:
                lines.append(f"| {sym} | {n} | {req} | {pct}% |")
            INCOMPLETE_PATH.write_text("\n".join(lines), encoding="utf-8")
            print(f"Incomplete: {[s[0] for s in incomplete]} -> {INCOMPLETE_PATH}", file=sys.stderr)
            return 1
        out_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            import pandas as pd
            df = pd.DataFrame(rows)
            if df.empty:
                print("No bars to write", file=sys.stderr)
                return 1
            df = df.sort_values(["symbol", "date"]).reset_index(drop=True)
            df.to_parquet(out_path, index=False)
        except Exception as e:
            print(f"Parquet write failed: {e}", file=sys.stderr)
            return 1
        print(f"Wrote {len(rows)} rows -> {out_path}")
        return 0

    # Chunked fetch: batches of chunk_size, append to parquet after each batch (OOM/signal safety)
    import pandas as pd
    out_path.parent.mkdir(parents=True, exist_ok=True)
    all_incomplete: list[tuple] = []
    chunks = [symbols[i : i + chunk_size] for i in range(0, len(symbols), chunk_size)]
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i + 1}/{len(chunks)}: {len(chunk)} symbols", file=sys.stderr)
        bars_by_sym = fetch_bars(chunk, args.start, args.end, args.timeframe)
        rows, incomplete = _bars_to_rows(chunk, bars_by_sym, required_days, min_days)
        for inc in incomplete:
            print(f"  Incomplete: {inc[0]} ({inc[3]}%)", file=sys.stderr)
            all_incomplete.append(inc)
        if not rows:
            continue
        df_batch = pd.DataFrame(rows).sort_values(["symbol", "date"]).reset_index(drop=True)
        if out_path.exists():
            try:
                df_existing = pd.read_parquet(out_path)
                df_combined = pd.concat([df_existing, df_batch], ignore_index=True)
            except Exception as e:
                print(f"Read existing parquet failed: {e}", file=sys.stderr)
                df_combined = df_batch
        else:
            df_combined = df_batch
        df_combined = df_combined.drop_duplicates(subset=["symbol", "date"], keep="first")
        df_combined = df_combined.sort_values(["symbol", "date"]).reset_index(drop=True)
        df_combined.to_parquet(out_path, index=False)
        print(f"  Appended {len(rows)} rows -> {out_path} ({len(df_combined)} total)", file=sys.stderr)
    if all_incomplete:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        lines = [
            "# Incomplete symbols (<90% coverage)",
            "",
            "| symbol | days | required | pct |",
            "|--------|------|----------|-----|",
        ]
        for sym, n, req, pct in all_incomplete:
            lines.append(f"| {sym} | {n} | {req} | {pct}% |")
        INCOMPLETE_PATH.write_text("\n".join(lines), encoding="utf-8")
        print(f"Incomplete: {[s[0] for s in all_incomplete]} -> {INCOMPLETE_PATH}", file=sys.stderr)
        return 1
    total_rows = len(pd.read_parquet(out_path)) if out_path.exists() else 0
    print(f"Wrote {total_rows} rows -> {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
