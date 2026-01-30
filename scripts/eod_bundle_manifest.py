#!/usr/bin/env python3
"""
EOD bundle manifest + integrity gate.

Memory Bank §5.5: Canonical 8-file bundle. Reports MUST use droplet production data (Memory Bank §3.2).
This script validates existence, non-empty, byte_size, line_count (jsonl), sha256 for each required file.
Outputs: reports/eod_manifests/EOD_MANIFEST_<DATE>.json and .md.
Exits non-zero if any required file is missing or empty (hard contract gate).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Canonical 8-file bundle (Memory Bank §5.5, docs/EOD_DATA_PIPELINE.md)
BUNDLE_FILES = [
    ("logs/attribution.jsonl", "attribution", True),
    ("logs/exit_attribution.jsonl", "exit_attribution", True),
    ("logs/master_trade_log.jsonl", "master_trade_log", True),
    ("state/blocked_trades.jsonl", "blocked_trades", True),
    ("state/daily_start_equity.json", "daily_start_equity", False),
    ("state/peak_equity.json", "peak_equity", False),
    ("state/signal_weights.json", "signal_weights", False),
    ("state/daily_universe_v2.json", "daily_universe_v2", False),
]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _line_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8", errors="replace") as f:
        return sum(1 for _ in f)


def run(base_dir: Path, target_date: str) -> dict:
    base_dir = base_dir.resolve()
    manifest_dir = base_dir / "reports" / "eod_manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)

    now_iso = datetime.now(timezone.utc).isoformat()
    results: list[dict] = []
    all_ok = True

    for rel_path, name, is_jsonl in BUNDLE_FILES:
        full = base_dir / rel_path
        exists = full.exists()
        if not exists:
            results.append({
                "path": rel_path,
                "name": name,
                "exists": False,
                "non_empty": False,
                "byte_size": 0,
                "line_count": 0,
                "sha256": None,
                "ok": False,
            })
            all_ok = False
            continue

        st = full.stat()
        byte_size = st.st_size
        non_empty = byte_size > 0
        line_count = _line_count(full) if is_jsonl else (1 if non_empty else 0)
        sha = _sha256(full) if non_empty else None
        ok = non_empty
        if not ok:
            all_ok = False

        results.append({
            "path": rel_path,
            "name": name,
            "exists": True,
            "non_empty": non_empty,
            "byte_size": byte_size,
            "line_count": line_count,
            "sha256": sha,
            "ok": ok,
        })

    payload = {
        "generated_utc": now_iso,
        "target_date": target_date,
        "base_dir": str(base_dir),
        "memory_bank": "§5.5 EOD Data Pipeline (Canonical); §3.2 Data Source Rule (reports use droplet production data)",
        "all_required_ok": all_ok,
        "files": results,
    }

    out_json = manifest_dir / f"EOD_MANIFEST_{target_date}.json"
    out_md = manifest_dir / f"EOD_MANIFEST_{target_date}.md"
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    # Markdown report
    lines = [
        f"# EOD Bundle Manifest — {target_date}",
        "",
        f"**Generated:** {now_iso}",
        f"**Base dir:** `{base_dir}`",
        "",
        "**Memory Bank:** §5.5 EOD Data Pipeline (Canonical); §3.2 Data Source Rule.",
        "",
        f"**Integrity:** {'PASS (all required files present and non-empty)' if all_ok else 'FAIL (missing or empty required file)'}",
        "",
        "## Files",
        "",
        "| Path | Exists | Non-empty | Bytes | Lines | SHA256 (first 16) | OK |",
        "|------|--------|-----------|-------|-------|-------------------|----|",
    ]
    for r in results:
        sha_short = (r["sha256"] or "")[:16] if r.get("sha256") else "—"
        lines.append(
            f"| {r['path']} | {r['exists']} | {r['non_empty']} | {r['byte_size']} | {r['line_count']} | {sha_short} | {r['ok']} |"
        )
    lines.extend(["", "---", ""])
    with out_md.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="EOD bundle manifest + integrity gate")
    parser.add_argument("--date", default=None, help="Target date YYYY-MM-DD (default: today UTC)")
    parser.add_argument("--base-dir", default=None, help="Repo root (default: parent of scripts/)")
    args = parser.parse_args()

    if args.base_dir:
        base_dir = Path(args.base_dir)
    else:
        base_dir = Path(__file__).resolve().parents[1]
    target_date = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    payload = run(base_dir, target_date)
    if not payload.get("all_required_ok"):
        print("EOD manifest FAIL: one or more required bundle files missing or empty.", file=sys.stderr)
        return 1
    print(f"EOD manifest PASS: reports/eod_manifests/EOD_MANIFEST_{target_date}.json|.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
