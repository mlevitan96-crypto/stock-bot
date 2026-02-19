#!/usr/bin/env python3
"""
Phase 6: MODEL D synthesis — integrity PASS/FAIL, edge present?, top signals, final verdict.
Reads: integrity_audit.md, baseline_results.md, conditional_edge_results.md, build_log.md.
Writes: reports/research_dataset/final_verdict.md
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "reports" / "research_dataset"


def main():
    integrity_path = OUT_DIR / "integrity_audit.md"
    baseline_path = OUT_DIR / "baseline_results.md"
    cond_path = OUT_DIR / "conditional_edge_results.md"
    build_path = OUT_DIR / "build_log.md"

    integrity_pass = False
    if integrity_path.exists():
        t = integrity_path.read_text(encoding="utf-8")
        integrity_pass = "**PASS**" in t and "FAIL" not in t.split("## Verdict")[-1].split("\n")[0]

    edge_found = False
    top_signals = []
    top_interactions = []
    if baseline_path.exists():
        t = baseline_path.read_text(encoding="utf-8")
        for line in t.splitlines():
            if "| " in line and "signal" not in line.lower() and "lift" in line:
                # | gs_uw | 0.0123 |
                m = re.search(r"\|\s*([^\|]+)\s*\|\s*([\d.-]+)\s*\|", line)
                if m:
                    sig, lift = m.group(1).strip(), float(m.group(2))
                    if abs(lift) > 0.001:
                        top_signals.append((sig, lift))
        top_signals.sort(key=lambda x: -abs(x[1]))
        top_signals = top_signals[:3]
        if top_signals and any(abs(l) > 0 for _, l in top_signals):
            edge_found = True
    if cond_path.exists():
        t = cond_path.read_text(encoding="utf-8")
        for line in t.splitlines():
            if " lift:" in line and "regime" in t[:t.find(line)]:
                m = re.search(r"-\s*(\S+)\s+lift:\s*([\d.-]+)", line)
                if m:
                    top_interactions.append((m.group(1), float(m.group(2))))
        top_interactions.sort(key=lambda x: -abs(x[1]))
        top_interactions = top_interactions[:3]

    lines = [
        "# Final Verdict (Phase 6 — MODEL D)",
        "",
        "## Integrity",
        f"- **Verdict:** {'PASS' if integrity_pass else 'FAIL'}",
        "",
        "## Edge",
        f"- **Edge present:** {'Yes (unconditional or conditional)' if edge_found else 'No'}",
        "",
        "## Top 3 signals (by OOS/decile lift)",
        "",
    ]
    for sig, lift in top_signals:
        lines.append(f"- {sig}: lift={lift:.4f}")
    if not top_signals:
        lines.append("- None")
    lines.extend(["", "## Top 3 signal×regime interactions", ""])
    for sig, lift in top_interactions:
        lines.append(f"- {sig}: lift={lift:.4f}")
    if not top_interactions:
        lines.append("- None")
    lines.extend([
        "",
        "## Recommendation",
        "",
    ])
    if edge_found and integrity_pass:
        lines.append("**EDGE FOUND — PROCEED TO CONDITIONAL SCORING**")
    else:
        lines.append("**NO EDGE — SIGNAL SET INSUFFICIENT, EXPAND DATA**")
        if not integrity_pass:
            lines.append("- Fix integrity audit failures first.")
        lines.append("- Propose: (1) more history, (2) additional macro/regime features, (3) broader universe.")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "final_verdict.md").write_text("\n".join(lines), encoding="utf-8")
    print("final_verdict.md written.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
