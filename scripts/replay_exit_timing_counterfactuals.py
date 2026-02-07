"""Counterfactual exit replay using hold floors (scenarios) + Alpaca bars. Exit-only: entries fixed."""
import argparse
import glob
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone


def parse_ts(x):
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return datetime.fromtimestamp(x, tz=timezone.utc)
    s = str(x)
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s).astimezone(timezone.utc)
    except Exception:
        return None


def load_scenarios(path):
    return (json.loads(open(path).read()) or {}).get("scenarios", {})


def load_exit_rows():
    files = sorted(glob.glob("logs/exit_attribution*.jsonl"))
    rows = []
    for f in files:
        for line in open(f):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def load_bars(alpaca_jsonl_path):
    """Returns dict: bars[symbol] = list of (t, close)"""
    bars = defaultdict(list)
    for line in open(alpaca_jsonl_path):
        line = line.strip()
        if not line:
            continue
        payload = json.loads(line)
        data = payload.get("data") or {}
        b = data.get("bars") or {}
        for sym, arr in b.items():
            for bar in arr:
                t = parse_ts(bar.get("t"))
                c = bar.get("c")
                if t is None or c is None:
                    continue
                bars[sym.upper()].append((t, float(c)))
    for sym in list(bars.keys()):
        bars[sym].sort(key=lambda x: x[0])
    return bars


def find_price_at_or_after(bars_list, ts):
    for t, c in bars_list:
        if t >= ts:
            return c, t
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenarios", default="config/exit_timing_scenarios.json")
    ap.add_argument("--alpaca-bars", default="artifacts/market_data/alpaca_bars.jsonl")
    ap.add_argument("--out-json", default="artifacts/scenario_replay/counterfactual_exit_replay.json")
    ap.add_argument("--out-md", default="artifacts/scenario_replay/counterfactual_exit_replay.md")
    args = ap.parse_args()

    scenarios = load_scenarios(args.scenarios)
    rows = load_exit_rows()

    if not os.path.exists(args.alpaca_bars):
        print("ERROR: Missing alpaca bars file:", args.alpaca_bars, file=sys.stderr)
        sys.exit(1)

    bars = load_bars(args.alpaca_bars)

    def norm(x, allowed=None):
        x = (x or "UNKNOWN")
        x = str(x).upper()
        if allowed and x not in allowed:
            return "UNKNOWN"
        return x

    baseline = defaultdict(lambda: {"pnl": 0.0, "exits": 0})
    for r in rows:
        key = f"{norm(r.get('mode'), {'LIVE','PAPER','SHADOW'})}:{norm(r.get('strategy'), {'EQUITY','WHEEL'})}"
        pnl = float(r.get("pnl") or 0.0)
        baseline[key]["pnl"] += pnl
        baseline[key]["exits"] += 1

    results = {"baseline_realized": dict(baseline), "scenarios": {}}
    skipped = defaultdict(int)

    for scen_name, scen in scenarios.items():
        params = scen.get("params") or {}
        scen_bucket = defaultdict(lambda: {"pnl": 0.0, "exits": 0, "rows_used": 0, "rows_skipped": 0})
        for r in rows:
            mode = norm(r.get("mode"), {"LIVE", "PAPER", "SHADOW"})
            strat = norm(r.get("strategy"), {"EQUITY", "WHEEL"})
            bucket = f"{mode}:{strat}"

            entry_ts = parse_ts(r.get("entry_ts") or r.get("entry_timestamp"))
            exit_ts = parse_ts(r.get("exit_ts") or r.get("timestamp"))
            entry_price = r.get("entry_price")
            qty = r.get("qty")
            side = str(r.get("side") or "").lower()
            sym = str(r.get("symbol") or "").upper()

            if entry_ts is None or exit_ts is None or entry_price is None or qty is None or sym == "":
                scen_bucket[bucket]["rows_skipped"] += 1
                skipped["missing_entry_or_exit_fields"] += 1
                continue

            try:
                entry_price = float(entry_price)
                qty = float(qty)
            except Exception:
                scen_bucket[bucket]["rows_skipped"] += 1
                skipped["bad_entry_or_qty"] += 1
                continue

            hold_floor = 0
            mp = params.get(mode, {}) or {}
            hold_floor = int(mp.get("min_hold_seconds_floor") or 0)
            regime = norm(r.get("regime_label"))
            ro = (mp.get("regime_overrides") or {}).get(regime, {}) if isinstance(mp.get("regime_overrides"), dict) else {}
            if ro.get("min_hold_seconds_floor") is not None:
                hold_floor = int(ro["min_hold_seconds_floor"])

            target_exit_ts = exit_ts
            min_allowed = entry_ts.timestamp() + hold_floor
            if target_exit_ts.timestamp() < min_allowed:
                target_exit_ts = datetime.fromtimestamp(min_allowed, tz=timezone.utc)

            blist = bars.get(sym)
            if not blist:
                scen_bucket[bucket]["rows_skipped"] += 1
                skipped["missing_bars_for_symbol"] += 1
                continue

            px, px_ts = find_price_at_or_after(blist, target_exit_ts)
            if px is None:
                scen_bucket[bucket]["rows_skipped"] += 1
                skipped["no_bar_after_target_exit"] += 1
                continue

            if side in ("sell", "short"):
                pnl = (entry_price - px) * qty
            else:
                pnl = (px - entry_price) * qty

            scen_bucket[bucket]["pnl"] += pnl
            scen_bucket[bucket]["exits"] += 1
            scen_bucket[bucket]["rows_used"] += 1

        results["scenarios"][scen_name] = {
            "description": scen.get("description", ""),
            "buckets": dict(scen_bucket),
        }

    os.makedirs(os.path.dirname(args.out_json) or ".", exist_ok=True)
    with open(args.out_json, "w") as f:
        json.dump({"results": results, "skipped": dict(skipped)}, f, indent=2, sort_keys=True)

    md = []
    md.append("# Counterfactual exit timing replay (exit-only)\n\n")
    md.append("## Baseline realized exits (as logged)\n\n")
    md.append("| bucket | pnl | exits |\n|---|---:|---:|\n")
    for k, v in sorted(baseline.items()):
        md.append(f"| {k} | {v['pnl']:.2f} | {v['exits']} |\n")

    md.append("\n## Scenario results (counterfactual P&L model)\n")
    for scen_name, scen_out in results["scenarios"].items():
        md.append(f"\n### {scen_name}\n\n")
        md.append(f"{scen_out.get('description', '')}\n\n")
        md.append("| bucket | pnl | exits | rows_used | rows_skipped |\n|---|---:|---:|---:|---:|\n")
        for k, v in sorted((scen_out.get("buckets") or {}).items()):
            md.append(f"| {k} | {v['pnl']:.2f} | {v['exits']} | {v.get('rows_used', 0)} | {v.get('rows_skipped', 0)} |\n")

    md.append("\n## Skips (why rows could not be replayed)\n\n")
    for k, v in sorted(skipped.items()):
        md.append(f"- **{k}:** {v}\n")

    with open(args.out_md, "w") as f:
        f.write("".join(md))

    print("Wrote", args.out_json)
    print("Wrote", args.out_md)


if __name__ == "__main__":
    main()
