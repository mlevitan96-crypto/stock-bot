#!/usr/bin/env python3
"""
CSA: Evaluate whether true replay rescoring is feasible from artifact discovery.
Verdict: TRUE_REPLAY_POSSIBLE or PROXY_ONLY. No promotion unless true replay is proven.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="CSA replay feasibility verdict")
    ap.add_argument("--discovery", required=True)
    ap.add_argument("--require-explicit-verdict", action="store_true", default=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    path = Path(args.discovery)
    if not path.exists():
        print(f"Discovery missing: {path}", file=sys.stderr)
        return 2

    data = json.loads(path.read_text(encoding="utf-8"))
    true_replay_ready = data.get("true_replay_ready", False)
    artifact_status = data.get("artifact_status", {})

    verdict = "TRUE_REPLAY_POSSIBLE" if true_replay_ready else "PROXY_ONLY"
    rationale = (
        "All required replay artifacts present; decision-grade rescore allowed."
        if true_replay_ready
        else "One or more required artifacts missing (signal_vectors, normalized_scores, decision_timestamps, entry_exit_reasons). Proxy-only; no promotion from shadow shortlist."
    )

    out = {
        "verdict": verdict,
        "rationale": rationale,
        "true_replay_ready": true_replay_ready,
        "artifact_status": artifact_status,
        "discovery_path": str(path.resolve()),
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("CSA_REPLAY_FEASIBILITY:", verdict)
    return 0


if __name__ == "__main__":
    sys.exit(main())
