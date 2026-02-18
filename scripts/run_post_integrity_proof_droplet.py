#!/usr/bin/env python3
"""
Droplet: Step 1 (exit quality proof) + sample attribution for entry_score.
Writes: 20260218_exit_quality_emission_proof.md
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

DATE = "20260218"
OUT_DIR = REPO / "reports" / "phase9_data_integrity"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def main() -> int:
    try:
        from droplet_client import DropletClient
    except ImportError:
        print("DropletClient not found", file=sys.stderr)
        return 1

    with DropletClient() as c:
        # A) Paper state
        out_state, _, _ = c._execute_with_cd("cat state/live_paper_run_state.json 2>/dev/null || echo '{}'", timeout=5)
        out_tmux, _, _ = c._execute_with_cd("tmux ls 2>/dev/null || echo 'none'", timeout=5)
        out_pane, _, _ = c._execute_with_cd("tmux capture-pane -pt stock_bot_paper_run -S -50 2>/dev/null || echo 'no-pane'", timeout=5)
        # B) Last exit_attribution ts
        out_last, _, _ = c._execute_with_cd(
            "tail -n 1 logs/exit_attribution.jsonl 2>/dev/null | python3 -c \"import sys,json; r=json.loads(sys.stdin.read()); print(r.get('ts') or r.get('timestamp') or 'NO_TS')\" 2>/dev/null || echo 'NO_TS'",
            timeout=10,
        )
        # C) Newest 500 lines: count with exit_quality_metrics
        out_sample, _, _ = c._execute_with_cd(
            "tail -n 500 logs/exit_attribution.jsonl 2>/dev/null | python3 -c '\n"
            "import sys, json\n"
            "n=0; m=0; ex=[]\n"
            "for line in sys.stdin:\n"
            "  try: r=json.loads(line)\n"
            "  except: continue\n"
            "  n+=1\n"
            "  if r.get(\"exit_quality_metrics\") is not None:\n"
            "    m+=1\n"
            "    if len(ex)<2: ex.append(r.get(\"exit_quality_metrics\"))\n"
            "print(\"sample_records\", n, \"with_exit_quality_metrics\", m)\n"
            "print(\"examples\", ex)\n"
            "' 2>&1",
            timeout=15,
        )
        # Attribution: last 200, count with entry_score in context
        out_attr, _, _ = c._execute_with_cd(
            "tail -n 200 logs/attribution.jsonl 2>/dev/null | python3 -c '\n"
            "import sys,json\n"
            "c=0; m=0\n"
            "for line in sys.stdin:\n"
            "  try: r=json.loads(line)\n"
            "  except: continue\n"
            "  c+=1\n"
            "  ctx = r.get(\"context\") or {}\n"
            "  if ctx.get(\"entry_score\") is not None: m+=1\n"
            "  elif r.get(\"entry_score\") is not None: m+=1\n"
            "print(\"sample\", c, \"with_entry_score\", m)\n"
            "' 2>&1",
            timeout=15,
        )

    # Parse sample output
    sample_records = with_eqm = 0
    examples_eqm = []
    for line in (out_sample or "").strip().split("\n"):
        if "sample_records" in line:
            parts = line.split()
            try:
                if "sample_records" in parts:
                    i = parts.index("sample_records")
                    if i + 1 < len(parts):
                        sample_records = int(parts[i + 1])
                if "with_exit_quality_metrics" in parts:
                    j = parts.index("with_exit_quality_metrics")
                    if j + 1 < len(parts):
                        with_eqm = int(parts[j + 1])
            except (ValueError, IndexError):
                pass
        if "examples" in line:
            try:
                rest = line.split("examples", 1)[-1].strip()
                if rest and rest != "[]":
                    examples_eqm = json.loads(rest) if rest.startswith("[") else []
            except Exception:
                pass
    attr_sample = attr_with_score = 0
    for line in (out_attr or "").strip().split("\n"):
        if "sample" in line and "with_entry_score" in line:
            parts = line.split()
            try:
                if "sample" in parts:
                    i = parts.index("sample")
                    if i + 1 < len(parts):
                        attr_sample = int(parts[i + 1])
                if "with_entry_score" in parts:
                    j = parts.index("with_entry_score")
                    if j + 1 < len(parts):
                        attr_with_score = int(parts[j + 1])
            except (ValueError, IndexError):
                pass

    proof_lines = [
        "# Exit quality emission proof (2026-02-18)",
        "",
        "## A) Paper run state (no overlay)",
        "```json",
        (out_state or "").strip()[:600],
        "```",
        "",
        "## B) Last exit_attribution record ts",
        (out_last or "").strip(),
        "",
        "## C) Newest 500 exit_attribution lines",
        "```",
        (out_sample or "").strip(),
        "```",
        "",
        "- **sample_records:** " + str(sample_records),
        "- **with_exit_quality_metrics:** " + str(with_eqm),
        "",
        "## Example exit_quality_metrics (1–2 redacted)",
        "```",
        json.dumps(examples_eqm[:2], indent=2) if examples_eqm else "(none yet)",
        "```",
        "",
        "## Attribution: last 200 lines, entry_score in context or top-level",
        "```",
        (out_attr or "").strip(),
        "```",
        "",
        "- **sample:** " + str(attr_sample) + ", **with_entry_score:** " + str(attr_with_score),
        "",
    ]
    (OUT_DIR / f"{DATE}_exit_quality_emission_proof.md").write_text("\n".join(proof_lines), encoding="utf-8")
    print("Wrote", OUT_DIR / f"{DATE}_exit_quality_emission_proof.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
