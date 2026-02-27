#!/usr/bin/env python3
"""
Aggregate profitability campaign: rank all iterations by PnL, emit top N and promotion payloads.
Rank ONLY by TOTAL_PNL_AFTER_COSTS (or rank_by arg). Promotion payloads are JSON config snippets
for PAPER/SHADOW.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]  # repo root (this file is in scripts/learning/)
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main() -> int:
    ap = argparse.ArgumentParser(description="Aggregate campaign by profitability, emit top N and promotion payloads")
    ap.add_argument("--campaign_dir", required=True, help="Campaign output dir (e.g. reports/learning_runs/RUN_TAG)")
    ap.add_argument("--rank_by", default="TOTAL_PNL_AFTER_COSTS", help="Metric to rank by")
    ap.add_argument("--emit_top_n", type=int, default=10, help="Number of top iterations to emit")
    ap.add_argument("--emit_promotion_payloads", action="store_true", help="Write promotion-ready configs for top ideas")
    ap.add_argument("--min_trades", type=int, default=0, help="Exclude iterations with trades_count < this from top_n and promotion (0 = no filter)")
    args = ap.parse_args()

    campaign_dir = Path(args.campaign_dir)
    if not campaign_dir.is_absolute():
        campaign_dir = REPO / campaign_dir
    iterations_dir = campaign_dir / "iterations"
    if not iterations_dir.exists():
        print("No iterations dir found; run campaign first.", file=sys.stderr)
        campaign_dir.mkdir(parents=True, exist_ok=True)
        (campaign_dir / "aggregate_result.json").write_text(
            json.dumps({"ranked": [], "top_n": [], "promotion_payloads": []}, indent=2),
            encoding="utf-8",
        )
        return 0

    results = []
    for path in sorted(iterations_dir.iterdir()):
        if not path.is_dir():
            continue
        res_path = path / "iteration_result.json"
        if not res_path.exists():
            continue
        try:
            data = json.loads(res_path.read_text(encoding="utf-8"))
            key = data.get(args.rank_by)
            if key is None:
                key = data.get("TOTAL_PNL_AFTER_COSTS")
            results.append({
                "iter_id": data.get("iter_id", path.name),
                "iter_path": str(path),
                "rank_key": key,
                **data,
            })
        except Exception:
            continue

    # Apply min_trades filter so 0-trade / tiny-sample policies cannot win
    if args.min_trades > 0:
        before = len(results)
        results = [r for r in results if (r.get("trades_count") or 0) >= args.min_trades]
        if before > len(results):
            print(f"Excluded {before - len(results)} iterations with trades_count < {args.min_trades}", file=sys.stderr)

    # Rank descending (higher PnL first); null/missing sort last
    def sort_key(r):
        v = r.get("rank_key")
        if v is None:
            return -1e9
        try:
            return float(v)
        except (TypeError, ValueError):
            return -1e9

    results.sort(key=sort_key, reverse=True)
    top_n = results[: args.emit_top_n]

    out = {
        "campaign_dir": str(campaign_dir),
        "rank_by": args.rank_by,
        "total_iterations": len(results),
        "ranked": [{"iter_id": r["iter_id"], "rank_key": r["rank_key"], "trades_count": r.get("trades_count")} for r in results],
        "top_n": [{"iter_id": r["iter_id"], "rank_key": r["rank_key"], "trades_count": r.get("trades_count"), "idea": r.get("idea")} for r in top_n],
        "promotion_payloads": [],
    }

    if args.emit_promotion_payloads and top_n:
        promo_dir = campaign_dir / "promotion_payloads"
        promo_dir.mkdir(parents=True, exist_ok=True)
        for i, r in enumerate(top_n):
            payload = {
                "iter_id": r["iter_id"],
                "rank_key": r["rank_key"],
                "idea": r.get("idea"),
                "trades_count": r.get("trades_count"),
                "win_rate_pct": r.get("win_rate_pct"),
                "mode": "PAPER_ONLY",
                "promotion_note": f"Campaign top {i+1} by {args.rank_by}",
            }
            out["promotion_payloads"].append(payload)
            (promo_dir / f"{r['iter_id']}_promotion.json").write_text(
                json.dumps(payload, indent=2, default=str), encoding="utf-8"
            )
        print(f"Emitted {len(top_n)} promotion payloads to {promo_dir}")

    (campaign_dir / "aggregate_result.json").write_text(
        json.dumps(out, indent=2, default=str), encoding="utf-8"
    )
    print(f"Ranked {len(results)} iterations by {args.rank_by}")
    for i, r in enumerate(top_n[:5], 1):
        print(f"  {i}. {r['iter_id']}  {args.rank_by}={r['rank_key']}  trades={r.get('trades_count')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
