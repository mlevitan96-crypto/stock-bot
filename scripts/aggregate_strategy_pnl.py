#!/usr/bin/env python3
"""Strategy-segmented PnL aggregation from exit attribution logs."""

import json
import glob
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LOGS_DIR = REPO_ROOT / "logs"
ARTIFACTS_DIR = REPO_ROOT / "artifacts"


def main():
    out = {"EQUITY": {"pnl": 0.0, "trades": 0}, "WHEEL": {"pnl": 0.0, "trades": 0}}
    pattern = str(LOGS_DIR / "exit_attribution*.jsonl")
    for f in glob.glob(pattern):
        try:
            with open(f) as fp:
                for line in fp:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        r = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    s = r.get("strategy", "EQUITY")
                    if s not in out:
                        out[s] = {"pnl": 0.0, "trades": 0}
                    out[s]["pnl"] = out[s].get("pnl", 0) + (r.get("pnl") or 0)
                    out[s]["trades"] = out[s].get("trades", 0) + 1
        except OSError:
            pass
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(ARTIFACTS_DIR / "strategy_pnl.json", "w") as fp:
        json.dump(out, fp, indent=2)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
