#!/usr/bin/env python3
"""
Static UW endpoint auditor (no more 404s, no hallucinated URLs).

Strategy:
- Scan *tracked files* (`git ls-files`) to avoid untracked workspace noise.
- Extract UW endpoint candidates from **Python code paths that actually call UW**
  (e.g., `uw_get(...)`, `uw_http_get(...)`, UW endpoint policy `path="..."`).
- Validate each extracted endpoint against the official OpenAPI spec in
  `unusual_whales_api/api_spec.yaml`.

Exit codes:
- 0: OK
- 1: invalid endpoints found or spec missing/unreadable
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Set

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.uw.uw_spec_loader import SPEC_PATH, get_valid_uw_paths, is_valid_uw_path  # noqa: E402


ENDPOINT_RE = re.compile(r"""(?P<q>["'])(?P<path>(?:https?://api\.unusualwhales\.com)?/api/[A-Za-z0-9_\-/{}/\.]+)(?P=q)""")


@dataclass(frozen=True)
class Finding:
    file: str
    line: int
    endpoint: str


def _tracked_files() -> List[Path]:
    try:
        out = subprocess.check_output(["git", "ls-files"], cwd=str(ROOT), text=True)
    except Exception:
        return []
    paths: List[Path] = []
    for rel in out.splitlines():
        rel = rel.strip()
        if not rel:
            continue
        p = ROOT / rel
        if p.exists() and p.is_file():
            paths.append(p)
    return paths


def _normalize_to_path(s: str) -> str:
    s = (s or "").strip()
    if not s:
        return ""
    if s.startswith("http://") or s.startswith("https://"):
        try:
            from urllib.parse import urlparse

            s = urlparse(s).path or s
        except Exception:
            return ""
    if not s.startswith("/"):
        s = "/" + s
    return s


def _py_ast_candidates(text: str) -> List[str]:
    """
    Extract UW endpoint strings from Python AST call-sites.
    Only consider call-sites that actually hit UW (`uw_get`, `uw_http_get`).
    """
    try:
        import ast

        tree = ast.parse(text)
    except Exception:
        return []

    out: List[str] = []

    def _fn_name(node) -> str:
        try:
            if isinstance(node, ast.Name):
                return str(node.id)
            if isinstance(node, ast.Attribute):
                return str(node.attr)
        except Exception:
            return ""
        return ""

    def _extract_str(node) -> str:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if hasattr(ast, "JoinedStr") and isinstance(node, ast.JoinedStr):
            # f-string: keep literals and convert {...} to {param}
            parts: List[str] = []
            for v in node.values:
                if isinstance(v, ast.Constant) and isinstance(v.value, str):
                    parts.append(v.value)
                else:
                    parts.append("{param}")
            return "".join(parts)
        return ""

    for n in ast.walk(tree):
        if not isinstance(n, ast.Call) or not n.args:
            continue
        name = _fn_name(n.func)
        if name not in ("uw_get", "uw_http_get"):
            continue
        s = _extract_str(n.args[0])
        if s and "/api/" in s:
            out.append(_normalize_to_path(s))
    return [x for x in out if x]


def _scan_file(path: Path) -> List[Finding]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []
    rel = str(path.relative_to(ROOT)).replace("\\", "/")

    # Python-only: enforce no hallucinated UW endpoints in actual UW call-sites.
    if not rel.endswith(".py"):
        return []

    # Scope to UW-related python only (avoid false positives from internal dashboard endpoints).
    uw_related = (
        rel.startswith("src/uw/")
        or rel.startswith("config/uw_")
        or rel.startswith("scripts/") and ("uw" in rel or "premarket" in rel or "postmarket" in rel)
        or rel.endswith("uw_flow_daemon.py")
        or rel.endswith("main.py")
        or "/uw" in rel
        or rel.endswith("uw_client.py")
    )
    if not uw_related:
        return []

    findings: List[Finding] = []

    # AST-based (primary)
    for ep in _py_ast_candidates(text):
        findings.append(Finding(file=rel, line=0, endpoint=ep))

    # Regex-based fallback: allow UW policy/config paths even when not in direct uw_get call-sites.
    if rel.startswith("config/uw_") or rel.startswith("src/uw/"):
        for m in ENDPOINT_RE.finditer(text):
            ep = _normalize_to_path(m.group("path") or "")
            if ep:
                findings.append(Finding(file=rel, line=0, endpoint=ep))

    return findings


def main() -> int:
    if not SPEC_PATH.exists():
        print(f"ERROR: missing UW OpenAPI spec at {SPEC_PATH}", file=sys.stderr)
        return 1

    valid = get_valid_uw_paths()
    if len(valid) < 50:
        print(f"ERROR: UW OpenAPI spec appears invalid (paths={len(valid)} < 50)", file=sys.stderr)
        return 1

    files = _tracked_files()
    if not files:
        print("ERROR: could not enumerate tracked files (git ls-files failed?)", file=sys.stderr)
        return 1

    all_findings: List[Finding] = []
    for p in files:
        all_findings.extend(_scan_file(p))

    bad: List[Finding] = []
    for f in all_findings:
        if not is_valid_uw_path(f.endpoint):
            bad.append(f)

    # Report
    print(f"UW_SPEC_PATH={SPEC_PATH}")
    print(f"UW_SPEC_PATHS={len(valid)}")
    print(f"UW_ENDPOINT_CANDIDATES_FOUND={len(all_findings)}")

    if bad:
        print("\nINVALID_ENDPOINTS:")
        for f in bad[:200]:
            loc = f"{f.file}:{f.line}" if f.line else f.file
            print(f"- {loc} -> {f.endpoint}")
        if len(bad) > 200:
            print(f"... and {len(bad) - 200} more")
        return 1

    print("UW_ENDPOINT_AUDIT_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

