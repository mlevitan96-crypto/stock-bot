#!/usr/bin/env python3
"""
Parse direction_reconstruction_30d.jsonl and compute reconstruction_source breakdown.
Exit 0 if synthetic <= 10%; else write DIRECTION_REPLAY_BLOCKED_SYNTHETIC.md and exit 1.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

def main() -> int:
    base = Path(__file__).resolve().parents[2]
    path = base / "reports" / "replay" / "direction_reconstruction_30d.jsonl"
    blocked_path = base / "reports" / "board" / "DIRECTION_REPLAY_BLOCKED_SYNTHETIC.md"
    total = 0
    telemetry = 0
    synthetic = 0
    other = 0
    if not path.exists():
        print("ERROR: direction_reconstruction_30d.jsonl not found", file=sys.stderr)
        return 1
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
            total += 1
            src = (r.get("reconstruction_source") or "").strip().lower()
            if src == "telemetry":
                telemetry += 1
            elif "synthetic" in src or src == "synthetic_from_regime":
                synthetic += 1
            else:
                other += 1
        except Exception:
            continue
    pct_telemetry = 100.0 * telemetry / total if total else 0.0
    pct_synthetic = 100.0 * synthetic / total if total else 0.0
    print(f"total={total} telemetry={telemetry} ({pct_telemetry:.1f}%) synthetic={synthetic} ({pct_synthetic:.1f}%) other={other}")
    if total == 0:
        print("ERROR: no trades in reconstruction file", file=sys.stderr)
        return 1
    if pct_synthetic > 10.0:
        blocked_path.parent.mkdir(parents=True, exist_ok=True)
        blocked_path.write_text(
            "# Direction Replay — BLOCKED (synthetic > 10%)\n\n"
            f"**Reconstruction source breakdown:** total={total}, telemetry={telemetry} ({pct_telemetry:.1f}%), "
            f"synthetic={synthetic} ({pct_synthetic:.1f}%).\n\n"
            "**Why this replay is not actionable:** Direction components are derived from live telemetry (intel_snapshot_entry at entry) only when `direction_intel_embed` exists on exit_attribution. When missing, we fall back to synthetic reconstruction from `regime_at_entry`. If more than 10% of trades are synthetic, the scenario PnL (B/C/D/E) is driven by inferred rather than observed intelligence; promotion would be based on synthetic data.\n\n"
            "**What is missing:** Ensure directional intelligence telemetry is captured at entry (capture_entry_intel_telemetry) and that exit_attribution records include direction_intel_embed. Then re-run the 30d cohort so that most reconstructions use telemetry.\n\n"
            "**Action:** Do not promote any scenario from this run. Re-run after telemetry coverage is sufficient (synthetic <= 10%).\n",
            encoding="utf-8",
        )
        print(f"BLOCKED: synthetic {pct_synthetic:.1f}% > 10%. Wrote {blocked_path}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
