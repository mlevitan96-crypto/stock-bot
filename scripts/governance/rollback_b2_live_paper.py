#!/usr/bin/env python3
"""
Rollback B2 from live_paper to shadow-only (config + optional droplet).
Updates config/b2_governance.json to shadow; writes reports/audit/B2_ROLLBACK_<timestamp>.md.
For droplet: set FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=false, restart (or run scripts/audit/b2_rollback_drill_on_droplet.py).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main() -> int:
    audit_dir = REPO / "reports" / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    cfg_path = REPO / "config" / "b2_governance.json"

    reason = "rollback drill"
    if len(sys.argv) > 1 and sys.argv[1].strip():
        reason = sys.argv[1].strip()

    previous = {"b2_mode": "live_paper", "b2_shadow_enabled": False, "b2_live_paper_enabled": True, "b2_live_enabled": False}
    if cfg_path.exists():
        try:
            previous = json.loads(cfg_path.read_text(encoding="utf-8"))
            previous = {k: previous[k] for k in ("b2_mode", "b2_shadow_enabled", "b2_live_paper_enabled", "b2_live_enabled") if k in previous}
        except Exception:
            pass

    new_config = {
        "_comment": "B2 rolled back to shadow-only. Re-enable live_paper via config + deploy or env on droplet.",
        "b2_mode": "shadow",
        "b2_shadow_enabled": True,
        "b2_live_paper_enabled": False,
        "b2_live_enabled": False,
        "notes": {
            "shadow": "Offline analysis only (scripts/shadow/run_b2_shadow.py).",
            "live_paper": "Runtime: suppress early signal_decay. Set b2_live_paper_enabled true to re-enable.",
            "live": "Future: real capital. Must remain false.",
        },
    }
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(json.dumps(new_config, indent=2), encoding="utf-8")

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    rollback_md = audit_dir / f"B2_ROLLBACK_{ts}.md"
    rollback_md.write_text(
        f"# B2 Rollback\n\n"
        f"**Generated (UTC):** {datetime.now(timezone.utc).isoformat()}\n\n"
        f"- **reason:** {reason}\n"
        f"- **previous mode:** {previous.get('b2_mode', 'unknown')} (shadow={previous.get('b2_shadow_enabled')}, live_paper={previous.get('b2_live_paper_enabled')}, live={previous.get('b2_live_enabled')})\n"
        f"- **new mode:** shadow (shadow=ON, live_paper=OFF, live=OFF)\n\n"
        f"Config updated: `config/b2_governance.json`. On droplet: set `FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT=false`, restart stock-bot.\n",
        encoding="utf-8",
    )
    print(f"Rollback written: {rollback_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
