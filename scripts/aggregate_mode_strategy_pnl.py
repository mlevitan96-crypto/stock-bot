#!/usr/bin/env python3
"""Mode+strategy PnL aggregation from exit attribution logs for promotion decisions."""

import json
import glob
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).resolve().parents[1]
LOGS_DIR = REPO_ROOT / "logs"
ARTIFACTS_DIR = REPO_ROOT / "artifacts"


def norm_mode(x):
    if not x:
        return "UNKNOWN"
    x = str(x).upper()
    if x in ("LIVE", "PAPER", "SHADOW"):
        return x
    return x


def norm_strategy(x):
    if not x:
        return "UNKNOWN"
    x = str(x).upper()
    if x in ("EQUITY", "WHEEL"):
        return x
    return x


def main():
    agg = defaultdict(lambda: {"pnl": 0.0, "exits": 0, "wins": 0, "losses": 0})
    pattern = str(LOGS_DIR / "exit_attribution*.jsonl")

    for f in sorted(glob.glob(pattern)):
        try:
            with open(f) as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        r = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    mode = norm_mode(r.get("mode") or r.get("run_mode"))
                    strat = norm_strategy(r.get("strategy") or r.get("strategy_label"))
                    key = f"{mode}:{strat}"

                    pnl = float(r.get("pnl", 0.0) or 0.0)
                    agg[key]["pnl"] += pnl
                    agg[key]["exits"] += 1

                    if pnl > 0:
                        agg[key]["wins"] += 1
                    elif pnl < 0:
                        agg[key]["losses"] += 1
        except OSError:
            pass

    out = {"by_mode_strategy": dict(agg)}
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(ARTIFACTS_DIR / "mode_strategy_pnl.json", "w") as fp:
        json.dump(out, fp, indent=2, sort_keys=True)
    print(f"Wrote artifacts/mode_strategy_pnl.json with {len(agg)} buckets")


if __name__ == "__main__":
    main()
