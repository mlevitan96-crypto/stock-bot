#!/usr/bin/env python3
"""
UW OpenAPI Spec Loader (endpoint allow-list)
===========================================

Goal:
- Provide a *single* authoritative list of UW endpoint paths from the official
  OpenAPI spec checked into this repo at `unusual_whales_api/api_spec.yaml`.

Design constraints:
- Avoid YAML dependencies: we only need the `paths:` keys, so we parse that section
  via indentation rules.
- Deterministic, side-effect free, safe to import.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Iterable, Set


ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = ROOT / "unusual_whales_api" / "api_spec.yaml"


def _extract_paths_from_openapi_yaml(text: str) -> Set[str]:
    """
    Extract top-level OpenAPI `paths` keys from YAML without needing a YAML parser.

    Assumptions (true for OpenAPI YAML):
    - `paths:` is a top-level key.
    - Each path key appears as `  /some/path:` (two-space indent under `paths:`).
    """
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].strip() == "paths:" and (len(lines[i]) - len(lines[i].lstrip(" "))) == 0:
            break
        i += 1
    if i >= len(lines):
        return set()

    out: Set[str] = set()
    # scan until next top-level key (indent 0)
    for j in range(i + 1, len(lines)):
        line = lines[j]
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent == 0:
            break
        # Path keys are like: "  /api/foo/bar:" (indent >= 2)
        s = line.strip()
        if s.startswith("/") and s.endswith(":"):
            out.add(s[:-1])
    return out


def _split_segments(path: str) -> list[str]:
    p = (path or "").strip()
    if not p.startswith("/"):
        p = "/" + p
    return [seg for seg in p.split("/") if seg]


def _is_param(seg: str) -> bool:
    s = (seg or "").strip()
    return s.startswith("{") and s.endswith("}") and len(s) >= 3


@lru_cache(maxsize=1)
def get_valid_uw_paths() -> set[str]:
    """
    Return the allow-list of valid UW endpoint paths (OpenAPI `paths` keys).
    """
    if not SPEC_PATH.exists():
        return set()
    text = SPEC_PATH.read_text(encoding="utf-8", errors="replace")
    return set(_extract_paths_from_openapi_yaml(text))


@lru_cache(maxsize=1)
def _compiled_templates() -> list[list[str]]:
    # Keep templates as segment lists for cheap matching.
    return [_split_segments(p) for p in get_valid_uw_paths()]


def is_valid_uw_path(candidate: str) -> bool:
    """
    Validate a candidate path against the OpenAPI `paths` set.

    Supports templated paths like `/api/stock/{symbol}` by treating `{...}` segments
    as wildcards.
    """
    if not candidate:
        return False
    cand = candidate.strip()
    if cand.startswith("http://") or cand.startswith("https://"):
        # Caller should pass paths, but be defensive.
        try:
            from urllib.parse import urlparse

            cand = urlparse(cand).path or cand
        except Exception:
            return False
    if not cand.startswith("/"):
        cand = "/" + cand

    valid = get_valid_uw_paths()
    if cand in valid:
        return True

    cand_segs = _split_segments(cand)
    for tmpl in _compiled_templates():
        if len(tmpl) != len(cand_segs):
            continue
        ok = True
        for tseg, cseg in zip(tmpl, cand_segs):
            if _is_param(tseg) or _is_param(cseg):
                if not cseg:
                    ok = False
                    break
                continue
            if tseg != cseg:
                ok = False
                break
        if ok:
            return True
    return False

