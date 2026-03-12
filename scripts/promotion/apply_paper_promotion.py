#!/usr/bin/env python3
"""
Apply paper promotion: resolve config by config_id from shortlist, write overlay, record applied.
Overlay is written to config/tuning/overlays/learning_promotion_${config_id}.json.
Activation: set GOVERNED_TUNING_CONFIG to that path and restart paper engine.
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply paper promotion for one config.")
    parser.add_argument("--config-id", required=True, help="Config ID to promote.")
    parser.add_argument("--intent", required=True, help="Path to PROMOTION_INTENT_${CONFIG_ID}_${DATE}.json.")
    parser.add_argument("--output", required=True, help="Output PROMOTION_APPLIED_${CONFIG_ID}_${DATE}.json path.")
    args = parser.parse_args()

    root = Path(os.getcwd())
    with open(root / args.intent, encoding="utf-8") as f:
        intent = json.load(f)
    date = intent.get("date", "")
    config_id = args.config_id

    # Resolve full config from shortlist: try intent date first, then any shortlist containing this config_id
    shadow_dir = root / "reports" / "shadow"
    shortlist_path = shadow_dir / f"PROMOTION_SHORTLIST_{date}.promotable.backfill.json"
    if not shortlist_path.exists():
        shortlist_path = shadow_dir / f"PROMOTION_SHORTLIST_{date}.promotable.json"
    if not shortlist_path.exists():
        # Find any shortlist that contains this config_id (e.g. promotion date differs from shortlist date)
        for path in sorted(shadow_dir.glob("PROMOTION_SHORTLIST_*.promotable.backfill.json"), reverse=True):
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                if any(e.get("config_id") == config_id for e in data.get("shortlist", [])):
                    shortlist_path = path
                    break
            except Exception:
                continue
        if not shortlist_path.exists():
            for path in sorted(shadow_dir.glob("PROMOTION_SHORTLIST_*.promotable.json"), reverse=True):
                try:
                    with open(path, encoding="utf-8") as f:
                        data = json.load(f)
                    if any(e.get("config_id") == config_id for e in data.get("shortlist", [])):
                        shortlist_path = path
                        break
                except Exception:
                    continue
    if not shortlist_path.exists():
        raise SystemExit(f"No shortlist found containing config_id {config_id} (tried date {date} and scan).")
    with open(shortlist_path, encoding="utf-8") as f:
        shortlist_data = json.load(f)
    shortlist = shortlist_data.get("shortlist", [])
    entry = next((e for e in shortlist if e.get("config_id") == config_id), None)
    if not entry:
        raise SystemExit(f"Config {config_id} not found in shortlist at {shortlist_path}")

    # Overlay path under config/tuning/overlays
    overlay_dir = root / "config" / "tuning" / "overlays"
    overlay_dir.mkdir(parents=True, exist_ok=True)
    overlay_path = overlay_dir / f"learning_promotion_{config_id}.json"
    overlay = {
        "version": f"learning_promotion_{config_id}",
        "config_id": config_id,
        "meta": {"mode": "paper", "intent": intent.get("intent"), "date": date},
        "weights": entry.get("config", {}),
    }
    with open(overlay_path, "w", encoding="utf-8") as f:
        json.dump(overlay, f, indent=2)
    print(f"Wrote overlay: {overlay_path}")

    applied = {
        "config_id": config_id,
        "date": date,
        "intent_path": args.intent,
        "overlay_path": str(overlay_path.relative_to(root)),
        "applied_at": datetime.now(timezone.utc).isoformat(),
        "mode": "paper",
        "instruction": f"Set GOVERNED_TUNING_CONFIG={overlay_path.relative_to(root)} and restart paper engine to activate.",
    }

    out_path = root / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(applied, f, indent=2)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
