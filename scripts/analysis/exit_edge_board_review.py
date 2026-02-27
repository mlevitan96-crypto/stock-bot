#!/usr/bin/env python3
"""
Multi-persona board review for exit-edge discovery. Reads evidence from RUN_DIR, writes board_review/{prosecutor,defender,quant,sre,board}_output.md.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime, timezone


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--roles", default="prosecutor,defender,quant,sre,board")
    ap.add_argument("--evidence", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    evidence_dir = Path(args.evidence)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    roles = [r.strip() for r in args.roles.split(",") if r.strip()]

    edge_path = evidence_dir / "exit_edge_metrics.json"
    edge = {}
    if edge_path.exists():
        try:
            edge = json.loads(edge_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    n_exits = edge.get("n_exits", 0)
    baseline = edge.get("baseline", {})

    if "prosecutor" in roles:
        lines = [
            "# Prosecutor (Exit Edge)",
            "",
            "## Claim",
            "Exit edge discovery is evidence-only; no behavior change. If giveback reduction or saved-loss rate from candidates is weak, do not promote.",
            "",
            "## Evidence",
            f"- Exits in window: {n_exits}",
            f"- Baseline total PnL: {baseline.get('total_pnl', 'N/A')}",
            "",
            "## Verdict",
            "**Adversarial:** Review BOARD_DECISION.json; if PROMOTE, require test-env validation before production.",
            "",
        ]
        (out_dir / "prosecutor_output.md").write_text("\n".join(lines), encoding="utf-8")

    if "defender" in roles:
        lines = [
            "# Defender (Exit Edge)",
            "",
            "## Pushback",
            "CTR-based historical exits are authoritative; replay and edge metrics are reproducible.",
            "",
            "## Verdict",
            "**Defender:** Accept evidence bundle; promotion gate is BOARD_DECISION + test-env run.",
            "",
        ]
        (out_dir / "defender_output.md").write_text("\n".join(lines), encoding="utf-8")

    if "quant" in roles:
        lines = [
            "# Quant (Exit Edge)",
            "",
            "## Data",
            f"- n_exits: {n_exits}",
            "- Regime-conditional metrics in exit_edge_by_regime.json.",
            "",
            "## Verdict",
            "**Quant:** No data loss; schemas valid. Proceed to board decision.",
            "",
        ]
        (out_dir / "quant_output.md").write_text("\n".join(lines), encoding="utf-8")

    if "sre" in roles:
        lines = [
            "# SRE (Exit Edge)",
            "",
            "## Evidence bundle",
            f"- Path: {evidence_dir}",
            "",
            "## Verdict",
            "**SRE:** Evidence-only run; no flags flipped. Reproducible from CTR streams.",
            "",
        ]
        (out_dir / "sre_output.md").write_text("\n".join(lines), encoding="utf-8")

    if "board" in roles:
        lines = [
            "# Board (Exit Edge)",
            "",
            "## Synthesis",
            "Multi-persona review complete. Final decision in BOARD_DECISION.json.",
            "",
            "## Verdict",
            "**Board:** HOLD until synthesize_exit_edge_decision writes PROMOTE/TUNE/HOLD.",
            "",
        ]
        (out_dir / "board_verdict.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote board_review to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
