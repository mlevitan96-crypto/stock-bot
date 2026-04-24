#!/usr/bin/env python3
"""
Shadow: Discover whether ledgers contain artifacts required for true replay rescoring.
Checks for signal_vectors, normalized_scores, decision_timestamps, entry_exit_reasons.
Read-only; no writes.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _load_json(p: Path) -> dict:
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _check_trade(t: dict, expected: list[str]) -> dict[str, bool]:
    out = {}
    for art in expected:
        if art == "signal_vectors":
            out[art] = isinstance(t.get("signal_vectors"), (list, dict)) or "signal_vector" in (t.keys() if isinstance(t, dict) else [])
        elif art == "normalized_scores":
            out[art] = "normalized_score" in (t.keys() if isinstance(t, dict) else []) or isinstance(t.get("normalized_scores"), (list, dict))
        elif art == "decision_timestamps":
            out[art] = bool(t.get("entry_ts") and t.get("exit_ts")) or "decision_ts" in (t.keys() if isinstance(t, dict) else [])
        elif art == "entry_exit_reasons":
            out[art] = ("exit_reason" in (t.keys() if isinstance(t, dict) else []) and bool(t.get("exit_reason"))) or "entry_reason" in (t.keys() if isinstance(t, dict) else [])
        else:
            out[art] = art in (t.keys() if isinstance(t, dict) else [])
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Discover replay artifacts in ledgers")
    ap.add_argument("--ledger-dir", default="reports/ledger")
    ap.add_argument("--expected-artifacts", nargs="+", default=["signal_vectors", "normalized_scores", "decision_timestamps", "entry_exit_reasons"])
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    ledger_dir = Path(args.ledger_dir)
    if not ledger_dir.exists():
        print(f"Ledger dir missing: {ledger_dir}", file=sys.stderr)
        return 2

    ledgers = list(ledger_dir.glob("FULL_TRADE_LEDGER_*.json"))
    artifact_status = {a: {"present": False, "source": None, "sample_count": 0} for a in args.expected_artifacts}
    sample_trade_keys = []

    for lp in ledgers[:5]:
        data = _load_json(lp)
        executed = data.get("executed", []) or []
        if not executed:
            continue
        first = executed[0] if isinstance(executed[0], dict) else {}
        if not sample_trade_keys and first:
            sample_trade_keys = list(first.keys())
        for t in executed[:20]:
            if not isinstance(t, dict):
                continue
            checks = _check_trade(t, args.expected_artifacts)
            for a, present in checks.items():
                if present:
                    artifact_status[a]["present"] = True
                    artifact_status[a]["source"] = str(lp)
                    artifact_status[a]["sample_count"] = artifact_status[a].get("sample_count", 0) + 1

    out = {
        "ledger_dir": str(ledger_dir.resolve()),
        "ledger_count": len(ledgers),
        "expected_artifacts": args.expected_artifacts,
        "artifact_status": artifact_status,
        "sample_trade_keys": sample_trade_keys,
        "true_replay_ready": all(artifact_status[a]["present"] for a in args.expected_artifacts),
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("Discovery: true_replay_ready =", out["true_replay_ready"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
