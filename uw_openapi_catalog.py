#!/usr/bin/env python3
"""
UW OpenAPI catalog (no external YAML deps).

UW hosts an OpenAPI YAML at:
  https://api.unusualwhales.com/api/openapi

The docs UI (Stoplight Elements) loads that document directly. We "save and use it"
by fetching the YAML and extracting a minimal catalog of operations we care about
without introducing PyYAML as a dependency.

We only parse the `paths:` section with a simple indentation-based scanner.
This is sufficient to discover exact REST paths/methods/tags/operationIds.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests


OPENAPI_URL = "https://api.unusualwhales.com/api/openapi"
DEFAULT_CACHE_PATH = Path("state/uw_openapi_catalog.json")


@dataclass
class Operation:
    path: str
    method: str
    operation_id: Optional[str]
    tags: List[str]
    # Best-effort parameter name list (query/path params) if present in YAML.
    parameters: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "method": self.method,
            "operation_id": self.operation_id,
            "tags": self.tags,
            "parameters": self.parameters,
        }


def fetch_openapi_yaml(timeout: float = 30.0) -> str:
    r = requests.get(OPENAPI_URL, timeout=timeout)
    r.raise_for_status()
    return r.text


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def parse_openapi_paths(yaml_text: str) -> List[Operation]:
    """
    Minimal parser for:
      paths:
        /api/foo:
          get:
            tags:
              - Something
            operationId: PublicApi.X.y
            parameters:
              - name: symbol
              - name: ticker
    """
    lines = yaml_text.splitlines()

    # Find "paths:" at column 0
    start = None
    for i, ln in enumerate(lines):
        if ln.strip() == "paths:" and _indent(ln) == 0:
            start = i + 1
            break
    if start is None:
        return []

    ops: List[Operation] = []
    current_path: Optional[str] = None
    current_method: Optional[str] = None
    current_tags: List[str] = []
    current_op_id: Optional[str] = None
    current_params: List[str] = []
    in_tags = False
    in_params = False

    def flush():
        nonlocal current_method, current_tags, current_op_id, current_params
        if current_path and current_method:
            ops.append(
                Operation(
                    path=current_path,
                    method=current_method,
                    operation_id=current_op_id,
                    tags=list(current_tags),
                    parameters=list(dict.fromkeys(current_params)),
                )
            )
        current_method = None
        current_tags = []
        current_op_id = None
        current_params = []

    i = start
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            i += 1
            continue

        ind = _indent(ln)
        # Exit paths section if we return to column 0 and hit another top-level key.
        if ind == 0 and ln.rstrip().endswith(":") and ln.strip() != "paths:":
            flush()
            break

        # Path line: indent 2, ends with colon, starts with /
        if ind == 2 and ln.strip().endswith(":") and ln.strip().startswith("/"):
            flush()
            current_path = ln.strip()[:-1]
            i += 1
            continue

        # Method line: indent 4
        if ind == 4 and ln.strip().endswith(":"):
            m = ln.strip()[:-1].lower()
            if m in ("get", "post", "put", "delete", "patch", "head", "options"):
                flush()
                current_method = m
                in_tags = False
                in_params = False
                i += 1
                continue

        # Fields under method: indent >= 6
        if current_path and current_method:
            s = ln.strip()
            if ind == 6 and s == "tags:":
                in_tags = True
                in_params = False
                i += 1
                continue
            if ind == 6 and s == "parameters:":
                in_params = True
                in_tags = False
                i += 1
                continue
            if ind == 6 and s.lower().startswith("operationid:"):
                # operationId: Foo
                current_op_id = s.split(":", 1)[1].strip() or None
                i += 1
                continue
            if in_tags:
                # tag list items are typically indent 8: "- Tag"
                if ind >= 8 and s.startswith("- "):
                    current_tags.append(s[2:].strip())
                    i += 1
                    continue
                # tags section ended
                if ind <= 6:
                    in_tags = False
            if in_params:
                # parameters list items have nested keys, easiest is to capture "- name: X"
                if "name:" in s:
                    # Might be "- name: symbol" or "name: symbol"
                    after = s.split("name:", 1)[1].strip()
                    if after:
                        # remove quotes if present
                        if after[0] in ("'", '"') and after[-1] == after[0]:
                            after = after[1:-1]
                        current_params.append(after)
                # parameters section ends when indent returns to 6 or less with a new key
                if ind == 6 and s.endswith(":") and s not in ("parameters:",):
                    in_params = False

        i += 1

    flush()
    # Remove entries with missing method/path
    return [o for o in ops if o.path and o.method]


def build_catalog(ops: List[Operation]) -> Dict[str, Any]:
    return {
        "fetched_from": OPENAPI_URL,
        "fetched_ts": int(time.time()),
        "operations": [o.to_dict() for o in ops],
    }


def save_catalog(catalog: Dict[str, Any], path: Path = DEFAULT_CACHE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(catalog, indent=2))
    tmp.replace(path)


def load_catalog(path: Path = DEFAULT_CACHE_PATH) -> Optional[Dict[str, Any]]:
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        return None
    return None


def refresh_catalog_if_needed(
    path: Path = DEFAULT_CACHE_PATH,
    max_age_sec: int = 7 * 86400,
) -> Dict[str, Any]:
    existing = load_catalog(path)
    if existing:
        ts = existing.get("fetched_ts", 0)
        if isinstance(ts, int) and ts > 0 and (time.time() - ts) < max_age_sec:
            return existing
    yml = fetch_openapi_yaml()
    ops = parse_openapi_paths(yml)
    catalog = build_catalog(ops)
    save_catalog(catalog, path)
    return catalog


def select_operations(catalog: Dict[str, Any], predicate) -> List[Dict[str, Any]]:
    out = []
    for op in catalog.get("operations", []):
        if not isinstance(op, dict):
            continue
        try:
            if predicate(op):
                out.append(op)
        except Exception:
            continue
    return out


def find_tagged_ops(catalog: Dict[str, Any], tag_substr: str) -> List[Dict[str, Any]]:
    t = tag_substr.lower()
    return select_operations(
        catalog,
        lambda op: any(isinstance(x, str) and t in x.lower() for x in (op.get("tags") or [])),
    )

