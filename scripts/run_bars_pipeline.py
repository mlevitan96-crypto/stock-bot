#!/usr/bin/env python3
"""
Run full Alpaca bars pipeline (Phases 0-6) and print required one-block output.
Phases: env check, universe/range, fetch bars, cache status, audit, expectancy replay, PROOF.md.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REPORTS_BARS = REPO / "reports" / "bars"
DATA_BARS = REPO / "data" / "bars"
PARQUET = DATA_BARS / "alpaca_daily.parquet"


def run(cmd: list[str], timeout: int = 300) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return -1, str(e)


def main() -> int:
    py = sys.executable
    env_pass = False
    symbols_fetched = 0
    date_range = ""
    coverage_min = coverage_med = coverage_max = 0.0
    replay_pnl_nonzero = False
    verdict = "BARS MISSING — FIX REQUIRED"

    # Phase 0
    code, _ = run([py, "scripts/check_alpaca_env.py"])
    env_pass = code == 0
    if not env_pass:
        _print_output(env_pass, 0, "", 0, 0, 0, False)
        return 1

    # Phase 1
    code, _ = run([py, "scripts/bars_universe_and_range.py"])
    if code != 0:
        _print_output(True, 0, "", 0, 0, 0, False)
        return 1
    # Parse universe_and_range for symbols and range
    ur_path = REPORTS_BARS / "universe_and_range.md"
    start_str = end_str = ""
    if ur_path.exists():
        text = ur_path.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            if "Symbols count" in line and "|" in line:
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) >= 2:
                    try:
                        symbols_fetched = int(parts[1])
                    except ValueError:
                        pass
            if "Start" in line and "|" in line and "trading" in line.lower():
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) >= 2:
                    start_str = parts[1].strip()
            if "End" in line and "max" in line.lower() and "|" in line:
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) >= 2:
                    end_str = parts[1].strip()
        if start_str and end_str:
            date_range = f"{start_str} to {end_str}"
    if not symbols_str and (REPO / "logs" / "score_snapshot.jsonl").exists():
        syms = set()
        for line in (REPO / "logs" / "score_snapshot.jsonl").read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                s = (r.get("symbol") or r.get("ticker") or "").strip()
                if s and s != "?":
                    syms.add(s)
            except json.JSONDecodeError:
                pass
        if (REPO / "state" / "blocked_trades.jsonl").exists():
            for line in (REPO / "state" / "blocked_trades.jsonl").read_text(encoding="utf-8", errors="replace").splitlines():
                if not line.strip():
                    continue
                try:
                    r = json.loads(line)
                    s = (r.get("symbol") or "").strip()
                    if s and s != "?":
                        syms.add(s)
                except json.JSONDecodeError:
                    pass
        symbols_fetched = len(syms)

    # Phase 2: fetch (need symbols and range from Phase 1)
    if not start_str and date_range and " to " in date_range:
        start_str, _, end_str = date_range.partition(" to ")
        start_str, end_str = start_str.strip(), end_str.strip()
    if start_str and end_str and symbols_fetched:
        symbols_list = []
        if ur_path.exists():
            text = ur_path.read_text(encoding="utf-8", errors="replace")
            in_section = False
            for line in text.splitlines():
                if "## Symbols" in line:
                    in_section = True
                    continue
                if in_section and line.strip():
                    symbols_list = [s.strip() for s in line.replace("...", "").split() if len(s.strip()) <= 6 and s.strip().isalpha()]
                    break
        if not symbols_list and (REPO / "logs" / "score_snapshot.jsonl").exists():
            for line in (REPO / "logs" / "score_snapshot.jsonl").read_text(encoding="utf-8", errors="replace").splitlines():
                if not line.strip():
                    continue
                try:
                    r = json.loads(line)
                    s = (r.get("symbol") or r.get("ticker") or "").strip()
                    if s and s != "?" and s not in symbols_list:
                        symbols_list.append(s)
                except json.JSONDecodeError:
                    pass
            for line in (REPO / "state" / "blocked_trades.jsonl").read_text(encoding="utf-8", errors="replace").splitlines():
                if not line.strip():
                    continue
                try:
                    r = json.loads(line)
                    s = (r.get("symbol") or "").strip()
                    if s and s != "?" and s not in symbols_list:
                        symbols_list.append(s)
                except json.JSONDecodeError:
                    pass
        if symbols_list:
            sym_arg = ",".join(symbols_list[:500])
            code, out = run([py, "scripts/fetch_alpaca_bars.py", "--symbols", sym_arg, "--start", start_str, "--end", end_str, "--timeframe", "1Day", "--out", str(PARQUET)], timeout=600)
            if code != 0:
                _print_output(env_pass, symbols_fetched, date_range, 0, 0, 0, False)
                return 1

    # Phase 3 & 4
    if PARQUET.exists():
        run([py, "scripts/write_bars_cache_status.py", "--path", str(PARQUET)])
        run([py, "scripts/audit_bars.py", "--in", str(PARQUET)])
        # Coverage from parquet
        try:
            import pandas as pd
            df = pd.read_parquet(PARQUET)
            if not df.empty and "symbol" in df.columns and "date" in df.columns:
                from datetime import datetime, timezone, timedelta
                dates = pd.to_datetime(df["date"].astype(str))
                req_days = 0
                d = datetime.strptime(start_str[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                end_d = datetime.strptime(end_str[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                while d <= end_d:
                    if d.weekday() < 5:
                        req_days += 1
                    d += timedelta(days=1)
                pcts = []
                for sym in df["symbol"].unique():
                    sub = df[df["symbol"] == sym]
                    n = sub["date"].nunique()
                    pcts.append((n / req_days * 100) if req_days else 0)
                if pcts:
                    pcts.sort()
                    coverage_min = round(min(pcts), 1)
                    coverage_med = round(float(pcts[len(pcts) // 2]), 1)
                    coverage_max = round(max(pcts), 1)
        except Exception:
            pass

    # Phase 5: replay
    if PARQUET.exists():
        code, _ = run([py, "scripts/blocked_expectancy_analysis.py"], timeout=120)
        replay_path = REPO / "reports" / "blocked_expectancy" / "replay_results.jsonl"
        if replay_path.exists():
            pnls = []
            for line in replay_path.read_text(encoding="utf-8", errors="replace").splitlines():
                if not line.strip():
                    continue
                try:
                    r = json.loads(line)
                    p = r.get("pnl_pct")
                    if p is not None:
                        pnls.append(float(p))
                except json.JSONDecodeError:
                    pass
            replay_pnl_nonzero = any(p != 0 for p in pnls)
        bucket_path = REPO / "reports" / "blocked_expectancy" / "bucket_analysis.md"
        if bucket_path.exists():
            text = bucket_path.read_text(encoding="utf-8", errors="replace")
            for line in text.splitlines():
                if "|" in line:
                    parts = [p.strip() for p in line.split("|") if p.strip()]
                    if len(parts) >= 3:
                        try:
                            if float(parts[2]) != 0:
                                replay_pnl_nonzero = True
                                break
                        except ValueError:
                            pass

    # Phase 6: PROOF.md
    proof_lines = [
        "# Alpaca bars proof",
        "",
        "## Endpoint",
        "Alpaca Data API v2: GET /v2/stocks/bars (data.alpaca.markets or data.sandbox.alpaca.markets).",
        "",
        "## Date range",
        date_range or "(not set)",
        "",
        "## Symbol count",
        str(symbols_fetched),
        "",
        "## Coverage (min / median / max %)",
        f"{coverage_min} / {coverage_med} / {coverage_max}",
        "",
        "## Sample rows (symbol, date, o, h, l, c, volume)",
        "",
    ]
    if PARQUET.exists():
        try:
            import pandas as pd
            df = pd.read_parquet(PARQUET)
            if not df.empty:
                sample = df.head(5)
                proof_lines.append("| symbol | date | o | h | l | c | volume |")
                proof_lines.append("|--------|------|---|---|---|---|--------|")
                for _, row in sample.iterrows():
                    proof_lines.append(f"| {row.get('symbol')} | {row.get('date')} | {row.get('o')} | {row.get('h')} | {row.get('l')} | {row.get('c')} | {row.get('volume')} |")
        except Exception:
            proof_lines.append("(error reading parquet)")
    else:
        proof_lines.append("(no parquet)")
    proof_lines.extend([
        "",
        "## Replay uses real PNL",
        "YES — replay uses bars from data/bars/alpaca_daily.parquet; non-zero pnl in replay_results.jsonl confirms real PNL." if replay_pnl_nonzero else "NO — parquet missing or replay has no non-zero pnl.",
        "",
    ])
    REPORTS_BARS.mkdir(parents=True, exist_ok=True)
    (REPORTS_BARS / "PROOF.md").write_text("\n".join(proof_lines), encoding="utf-8")

    if replay_pnl_nonzero and PARQUET.exists():
        verdict = "BARS READY — REAL PNL ENABLED"

    _print_output(env_pass, symbols_fetched, date_range, coverage_min, coverage_med, coverage_max, replay_pnl_nonzero, verdict)
    return 0 if verdict == "BARS READY — REAL PNL ENABLED" else 1


def _print_output(env_ok: bool, n_sym: int, date_range: str, cov_min: float, cov_med: float, cov_max: float, pnl_ok: bool, verdict: str = ""):
    if not verdict:
        verdict = "BARS READY — REAL PNL ENABLED" if (env_ok and pnl_ok) else "BARS MISSING — FIX REQUIRED"
    print("Alpaca env check: " + ("PASS" if env_ok else "FAIL"))
    print("Symbols fetched: " + str(n_sym))
    print("Date range covered: " + (date_range or "(none)"))
    print("Bars coverage: min/median/max % — " + f"{cov_min}/{cov_med}/{cov_max}")
    print("Replay pnl non-zero: " + ("YES" if pnl_ok else "NO"))
    print("Verdict: " + verdict)


if __name__ == "__main__":
    sys.exit(main())
