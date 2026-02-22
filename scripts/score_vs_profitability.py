#!/usr/bin/env python3
# Score-vs-profitability: bucket trades by entry_score. Output: score_bands.json, score_vs_profitability.md
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
BANDS = [(1.0, 1.5), (1.5, 2.0), (2.0, 2.5), (2.5, 3.0), (3.0, 3.5), (3.5, 4.0), (4.0, 5.0), (5.0, 10.0)]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trades", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    p = REPO / args.trades if not Path(args.trades).is_absolute() else Path(args.trades)
    out = REPO / args.out if not Path(args.out).is_absolute() else Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    trades = []
    if p.suffix == ".json":
        d = json.loads(p.read_text(encoding="utf-8"))
        trades = d.get("trades") or []
    else:
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.strip():
                try: trades.append(json.loads(line))
                except Exception: pass
    if not trades:
        out.joinpath("score_bands.json").write_text(json.dumps({"bands": [], "total_trades": 0, "recommendation": "No trades."}, indent=2))
        out.joinpath("score_vs_profitability.md").write_text("# Score vs profitability\n\nNo trades.\n")
        return 0
    band_stats = []
    for lo, hi in BANDS:
        sub = [t for t in trades if lo < float(t.get("entry_score") or 0) <= hi]
        if not sub:
            band_stats.append({"score_band": f"({lo},{hi}]", "trade_count": 0, "win_rate_pct": None, "net_pnl_usd": 0.0, "avg_pnl_usd": None})
            continue
        pnls = [float(t.get("pnl_usd") or 0) for t in sub]
        n, w = len(sub), sum(1 for x in pnls if x > 0)
        band_stats.append({"score_band": f"({lo},{hi}]", "trade_count": n, "win_rate_pct": round(w/n*100, 2), "net_pnl_usd": round(sum(pnls), 2), "avg_pnl_usd": round(sum(pnls)/n, 2)})
    total_pnl = sum(float(t.get("pnl_usd") or 0) for t in trades)
    prof = [b["score_band"] for b in band_stats if (b.get("net_pnl_usd") or 0) > 0 and (b.get("trade_count") or 0) >= 10]
    rec = "Profitable bands: " + ", ".join(prof) + ". Consider min_exec_score at or above lower edge." if prof else "No band with n>=10 and net_pnl>0; gather more data or tune signals."
    j = {"bands": band_stats, "total_trades": len(trades), "total_net_pnl_usd": round(total_pnl, 2), "recommendation": rec}
    out.joinpath("score_bands.json").write_text(json.dumps(j, indent=2), encoding="utf-8")
    lines = ["# Score vs profitability", "", "| Band | Trades | Win% | Net PnL |", "|------|--------|------|--------|"]
    for b in band_stats:
        lines.append(f"| {b['score_band']} | {b['trade_count']} | {b.get('win_rate_pct')} | {b['net_pnl_usd']} |")
    lines.extend(["", "## Recommendation", "", rec, ""])
    out.joinpath("score_vs_profitability.md").write_text("\n".join(lines), encoding="utf-8")
    print("Wrote", out / "score_bands.json", "and", out / "score_vs_profitability.md")
    return 0

if __name__ == "__main__":
    sys.exit(main())
