#!/usr/bin/env python3
"""
Signal normalization helpers (additive, schema-only)
===================================================

Goal:
- Ensure trade logs ALWAYS serialize `signals` as a JSON array (list), never as:
  - Python set
  - stringified set (e.g. "{'flow', 'darkpool'}")
  - None

This module is intentionally pure/side-effect-free and safe to call from
live/shadow execution paths and telemetry builders.
"""

from __future__ import annotations

from typing import Any, List


def normalize_signals(sig: Any) -> List[str]:
    if sig is None:
        return []
    if isinstance(sig, list):
        # Preserve list ordering as provided (caller may sort).
        out: List[str] = []
        for x in sig:
            if x is None:
                continue
            s = str(x).strip()
            if s:
                out.append(s)
        return out
    if isinstance(sig, set):
        return sorted([str(x).strip() for x in sig if str(x).strip()])
    if isinstance(sig, str):
        s = sig.strip()
        # detect stringified set: "{'flow', 'darkpool'}"
        if s.startswith("{") and s.endswith("}"):
            inner = s[1:-1].strip()
            if not inner:
                return []
            parts = [p.strip().strip("'").strip('"') for p in inner.split(",")]
            return sorted([p for p in parts if p])
        # fallback: wrap string in list
        return [s] if s else []
    # fallback: wrap unknown type
    return [str(sig)]

