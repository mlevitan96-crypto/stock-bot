#!/usr/bin/env python3
"""
B3 — REPLAY ORCHESTRATOR (EQUITY).
Generate many candidate levers (exit tweaks, entry thresholds, regime filters, signal ablations, targets),
run replay scripts, aggregate into campaign_results.json, rank by expectancy / win_rate / trade_count.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main() -> int:
    ap = __import__("argparse").ArgumentParser()
    ap.add_argument("--out-dir", type=Path, default=None, help="Campaign output dir (default: reports/replay/equity_replay_campaign_<ts>)")
    ap.add_argument("--max-candidates", type=int, default=50, help="Max candidate levers to run (per type)")
    args = ap.parse_args()

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = (args.out_dir or REPO / "reports" / "replay" / f"equity_replay_campaign_{ts}").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    results = []
    scripts_dir = REPO / "scripts" / "replay"

    # Exit: flow_deterioration sweep
    for fd in [0.22, 0.25, 0.27, 0.30, 0.33]:
        out_file = out_dir / f"exit_fd_{fd}.json"
        try:
            subprocess.run(
                [sys.executable, str(scripts_dir / "equity_exit_replay.py"), "--flow-deterioration", str(fd), "--out", str(out_file)],
                cwd=str(REPO), timeout=60, check=False, capture_output=True,
            )
            if out_file.exists():
                data = json.loads(out_file.read_text(encoding="utf-8"))
                data["lever_type"] = "exit"
                data["lever_params"] = {"flow_deterioration": fd}
                results.append(data)
        except Exception:
            pass

    # Entry: MIN_EXEC_SCORE sweep
    for score in [2.3, 2.5, 2.7, 2.9, 3.0]:
        out_file = out_dir / f"entry_score_{score}.json"
        try:
            subprocess.run(
                [sys.executable, str(scripts_dir / "equity_entry_replay.py"), "--min-exec-score", str(score), "--out", str(out_file)],
                cwd=str(REPO), timeout=60, check=False, capture_output=True,
            )
            if out_file.exists():
                data = json.loads(out_file.read_text(encoding="utf-8"))
                data["lever_type"] = "entry"
                data["lever_params"] = {"min_exec_score": score}
                results.append(data)
        except Exception:
            pass

    # Rank: expectancy desc, then win_rate desc, then trade_count >= 30
    min_trades = 30
    ranked = [r for r in results if (r.get("trade_count") or 0) >= min_trades]
    ranked.sort(key=lambda x: (-(x.get("expectancy_per_trade") or 0), -(x.get("win_rate") or 0), -(x.get("trade_count") or 0)))

    campaign = {
        "campaign_ts": ts,
        "out_dir": str(out_dir),
        "total_candidates_run": len(results),
        "ranked_candidates": ranked[:20],
        "all_results": results,
    }
    (out_dir / "campaign_results.json").write_text(json.dumps(campaign, indent=2), encoding="utf-8")
    (out_dir / "ranked_candidates.json").write_text(json.dumps(ranked[:20], indent=2), encoding="utf-8")
    print(f"Wrote {out_dir / 'campaign_results.json'} and ranked_candidates.json (ranked {len(ranked)} with >= {min_trades} trades)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
