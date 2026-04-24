#!/usr/bin/env python3
"""
Shadow: Inventory all signal-related gates and weights from config.
Produces a flat list of gate-like structures (boolean flags, thresholds, weights) for classification.
Read-only scan; no config changes.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _load_json(p: Path) -> dict:
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _load_yaml(p: Path) -> dict:
    if not p.exists():
        return {}
    try:
        import yaml
        return yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def _flatten(obj: Any, prefix: str, out: list[dict], source: str) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            key_path = f"{prefix}.{k}" if prefix else k
            if isinstance(v, (dict, list)) and k not in ("modes", "contract", "notes"):
                _flatten(v, key_path, out, source)
            else:
                gate_type = "boolean" if isinstance(v, bool) else "threshold" if isinstance(v, (int, float)) else "weight"
                if isinstance(v, dict):
                    gate_type = "object"
                out.append({
                    "source": source,
                    "key_path": key_path,
                    "type": gate_type,
                    "value": v,
                })
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _flatten(v, f"{prefix}[{i}]", out, source)


def inventory(config_dir: Path) -> list[dict]:
    config_dir = config_dir.resolve()
    gates: list[dict] = []

    # exit_regimes.json: fire_sale, let_it_breathe (enabled + thresholds)
    er = _load_json(config_dir / "exit_regimes.json")
    for regime, opts in (er or {}).items():
        if isinstance(opts, dict):
            for k, v in opts.items():
                gates.append({
                    "source": "exit_regimes.json",
                    "key_path": f"exit_regimes.{regime}.{k}",
                    "type": "boolean" if isinstance(v, bool) else "threshold",
                    "value": v,
                })

    # mode_governance.json: modes.*.risk.*_enabled, exits.*_enabled
    mg = _load_json(config_dir / "mode_governance.json")
    for mode, mode_cfg in (mg.get("modes") or {}).items():
        if not isinstance(mode_cfg, dict):
            continue
        for section, section_cfg in mode_cfg.items():
            if not isinstance(section_cfg, dict):
                continue
            for k, v in section_cfg.items():
                gates.append({
                    "source": "mode_governance.json",
                    "key_path": f"modes.{mode}.{section}.{k}",
                    "type": "boolean" if isinstance(v, bool) else "threshold",
                    "value": v,
                })

    # tuning/schema.json exit_weights + entry_thresholds (schema only; actual values from active/overlays)
    schema = _load_json(config_dir / "tuning" / "schema.json")
    for prop, spec in (schema.get("properties") or {}).items():
        if prop in ("exit_weights", "entry_thresholds") and isinstance(spec, dict):
            for sub in (spec.get("properties") or {}).keys():
                gates.append({
                    "source": "tuning/schema.json",
                    "key_path": f"tuning.{prop}.{sub}",
                    "type": "weight",
                    "value": None,
                })

    # tuning/active.json or overlays: concrete exit_weights
    active = _load_json(config_dir / "tuning" / "active.json")
    for k, v in (active.get("exit_weights") or {}).items():
        gates.append({
            "source": "tuning/active.json",
            "key_path": f"exit_weights.{k}",
            "type": "weight",
            "value": v,
        })

    # policy_variants: signal_decay (decay_ratio_threshold, disable_decay_*), live_safety, auto_rollback
    pv = _load_json(config_dir / "policy_variants.json")
    for variant, opts in (pv or {}).items():
        if variant in ("live", "paper"):
            continue
        if not isinstance(opts, dict):
            continue
        for section, section_cfg in opts.items():
            if not isinstance(section_cfg, dict):
                continue
            for k, v in section_cfg.items():
                gates.append({
                    "source": "policy_variants.json",
                    "key_path": f"policy_variants.{variant}.{section}.{k}",
                    "type": "boolean" if isinstance(v, bool) else "threshold",
                    "value": v,
                })

    # uw_micro_signal_weights.yaml: already weights
    uw = _load_yaml(config_dir / "uw_micro_signal_weights.yaml")
    for section, section_cfg in (uw or {}).items():
        if section == "version" or not isinstance(section_cfg, dict):
            continue
        for k, v in section_cfg.items():
            if isinstance(v, (int, float)):
                gates.append({
                    "source": "uw_micro_signal_weights.yaml",
                    "key_path": f"uw_micro.{section}.{k}",
                    "type": "weight",
                    "value": v,
                })

    return gates


def main() -> int:
    ap = argparse.ArgumentParser(description="Inventory signal gates from config")
    ap.add_argument("--config-dir", default="config", help="Config directory (repo root relative)")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    config_dir = Path(args.config_dir)
    if not config_dir.exists():
        print(f"Config dir missing: {config_dir}", file=sys.stderr)
        return 2

    gates = inventory(config_dir)
    out = {
        "config_dir": str(config_dir.resolve()),
        "gate_count": len(gates),
        "gates": gates,
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("Inventoried", len(gates), "gates")
    return 0


if __name__ == "__main__":
    sys.exit(main())
